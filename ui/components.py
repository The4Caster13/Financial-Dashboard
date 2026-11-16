from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.exceptions import PreventUpdate

from ui import theme


def live_indicator() -> html.Div:
    return html.Div(
        [
            html.Span(className="live-dot"),
            html.Span("Live"),
            html.Span(f" · updated {dt.datetime.now().strftime('%H:%M:%S')}", className="stat-sub"),
        ],
        className="live-indicator",
    )


def format_number(value, kind: str = "number", decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if kind == "percent":
        return f"{value * 100:.{decimals}f}%"
    if kind == "percent_raw":
        return f"{value:.{decimals}f}%"
    if kind == "compact":
        for suffix, threshold in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
            if abs(value) >= threshold:
                return f"{value / threshold:.{decimals}f}{suffix}"
        return f"{value:.{decimals}f}"
    if kind == "price":
        return f"${value:,.{decimals}f}"
    return f"{value:,.{decimals}f}"


def delta_badge(value, pct: bool = True, decimals: int = 2) -> html.Span:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return html.Span("—", className="delta-badge delta-flat")
    arrow = "▲" if value >= 0 else "▼"
    css_class = "delta-badge delta-up" if value >= 0 else "delta-badge delta-down"
    text = f"{arrow} {abs(value):.{decimals}f}{'%' if pct else ''}"
    return html.Span(text, className=css_class)


def stat_card(label: str, value: str, delta=None, sub: str | None = None) -> html.Div:
    children = [
        html.Div(label, className="stat-label"),
        html.Div(value, className="stat-value"),
    ]
    footer = []
    if delta is not None:
        footer.append(delta)
    if sub:
        footer.append(html.Span(sub, className="stat-sub"))
    if footer:
        children.append(html.Div(footer, className="stat-footer"))
    return html.Div(children, className="stat-card")


def error_message(message: str) -> html.Div:
    return html.Div(
        [html.Span("⚠", className="error-icon"), html.Span(message)],
        className="error-message",
    )


def loading(component_id: str, children) -> dcc.Loading:
    return dcc.Loading(id=f"{component_id}-loading", type="circle", color=theme.CATEGORICAL[0], children=children)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str = theme.CATEGORICAL[0],
    fill: bool = False,
    y_title: str | None = None,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[y],
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy" if fill else None,
            fillcolor=theme.with_alpha(color, 0.12) if fill else None,
            hovertemplate="%{x|%b %d, %Y}<br><b>%{y:,.2f}</b><extra></extra>",
        )
    )
    layout = dict(theme.PLOTLY_LAYOUT)
    fig.update_layout(**layout, showlegend=False, hovermode="x unified")
    if y_title:
        fig.update_yaxes(title_text=y_title)
    return fig


def multi_line_chart(series: dict[str, pd.DataFrame], x: str, y: str, y_title: str | None = None) -> go.Figure:
    fig = go.Figure()
    for i, (name, df) in enumerate(series.items()):
        color = theme.CATEGORICAL[i % len(theme.CATEGORICAL)]
        fig.add_trace(
            go.Scatter(
                x=df[x], y=df[y], mode="lines", name=name,
                line=dict(color=color, width=2),
                hovertemplate=f"{name}<br>%{{x|%b %d, %Y}}<br><b>%{{y:,.2f}}</b><extra></extra>",
            )
        )
    layout = dict(theme.PLOTLY_LAYOUT)
    fig.update_layout(**layout, hovermode="x unified")
    if y_title:
        fig.update_yaxes(title_text=y_title)
    return fig


def bar_chart(
    labels: list[str],
    values: list[float],
    highlight: str | None = None,
    orientation: str = "v",
    value_suffix: str = "",
) -> go.Figure:
    colors = [
        theme.CATEGORICAL[0] if lbl != highlight else theme.STATUS_WARNING
        for lbl in labels
    ]
    fig = go.Figure()
    if orientation == "h":
        fig.add_trace(go.Bar(
            y=labels, x=values, orientation="h", marker_color=colors,
            text=[f"{v:,.2f}{value_suffix}" if pd.notna(v) else "—" for v in values],
            textposition="outside", textfont=dict(color=theme.TEXT_SECONDARY),
            hovertemplate="%{y}<br><b>%{x:,.2f}</b><extra></extra>",
        ))
    else:
        fig.add_trace(go.Bar(
            x=labels, y=values, marker_color=colors,
            text=[f"{v:,.2f}{value_suffix}" if pd.notna(v) else "—" for v in values],
            textposition="outside", textfont=dict(color=theme.TEXT_SECONDARY),
            hovertemplate="%{x}<br><b>%{y:,.2f}</b><extra></extra>",
        ))
    layout = dict(theme.PLOTLY_LAYOUT)
    fig.update_layout(**layout, showlegend=False)
    return fig


def data_table(
    df: pd.DataFrame,
    table_id: str,
    page_size: int = 15,
    numeric_cols: list[str] | None = None,
    markdown_cols: list[str] | None = None,
):
    numeric_cols = numeric_cols or []
    markdown_cols = markdown_cols or []
    columns = []
    for col in df.columns:
        col_def = {"name": str(col).replace("_", " ").title(), "id": str(col)}
        if col in numeric_cols:
            col_def["type"] = "numeric"
        if col in markdown_cols:
            col_def["presentation"] = "markdown"
        columns.append(col_def)
    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=df.to_dict("records"),
        page_size=page_size,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": theme.PAGE_PLANE,
            "color": theme.TEXT_MUTED,
            "fontWeight": "600",
            "border": "none",
            "borderBottom": f"1px solid {theme.GRIDLINE}",
            "textTransform": "uppercase",
            "fontSize": "11px",
            "letterSpacing": "0.04em",
        },
        style_cell={
            "backgroundColor": theme.SURFACE,
            "color": theme.TEXT_SECONDARY,
            "border": "none",
            "borderBottom": f"1px solid {theme.GRIDLINE}",
            "padding": "8px 12px",
            "fontSize": "13px",
            "fontFamily": "system-ui, -apple-system, 'Segoe UI', sans-serif",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#1e1e1d"},
        ],
        style_cell_conditional=[
            {"if": {"column_id": c}, "fontVariantNumeric": "tabular-nums", "textAlign": "right"}
            for c in numeric_cols
        ],
    )


def format_display_df(df: pd.DataFrame, formats: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    for col, kind in formats.items():
        if col in out.columns:
            out[col] = out[col].apply(lambda v: format_number(v, kind))
    return out


def financial_statement_table(df: pd.DataFrame, table_id: str) -> dash_table.DataTable:
    working = df.copy()
    period_col = "period_ending" if "period_ending" in working.columns else working.columns[0]
    periods = working[period_col].astype(str).tolist()
    working = working.drop(columns=[c for c in ["period_ending", "fiscal_period", "fiscal_year"] if c in working.columns])
    working = working.select_dtypes(include="number")
    transposed = working.T
    transposed.columns = periods
    transposed.insert(0, "Line Item", [str(i).replace("_", " ").title() for i in transposed.index])
    for col in periods:
        transposed[col] = transposed[col].apply(lambda v: format_number(v, "compact"))
    return data_table(transposed, table_id=table_id, page_size=40)


def _time_ago(published: pd.Timestamp) -> str:
    seconds = (pd.Timestamp.now(tz="UTC") - published).total_seconds()
    if seconds < 3600:
        return f"{max(int(seconds // 60), 1)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"


def news_list(df: pd.DataFrame, limit: int | None = None, compact: bool = False) -> list:
    items = []
    date_col = "date" if "date" in df.columns else None
    rows = df if limit is None else df.head(limit)
    for _, row in rows.iterrows():
        title = row.get("title", "Untitled")
        url = row.get("url")
        source = row.get("source") or row.get("provider")
        if compact:
            tag = row.get("tag")
            meta = [html.Span(tag, className="news-tag")] if isinstance(tag, str) else []
            meta.append(html.Span(" · ".join(v for v in [source, _time_ago(row["date"])] if v)))
            items.append(html.Div(
                [html.A(title, href=url, target="_blank", className="news-title", title=title),
                 html.Div(meta, className="news-meta")],
                className="news-item news-item--compact",
            ))
            continue
        date_str = ""
        if date_col and pd.notna(row.get(date_col)):
            date_str = pd.to_datetime(row[date_col]).strftime("%b %d, %Y %H:%M")
        meta = " · ".join(v for v in [source, date_str] if v)
        headline = html.A(title, href=url, target="_blank", className="news-title") if url else html.Span(title)
        items.append(
            html.Div(
                [headline, html.Div(meta, className="stat-sub")],
                style={"padding": "10px 0", "borderBottom": f"1px solid {theme.GRIDLINE}"},
            )
        )
    return items or [html.Div("No headlines available.", className="stat-sub")]


def section_header(title: str, subtitle: str | None = None) -> html.Div:
    children = [html.H2(title, className="section-title")]
    if subtitle:
        children.append(html.P(subtitle, className="section-subtitle"))
    return html.Div(children, className="section-header")


def movers_table(df: pd.DataFrame, detailed: bool = False) -> html.Table:
    cols = [("Symbol", None), ("Name", None), ("Price", "num"), ("Change", "num"), ("Volume", "num")]
    if detailed:
        cols += [("Mkt cap", "num"), ("52-wk range", "num"), ("Fwd P/E", "num")]
    head = html.Tr([html.Th(label, className=cls) for label, cls in cols])

    def num(value):
        return value if isinstance(value, (int, float)) and pd.notna(value) else None

    body = []
    for _, row in df.iterrows():
        symbol = row["symbol"]
        name = row["name"] if isinstance(row["name"], str) else ""
        pct = num(row.get("percent_change"))
        cells = [
            html.Td(dcc.Link(symbol, href=f"/company?symbol={symbol}", className="table-symbol")),
            html.Td(name, className="table-name", title=name),
            html.Td(format_number(row.get("price"), "price"), className="num"),
            html.Td(delta_badge(pct * 100 if pct is not None else None), className="num"),
            html.Td(format_number(row.get("volume"), "compact", 1), className="num"),
        ]
        if detailed:
            lo, hi = num(row.get("year_low")), num(row.get("year_high"))
            pe = num(row.get("pe_forward"))
            cells += [
                html.Td(format_number(row.get("market_cap"), "compact", 1), className="num"),
                html.Td(f"{format_number(lo, 'price')} – {format_number(hi, 'price')}" if lo and hi else "—",
                        className="num"),
                html.Td(format_number(pe, "number", 1) if pe is not None and pe > 0 else "—", className="num"),
            ]
        body.append(html.Tr(cells))
    return html.Table([html.Thead(head), html.Tbody(body)], className="dense-table")


def blank_figure(message: str = "", color: str = theme.STATUS_SERIOUS) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**theme.PLOTLY_LAYOUT)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    if message:
        fig.add_annotation(text=message, showarrow=False, font=dict(color=color, size=12))
    return fig


def _heatmap_color(pct: float | None) -> str:
    if pd.isna(pct):
        return theme.HEATMAP_MID
    pole = theme.HEATMAP_UP if pct >= 0 else theme.HEATMAP_DOWN
    t = min(abs(pct) / theme.HEATMAP_CLAMP, 1.0)
    mid = [int(theme.HEATMAP_MID[i:i + 2], 16) for i in (1, 3, 5)]
    end = [int(pole[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in zip(mid, end))


def heatmap_figure(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    df = df.copy()
    caps = df["market_cap"].dropna()
    df["size"] = df["market_cap"].fillna(caps.median()) if len(caps) else 1.0

    def pct_text(v) -> str:
        return f"{v:+.2f}%" if pd.notna(v) else "—"

    ids, labels, parents, values, colors, texts, hovers = [], [], [], [], [], [], []
    for sector, group in df.groupby("sector", sort=False):
        sector_move = pct_text(group["sector_pct"].iloc[0])
        ids.append(f"sector:{sector}")
        labels.append(f"{sector}  {sector_move}")
        parents.append("")
        values.append(float(group["size"].sum()))
        colors.append(theme.HEATMAP_PARENT)
        texts.append(labels[-1])
        hovers.append(f"<b>{sector}</b><br>Sector ETF {sector_move}<br>{len(group)} stocks")
    for _, row in df.iterrows():
        pct = row["pct_change"]
        ids.append(row["symbol"])
        labels.append(row["symbol"])
        parents.append(f"sector:{row['sector']}")
        values.append(float(row["size"]))
        colors.append(_heatmap_color(pct))
        texts.append(f"<b>{row['symbol']}</b><br>{pct_text(pct)}")
        hovers.append(
            f"<b>{row['symbol']}</b> · {row['name']}<br>{pct_text(pct)} · {format_number(row['last'], 'price')}"
            f"<br>Mkt cap {format_number(row['market_cap'], 'compact', 1)}<br><i>Click for company detail</i>"
        )

    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
        text=texts, texttemplate="%{text}", textposition="middle center",
        hovertext=hovers, hovertemplate="%{hovertext}<extra></extra>",
        marker=dict(colors=colors, line=dict(width=2, color=theme.SURFACE),
                    pad=dict(t=21 if compact else 24, l=1, r=1, b=1)),
        textfont=dict(color=theme.TEXT_PRIMARY, size=12),
        tiling=dict(pad=2),
        pathbar=dict(visible=not compact, textfont=dict(color=theme.TEXT_SECONDARY)),
        sort=True,
    ))
    fig.update_layout(
        paper_bgcolor=theme.SURFACE,
        margin=dict(l=0, r=0, t=0, b=0),
        font=theme.PLOTLY_LAYOUT["font"],
        hoverlabel=theme.PLOTLY_LAYOUT["hoverlabel"],
        uniformtext=dict(minsize=9, mode="hide"),
        uirevision="heatmap",
    )
    return fig


def company_route_from_heatmap_click(click: dict | None) -> tuple[str, str]:
    symbol = click["points"][0].get("id", "") if click else ""
    if not symbol or symbol.startswith("sector:"):
        raise PreventUpdate
    return "/company", f"?symbol={symbol}"

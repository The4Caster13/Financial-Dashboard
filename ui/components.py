"""Reusable Dash UI building blocks — stat cards, delta badges, charts, tables."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
from dash import dash_table, dcc, html

from ui import theme


def live_indicator() -> html.Div:
    """A small pulsing dot + timestamp, dropped at the top of auto-refreshing
    pages so it's visible this isn't a static snapshot."""
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
        # OpenBB's documented convention: these fields are a "normalized percent"
        # fraction (0.05 == 5%), so scale by 100 to display.
        return f"{value * 100:.{decimals}f}%"
    if kind == "percent_raw":
        # A handful of fields (notably yfinance's `metrics.dividend_yield`) are
        # already in percent units despite being documented as normalized —
        # an upstream inconsistency. Display as-is, no scaling.
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
            fillcolor=_with_alpha(color, 0.12) if fill else None,
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
            text=[f"{v:,.2f}{value_suffix}" if v is not None else "—" for v in values],
            textposition="outside", textfont=dict(color=theme.TEXT_SECONDARY),
            hovertemplate="%{y}<br><b>%{x:,.2f}</b><extra></extra>",
        ))
    else:
        fig.add_trace(go.Bar(
            x=labels, y=values, marker_color=colors,
            text=[f"{v:,.2f}{value_suffix}" if v is not None else "—" for v in values],
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
    """Return a copy with the given columns rendered through format_number —
    for tables where raw fractions/large numbers need human formatting."""
    out = df.copy()
    for col, kind in formats.items():
        if col in out.columns:
            out[col] = out[col].apply(lambda v: format_number(v, kind))
    return out


def financial_statement_table(df: pd.DataFrame, table_id: str) -> dash_table.DataTable:
    """Transpose an OpenBB statement DataFrame (rows=periods) into IB-style
    line-items-as-rows / periods-as-columns, with compact-formatted values."""
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


def news_list(df: pd.DataFrame, limit: int | None = None) -> list:
    """Render a DataFrame of news rows (title/url/source/date columns) as a
    simple headline list — used on both the Overview headlines panel and the
    News & Sentiment page."""
    items = []
    date_col = "date" if "date" in df.columns else None
    rows = df if limit is None else df.head(limit)
    for _, row in rows.iterrows():
        title = row.get("title", "Untitled")
        url = row.get("url")
        source = row.get("source") or row.get("provider")
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


def _with_alpha(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

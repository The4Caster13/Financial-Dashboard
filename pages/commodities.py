from __future__ import annotations

import datetime as dt

import dash
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from config import COMMODITIES, REFRESH_INTERVAL_MS
from data.commodities import get_commodities_snapshot, get_commodity_history
from data.errors import DataUnavailableError
from ui import theme
from ui.components import delta_badge, error_message, format_number, live_indicator, section_header, stat_card

dash.register_page(__name__, path="/commodities", name="Commodities")


def _build_snapshot_panel():
    try:
        df = get_commodities_snapshot()
    except DataUnavailableError as exc:
        return html.Div([section_header("Commodities Snapshot"), error_message(str(exc))], className="panel")

    cards = [
        html.Div(
            stat_card(
                row["label"],
                format_number(row["last"], "price"),
                delta=delta_badge(row["pct_change"]),
                sub=f"vol {format_number(row['volume'], 'compact', 0)}",
            ),
            id={"type": "commodity-card", "symbol": row["symbol"]},
            n_clicks=0,
            style={"cursor": "pointer"},
        )
        for _, row in df.iterrows()
    ]
    return html.Div(
        [
            live_indicator(),
            section_header("Commodities Snapshot", "Front-month futures — click one for detail"),
            html.Div(cards, className="stat-grid"),
        ],
        className="panel",
    )


def layout(**kwargs):
    default_symbol = next(iter(COMMODITIES))
    return html.Div(
        [
            dcc.Interval(id="commodities-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
            html.Div(id="commodity-snapshot-content"),
            html.Div(
                [
                    html.Label("Symbol", className="stat-sub"),
                    dcc.Dropdown(
                        id="commodity-select",
                        options=[{"label": v, "value": k} for k, v in COMMODITIES.items()],
                        value=default_symbol,
                        clearable=False,
                        className="control-input",
                        style={"width": "260px"},
                    ),
                ],
                className="panel",
                style={"display": "flex", "gap": "12px", "alignItems": "center"},
            ),
            dcc.Loading(html.Div(id="commodity-detail"), type="circle"),
        ]
    )


@dash.callback(Output("commodity-snapshot-content", "children"), Input("commodities-interval", "n_intervals"))
def _render_snapshot(_n_intervals):
    return _build_snapshot_panel()


@dash.callback(
    Output("commodity-select", "value"),
    Input({"type": "commodity-card", "symbol": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def _select_from_card(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise dash.exceptions.PreventUpdate
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        return triggered_id["symbol"]
    raise dash.exceptions.PreventUpdate


@dash.callback(
    Output("commodity-detail", "children"),
    Input("commodity-select", "value"),
    Input("commodities-interval", "n_intervals"),
)
def _render_detail(symbol, _n_intervals):
    if not symbol:
        raise dash.exceptions.PreventUpdate
    label = COMMODITIES.get(symbol, symbol)
    try:
        start = (dt.date.today() - dt.timedelta(days=180)).isoformat()
        df = get_commodity_history(symbol, start_date=start)
    except DataUnavailableError as exc:
        return error_message(str(exc))

    df = df.reset_index()
    date_col = "date" if "date" in df.columns else df.columns[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[date_col], y=df["close"], mode="lines", name="Price",
        line=dict(color=theme.CATEGORICAL[0], width=2), yaxis="y1",
        hovertemplate="%{x|%b %d, %Y}<br><b>%{y:,.2f}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df[date_col], y=df["volume"], name="Volume", yaxis="y2",
        marker_color=theme.GRIDLINE, opacity=0.7,
        hovertemplate="%{x|%b %d, %Y}<br>Vol %{y:,.0f}<extra></extra>",
    ))
    layout = dict(theme.PLOTLY_LAYOUT)
    layout.update(
        height=420,
        hovermode="x unified",
        xaxis=dict(gridcolor=theme.GRIDLINE, zerolinecolor=theme.BASELINE, linecolor=theme.BASELINE,
                     tickfont=dict(color=theme.TEXT_MUTED)),
        yaxis=dict(title="Price", gridcolor=theme.GRIDLINE, domain=[0.3, 1]),
        yaxis2=dict(title="Volume", domain=[0, 0.22], showgrid=False),
        legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)", font=dict(color=theme.TEXT_SECONDARY)),
    )
    fig.update_layout(**layout)

    return html.Div(
        [section_header(f"{label} ({symbol})", "6-month price & volume"),
         dcc.Graph(figure=fig, config={"displayModeBar": False})],
        className="panel",
    )

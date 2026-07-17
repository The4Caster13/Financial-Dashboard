from __future__ import annotations

import dash
from dash import Input, Output, State, dcc, html

from data.comps import METRIC_FORMATS, get_comps_table, suggest_peers
from data.errors import DataUnavailableError
from ui.components import bar_chart, data_table, error_message, format_number, section_header

dash.register_page(__name__, path="/comps", name="Comps")

CHART_METRICS = ["P/E (TTM)", "EV/EBITDA", "EV/Revenue", "P/B"]


def layout(symbol: str | None = None, **kwargs):
    target = (symbol or "AAPL").upper()
    try:
        peers = suggest_peers(target)
    except DataUnavailableError:
        peers = []

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Target", className="stat-sub"),
                            dcc.Input(id="comps-target-input", value=target, type="text", debounce=True,
                                      className="ticker-search", style={"width": "120px", "textTransform": "uppercase"}),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "4px"},
                    ),
                    html.Div(
                        [
                            html.Label("Peers (comma-separated — edit freely)", className="stat-sub"),
                            dcc.Input(id="comps-peers-input", value=", ".join(peers), type="text", debounce=True,
                                      className="ticker-search", style={"width": "440px", "textTransform": "uppercase"}),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "4px"},
                    ),
                    html.Button("Auto-suggest peers", id="comps-suggest-btn", n_clicks=0, className="ticker-search",
                                 style={"cursor": "pointer", "alignSelf": "flex-end"}),
                ],
                className="panel",
                style={"display": "flex", "gap": "20px", "alignItems": "center", "flexWrap": "wrap"},
            ),
            dcc.Loading(html.Div(id="comps-content"), type="circle"),
        ]
    )


@dash.callback(
    Output("comps-peers-input", "value"),
    Input("comps-suggest-btn", "n_clicks"),
    State("comps-target-input", "value"),
    prevent_initial_call=True,
)
def _refresh_peers(_n_clicks, target):
    if not target:
        raise dash.exceptions.PreventUpdate
    try:
        peers = suggest_peers(target.strip().upper())
    except DataUnavailableError:
        peers = []
    return ", ".join(peers)


@dash.callback(
    Output("comps-content", "children"),
    Input("comps-target-input", "value"),
    Input("comps-peers-input", "value"),
)
def _render_comps(target, peers_raw):
    if not target:
        raise dash.exceptions.PreventUpdate
    target = target.strip().upper()
    peers = [p.strip().upper() for p in (peers_raw or "").split(",") if p.strip()]
    symbols = tuple(dict.fromkeys([target] + peers))

    try:
        df = get_comps_table(symbols)
    except DataUnavailableError as exc:
        return error_message(str(exc))

    formatted = df.copy()
    for label in formatted.index:
        kind = METRIC_FORMATS.get(label, "number")
        formatted.loc[label] = formatted.loc[label].apply(lambda v: format_number(v, kind))
    table_df = formatted.reset_index().rename(columns={"index": "Metric"})
    table_panel = html.Div(
        [
            section_header("Comps Table", f"{len(symbols)} companies · target highlighted"),
            data_table(table_df, table_id="comps-table", page_size=len(table_df)),
        ],
        className="panel",
    )

    charts = []
    for metric in CHART_METRICS:
        if metric not in df.index:
            continue
        row = df.loc[metric]
        values = [float(v) if _is_num(v) else None for v in row.tolist()]
        fig = bar_chart(list(row.index), values, highlight=target)
        fig.update_layout(height=280)
        charts.append(
            html.Div(
                [html.H3(metric, className="section-subtitle", style={"marginBottom": "4px"}),
                 dcc.Graph(figure=fig, config={"displayModeBar": False})],
                className="panel",
                style={"flex": "1 1 380px"},
            )
        )

    charts_panel = html.Div(charts, style={"display": "flex", "flexWrap": "wrap", "gap": "16px"})

    summary = _summary_panel(df, target)

    return html.Div([table_panel, charts_panel, summary])


def _summary_panel(df, target):
    rows = []
    for metric in CHART_METRICS:
        if metric not in df.index:
            continue
        row = df.loc[metric].apply(lambda v: float(v) if _is_num(v) else None)
        peer_values = row.drop(labels=[target], errors="ignore").dropna()
        if peer_values.empty:
            continue
        rows.append({
            "Metric": metric,
            "Target": round(row.get(target), 2) if _is_num(row.get(target)) else "—",
            "Peer Median": round(peer_values.median(), 2),
            "Peer Mean": round(peer_values.mean(), 2),
            "Peer Min": round(peer_values.min(), 2),
            "Peer Max": round(peer_values.max(), 2),
        })
    if not rows:
        return html.Div()
    import pandas as pd
    summary_df = pd.DataFrame(rows)
    return html.Div(
        [
            section_header("Peer Group Summary", "Implied range from peer multiples"),
            data_table(summary_df, table_id="comps-summary-table", page_size=10,
                        numeric_cols=["Target", "Peer Median", "Peer Mean", "Peer Min", "Peer Max"]),
        ],
        className="panel",
    )


def _is_num(v) -> bool:
    try:
        return v is not None and float(v) == float(v)
    except (TypeError, ValueError):
        return False

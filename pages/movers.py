from __future__ import annotations

import dash
from dash import Input, Output, dcc, html

from config import REFRESH_INTERVAL_MS
from data.errors import DataUnavailableError
from data.market import get_movers
from ui.components import error_message, live_indicator, movers_table, section_header

dash.register_page(__name__, path="/movers", name="Movers")

_LISTS = (("gainers", "Top gainers"), ("losers", "Top losers"), ("active", "Most active"))


def layout(**kwargs):
    return html.Div(
        [
            dcc.Interval(id="movers-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
            dcc.Link("← Overview", href="/", className="back-link"),
            html.Div(
                [
                    html.Div(
                        [section_header("Market movers", "US equities, today · via Yahoo Finance. "
                                                         "Click a symbol for its company page."),
                         html.Div(id="movers-status", className="page-head-aside")],
                        className="page-head-row",
                    ),
                    html.Div(
                        [
                            dcc.Tabs(id="movers-tab", value="gainers",
                                     children=[dcc.Tab(label=label, value=key) for key, label in _LISTS],
                                     parent_className="ov-tabs-parent", className="ov-tabs"),
                            html.Div(
                                [html.Label("Rows", className="stat-sub"),
                                 dcc.RadioItems(id="movers-rows", options=[10, 25, 50], value=25, inline=True,
                                                className="radio-pills")],
                                className="control-row",
                            ),
                        ],
                        className="toolbar-row",
                    ),
                    html.Div(id="movers-table"),
                ],
                className="panel panel--compact-tabs",
            ),
        ]
    )


@dash.callback(
    Output("movers-table", "children"),
    Output("movers-status", "children"),
    Input("movers-tab", "value"),
    Input("movers-rows", "value"),
    Input("movers-interval", "n_intervals"),
)
def _render(category, rows, _n):
    try:
        df = get_movers(category, limit=50).head(rows)
    except DataUnavailableError as exc:
        return error_message(str(exc)), live_indicator()
    if df.empty:
        return html.Div("No data right now.", className="stat-sub"), live_indicator()
    return movers_table(df, detailed=True), live_indicator()

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html

from config import APP_NAME
from ui.navbar import build_navbar

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title=APP_NAME,
)
server = app.server

app.layout = html.Div(
    [
        build_navbar(),
        html.Div(dash.page_container, className="page-container"),
    ]
)


@app.callback(
    # Dash's own page-routing machinery listens on its internal
    # `_pages_location` component (see dash/dash.py's `_ID_LOCATION`) — a
    # second, separate dcc.Location wouldn't drive routing, so target that
    # one directly instead of adding our own.
    Output("_pages_location", "pathname"),
    Output("_pages_location", "search"),
    Input("global-ticker-search", "value"),
    prevent_initial_call=True,
)
def _search_ticker(value):
    if not value:
        raise dash.exceptions.PreventUpdate
    return "/company", f"?symbol={value.strip().upper()}"

from __future__ import annotations

import dash
from dash import Input, Output, dcc, html

from config import SECTORS
from data.errors import DataUnavailableError
from data.market import run_screener
from ui.components import data_table, error_message, format_display_df, section_header

dash.register_page(__name__, path="/screener", name="Screener")

_NUMERIC_FIELDS = [
    ("screener-mktcap-min", "Market Cap Min ($)", None),
    ("screener-mktcap-max", "Market Cap Max ($)", None),
    ("screener-price-min", "Price Min", None),
    ("screener-price-max", "Price Max", None),
    ("screener-beta-min", "Beta Min", None),
    ("screener-beta-max", "Beta Max", None),
    ("screener-volume-min", "Volume Min", None),
]

def layout(**kwargs):
    numeric_inputs = [
        html.Div(
            [html.Label(label, className="stat-sub"),
             dcc.Input(id=comp_id, type="number", className="ticker-search", style={"width": "150px"})],
            style={"display": "flex", "flexDirection": "column", "gap": "4px"},
        )
        for comp_id, label, _ in _NUMERIC_FIELDS
    ]

    controls = html.Div(
        [
            html.Div(
                [html.Label("Sector", className="stat-sub"),
                 dcc.Dropdown(
                     id="screener-sector",
                     options=[{"label": s.replace("_", " ").title(), "value": s} for s in SECTORS],
                     placeholder="Any sector",
                     className="control-input",
                     style={"width": "220px"},
                 )],
                style={"display": "flex", "flexDirection": "column", "gap": "4px"},
            ),
            *numeric_inputs,
            html.Button("Run Screener", id="screener-run-btn", n_clicks=0, className="ticker-search",
                         style={"cursor": "pointer", "alignSelf": "flex-end"}),
        ],
        className="panel",
        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "alignItems": "flex-end"},
    )

    return html.Div([controls, dcc.Loading(html.Div(id="screener-content"), type="circle")])


@dash.callback(
    Output("screener-content", "children"),
    Input("screener-run-btn", "n_clicks"),
    Input("screener-sector", "value"),
    [Input(comp_id, "value") for comp_id, _, _ in _NUMERIC_FIELDS],
)
def _run_screener(_n_clicks, sector, *numeric_values):
    kwargs = {"sector": sector}
    field_names = ["mktcap_min", "mktcap_max", "price_min", "price_max", "beta_min", "beta_max", "volume_min"]
    kwargs.update(dict(zip(field_names, numeric_values)))

    try:
        df = run_screener(**kwargs)
    except DataUnavailableError as exc:
        return error_message(str(exc))

    if df.empty:
        return html.Div("No matches for the current filters.", className="stat-sub")

    cols = [c for c in ["symbol", "name", "price", "percent_change", "market_cap", "pe_forward",
                          "dividend_yield", "volume", "exchange"] if c in df.columns]
    view = format_display_df(df[cols], {
        "price": "price", "percent_change": "percent", "market_cap": "compact",
        "pe_forward": "number", "dividend_yield": "percent", "volume": "compact",
    })
    view["symbol"] = view["symbol"].apply(lambda s: f"[{s}](/company?symbol={s})")

    return html.Div(
        [
            section_header("Results", f"{len(df)} matches"),
            data_table(view, table_id="screener-table", page_size=20, markdown_cols=["symbol"]),
        ],
        className="panel",
    )

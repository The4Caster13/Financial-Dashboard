from __future__ import annotations

import datetime as dt

import dash
from dash import Input, Output, dcc, html

from config import REFRESH_INTERVAL_MS
from data.company import (
    get_analyst_consensus,
    get_balance_sheet,
    get_cash_flow,
    get_historical_prices,
    get_income_statement,
    get_metrics,
    get_profile,
    get_quote,
)
from data.errors import DataUnavailableError
from ui.components import (
    delta_badge,
    error_message,
    financial_statement_table,
    format_number,
    line_chart,
    live_indicator,
    section_header,
    stat_card,
)

dash.register_page(__name__, path="/company", name="Company")


def layout(symbol: str | None = None, **kwargs):
    symbol = (symbol or "AAPL").upper()
    return html.Div(
        [
            html.Div(
                [
                    html.Label("Ticker", className="stat-sub", style={"marginRight": "8px"}),
                    dcc.Input(
                        id="company-symbol-input",
                        value=symbol,
                        type="text",
                        debounce=True,
                        className="ticker-search",
                        style={"width": "140px", "textTransform": "uppercase"},
                    ),
                ],
                className="panel",
                style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "12px 16px"},
            ),
            dcc.Interval(id="company-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
            dcc.Loading(html.Div(id="company-content"), type="circle"),
        ]
    )


@dash.callback(
    Output("company-content", "children"),
    Input("company-symbol-input", "value"),
    Input("company-interval", "n_intervals"),
)
def _render_company(symbol, _n_intervals):
    if not symbol:
        raise dash.exceptions.PreventUpdate
    symbol = symbol.strip().upper()

    try:
        quote = get_quote(symbol)
        profile = get_profile(symbol)
    except DataUnavailableError as exc:
        return error_message(str(exc))

    header = _header(symbol, quote, profile)

    try:
        metrics = get_metrics(symbol)
        stats_panel = _key_stats(metrics, quote)
    except DataUnavailableError as exc:
        stats_panel = html.Div([section_header("Key Stats"), error_message(str(exc))], className="panel")

    try:
        start = (dt.date.today() - dt.timedelta(days=365)).isoformat()
        hist = get_historical_prices(symbol, start_date=start)
        fig = line_chart(hist.reset_index(), x=hist.index.name or "date", y="close", fill=True, y_title="Price")
        fig.update_layout(height=320)
        price_panel = html.Div(
            [section_header("Price — Last 12 Months"), dcc.Graph(figure=fig, config={"displayModeBar": False})],
            className="panel",
        )
    except DataUnavailableError as exc:
        price_panel = html.Div([section_header("Price"), error_message(str(exc))], className="panel")

    try:
        consensus = get_analyst_consensus(symbol)
        analyst_panel = _analyst_panel(consensus)
    except DataUnavailableError as exc:
        analyst_panel = html.Div([section_header("Analyst Estimates"), error_message(str(exc))], className="panel")

    statements_panel = _statements_panel(symbol)

    return html.Div([live_indicator(), header, stats_panel, price_panel, analyst_panel, statements_panel])


def _header(symbol, quote, profile):
    name = profile.get("name") or quote.get("name") or symbol
    last = quote.get("last_price") or quote.get("close")
    prev_close = quote.get("prev_close")
    change = (last - prev_close) if (last is not None and prev_close) else None
    pct = (change / prev_close * 100) if (change is not None and prev_close) else None
    sector = profile.get("sector")
    industry = profile.get("industry_category") or profile.get("industry")
    exchange = quote.get("exchange")

    return html.Div(
        [
            html.Div(
                [
                    html.Span(f"{symbol}", className="symbol-name"),
                    html.Span(name, className="symbol-meta", style={"fontSize": "15px"}),
                ],
                className="symbol-header",
            ),
            html.Div(
                [
                    html.Span(format_number(last, "price"), className="symbol-price"),
                    delta_badge(pct),
                    html.Span(f"{change:+.2f}" if change is not None else "", className="stat-sub"),
                ],
                className="symbol-header",
            ),
            html.Div(
                " · ".join(v for v in [sector, industry, exchange] if v),
                className="symbol-meta",
            ),
        ],
        className="panel",
    )


def _key_stats(metrics, quote):
    cards = [
        stat_card("Market Cap", format_number(metrics.get("market_cap"), "compact")),
        stat_card("P/E (TTM)", format_number(metrics.get("pe_ratio"))),
        stat_card("Forward P/E", format_number(metrics.get("forward_pe"))),
        stat_card("PEG Ratio", format_number(metrics.get("peg_ratio"))),
        stat_card("EV/EBITDA", format_number(metrics.get("enterprise_to_ebitda"))),
        stat_card("EV/Revenue", format_number(metrics.get("enterprise_to_revenue"))),
        stat_card("Price/Book", format_number(metrics.get("price_to_book"))),
        stat_card("Beta", format_number(metrics.get("beta"))),
        stat_card("Dividend Yield", format_number(metrics.get("dividend_yield"), "percent_raw")),
        stat_card("Gross Margin", format_number(metrics.get("gross_margin"), "percent")),
        stat_card("Operating Margin", format_number(metrics.get("operating_margin"), "percent")),
        stat_card("Net Margin", format_number(metrics.get("profit_margin"), "percent")),
        stat_card("ROE", format_number(metrics.get("return_on_equity"), "percent")),
        stat_card("ROA", format_number(metrics.get("return_on_assets"), "percent")),
        stat_card("Debt/Equity", format_number(metrics.get("debt_to_equity"))),
        stat_card("52W Range", f"{format_number(quote.get('year_low'), 'price')} – {format_number(quote.get('year_high'), 'price')}"),
    ]
    return html.Div([section_header("Key Stats"), html.Div(cards, className="stat-grid")], className="panel")


def _analyst_panel(consensus):
    cards = [
        stat_card("Recommendation", str(consensus.get("recommendation", "—")).replace("_", " ").title()),
        stat_card("Target Low", format_number(consensus.get("target_low"), "price")),
        stat_card("Target Median", format_number(consensus.get("target_median"), "price")),
        stat_card("Target High", format_number(consensus.get("target_high"), "price")),
        stat_card("Analysts", format_number(consensus.get("number_of_analysts"), "number", 0)),
    ]
    return html.Div([section_header("Analyst Estimates"), html.Div(cards, className="stat-grid")], className="panel")


def _statements_panel(symbol):
    try:
        income = get_income_statement(symbol)
        balance = get_balance_sheet(symbol)
        cash = get_cash_flow(symbol)
    except DataUnavailableError as exc:
        return html.Div([section_header("Financial Statements"), error_message(str(exc))], className="panel")

    tabs = dcc.Tabs(
        [
            dcc.Tab(label="Income Statement", children=[financial_statement_table(income, "income-table")]),
            dcc.Tab(label="Balance Sheet", children=[financial_statement_table(balance, "balance-table")]),
            dcc.Tab(label="Cash Flow", children=[financial_statement_table(cash, "cash-table")]),
        ]
    )
    return html.Div([section_header("Financial Statements", "Annual, most recent periods"), tabs], className="panel")

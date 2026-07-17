from __future__ import annotations

import dash
from dash import Input, Output, dcc, html

from config import REFRESH_INTERVAL_MS
from data.commodities import get_commodities_snapshot
from data.errors import DataUnavailableError
from data.market import get_index_snapshot, get_movers, get_sector_performance
from data.news import get_world_news
from data.sentiment import get_fear_greed
from ui.components import (
    bar_chart,
    data_table,
    delta_badge,
    error_message,
    format_display_df,
    format_number,
    live_indicator,
    news_list,
    section_header,
    stat_card,
)
from ui.theme import delta_color

dash.register_page(__name__, path="/", name="Overview")


def _fear_greed_panel() -> html.Div:
    try:
        fg = get_fear_greed()
    except DataUnavailableError as exc:
        return html.Div(
            [section_header("Fear & Greed Index"), error_message(str(exc))], className="panel"
        )

    return html.Div(
        [
            section_header("Fear & Greed Index", "CNN's market sentiment gauge (0 = extreme fear, 100 = extreme greed)"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(f"{fg['score']:.0f}", className="stat-value", style={"fontSize": "40px"}),
                            html.Div(fg["rating"].replace("_", " ").title(), className="stat-sub",
                                      style={"color": delta_color(fg["score"] - 50)}),
                        ],
                        style={"minWidth": "120px"},
                    ),
                    html.Div(
                        [
                            html.Div([html.Span("Previous close: ", className="stat-sub"),
                                       html.Span(f"{fg['previous_close']:.0f}")]),
                            html.Div([html.Span("1 week ago: ", className="stat-sub"),
                                       html.Span(f"{fg['previous_week']:.0f}")]),
                            html.Div([html.Span("1 month ago: ", className="stat-sub"),
                                       html.Span(f"{fg['previous_month']:.0f}")]),
                            html.Div([html.Span("1 year ago: ", className="stat-sub"),
                                       html.Span(f"{fg['previous_year']:.0f}")]),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "4px", "fontSize": "13px"},
                    ),
                ],
                style={"display": "flex", "gap": "32px", "alignItems": "center"},
            ),
        ],
        className="panel",
    )


def _headlines_panel() -> html.Div:
    try:
        df = get_world_news(limit=20)
    except DataUnavailableError as exc:
        return html.Div([section_header("Top Headlines"), error_message(str(exc))], className="panel")

    return html.Div(
        [section_header("Top Headlines", "Latest from major outlets — Yahoo Finance, WSJ, Barron's, and more")]
        + news_list(df, limit=6),
        className="panel",
    )


def _index_snapshot() -> html.Div:
    try:
        df = get_index_snapshot()
    except DataUnavailableError as exc:
        return html.Div([section_header("Major Indices"), error_message(str(exc))], className="panel")

    cards = [
        stat_card(
            row["label"],
            format_number(row["last"], "number"),
            delta=delta_badge(row["pct_change"]),
        )
        for _, row in df.iterrows()
    ]
    return html.Div(
        [section_header("Major Indices"), html.Div(cards, className="stat-grid")],
        className="panel",
    )


def _commodities_strip() -> html.Div:
    try:
        df = get_commodities_snapshot()
    except DataUnavailableError as exc:
        return html.Div([section_header("Commodities"), error_message(str(exc))], className="panel")

    cards = [
        stat_card(
            row["label"],
            format_number(row["last"], "price"),
            delta=delta_badge(row["pct_change"]),
            sub=f"vol {format_number(row['volume'], 'compact', 0)}",
        )
        for _, row in df.iterrows()
    ]
    return html.Div(
        [section_header("Commodities", "Front-month futures — see the Commodities page for detail"),
         html.Div(cards, className="stat-grid")],
        className="panel",
    )


def _sector_performance() -> html.Div:
    try:
        df = get_sector_performance()
    except DataUnavailableError as exc:
        return html.Div([section_header("Sector Performance"), error_message(str(exc))], className="panel")

    fig = bar_chart(df["sector"].tolist(), df["pct_change"].tolist(), orientation="h", value_suffix="%")
    fig.update_layout(height=340)
    return html.Div(
        [section_header("Sector Performance", "Sector SPDR ETFs, daily % change"), html.Div(dash.dcc.Graph(figure=fig, config={"displayModeBar": False}))],
        className="panel",
    )


def _movers_panel() -> html.Div:
    tabs = []
    for key, label in (("gainers", "Top Gainers"), ("losers", "Top Losers"), ("active", "Most Active")):
        try:
            df = get_movers(key, limit=10)
            cols = [c for c in ["symbol", "name", "price", "percent_change", "volume"] if c in df.columns]
            view = format_display_df(df[cols], {"price": "price", "percent_change": "percent", "volume": "compact"})
            content = data_table(view, table_id=f"movers-{key}", page_size=10)
        except DataUnavailableError as exc:
            content = error_message(str(exc))
        tabs.append(dash.dcc.Tab(label=label, children=[html.Div(content, style={"marginTop": "12px"})],
                                    className="custom-tab", selected_className="custom-tab--selected"))

    return html.Div(
        [section_header("Market Movers"), dash.dcc.Tabs(tabs)],
        className="panel",
    )


def layout(**kwargs):
    return html.Div(
        [
            dcc.Interval(id="overview-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
            html.Div(id="overview-content"),
        ]
    )


@dash.callback(Output("overview-content", "children"), Input("overview-interval", "n_intervals"))
def _render_overview(_n_intervals):
    return html.Div(
        [
            live_indicator(),
            _fear_greed_panel(),
            _headlines_panel(),
            _index_snapshot(),
            _sector_performance(),
            _movers_panel(),
            _commodities_strip(),
        ]
    )

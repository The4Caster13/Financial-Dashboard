from __future__ import annotations

import dash
import pandas as pd
from dash import Input, Output, dcc, html

from data.errors import DataUnavailableError
from data.news import get_company_news, get_world_news
from data.sentiment import get_fear_greed
from ui import theme
from ui.components import error_message, line_chart, news_list, section_header
from ui.theme import delta_color

dash.register_page(__name__, path="/news", name="News & Sentiment")


def layout(symbol: str | None = None, **kwargs):
    return html.Div(
        [
            _fear_greed_detail(),
            html.Div(
                [
                    html.Label("Ticker", className="stat-sub"),
                    dcc.Input(id="news-symbol-input", value=(symbol or "AAPL").upper(), type="text", debounce=True,
                               className="ticker-search", style={"width": "140px", "textTransform": "uppercase"}),
                ],
                className="panel",
                style={"display": "flex", "gap": "12px", "alignItems": "center"},
            ),
            dcc.Loading(html.Div(id="company-news-content"), type="circle"),
            _world_news_panel(),
        ]
    )


def _fear_greed_detail():
    try:
        fg = get_fear_greed()
    except DataUnavailableError as exc:
        return html.Div([section_header("Fear & Greed Index"), error_message(str(exc))], className="panel")

    children = [
        section_header("Fear & Greed Index", "CNN's market sentiment gauge (0 = extreme fear, 100 = extreme greed)"),
        html.Div(
            [
                html.Div(f"{fg['score']:.0f}", className="stat-value", style={"fontSize": "40px"}),
                html.Div(fg["rating"].replace("_", " ").title(), className="stat-sub",
                          style={"color": delta_color(fg["score"] - 50), "fontSize": "14px"}),
            ],
        ),
    ]

    hist = fg.get("historical") or []
    if hist:
        df = pd.DataFrame(hist)
        if "x" in df.columns and "y" in df.columns:
            df["date"] = pd.to_datetime(df["x"], unit="ms")
            df = df.rename(columns={"y": "score"}).sort_values("date")
            fig = line_chart(df, x="date", y="score", color=theme.CATEGORICAL[0], fill=True, y_title="Score")
            fig.update_layout(height=260)
            fig.add_hline(y=50, line_dash="dot", line_color=theme.BASELINE)
            children.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))

    return html.Div(children, className="panel")


def _world_news_panel():
    try:
        df = get_world_news(limit=12)
    except DataUnavailableError as exc:
        return html.Div([section_header("Market News"), error_message(str(exc))], className="panel")
    return html.Div(
        [section_header("Market News", "Broad-market headlines")] + news_list(df),
        className="panel",
    )


@dash.callback(Output("company-news-content", "children"), Input("news-symbol-input", "value"))
def _render_company_news(symbol):
    if not symbol:
        raise dash.exceptions.PreventUpdate
    symbol = symbol.strip().upper()
    try:
        df = get_company_news(symbol, limit=15)
    except DataUnavailableError as exc:
        return html.Div([section_header(f"{symbol} News"), error_message(str(exc))], className="panel")
    return html.Div([section_header(f"{symbol} News")] + news_list(df), className="panel")

from __future__ import annotations

import dash
import pandas as pd
from dash import Input, Output, dcc, html

from config import REFRESH_INTERVAL_MS
from data.errors import DataUnavailableError
from data.market import get_heatmap_data
from ui import theme
from ui.components import (
    bar_chart,
    blank_figure,
    company_route_from_heatmap_click,
    data_table,
    error_message,
    heatmap_figure,
    live_indicator,
    section_header,
)

dash.register_page(__name__, path="/heatmap", name="Heatmap")

_TICK = Input("heatmap-interval", "n_intervals")


def _legend() -> html.Div:
    clamp = theme.HEATMAP_CLAMP
    gradient = f"linear-gradient(90deg, {theme.HEATMAP_DOWN}, {theme.HEATMAP_MID}, {theme.HEATMAP_UP})"
    return html.Div(
        [html.Span(f"−{clamp:.0f}%"), html.Span(className="heatmap-legend-bar", style={"background": gradient}),
         html.Span(f"+{clamp:.0f}%")],
        className="heatmap-legend",
        title=f"Daily % change; tiles at or beyond ±{clamp:.0f}% take the full color",
    )


def layout(**kwargs):
    return html.Div(
        [
            dcc.Interval(id="heatmap-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
            dcc.Link("← Overview", href="/", className="back-link"),
            html.Div(
                [
                    html.Div(
                        [
                            section_header(
                                "Market heatmap",
                                "Largest S&P 500 names by sector · size = market cap · color = daily % change. "
                                "Click a sector to zoom in (click its header again to zoom out); "
                                "click a stock to open its company page.",
                            ),
                            html.Div([html.Div(id="heatmap-status"), _legend()], className="page-head-aside"),
                        ],
                        className="page-head-row",
                    ),
                    html.Div(
                        dcc.Graph(
                            id="heatmap-graph",
                            figure=blank_figure("Loading heatmap…", color=theme.TEXT_MUTED),
                            responsive=True,
                            config={"displayModeBar": False},
                            style={"position": "absolute", "inset": "0"},
                        ),
                        className="heatmap-full",
                    ),
                ],
                className="panel",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            section_header("Sector performance", "Sector SPDR ETFs, daily % change"),
                            dcc.Graph(id="heatmap-sectors-graph", figure=blank_figure(),
                                      config={"displayModeBar": False}),
                        ],
                        className="panel",
                    ),
                    html.Div(
                        [section_header("All stocks", "Click a column header to sort"),
                         html.Div(id="heatmap-table")],
                        className="panel",
                    ),
                ],
                className="two-col",
            ),
        ]
    )


@dash.callback(Output("heatmap-status", "children"), _TICK)
def _render_status(_n):
    return live_indicator()


@dash.callback(Output("heatmap-graph", "figure"), _TICK)
def _render_heatmap(_n):
    try:
        df = get_heatmap_data()
    except DataUnavailableError as exc:
        return blank_figure(str(exc))
    return heatmap_figure(df)


@dash.callback(
    Output("_pages_location", "pathname", allow_duplicate=True),
    Output("_pages_location", "search", allow_duplicate=True),
    Input("heatmap-graph", "clickData"),
    prevent_initial_call=True,
)
def _heatmap_click(click):
    return company_route_from_heatmap_click(click)


@dash.callback(Output("heatmap-sectors-graph", "figure"), _TICK)
def _render_sectors(_n):
    try:
        stocks = get_heatmap_data()
    except DataUnavailableError as exc:
        return blank_figure(str(exc))
    df = (stocks.groupby("sector", sort=False)["sector_pct"].first().reset_index()
          .rename(columns={"sector_pct": "pct_change"})
          .sort_values("pct_change", ascending=False, na_position="last"))

    fig = bar_chart(df["sector"].tolist(), df["pct_change"].tolist(), orientation="h", value_suffix="%")
    fig.update_traces(marker_cornerradius=4, cliponaxis=False, textfont_size=11)
    fig.update_layout(height=400, margin=dict(l=4, r=8, t=4, b=4), bargap=0.45)
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=True, zerolinecolor=theme.BASELINE)
    fig.update_yaxes(autorange="reversed", automargin=True, showgrid=False, ticks="",
                     tickfont=dict(color=theme.TEXT_SECONDARY, size=12))
    values = [v for v in df["pct_change"] if pd.notna(v)]
    if values:
        lo, hi = min(values + [0.0]), max(values + [0.0])
        pad = (hi - lo) * 0.3 or 1.0
        fig.update_xaxes(range=[lo - pad if lo < 0 else 0, hi + pad if hi > 0 else 0])
    return fig


@dash.callback(Output("heatmap-table", "children"), _TICK)
def _render_table(_n):
    try:
        df = get_heatmap_data()
    except DataUnavailableError as exc:
        return error_message(str(exc))

    view = pd.DataFrame({
        "symbol": [f"[{s}](/company?symbol={s})" for s in df["symbol"]],
        "name": df["name"],
        "sector": df["sector"],
        "price": df["last"].round(2),
        "change_%": df["pct_change"].round(2),
        "mkt_cap_$B": (df["market_cap"] / 1e9).round(1),
    }).sort_values("change_%", ascending=False, na_position="last")
    return data_table(view, table_id="heatmap-stocks", page_size=15,
                      numeric_cols=["price", "change_%", "mkt_cap_$B"], markdown_cols=["symbol"])

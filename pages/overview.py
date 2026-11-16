from __future__ import annotations

import math
from urllib.parse import quote

import dash
from dash import Input, Output, dcc, html

from config import REFRESH_INTERVAL_MS
from data.commodities import get_commodities_snapshot
from data.errors import DataUnavailableError
from data.market import get_heatmap_data, get_index_snapshot, get_movers
from data.news import get_mna_news, get_world_news
from data.sentiment import get_fear_greed
from ui import theme
from ui.components import (
    blank_figure,
    company_route_from_heatmap_click,
    delta_badge,
    format_number,
    heatmap_figure,
    live_indicator,
    movers_table,
    news_list,
)

dash.register_page(__name__, path="/", name="Overview")

_TICK = Input("overview-interval", "n_intervals")
_MOVER_TABS = (("gainers", "Top gainers"), ("losers", "Top losers"), ("active", "Most active"))


def _loading() -> html.Div:
    return html.Div("Loading…", className="ov-placeholder")


def _inline_error(message: str) -> html.Div:
    return html.Div([html.Span("⚠", className="error-icon"), html.Span(message)],
                    className="error-message ov-error")


def _panel(title: str, *children, subtitle: str | None = None, href: str | None = None) -> html.Section:
    head = [html.H2(title, className="ov-panel-title")]
    if subtitle:
        head.append(html.Span(subtitle, className="ov-panel-sub"))
    if href:
        head.append(dcc.Link([html.Span("Expand"), html.Span("↗", className="expand-icon")],
                             href=href, className="expand-link"))
    return html.Section([html.Div(head, className="ov-panel-head"), *children], className="ov-panel")


def layout(**kwargs):
    return html.Div(
        [
            dcc.Interval(id="overview-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
            html.Div(id="ov-status", className="ov-status"),
            html.Div(
                [
                    dcc.Link(_loading(), id="ov-fear-greed", href="/news", className="mini-tile mini-tile--link ov-fg",
                             title="CNN Fear & Greed Index — open News & Sentiment for its history"),
                    html.Div(_loading(), id="ov-indices", className="ov-tiles ov-indices"),
                    html.Div(_loading(), id="ov-commodities", className="ov-tiles ov-commodities"),
                ],
                className="ov-strip",
            ),
            html.Div(
                [
                    _panel(
                        "Market heatmap",
                        html.Div(
                            dcc.Graph(
                                id="ov-heatmap-graph",
                                figure=blank_figure("Loading heatmap…", color=theme.TEXT_MUTED),
                                responsive=True,
                                config={"displayModeBar": False},
                                style={"position": "absolute", "inset": "0"},
                            ),
                            className="ov-chart",
                        ),
                        subtitle="Size = market cap · color = daily % change",
                        href="/heatmap",
                    ),
                    _panel(
                        "Market movers",
                        dcc.Tabs(
                            id="ov-movers-tab",
                            value="gainers",
                            children=[dcc.Tab(label=label, value=key) for key, label in _MOVER_TABS],
                            persistence=True,
                            parent_className="ov-tabs-parent",
                            className="ov-tabs",
                        ),
                        html.Div(_loading(), id="ov-movers-table", className="ov-scroll"),
                        href="/movers",
                    ),
                    html.Div(
                        [
                            _panel("Top headlines", html.Div(_loading(), id="ov-headlines", className="ov-scroll"),
                                   subtitle="Broad-market news", href="/news"),
                            _panel("Potential M&A", html.Div(_loading(), id="ov-mna", className="ov-scroll"),
                                   subtitle="Talks, bids & sale processes · 3 days", href="/mna"),
                        ],
                        className="ov-stack",
                    ),
                ],
                className="ov-main",
            ),
        ],
        className="ov-root",
    )


@dash.callback(Output("ov-status", "children"), _TICK)
def _render_status(_n):
    return live_indicator()


_FG_ZONES = (
    (0, 25, "Extreme fear", theme.STATUS_CRITICAL),
    (25, 45, "Fear", theme.FEAR_TINT),
    (45, 55, "Neutral", theme.TEXT_MUTED),
    (55, 75, "Greed", theme.GREED_TINT),
    (75, 100, "Extreme greed", theme.STATUS_GOOD),
)
_GAUGE_RADIUS = 50
_GAUGE_RING = 9


def _fg_zone(score: float):
    for lo, hi, label, color in _FG_ZONES:
        if score < hi:
            return lo, hi, label, color
    return _FG_ZONES[-1]


def _fear_greed_gauge(score: float) -> html.Div:
    active = _fg_zone(score)
    gap = 1.2
    stops = []
    for zone in _FG_ZONES:
        lo, hi, _label, color = zone
        start = lo * 1.8 + (gap if lo > 0 else 0)
        end = hi * 1.8 - (gap if hi < 100 else 0)
        fill = color if zone == active else theme.with_alpha(color, 0.28)
        stops.append(f"{fill} {start:.1f}deg {end:.1f}deg")
        if hi < 100:
            stops.append(f"transparent {end:.1f}deg {end + 2 * gap:.1f}deg")
    stops.append("transparent 180deg")

    r = _GAUGE_RADIUS
    inner = r - _GAUGE_RING
    ring = (f"radial-gradient(circle {r}px at 50% 100%, transparent {inner - 0.5}px, "
            f"#000 {inner}px, #000 {r - 0.5}px, transparent {r}px)")
    phi = math.pi * (1 - score / 100)
    track = r - _GAUGE_RING / 2

    return html.Div(
        [
            html.Div(className="fg-arc", style={
                "width": f"{2 * r}px",
                "height": f"{r}px",
                "background": f"conic-gradient(from 270deg at 50% 100%, {', '.join(stops)})",
                "maskImage": ring,
                "WebkitMaskImage": ring,
            }),
            html.Div(className="fg-dot", style={"left": f"{r + track * math.cos(phi):.1f}px",
                                                "top": f"{r - track * math.sin(phi):.1f}px"}),
            html.Div(f"{score:.0f}", className="fg-score"),
        ],
        className="fg-gauge",
        style={"width": f"{2 * r}px", "height": f"{r + 6}px"},
    )


@dash.callback(Output("ov-fear-greed", "children"), _TICK)
def _render_fear_greed(_n):
    label = html.Div([html.Span("Fear & Greed"), html.Span("↗", className="expand-icon")],
                     className="mini-label fg-label")
    try:
        fg = get_fear_greed()
    except DataUnavailableError:
        return [label, html.Div("Unavailable", className="stat-sub")]

    score = fg["score"]
    _lo, _hi, zone_label, zone_color = _fg_zone(score)
    return [
        label,
        html.Div(
            [
                _fear_greed_gauge(score),
                html.Div(
                    [
                        html.Div(zone_label, className="fg-rating", style={"color": zone_color}),
                        html.Div(f"Prev {fg['previous_close']:.0f} · 1W {fg['previous_week']:.0f}",
                                 className="fg-history"),
                        html.Div(f"1M {fg['previous_month']:.0f} · 1Y {fg['previous_year']:.0f}",
                                 className="fg-history"),
                    ],
                    className="fg-text",
                ),
            ],
            className="fg-body",
        ),
    ]


def _mini_tile(label: str, value: str, delta, hint: str | None = None, href: str | None = None):
    children = [html.Div(label, className="mini-label"),
                html.Div([html.Span(value, className="mini-value"), delta], className="mini-row")]
    if href:
        return dcc.Link(children, href=href, className="mini-tile mini-tile--link", title=hint)
    return html.Div(children, className="mini-tile", title=hint)


@dash.callback(Output("ov-indices", "children"), _TICK)
def _render_indices(_n):
    try:
        df = get_index_snapshot()
    except DataUnavailableError as exc:
        return _inline_error(str(exc))
    return [_mini_tile(row["label"], format_number(row["last"], "number"), delta_badge(row["pct_change"]))
            for _, row in df.iterrows()]


@dash.callback(Output("ov-commodities", "children"), _TICK)
def _render_commodities(_n):
    try:
        df = get_commodities_snapshot()
    except DataUnavailableError as exc:
        return _inline_error(str(exc))
    return [
        _mini_tile(row["label"], format_number(row["last"], "price"), delta_badge(row["pct_change"]),
                   hint=f"{row['label']} ({row['symbol']}) · volume {format_number(row['volume'], 'compact', 1)}"
                        " — click for the price & volume chart",
                   href=f"/commodities?symbol={quote(row['symbol'])}")
        for _, row in df.iterrows()
    ]


@dash.callback(Output("ov-heatmap-graph", "figure"), _TICK)
def _render_heatmap(_n):
    try:
        df = get_heatmap_data()
    except DataUnavailableError as exc:
        return blank_figure(str(exc))
    return heatmap_figure(df, compact=True)


@dash.callback(
    Output("_pages_location", "pathname", allow_duplicate=True),
    Output("_pages_location", "search", allow_duplicate=True),
    Input("ov-heatmap-graph", "clickData"),
    prevent_initial_call=True,
)
def _heatmap_click(click):
    return company_route_from_heatmap_click(click)


@dash.callback(Output("ov-movers-table", "children"), _TICK, Input("ov-movers-tab", "value"))
def _render_movers(_n, category):
    try:
        df = get_movers(category, limit=10)
    except DataUnavailableError as exc:
        return _inline_error(str(exc))
    if df.empty:
        return html.Div("No data right now.", className="ov-placeholder")
    return movers_table(df)


@dash.callback(Output("ov-headlines", "children"), _TICK)
def _render_headlines(_n):
    try:
        df = get_world_news(limit=20)
    except DataUnavailableError as exc:
        return _inline_error(str(exc))
    return news_list(df, limit=15, compact=True)


@dash.callback(Output("ov-mna", "children"), _TICK)
def _render_mna(_n):
    try:
        df = get_mna_news("potential", days=3, limit=25)
    except DataUnavailableError as exc:
        return _inline_error(str(exc))
    return news_list(df, compact=True)

from __future__ import annotations

import dash
from dash import Input, Output, dcc, html

from config import REFRESH_INTERVAL_MS
from data.errors import DataUnavailableError
from data.news import MNA_STAGE_LABELS, get_mna_news
from ui.components import error_message, live_indicator, news_list, section_header

dash.register_page(__name__, path="/mna", name="M&A")

_FEEDS = (
    ("potential", "Potential deals", "Talks, bids & companies exploring a sale"),
    ("announced", "Announced deals", "Signed, completed & terminated deals"),
)


def _feed_panel(kind: str, title: str, subtitle: str) -> html.Div:
    return html.Div(
        [
            section_header(title, subtitle),
            dcc.Checklist(
                id=f"mna-{kind}-stages",
                options=MNA_STAGE_LABELS[kind],
                value=MNA_STAGE_LABELS[kind],
                inline=True,
                className="radio-pills",
            ),
            html.Div(id=f"mna-{kind}-list", className="mna-list"),
        ],
        className="panel",
    )


def layout(**kwargs):
    return html.Div(
        [
            dcc.Interval(id="mna-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
            dcc.Link("← Overview", href="/", className="back-link"),
            html.Div(
                [
                    section_header("Mergers & acquisitions",
                                   "Deal headlines from Google News, de-duplicated across outlets. "
                                   "Stage tags are inferred from headline wording — treat them as a guide."),
                    html.Div(
                        [html.Label("Lookback", className="stat-sub"),
                         dcc.RadioItems(id="mna-days", options=[{"label": f"{d}d", "value": d} for d in (1, 3, 7)],
                                        value=3, inline=True, className="radio-pills"),
                         html.Div(id="mna-status")],
                        className="control-row",
                    ),
                ],
                className="panel page-head-row",
            ),
            html.Div([_feed_panel(*feed) for feed in _FEEDS], className="two-col"),
        ]
    )


@dash.callback(Output("mna-status", "children"), Input("mna-interval", "n_intervals"))
def _render_status(_n):
    return live_indicator()


def _render_feed(kind: str, days: int, stages: list[str]):
    try:
        df = get_mna_news(kind, days=days, limit=60)
    except DataUnavailableError as exc:
        return error_message(str(exc))
    stages = set(stages)
    show_untagged = stages >= set(MNA_STAGE_LABELS[kind])
    df = df[df["tag"].isin(stages) | (df["tag"].isna() & show_untagged)]
    counts = df["tag"].fillna("Other").value_counts()
    summary = html.Div(
        f"{len(df)} stories · " + " · ".join(f"{label} {n}" for label, n in counts.items()),
        className="stat-sub mna-summary",
    )
    return [summary, *news_list(df, compact=True)]


@dash.callback(
    Output("mna-potential-list", "children"),
    Input("mna-days", "value"),
    Input("mna-potential-stages", "value"),
    Input("mna-interval", "n_intervals"),
)
def _render_potential(days, stages, _n):
    return _render_feed("potential", days, stages)


@dash.callback(
    Output("mna-announced-list", "children"),
    Input("mna-days", "value"),
    Input("mna-announced-stages", "value"),
    Input("mna-interval", "n_intervals"),
)
def _render_announced(days, stages, _n):
    return _render_feed("announced", days, stages)

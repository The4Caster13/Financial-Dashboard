"""Color tokens for Plotly figures — dark-mode slice of the validated dataviz
palette (see the dataviz skill's references/palette.md). Keep in sync with the
CSS custom properties in assets/style.css."""
from __future__ import annotations

SURFACE = "#1a1a19"
PAGE_PLANE = "#0d0d0d"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#c3c2b7"
TEXT_MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BASELINE = "#383835"
BORDER = "rgba(255,255,255,0.10)"

# Fixed-order categorical hues — never reassign per-filter, never cycle past 8.
CATEGORICAL = [
    "#3987e5",  # blue
    "#008300",  # green
    "#d55181",  # magenta
    "#c98500",  # yellow
    "#199e70",  # aqua
    "#d95926",  # orange
    "#9085e9",  # violet
    "#e66767",  # red
]

SEQUENTIAL_BLUE = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]

DIVERGING = ["#3987e5", "#383835", "#e66767"]  # blue -> neutral gray -> red

# Status roles — reserved for state/delta, never reused as a categorical series.
STATUS_GOOD = "#0ca30c"
STATUS_WARNING = "#fab219"
STATUS_SERIOUS = "#ec835a"
STATUS_CRITICAL = "#d03b3b"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=TEXT_SECONDARY, size=12),
    margin=dict(l=48, r=16, t=16, b=32),
    xaxis=dict(gridcolor=GRIDLINE, zerolinecolor=BASELINE, linecolor=BASELINE, tickfont=dict(color=TEXT_MUTED)),
    yaxis=dict(gridcolor=GRIDLINE, zerolinecolor=BASELINE, linecolor=BASELINE, tickfont=dict(color=TEXT_MUTED)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SECONDARY)),
    hoverlabel=dict(bgcolor="#242423", font=dict(color=TEXT_PRIMARY), bordercolor=BORDER),
)


def delta_color(value: float | None) -> str:
    if value is None:
        return TEXT_MUTED
    return STATUS_GOOD if value >= 0 else STATUS_CRITICAL

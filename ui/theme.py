from __future__ import annotations

SURFACE = "#1a1a19"
PAGE_PLANE = "#0d0d0d"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#c3c2b7"
TEXT_MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BASELINE = "#383835"
BORDER = "rgba(255,255,255,0.10)"

CATEGORICAL = [
    "#3987e5",
    "#008300",
    "#d55181",
    "#c98500",
    "#199e70",
    "#d95926",
    "#9085e9",
    "#e66767",
]

SEQUENTIAL_BLUE = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]

DIVERGING = ["#3987e5", "#383835", "#e66767"]

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


HEATMAP_DOWN = STATUS_CRITICAL
HEATMAP_MID = BASELINE
HEATMAP_UP = STATUS_GOOD
HEATMAP_CLAMP = 3.0
HEATMAP_PARENT = "#242423"

FEAR_TINT = "#e66767"
GREED_TINT = "#4cb84c"


def delta_color(value: float | None) -> str:
    if value is None:
        return TEXT_MUTED
    return STATUS_GOOD if value >= 0 else STATUS_CRITICAL


def with_alpha(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"



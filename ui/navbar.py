from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


def build_navbar() -> dbc.Navbar:
    links = [
        dbc.NavItem(dbc.NavLink(page["name"], href=page["path"], className="nav-link-item"))
        for page in dash.page_registry.values()
    ]
    return dbc.Navbar(
        dbc.Container(
            [
                html.Div(
                    [
                        html.Span("◆", className="brand-mark"),
                        html.Span("Finance Research Dashboard", className="brand-text"),
                    ],
                    className="brand",
                ),
                dbc.Nav(links, className="ms-4 me-auto", navbar=True),
                dcc.Input(
                    id="global-ticker-search",
                    type="text",
                    placeholder="Search ticker…",
                    debounce=True,
                    className="ticker-search",
                ),
            ],
            fluid=True,
            className="d-flex align-items-center",
        ),
        color=None,
        dark=True,
        className="app-navbar",
    )

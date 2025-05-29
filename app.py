import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

FA621 = "https://use.fontawesome.com/releases/v6.2.1/css/all.css"
APP_TITLE = "SWP Climate Adaptation Plan Dashboard"

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.SPACELAB,  # Dash Themes CSS
        FA621,  # Font Awesome Icons CSS
    ],
    title=APP_TITLE,
    use_pages=True,
)

pages = [
    dbc.NavItem(dbc.NavLink(page["name"], href=page["relative_path"]))
    for page in dash.page_registry.values()
]

navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
            [
                html.Img(src="/assets/dwr_seal.png", height="50px", className="me-2"),
                html.Span("State Water Project Climate Adaptation Plan", style={"fontSize": "2rem"})
            ],
            href="/",
            style={"color": "white", "display": "flex", "alignItems": "center"}
        ),

        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

        dbc.Collapse(
            dbc.Nav(pages,
                    className="ms-auto",
                    navbar=True
                    ),
            id="navbar-collapse",
            is_open=False,
            navbar=True,
        )
    ]),
    color="#007fbd",  # still needs custom CSS for full override
    dark=True,
    sticky="top"
)

# Callback to handle toggling collapse on mobile
@app.callback(
    dash.Output("navbar-collapse", "is_open"),
    dash.Input("navbar-toggler", "n_clicks"),
    dash.State("navbar-collapse", "is_open"),
)
def toggle_navbar(n, is_open):
    if n:
        return not is_open
    return is_open

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        navbar,
        dash.page_container,
    ],
)

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)

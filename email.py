navbar = dbc.Navbar(
    dbc.Container(
        [
            html.Img(src="/assets/TD_Securities_logo.svg", height="40px"),
            dbc.NavbarBrand(
                "Vega Map Generator",
                className="fw-bold text-dark"
            ),
        ],
        fluid=True,
        className="px-0"
    ),
    className="bg-white shadow-sm",
    sticky="top",
    style={"padding":"20px 0"}
)

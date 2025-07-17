navbar = dbc.Navbar(
    dbc.Container([
        html.Img(src="/assets/TD_Securities_logo.svg", height="40px"),
        dbc.NavbarBrand("Vega Map Generator", className="ms-3 fw-bold text-dark"),
    ]),
    className="bg-white shadow-sm",
    sticky="top",
    style={"padding":"20px"}
)

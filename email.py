navbar = dbc.Navbar(
    dbc.Container(
        dbc.NavbarBrand(
            [
                html.Img(
                    src="/assets/TD_Securities_logo.svg",
                    height="40px",
                    className="me-1"   
                ),
                html.Span(
                    "Vega Map Generator",
                    className="fw-bold text-dark"
                ),
            ],
            className="d-flex align-items-center px-0"
        ),
        fluid=True,
        className="px-0" 
    ),
    className="bg-white shadow-sm",
    sticky="top",
    style={"padding":"20px 0"} 
)

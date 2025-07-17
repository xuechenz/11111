navbar = dbc.Navbar(
    dbc.Container([
        html.Img(src="/assets/TD_Securities_logo.svg", height="40px"),
        dbc.NavbarBrand(
            html.Span(
                "Vega Map Generator",
                style={"color": "green"}  
            ),
            className="ms-3 fw-bold",
            style={
                "backgroundColor": "white",                        
                "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)",    
                "padding": "6px 12px",                            
                "borderRadius": "6px"                       
            }
        ),
    ]),
    light=True,             
    style={"boxShadow": "none"}, 
    sticky="top"
)

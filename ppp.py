external = [
    dbc.themes.LUX,                                
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css"
]

app = dash.Dash(__name__, external_stylesheets=external, suppress_callback_exceptions=True)
server = app.server
app.title = "GED Manager"

navbar = dbc.NavbarSimple(                        
    brand=html.Span([
        html.Img(src="assets/TD_Securities_logo.svg",
                 height="32px",
                 className="me-2"),
        "GED MANAGER"
    ], className="d-flex align-items-center"),
    color="light",
    className="mb-4 shadow-sm",
    brand_style={"fontWeight": "bold",
                 "fontSize": "20px",
                 "color": "black"}
)

app.layout = dbc.Container(                        
    [
        navbar,                                  
        html.H2("GED Manager"),                   
        dcc.Tabs(id='tabs-example', value='tab-1', children=[
            dcc.Tab(label='Volatility', value='volatility', id='volatility', children=[]),
            dcc.Tab(label='Dividend',   value='dividend',   id='dividend',   children=[]),
            dcc.Tab(label='Repo',       value='repo',       id='repo',       children=[]),
            dcc.Tab(label='Rate',       value='rate',       id='rate',       children=[]),
            dcc.Tab(label='Correlation',value='correlation',id='correlation',children=[]),
            dcc.Tab(label='Spot',       value='spot',       id='spot',       children=[]),
        ],
        className="mb-4",
        colors={                               
            "border": "transparent",
            "primary": "#0d6efd",
            "background": "#f8f9fa"
        }),
        html.Div(id='tabs-example-content')
    ],
    fluid=True,
    class_name="px-4"                           
)

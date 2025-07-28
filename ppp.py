import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.LUX,     
                        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True    
app.layout = dbc.Container([

    dbc.NavbarSimple(
        brand=html.Span("GED MANAGER", className="fw-bold"),
        color="light",
        className="mb-4 shadow-sm",
        brand_style={"fontSize":"24px", "color":"black"}
    ),

    dbc.Row([
        dbc.Col(
            dcc.Tabs(
                id='tabs-example',               
                value='tab-1',                    
                children=[
                    dcc.Tab(label='Volatility',  value='volatility',  id='volatility',  children=[]),
                    dcc.Tab(label='Dividend',    value='dividend',    id='dividend',    children=[]),
                    dcc.Tab(label='Repo',        value='repo',        id='repo',        children=[]),
                    dcc.Tab(label='Rate',        value='rate',        id='rate',        children=[]),
                    dcc.Tab(label='Correlation', value='correlation', id='correlation', children=[]),
                    dcc.Tab(label='Spot',        value='spot',        id='spot',        children=[]),
                ],
                colors={"border":"transparent",
                        "primary":"#0defd",
                        "background":"#f8f9fa"}
            ),
            width=12
        )
    ]),

    dbc.Row([
        dbc.Col(html.Div(id='tabs-example-content'), width=12)
    ])

], fluid=True, className="px-4")

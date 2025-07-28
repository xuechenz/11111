app.layout = dbc.Container([
    navbar,
    dbc.Tabs(
        id='tabs-example',                
        active_tab='volatility',          
        pills=True,                      
        children=[
            dbc.Tab(label='Volatility',  tab_id='volatility'),
            dbc.Tab(label='Dividend',    tab_id='dividend'),
            dbc.Tab(label='Repo',        tab_id='repo'),
            dbc.Tab(label='Rate',        tab_id='rate'),
            dbc.Tab(label='Correlation', tab_id='correlation'),
            dbc.Tab(label='Spot',        tab_id='spot'),
        ]
    ),
    html.Div(id='tabs-example-content')
], fluid=True, class_name="px-4")

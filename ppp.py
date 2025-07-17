dcc.Tab(label="Vega Map", children=[
    html.Div(id="progress-text", style={"margin":"10px 0"}),
    dcc.Loading(dcc.Graph(id="vega-heatmap"), type="circle"),
    html.Div(id="vega-extra-container", style={"marginTop":"20px"}),
    dbc.Button("Download Vega CSV", id="btn-dl-vega-csv", color="secondary", className="mt-3 me-2", disabled=True),
    dbc.Button("Download Vega Map", id="btn-dl-vega-png", color="secondary", className="mt-3", disabled=True),
    dcc.Download(id="dl-vega-csv"),
    dcc.Download(id="dl-vega-png"),
    dcc.Interval(id="vega-worker", interval=500, n_intervals=0, disabled=True),
])

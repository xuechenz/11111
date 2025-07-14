bump_tab = dcc.Tab(label="Bump Settings", children=[
    dbc.Container([
        textarea("bump_stock_ids", "Bump Stock IDs", DEFAULTS["Bump_Stock_IDs"]),
        textarea("bump_sizes", "Bump Sizes", DEFAULTS["Bump_Sizes"]),
        dbc.Button("Save Bump Settings", id="btn-save-bump", color="primary", className="mt-2"),
    ], className="p-3")
])

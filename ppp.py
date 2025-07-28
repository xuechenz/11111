# ========= 1. Volatility =========
@app.callback(Output('volatility', 'children'),
              Input('tabs-example', 'active_tab'))
def update_tabs1(active_tab):
    if active_tab == 'volatility':
        return dbc.Tabs(
            id='subtabs1',
            active_tab='subtab1-1',
            pills=True, justify=True,
            children=[
                dbc.Tab(label='Data',          tab_id='subtab1-1'),
                dbc.Tab(label='Visualization', tab_id='subtab1-2'),
                dbc.Tab(label='Analysis',      tab_id='subtab1-3'),
                dbc.Tab(label='Benchmark',     tab_id='subtab1-4'),
                dbc.Tab(label='Fitter',        tab_id='subtab1-5'),
                dbc.Tab(label='Spread',        tab_id='subtab1-6'),
            ]
        )

# ========= 2. Dividend =========
@app.callback(Output('dividend', 'children'),
              Input('tabs-example', 'active_tab'))
def update_tabs2(active_tab):
    if active_tab == 'dividend':
        return dbc.Tabs(
            id='subtabs2',
            active_tab='subtab2-1',
            pills=True, justify=True,
            children=[
                dbc.Tab(label='Data',          tab_id='subtab2-1'),
                dbc.Tab(label='Visualization', tab_id='subtab2-2'),
                dbc.Tab(label='Analysis',      tab_id='subtab2-3'),
                dbc.Tab(label='Benchmark',     tab_id='subtab2-4'),
                dbc.Tab(label='Fitter',        tab_id='subtab2-5'),
                dbc.Tab(label='Spread',        tab_id='subtab2-6'),
            ]
        )

# ========= 3. Repo =========
@app.callback(Output('repo', 'children'),
              Input('tabs-example', 'active_tab'))
def update_tabs3(active_tab):
    if active_tab == 'repo':
        return dbc.Tabs(
            id='subtabs3',
            active_tab='subtab3-1',
            pills=True, justify=True,
            children=[
                dbc.Tab(label='Data',          tab_id='subtab3-1'),
                dbc.Tab(label='Visualization', tab_id='subtab3-2'),
                dbc.Tab(label='Analysis',      tab_id='subtab3-3'),
                dbc.Tab(label='Benchmark',     tab_id='subtab3-4'),
                dbc.Tab(label='Fitter',        tab_id='subtab3-5'),
                dbc.Tab(label='Spread',        tab_id='subtab3-6'),
            ]
        )

# ========= 4. Rate =========
@app.callback(Output('rate', 'children'),
              Input('tabs-example', 'active_tab'))
def update_tabs4(active_tab):
    if active_tab == 'rate':
        return dbc.Tabs(
            id='subtabs4',
            active_tab='subtab4-1',
            pills=True, justify=True,
            children=[
                dbc.Tab(label='Data',          tab_id='subtab4-1'),
                dbc.Tab(label='Visualization', tab_id='subtab4-2'),
                dbc.Tab(label='Analysis',      tab_id='subtab4-3'),
                dbc.Tab(label='Benchmark',     tab_id='subtab4-4'),
                dbc.Tab(label='Fitter',        tab_id='subtab4-5'),
                dbc.Tab(label='Spread',        tab_id='subtab4-6'),
            ]
        )

# ========= 5. Correlation =========
@app.callback(Output('correlation', 'children'),
              Input('tabs-example', 'active_tab'))
def update_tabs5(active_tab):
    if active_tab == 'correlation':
        return dbc.Tabs(
            id='subtabs5',
            active_tab='subtab5-1',
            pills=True, justify=True,
            children=[
                dbc.Tab(label='Data',          tab_id='subtab5-1'),
                dbc.Tab(label='Visualization', tab_id='subtab5-2'),
                dbc.Tab(label='Analysis',      tab_id='subtab5-3'),
                dbc.Tab(label='Benchmark',     tab_id='subtab5-4'),
                dbc.Tab(label='Fitter',        tab_id='subtab5-5'),
                dbc.Tab(label='Spread',        tab_id='subtab5-6'),
            ]
        )

# ========= 6. Spot =========
@app.callback(Output('spot', 'children'),
              Input('tabs-example', 'active_tab'))
def update_tabs6(active_tab):
    if active_tab == 'spot':
        return dbc.Tabs(
            id='subtabs6',
            active_tab='subtab6-1',
            pills=True, justify=True,
            children=[
                dbc.Tab(label='Data',          tab_id='subtab6-1'),
                dbc.Tab(label='Visualization', tab_id='subtab6-2'),
                dbc.Tab(label='Analysis',      tab_id='subtab6-3'),
                dbc.Tab(label='Benchmark',     tab_id='subtab6-4'),
                dbc.Tab(label='Fitter',        tab_id='subtab6-5'),
                dbc.Tab(label='Spread',        tab_id='subtab6-6'),
            ]
        )

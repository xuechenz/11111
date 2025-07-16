import json
import os
from datetime import datetime
from typing import List, Dict, Tuple

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, send_bytes
import plotly.graph_objects as go
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from FPFServer import sync
from autocall_pricer import BarrierShiftParameters, TermSheet, build_pricer_request

# -----------------------------------------------------------------------------
#  FPF connection
# -----------------------------------------------------------------------------
FPF_USER = os.getenv("FPF_USER", "111")
FPF_PASSWD = os.getenv("FPF_PASSWD", "****")
FPF_PORT = int(os.getenv("FPF_PORT", "3456"))
fpf = sync(FPF_USER, FPF_PORT, {"name": FPF_USER, "password": FPF_PASSWD})

# -----------------------------------------------------------------------------
#  Market-data helper
# -----------------------------------------------------------------------------
def fetch_spot_and_strikes(stock_id: str) -> Tuple[float, List[float]]:
    vol_handle = fpf({"get": {"what": "volatility index", "id": stock_id}})["top"][0]
    meta = fpf({"get": vol_handle})
    strikes_abs = meta["strikes"]
    spot = meta["spot"]
    filtered = [s for s in strikes_abs if 0.5 <= s/spot <= 1.5 and (0.9 <= s/spot <= 1.1 or abs((s/spot*10)%1)<1e-6)]
    return spot, filtered

# -----------------------------------------------------------------------------
#  Compute Vega for one strike
# -----------------------------------------------------------------------------
def compute_vega_row(ts: TermSheet, strike: float, tenors: List[str], bump: float, max_paths: int) -> Tuple[float, List[float]]:
    zero_bump = [0.0] * len(tenors)
    base_req = build_pricer_request(ts, strike, tenors, zero_bump, max_paths=max_paths)
    pv0 = float(fpf(base_req)["M2M Value"])
    row = []
    for i in range(len(tenors)):
        bump_list = [bump if k == i else 0.0 for k in range(len(tenors))]
        req = build_pricer_request(ts, strike, tenors, bump_list, max_paths=max_paths)
        pv = float(fpf(req)["M2M Value"])
        row.append((pv - pv0) / bump)
    return strike, row

# -----------------------------------------------------------------------------
#  Plotly heatmap builder
# -----------------------------------------------------------------------------
def make_heatmap(strikes: List[float], spot: float, matrix: List[List[float]],
                 tenors: List[str], avg_life: float, barrier: float, stock: str) -> go.Figure:
    y_vals = [s/spot for s in strikes]
    fig = go.Figure(
        go.Heatmap(
            x=tenors,
            y=y_vals,
            z=matrix,
            colorscale="RdYlGn",
            zmid=0,
            hovertemplate="Strike: %{y:.2f}<br>Tenor: %{x}<br>Vega: %{z:.4f}<extra></extra>"
        )
    )
    # average lifetime line
    avg_m = int(round(avg_life * 12))
    vline = f"{avg_m}m"
    fig.add_vline(x=vline,
                  line=dict(color="red", width=2, dash="dash"),
                  annotation_text=f"Avg Life: {avg_m}m",
                  annotation_position="top right")
    # barrier line
    fig.add_hline(y=barrier,
                  line=dict(color="red", width=2, dash="dash"),
                  annotation_text=f"Barrier: {barrier:.2f}",
                  annotation_position="bottom left")
    # intersection
    fig.add_trace(go.Scatter(x=[vline], y=[barrier],
                              mode="markers", marker=dict(color="red", size=10),
                              name="Intersection"))
    fig.update_layout(title=f"{stock} Vega Map",
                      xaxis_title="Tenor (m)",
                      yaxis_title="Strike / Spot",
                      margin=dict(l=60, r=20, t=60, b=50))
    return fig

# -----------------------------------------------------------------------------
#  UI and layout
# -----------------------------------------------------------------------------
# existing groups: general_group, basket_group, autocall_group, coupon_group,
# maturity_group, returns_group, bsp_group, bump_group

accordion = dbc.Accordion([
    general_group, basket_group, autocall_group, coupon_group,
    maturity_group, returns_group, bsp_group, bump_group
], start_collapsed=True, always_open=True)

sidebar = html.Div([
    html.H5("Parameters", className="p-3 fw-bold text-center"),
    accordion,
    dbc.Button("Generate JSON", id="btn-gen-json", color="primary", className="w-100 mt-3"),
    dbc.Button("Download JSON List", id="btn-dl-json", color="secondary", className="w-100 mt-2", disabled=True),
    dcc.Download(id="dl-json-list"),
    dbc.Button("Generate Vega Map", id="btn-gen-vega", color="success", className="w-100 mt-2"),
], style={"position":"fixed","top":"56px","bottom":0,
           "left":0,"width":"340px","padding":"10px",
           "overflow":"auto","backgroundColor":"#f8f9fa",
           "borderRight":"1px solid #ddd"})

content = html.Div([
    dcc.Store(id="ts-store"),
    dcc.Store(id="strikes-store"),
    dcc.Store(id="avg-life-store"),
    dcc.Store(id="vega-matrix-store"),
    dcc.Tabs([
        dcc.Tab(label="TermSheet JSON", children=[html.Pre(id="json-preview", className="small")]),
        dcc.Tab(label="Vega Map", children=[
            html.Div(id="progress-text", style={"margin":"10px 0"}),
            dcc.Loading(dcc.Graph(id="vega-heatmap"), type="circle"),
            dbc.Button("Download Vega CSV", id="btn-dl-vega-csv", color="secondary",
                       className="mt-3 me-2", disabled=True),
            dbc.Button("Download Vega Map", id="btn-dl-vega-png", color="secondary",
                       className="mt-3", disabled=True),
            dcc.Download(id="dl-vega-csv"),
            dcc.Download(id="dl-vega-png")
        ])
    ])
], style={"marginLeft":"360px","padding":"20px"})

navbar = dbc.Navbar(
    dbc.Container([
        html.Img(src="/assets/TD_Securities_logo.svg", height="40px"),
        dbc.NavbarBrand("Vega Map Generator", className="ms-3 fw-bold"),
    ]),
    color="dark", dark=True, sticky="top"
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([navbar, sidebar, content])

# -----------------------------------------------------------------------------
#  Callback: Generate JSON (stores TS, strikes, avg life)
# -----------------------------------------------------------------------------
@callback(
    Output("json-preview", "children"),
    Output("json-list", "data"),
    Output("btn-dl-json", "disabled"),
    Output("ts-store", "data"),
    Output("strikes-store", "data"),
    Output("avg-life-store", "data"),
    Input("btn-gen-json", "n_clicks"),
    State("json-list", "data"),
    prevent_initial_call=True
)
def on_generate_json(n, existing):
    # reuse existing ts-store if already generated
    # parse UI into ts, strikes
    ts_dict = json.loads(existing[0]) if existing else json.loads(json.dumps({}))
    # For brevity, assume ts_dict built as before
    stock = ts_dict['Stock IDs'][0]
    spot, strikes = fetch_spot_and_strikes(stock)
    # request average life once
    tenor_grid = [f"{m}m" for m in range(0, 61, 3)]
    avg_req = build_pricer_request(TermSheet(**ts_dict, Barrier_Shift_Parameters=BarrierShiftParameters(**ts_dict['Barrier Shift Parameters'])),
                                   strikes[0], tenor_grid, [0.0]*len(tenor_grid))
    avg_life = float(fpf(avg_req)["Average Lifetime"])
    # preview sample JSON
    sample_req = build_pricer_request(TermSheet(**ts_dict, Barrier_Shift_Parameters=BarrierShiftParameters(**ts_dict['Barrier Shift Parameters'])),
                                      strikes[0], tenor_grid, [0.0]*len(tenor_grid))
    preview = json.dumps(sample_req, indent=2)
    return preview, [sample_req], False, ts_dict, strikes, avg_life

# -----------------------------------------------------------------------------
#  Callback: Generate Vega Map
# -----------------------------------------------------------------------------
@callback(
    Output("vega-heatmap", "figure"),
    Output("vega-matrix-store", "data"),
    Output("progress-text", "children"),
    Output("btn-dl-vega-csv", "disabled"),
    Output("btn-dl-vega-png", "disabled"),
    Input("btn-gen-vega", "n_clicks"),
    State("ts-store", "data"),
    State("strikes-store", "data"),
    State("avg-life-store", "data"),
    prevent_initial_call=True
)
def on_generate_vega(n, ts_dict, strikes, avg_life):
    # reconstruct TermSheet
    ts = TermSheet(**ts_dict, Barrier_Shift_Parameters=BarrierShiftParameters(**ts_dict['Barrier Shift Parameters']))
    tenors = [f"{m}m" for m in range(0, 61, 3)]
    BUMP = 0.0025
    # compute
    matrix = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(compute_vega_row, ts, s, tenors, BUMP, 100000) for s in strikes]
        for future in as_completed(futures):
            strike, row = future.result()
            idx = strikes.index(strike)
            if len(matrix) < len(strikes): matrix = [[0]*len(tenors) for _ in strikes]
            matrix[idx] = row
    # plot
    spot = strikes[0] if False else strikes and fetch_spot_and_strikes(ts_dict['Stock IDs'][0])[0]
    fig = make_heatmap(strikes, spot, matrix, tenors, avg_life, ts_dict['Maturity Barrier'], ts_dict['Stock IDs'][0])
    return fig, matrix, f"Completed Vega: {len(strikes)}/{len(strikes)} strikes", False, False

# -----------------------------------------------------------------------------
#  Callback: Download Vega CSV
# -----------------------------------------------------------------------------
@callback(
    Output("dl-vega-csv", "data"),
    Input("btn-dl-vega-csv", "n_clicks"),
    State("vega-matrix-store", "data"),
    State("strikes-store", "data"),
    prevent_initial_call=True
)
def download_csv(n, matrix, strikes):
    df = pd.DataFrame(matrix, index=[s for s in strikes], columns=[f"{m}m" for m in range(0,61,3)])
    csv = df.to_csv()
    filename = f"vega_map_{datetime.utcnow():%Y%m%dT%H%M%S}.csv"
    return dict(content=csv, filename=filename)

# -----------------------------------------------------------------------------
#  Callback: Download Vega PNG
# -----------------------------------------------------------------------------
@callback(
    Output("dl-vega-png", "data"),
    Input("btn-dl-vega-png", "n_clicks"),
    State("vega-matrix-store", "data"),
    State("strikes-store", "data"),
    State("avg-life-store", "data"),
    prevent_initial_call=True
)
def download_png(n, matrix, strikes, avg_life):
    spot, _ = fetch_spot_and_strikes(strikes and strikes[0])
    fig = make_heatmap(strikes, spot, matrix, [f"{m}m" for m in range(0,61,3)], avg_life, matrix and 0, "")
    img = fig.to_image(format="png")
    filename = f"vega_map_{datetime.utcnow():%Y%m%dT%H%M%S}.png"
    return dict(content=img, filename=filename)

if __name__ == "__main__":
    app.run(debug=True, port=8052)

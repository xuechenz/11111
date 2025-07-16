import json
import os
from datetime import datetime
from typing import List, Dict, Tuple

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, send_bytes
import plotly.graph_objects as go
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
    pv0 = float(fpf(build_pricer_request(ts, strike, tenors, zero_bump, max_paths=max_paths))["M2M Value"])
    row = []
    for i in range(len(tenors)):
        bump_list = [bump if k == i else 0.0 for k in range(len(tenors))]
        pv = float(fpf(build_pricer_request(ts, strike, tenors, bump_list, max_paths=max_paths))["M2M Value"])
        row.append((pv - pv0) / bump)
    return strike, row

# -----------------------------------------------------------------------------
#  Plotly heatmap builder
# -----------------------------------------------------------------------------
def make_heatmap(strikes: List[float], spot: float, matrix: List[List[float]], tenors: List[str], avg_life: float, barrier: float, stock: str) -> go.Figure:
    y_vals = [s/spot for s in strikes]
    fig = go.Figure(
        go.Heatmap(x=tenors, y=y_vals, z=matrix, colorscale="RdYlGn", zmid=0,
                   hovertemplate="Strike: %{y:.2f}<br>Tenor: %{x}<br>Vega: %{z:.4f}<extra></extra>")
    )
    avg_m = int(round(avg_life * 12))
    vline = f"{avg_m}m"
    fig.add_vline(x=vline, line=dict(color="red", width=2, dash="dash"),
                  annotation_text=f"Avg Life: {avg_m}m", annotation_position="top right")
    fig.add_hline(y=barrier, line=dict(color="red", width=2, dash="dash"),
                  annotation_text=f"Barrier: {barrier:.2f}", annotation_position="bottom left")
    fig.add_trace(go.Scatter(x=[vline], y=[barrier], mode="markers", marker=dict(color="red", size=10), name="Intersection"))
    fig.update_layout(title=f"{stock} Vega Map", xaxis_title="Tenor (m)", yaxis_title="Strike / Spot",
                      margin=dict(l=60, r=20, t=60, b=50))
    return fig

# -----------------------------------------------------------------------------
#  UI Definitions (omitting group defs for brevity)
# -----------------------------------------------------------------------------
accordion = dbc.Accordion([general_group, basket_group, autocall_group, coupon_group, maturity_group, returns_group, bsp_group, bump_group], start_collapsed=True, always_open=True)
sidebar = html.Div([
    html.H5("Parameters", className="p-3 fw-bold text-center"),
    accordion,
    dbc.Button("Generate JSON", id="btn-gen-json", color="primary", className="w-100 mt-3"),
    dbc.Button("Download JSON List", id="btn-dl-json", color="secondary", className="w-100 mt-2", disabled=True),
    dcc.Download(id="dl-json-list"),
    dbc.Button("Generate Vega Map", id="btn-gen-vega", color="success", className="w-100 mt-2")
], style={"position":"fixed","top":"56px","bottom":0,"left":0,"width":"340px","padding":"10px","overflow":"auto","backgroundColor":"#f8f9fa","borderRight":"1px solid #ddd"})
content = html.Div([
    dcc.Tabs([
        dcc.Tab(label="TermSheet JSON", children=[html.Pre(id="json-preview", className="small")]),
        dcc.Tab(label="Vega Map", children=[
            html.Div(id="progress-text", style={"margin":"10px 0"}),
            dcc.Loading(dcc.Graph(id="vega-heatmap"), type="circle"),
            dbc.Button("Download Vega CSV", id="btn-dl-vega-csv", color="secondary", className="mt-3 me-2", disabled=True),
            dbc.Button("Download Vega Map", id="btn-dl-vega-png", color="secondary", className="mt-3", disabled=True),
            dcc.Download(id="dl-vega-csv"), dcc.Download(id="dl-vega-png")
        ])
    ])
], style={"marginLeft":"360px","padding":"20px"})
navbar = dbc.Navbar(dbc.Container([html.Img(src="/assets/TD_Securities_logo.svg",height="40px"),dbc.NavbarBrand("Vega Map Generator",className="ms-3 fw-bold")]), color="dark", dark=True, sticky="top")
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([navbar, sidebar, content])

# -----------------------------------------------------------------------------
#  Callback: Generate Vega Map using ThreadPoolExecutor
# -----------------------------------------------------------------------------
@callback(
    Output("vega-heatmap","figure"),
    Output("progress-text","children"),
    Output("btn-dl-vega-csv","disabled"),
    Output("btn-dl-vega-png","disabled"),
    Input("btn-gen-vega","n_clicks"),
    State("ts-store","data"),
    State("strikes-store","data"),
    State("avg-life-store","data"),
    prevent_initial_call=True
)
def on_generate_vega(n_clicks, ts_dict: Dict, strikes: List[float], avg_life: float):
    # Reconstruct TermSheet
    bsp = BarrierShiftParameters(**ts_dict['Barrier Shift Parameters'])
    ts = TermSheet(**{**ts_dict, 'Barrier_Shift_Parameters': bsp})
    tenors = [f"{m}m" for m in range(0,61,3)]
    spot = ts_dict['Initial Levels'][0]
    barrier = ts_dict['Maturity Barrier']
    stock = ts_dict['Stock IDs'][0]
    # Multi-thread compute
    matrix: List[List[float]] = []
    total = len(strikes)
    done = 0
    max_workers = min(16, total)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(compute_vega_row, ts, s, tenors, 0.0025, 100000): s for s in strikes}
        for future in as_completed(futures):
            strike, row = future.result()
            matrix.append(row)
            done += 1
    fig = make_heatmap(strikes, spot, matrix, tenors, avg_life, barrier, stock)
    # Enable downloads after done
    return fig, f"Done: {done}/{total}", False, False

# -----------------------------------------------------------------------------
#  Download callbacks (unchanged)...
# -----------------------------------------------------------------------------
# toggle_download, download_csv, download_png definitions here

if __name__ == "__main__": app.run(debug=True, port=8052)

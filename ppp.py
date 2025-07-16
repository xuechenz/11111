import json
import os
from datetime import datetime
from typing import List, Dict, Tuple

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed

from FPFServer import sync
from autocall_pricer import BarrierShiftParameters, TermSheet, build_pricer_request

# -----------------------------------------------------------------------------
#  FPF connection settings
# -----------------------------------------------------------------------------
FPF_HOST   = os.getenv("FPF_HOST", "mkcoe04")
FPF_PORT   = int(os.getenv("FPF_PORT", "3456"))
FPF_USER   = os.getenv("FPF_USER", "111")
FPF_PASSWD = os.getenv("FPF_PASSWD", "****")

fpf = sync(
    FPF_USER,
    FPF_PORT,
    {"name": FPF_USER, "password": FPF_PASSWD},
)

# -----------------------------------------------------------------------------
#  Market‑data helper – fetch spot & filtered strikes
# -----------------------------------------------------------------------------
def fetch_spot_and_strikes(stock_id: str) -> Tuple[float, List[float]]:
    vol_handle   = fpf({"get": {"what": "volatility index", "id": stock_id}})["top"][0]
    meta         = fpf({"get": vol_handle})
    strikes_abs  = meta["strikes"]
    strike_spot  = meta["spot"]
    filtered     = []
    for s in strikes_abs:
        pct = s / strike_spot
        if 0.5 <= pct <= 1.5 and (0.9 <= pct <= 1.1 or abs((pct * 10) % 1) < 1e-6):
            filtered.append(s)
    return strike_spot, filtered

# -----------------------------------------------------------------------------
#  Compute row of Vega for one strike
# -----------------------------------------------------------------------------
def compute_vega_row(
    ts: TermSheet,
    strike_abs: float,
    tenor_grid: List[str],
    bump_size: float,
    max_paths: int
) -> Tuple[float, List[float]]:
    zero_bump_list = [0.0] * len(tenor_grid)
    req_base = build_pricer_request(ts, strike_abs, tenor_grid, zero_bump_list, max_paths=max_paths)
    pv_before = float(fpf(req_base)["M2M Value"])
    row = []
    for i in range(len(tenor_grid)):
        bump_list = [bump_size if k == i else 0.0 for k in range(len(tenor_grid))]
        req = build_pricer_request(ts, strike_abs, tenor_grid, bump_list, max_paths=max_paths)
        pv_after = float(fpf(req)["M2M Value"])
        row.append((pv_after - pv_before) / bump_size)
    return strike_abs, row

# -----------------------------------------------------------------------------
#  Build Plotly heatmap figure with annotations
# -----------------------------------------------------------------------------
def make_heatmap(
    strikes: List[float],
    spot: float,
    vega_matrix: List[List[float]],
    tenor_grid: List[str],
    avg_life: float,
    barrier_pct: float,
    stock_id: str
) -> go.Figure:
    strikes_pct = [s / spot for s in strikes]
    avg_months = int(round(avg_life * 12))
    avg_label = f"{avg_months}m"
    title = f"{stock_id} Vega Map"
    fig = go.Figure(
        go.Heatmap(
            x=tenor_grid,
            y=strikes_pct,
            z=vega_matrix,
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="Vega"),
            hovertemplate="Strike: %{y:.2f}<br>Tenor: %{x}<br>Vega: %{z:.4f}<extra></extra>"
        )
    )
    # average life vertical line
    if avg_label in tenor_grid:
        fig.add_vline(x=avg_label, line=dict(color="red", width=2), annotation_text=f"Avg Life: {avg_months}m", annotation_position="top")
    else:
        fig.add_vline(x=avg_months, line=dict(color="red", width=2), annotation_text=f"Avg Life: {avg_months}m", annotation_position="top")
    # barrier horizontal line
    fig.add_hline(y=barrier_pct, line=dict(color="red", width=2), annotation_text=f"Barrier: {barrier_pct:.2f}", annotation_position="right")
    fig.update_xaxes(title_text="Tenor (m)")
    fig.update_yaxes(title_text="Strike / Spot")
    fig.update_layout(title_text=title, autosize=True)
    return fig

# -----------------------------------------------------------------------------
#  UI setup omitted for brevity (assume previous definitions intact)
# -----------------------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([sidebar, content])

# -----------------------------------------------------------------------------
#  Generate Vega Map callback
# -----------------------------------------------------------------------------
@callback(
    Output("vega-heatmap", "figure"),
    Input("btn-gen-vega", "n_clicks"),
    [State(i, "value") for i in state_ids],
    prevent_initial_call=True
)
def on_click_vega(n, *vals):
    ui = dict(zip(state_ids, vals))
    # parse BarrierShiftParameters & TermSheet
    bsp = BarrierShiftParameters(...)
    ts = TermSheet(...)
    # market data
    stock_id = ui["stock_ids"].split(",")[0].strip()
    spot, strikes = fetch_spot_and_strikes(stock_id)
    ts.Initial_Levels = [spot]
    tenor_grid = [f"{m}m" for m in range(0, 61, 3)]
    BUMP = 0.0025
    max_paths = 100000
    # fetch avg life once using first strike
    zero_bump = [0.0] * len(tenor_grid)
    base_req = build_pricer_request(ts, strikes[0], tenor_grid, zero_bump, max_paths=max_paths)
    avg_resp = fpf(base_req)
    avg_life = float(avg_resp.get("Average Lifetime", 0.0))
    # parallel vega
    matrix = [[0]*len(tenor_grid) for _ in strikes]
    with ThreadPoolExecutor(max_workers=min(8, len(strikes))) as ex:
        futures = {ex.submit(compute_vega_row, ts, s, tenor_grid, BUMP, max_paths): s for s in strikes}
        for fut in as_completed(futures):
            strike, row = fut.result()
            idx = strikes.index(strike)
            matrix[idx] = row
    barrier_pct = float(ui.get("mat_barrier", 0.0))
    fig = make_heatmap(strikes, spot, matrix, tenor_grid, avg_life, barrier_pct, stock_id)
    return fig

if __name__ == "__main__":
    app.run(debug=True, port=8052)

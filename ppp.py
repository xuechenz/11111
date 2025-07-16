import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx

# External pricing‑engine helpers -------------------------------------------------------------
from FPFServer import sync
from autocall_pricer import (
    BarrierShiftParameters,
    TermSheet,
    build_pricer_request,
)

# ---------------------------------------------------------------------------------------------
# ⚙️  STATIC CONFIG  –  host / port can be changed via env vars so prod & dev share same code.
# ---------------------------------------------------------------------------------------------
FPF_HOST   = os.getenv("FPF_HOST", "111")
FPF_PORT   = int(os.getenv("FPF_PORT", "111"))
FPF_USER   = os.getenv("FPF_USER", "111")         # ⚠️ replace with real creds / use vault in prod
FPF_PASSWD = os.getenv("FPF_PASSWD", "****")        # ⚠️ masked here for safety

# Connect once at start‑up; the TCP channel will be reused by callbacks
fpf = sync(FPF_USER, FPF_PORT, {"name": FPF_USER, "password": FPF_PASSWD})

# ---------------------------------------------------------------------------------------------
# Helper – market data fetch (spot & filtered strike list)
# ---------------------------------------------------------------------------------------------

def fetch_spot_and_strikes(stock_id: str):
    """Query FPF for spot & strikes, then keep 50‑150 % with 10 % step, dense 90‑110 %."""
    vol_handle = fpf({"get": {"what": "volatility index", "id": stock_id}})["top"][0]
    strike_meta = fpf({"get": vol_handle})
    strikes_abs = strike_meta["strikes"]
    strike_spot = strike_meta["spot"]

    pct_strikes = [s / strike_spot for s in strikes_abs]
    filtered_abs = []
    for abs_k, pct in zip(strikes_abs, pct_strikes):
        if 0.5 <= pct <= 1.5:
            if 0.9 <= pct <= 1.1:
                filtered_abs.append(abs_k)
            else:
                if abs(((pct * 10) % 1)) < 1e-6:   # multiples of 10 %
                    filtered_abs.append(abs_k)
    return strike_spot, filtered_abs

# ---------------------------------------------------------------------------------------------
# UI building blocks – kept from previous version & expanded where needed
# ---------------------------------------------------------------------------------------------
DEFAULTS = {...}  # ⚠️  SAME big dict as before (truncated here for brevity)

# ---- small helpers (text_input / textarea / bool_switch) remain unchanged ----
# (omitted in this snippet – keep identical to previous commit)

# ---- accordion groups (general_group, basket_group, etc.) identical to last commit ----
# (omitted – they already cover all TermSheet fields)

accordion = dbc.Accordion([...], start_collapsed=True, always_open=True)  # same as before

sidebar = html.Div([
    html.H5("Parameters", className="p-3 fw-bold text-center"),
    accordion,
    dbc.Button("Generate JSON", id="btn-gen-json", color="primary", className="w-100 mt-3"),
    dbc.Button("Download JSON List", id="btn-dl-json", color="secondary", className="w-100 mt-2", disabled=True),
    dcc.Download(id="dl-json-list"),
], style=dict(position="fixed", top="56px", bottom="0", left="0", width="360px", padding="10px", overflow="auto", backgroundColor="#f8f9fa", borderRight="1px solid #ddd"))

content = html.Div([
    dcc.Tabs([
        dcc.Tab(label="TermSheet JSON", children=[html.Pre(id="json-preview", className="small")]),
    ]),
], style={"marginLeft": "370px", "padding": "20px"})

navbar = dbc.Navbar(
    dbc.Container([
        html.Img(src="/assets/TD_Securities_logo.svg", height="40px"),
        dbc.NavbarBrand("Vega Map Generator", className="ms-3 fw-bold"),
    ]), color="dark", dark=True, sticky="top")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([navbar, sidebar, content, dcc.Store(id="json-list-store")])

# ---------------------------------------------------------------------------------------------
# Parsing helpers (same as before) -------------------------------------------------------------
# ---------------------------------------------------------------------------------------------

def _parse_list(s: str, typ=float):
    if s is None:
        return []
    toks = [x.strip() for x in s.split(',') if x.strip()]
    return toks if typ is str else [typ(t) for t in toks]

def _parse_float(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

def _parse_bool(check_val):
    return bool(check_val)

# ---------------------------------------------------------------------------------------------
# Callback – Generate TermSheet + first bump pricer request & store ALL requests list
# ---------------------------------------------------------------------------------------------

state_ids = [...]  # SAME big list of component IDs as previous commit

@callback(
    Output("json-preview", "children"),
    Output("json-list-store", "data"),
    Output("btn-dl-json", "disabled"),
    Input("btn-gen-json", "n_clicks"),
    [State(cid, "value") for cid in state_ids],
    prevent_initial_call=True,
)
def generate_json(_, *vals):
    user_inputs = dict(zip(state_ids, vals))

    # ► 1. fetch spot & strikes
    stock_id   = _parse_list(user_inputs["stock_ids"], str)[0]
    spot, strikes_abs = fetch_spot_and_strikes(stock_id)

    # ► 2. build BarrierShiftParameters
    bsp = BarrierShiftParameters(
        Autocall_Absolute_Shift=_parse_list(user_inputs["bsp_autocall_shift"]),
        Autocall_Shift_Dates=_parse_list(user_inputs["bsp_autocall_dates"], str),
        Coupon_Absolute_Shift=_parse_list(user_inputs["bsp_coupon_shift"]),
        Coupon_Absolute_Spread=_parse_list(user_inputs["bsp_coupon_spread"]),
        Coupon_Shift_Dates=_parse_list(user_inputs["bsp_coupon_dates"], str),
        Maturity_Barrier_Absolute_Shift=_parse_float(user_inputs["bsp_mat_shift"]),
        Maturity_Barrier_Absolute_Spread=_parse_float(user_inputs["bsp_mat_spread"]),
        Maturity_Barrier_Knock_Out_Levels_Absolute_Shift=_parse_list(user_inputs["bsp_mat_ko_shift"]),
    )

    # ► 3. build TermSheet (Initial_Levels set to spot)
    ts = TermSheet(
        Accrues_When=user_inputs["acc_when"],
        Autocall_Barrier=_parse_list(user_inputs["autocall_barrier"]),
        Autocall_Dates=_parse_list(user_inputs["autocall_dates"], str),
        Autocall_Ex_Dates=_parse_list(user_inputs["autocall_ex_dates"], str),
        Autocall_Pay_Dates=_parse_list(user_inputs["autocall_pay_dates"], str),
        Basket_Level_Type=user_inputs["basket_level_type"],
        Basket_Weights=_parse_list(user_inputs["basket_weights"]),
        Coupon_Determination_Dates=_parse_list(user_inputs["coupon_det_dates"], str),
        Coupon_Determination_Ex_Dates=_parse_list(user_inputs["coupon_det_ex_dates"], str),
        Coupon_Low_Barrier=_parse_list(user_inputs["coupon_low_barrier"]),
        Coupon_Memory_Cutoff_Dates=_parse_list(user_inputs["coupon_mem_cutoff_dates"], str),
        Coupon_Memory_Multiplier=_parse_list(user_inputs["coupon_memory_mult"]),
        Coupon_Multiple_Observation_Barrier_Type=user_inputs["coupon_mult_obs_type"],
        Coupon_Pay_Dates=_parse_list(user_inputs["coupon_pay_dates"], str),
        Daycount_Basis=user_inputs["daycount_basis"],
        Downside_Participation=_parse_float(user_inputs["downside_participation"]),
        Fixed_Return=_parse_list(user_inputs["fixed_return"]),
        Floating_Payment_Multiplier=_parse_float(user_inputs["floating_payment_mult"]),
        Guaranteed_Minimum_Maturity_Return=_parse_float(user_inputs["gmmr"]),
        Initial_Levels=[spot],
        Is_Note=_parse_bool(user_inputs["is_note"]),
        Maturity_Barrier=_parse_float(user_inputs["mat_barrier"]),
        Maturity_Date=user_inputs["mat_date"],
        Maturity_Option_Barrier_Type=user_inputs["mat_opt_type"],
        Maturity_Settlement_Date=user_inputs["mat_settle_date"],
        Participation=_parse_list(user_inputs["participation"]),
        Participation_With_Memory_Coupons=_parse_list(user_inputs["participation_mem"]),
        Pay_ID=user_inputs["pay_id"],
        Premium_Settlement_Date=user_inputs["premium_settle_date"],
        Return_Notional_At_Recall=_parse_bool(user_inputs["ret_notional"]),
        Stock_IDs=[stock_id],
        Strike_Setting_Date=_parse_list(user_inputs["strike_setting_date"], str),
        Variable_Coupon_Strike=_parse_list(user_inputs["variable_coupon_strike"]),
        Variable_Coupon_Strike_With_Memory_Coupons=_parse_list(user_inputs["variable_coupon_strike_mem"]),
        Barrier_Shift_Parameters=bsp,
    )

    # ► 4. Build list of pricer JSONs (baseline + per‑tenor bumps)
    tenor_grid = [f"{m}m" for m in range(0, 61, 3)]
    n_tenor    = len(tenor_grid)
    bump_size  = 0.0025
    zero_bump  = [0.0] * n_tenor

    json_requests: List[Dict] = []

    for strike_abs in strikes_abs:
        # baseline
        json_requests.append(build_pricer_request(ts, strike_abs, tenor_grid, zero_bump))
        # first bump only (tenor 0) – used for preview
        first_bump = [bump_size] + [0.0]*(n_tenor-1)
        json_requests.append(build_pricer_request(ts, strike_abs, tenor_grid, first_bump))

    preview_json = json.dumps(json_requests[1], indent=2)  # display first bump example

    return preview_json, json_requests, False  # enable download button

# ---------------------------------------------------------------------------------------------
# Download callback ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
@callback(Output("dl-json-list", "data"),
          Input("btn-dl-json", "n_clicks"),
          State("json-list-store", "data"),
          prevent_initial_call=True)
def download_json(_, json_list):
    if not json_list:
        return dash.no_update
    fname = f"vega_pricer_requests_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    return dict(content=json.dumps(json_list, indent=2), filename=fname)

# ---------------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8052)

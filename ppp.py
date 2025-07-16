import json
import os
from datetime import datetime
from typing import List, Dict

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback

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

def fetch_spot_and_strikes(stock_id: str):
    vol_handle   = fpf({"get": {"what": "volatility index", "id": stock_id}})["top"][0]
    strike_meta  = fpf({"get": vol_handle})
    strikes_abs  = strike_meta["strikes"]
    strike_spot  = strike_meta["spot"]

    pct_list, filtered = [], []
    for s in strikes_abs:
        pct = s / strike_spot
        pct_list.append(pct)
        if 0.5 <= pct <= 1.5 and (0.9 <= pct <= 1.1 or abs(((pct*10) % 1)) < 1e-6):
            filtered.append(s)
    return strike_spot, filtered

# -----------------------------------------------------------------------------
#  UI helpers
# -----------------------------------------------------------------------------

def text_input(i, lbl, val, **kw):
    return dbc.FormFloating([dbc.Input(id=i, value=val, placeholder=" ", **kw), dbc.Label(lbl)], className="mb-2")

def textarea(i, lbl, val, rows=2):
    return dbc.FormFloating([
        dbc.Textarea(id=i, value=val, placeholder="", style={"height": f"{rows*30}px"}),
        dbc.Label(lbl),
    ], className="mb-2")

def bool_switch(i, lbl, checked):
    return dbc.Checklist(id=i, options=[{"label": lbl, "value": "yes"}], value=["yes"] if checked else [], switch=True, className="mb-2")

# -----------------------------------------------------------------------------
#  Default values (truncated for brevity – keep same as before)
# -----------------------------------------------------------------------------
DEFAULTS = {...}

# -----------------------------------------------------------------------------
#  Build accordion groups (identical to previous except **Initial_Levels removed**)
# -----------------------------------------------------------------------------
# General, Basket, Autocall, Coupon, Maturity definitions unchanged
# Returns group now omits Initial_Levels input
returns_group = dbc.AccordionItem([
    textarea("participation", "Participation", DEFAULTS["Participation"]),
    textarea("participation_mem", "Participation_With_Memory_Coupons", DEFAULTS["Participation_With_Memory_Coupons"]),
    textarea("variable_coupon_strike", "Variable_Coupon_Strike", DEFAULTS["Variable_Coupon_Strike"]),
    textarea("variable_coupon_strike_mem", "Variable_Coupon_Strike_With_Memory_Coupons", DEFAULTS["Variable_Coupon_Strike_With_Memory_Coupons"]),
    bool_switch("ret_notional", "Return_Notional_At_Recall", DEFAULTS["Return_Notional_At_Recall"] == "yes"),
    text_input("downside_participation", "Downside_Participation", DEFAULTS["Downside_Participation"], type="number"),
    textarea("fixed_return", "Fixed_Return", DEFAULTS["Fixed_Return"]),
    text_input("floating_payment_mult", "Floating_Payment_Multiplier", DEFAULTS["Floating_Payment_Multiplier"], type="number"),
    text_input("gmmr", "Guaranteed_Minimum_Maturity_Return", DEFAULTS["Guaranteed_Minimum_Maturity_Return"], type="number"),
], title="Returns & Participation")

# Barrier shift + bump groups unchanged
accordion = dbc.Accordion([...], start_collapsed=True, always_open=True)

sidebar = html.Div([
    html.H5("Parameters", className="p-3 fw-bold text-center"),
    accordion,
    dbc.Button("Generate JSON", id="btn-gen-json", color="primary", className="w-100 mt-3"),
    dbc.Button("Download JSON List", id="btn-dl-json", color="secondary", className="w-100 mt-2", disabled=True),
    dcc.Download(id="dl-json-list"),
])

content = html.Div([
    dcc.Tabs([dcc.Tab(label="TermSheet JSON", children=[html.Pre(id="json-preview", className="small")])]),
])

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([sidebar, content, dcc.Store(id="json-list")])

# -----------------------------------------------------------------------------
#  Parsing helpers
# -----------------------------------------------------------------------------

def _pl(s, typ=float):
    return [typ(x.strip()) for x in s.split(',') if x.strip()] if s else []

def _pf(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

def _pb(v):
    return bool(v)

# -----------------------------------------------------------------------------
#  Component IDs (initial‑levels removed)
# -----------------------------------------------------------------------------
state_ids = [
    # ... full list without "init_levels"
]

@callback(
    Output("json-preview", "children"),
    Output("json-list", "data"),
    Output("btn-dl-json", "disabled"),
    Input("btn-gen-json", "n_clicks"),
    [State(cid, "value") for cid in state_ids],
    prevent_initial_call=True,
)
def build_json(_, *vals):
    ui = dict(zip(state_ids, vals))

    stock_id = _pl(ui["stock_ids"], str)[0]
    spot, strikes_abs = fetch_spot_and_strikes(stock_id)

    bsp = BarrierShiftParameters(
        Autocall_Absolute_Shift=_pl(ui["bsp_autocall_shift"]),
        Autocall_Shift_Dates=_pl(ui["bsp_autocall_dates"], str),
        Coupon_Absolute_Shift=_pl(ui["bsp_coupon_shift"]),
        Coupon_Absolute_Spread=_pl(ui["bsp_coupon_spread"]),
        Coupon_Shift_Dates=_pl(ui["bsp_coupon_dates"], str),
        Maturity_Barrier_Absolute_Shift=_pf(ui["bsp_mat_shift"]),
        Maturity_Barrier_Absolute_Spread=_pf(ui["bsp_mat_spread"]),
        Maturity_Barrier_Knock_Out_Levels_Absolute_Shift=_pl(ui["bsp_mat_ko_shift"]),
    )

    ts = TermSheet(
        # same as before, but **Initial_Levels=[spot]** and no field sourced from user
        Initial_Levels=[spot],
        # ... all other fields parsed from ui
        Barrier_Shift_Parameters=bsp,
    )

    tenor_grid = [f"{m}m" for m in range(0, 61, 3)]
    zero_bump = [0.0] * len(tenor_grid)
    bump      = [0.0025] + [0.0]*(len(tenor_grid)-1)

    reqs = []
    for k in strikes_abs:
        reqs.append(build_pricer_request(ts, k, tenor_grid, zero_bump))
        reqs.append(build_pricer_request(ts, k, tenor_grid, bump))

    return json.dumps(reqs[1], indent=2), reqs, False

@callback(Output("dl-json-list", "data"), Input("btn-dl-json", "n_clicks"), State("json-list", "data"), prevent_initial_call=True)
def dl(_, data):
    if not data:
        return dash.no_update
    fn = f"vega_requests_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    return dict(content=json.dumps(data, indent=2), filename=fn)

if __name__ == "__main__":
    app.run(debug=True, port=8052)

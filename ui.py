import json
from datetime import datetime
from typing import List

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx

# -------------------------------------------------------------
#  Internal dataclass models come from your pricing library
# -------------------------------------------------------------
from autocall_pricer import TermSheet, BarrierShiftParameters

# ---------------------------------------------------------------------------
#  Helper functions for parsing UI string inputs ➜ python objects
# ---------------------------------------------------------------------------

def _parse_list(s: str, typ=float) -> List:
    """Convert a comma‑separated string to a python list of given type."""
    if s is None:
        return []
    s = s.strip()
    if not s:
        return []
    if typ is str:
        return [x.strip() for x in s.split(",") if x.strip()]
    return [typ(x.strip()) for x in s.split(",") if x.strip()]


def _parse_float(s: str, default: float = 0.0) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _parse_bool(switch_value):
    return bool(switch_value)  # checklist returns ["yes"] when checked

# ---------------------------------------------------------------------------
#  Default values used to pre‑populate the form
# ---------------------------------------------------------------------------
DEFAULTS = dict(
    # General
    Accrues_When="Inside Range",
    Daycount_Basis="ACT/365",
    Pay_ID="USD",
    Stock_IDs="NDX.IDX",
    Strike_Setting_Date="2025-07-07",
    Premium_Settlement_Date="2025-07-10",
    Is_Note="yes",  # checked by default
    # Basket
    Basket_Level_Type="Weighted Sum of Asset Returns",
    Basket_Weights="1",
    # Autocall
    Autocall_Barrier="1,1,1,1",
    Autocall_Dates="2025-11-07,2026-02-09,2026-05-07,2026-08-07",
    Autocall_Ex_Dates="",
    Autocall_Pay_Dates="2025-11-12,2026-02-12,2026-05-12,2026-08-12",
    # Coupon
    Coupon_Determination_Dates="2025-11-10,2026-02-09,2026-05-07,2026-08-07",
    Coupon_Determination_Ex_Dates="",
    Coupon_Low_Barrier="0.7,0.7,0.7,0.7",
    Coupon_Memory_Cutoff_Dates="",
    Coupon_Memory_Multiplier="1,1,1,1",
    Coupon_Multiple_Observation_Barrier_Type="Inside Range",
    Coupon_Pay_Dates="2025-11-12,2026-02-12,2026-05-12,2026-08-12",
    # Maturity
    Maturity_Barrier="0.7",
    Maturity_Date="2026-08-07",
    Maturity_Option_Barrier_Type="Knock-In",
    Maturity_Settlement_Date="2026-08-12",
    # Returns & Participation
    Participation="0,0,0,0",
    Participation_With_Memory_Coupons="0,0,0,0",
    Variable_Coupon_Strike="1,1,1,1",
    Variable_Coupon_Strike_With_Memory_Coupons="1,1,1,1",
    Return_Notional_At_Recall="yes",
    Downside_Participation="1",
    Fixed_Return="0,0,0,0",
    Floating_Payment_Multiplier="1",
    Guaranteed_Minimum_Maturity_Return="0",
    Initial_Levels="22726.0125611",
    # Barrier Shift Parameters
    BSP_Autocall_Absolute_Shift="-0.0087,-0.0087,-0.0087,-0.0087",
    BSP_Autocall_Shift_Dates="2025-11-07,2026-02-09,2026-05-07,2026-08-07",
    BSP_Coupon_Absolute_Shift="-0.0087,-0.0087,-0.0087,-0.0087",
    BSP_Coupon_Absolute_Spread="0.0174,0.0174,0.0174,0.0174",
    BSP_Coupon_Shift_Dates="2025-11-07,2026-02-09,2026-05-07,2026-08-07",
    BSP_Maturity_Barrier_Absolute_Shift="-0.0087",
    BSP_Maturity_Barrier_Absolute_Spread="0.0174",
    BSP_Maturity_Barrier_Knock_Out_Levels_Absolute_Shift="-0.0087",
    # Bumps
    Bump_Stock_IDs="NDX.IDX",
    Bump_Sizes="0.0025",
)

# ---------------------------------------------------------------------------
#  Small UI component helpers
# ---------------------------------------------------------------------------

def text_input(id_, label, value, type_="text", **kwargs):
    return dbc.FormFloating([
        dbc.Input(id=id_, value=value, type=type_, placeholder=" ", **kwargs),
        dbc.Label(label),
    ], className="mb-2")


def textarea(id_, label, value, rows=2):
    return dbc.FormFloating([
        dbc.Textarea(id=id_, value=value, placeholder="", style={"height": f"{rows*30}px"}),
        dbc.Label(label),
    ], className="mb-2")


def bool_switch(id_, label, checked):
    return dbc.Checklist(
        id=id_, options=[{"label": label, "value": "yes"}], value=["yes"] if checked else [], switch=True, className="mb-2"
    )

# ---------------------------------------------------------------------------
#  Accordion groups
# ---------------------------------------------------------------------------
# General
general_group = dbc.AccordionItem([
    text_input("acc_when", "Accrues_When", DEFAULTS["Accrues_When"]),
    text_input("daycount_basis", "Daycount_Basis", DEFAULTS["Daycount_Basis"]),
    text_input("pay_id", "Pay_ID", DEFAULTS["Pay_ID"]),
    textarea("stock_ids", "Stock_IDs", DEFAULTS["Stock_IDs"]),
    text_input("strike_setting_date", "Strike_Setting_Date", DEFAULTS["Strike_Setting_Date"], type_="text"),
    text_input("premium_settle_date", "Premium_Settlement_Date", DEFAULTS["Premium_Settlement_Date"], type_="text"),
    bool_switch("is_note", "Is_Note", DEFAULTS["Is_Note"] == "yes"),
], title="General")

# Basket
basket_group = dbc.AccordionItem([
    text_input("basket_level_type", "Basket_Level_Type", DEFAULTS["Basket_Level_Type"]),
    textarea("basket_weights", "Basket_Weights", DEFAULTS["Basket_Weights"]),
], title="Basket")

# Autocall
autocall_group = dbc.AccordionItem([
    textarea("autocall_barrier", "Autocall_Barrier", DEFAULTS["Autocall_Barrier"]),
    textarea("autocall_dates", "Autocall_Dates", DEFAULTS["Autocall_Dates"]),
    textarea("autocall_ex_dates", "Autocall_Ex_Dates", DEFAULTS["Autocall_Ex_Dates"]),
    textarea("autocall_pay_dates", "Autocall_Pay_Dates", DEFAULTS["Autocall_Pay_Dates"]),
], title="Autocall")

# Coupon
coupon_group = dbc.AccordionItem([
    textarea("coupon_det_dates", "Coupon_Determination_Dates", DEFAULTS["Coupon_Determination_Dates"]),
    textarea("coupon_det_ex_dates", "Coupon_Determination_Ex_Dates", DEFAULTS["Coupon_Determination_Ex_Dates"]),
    textarea("coupon_low_barrier", "Coupon_Low_Barrier", DEFAULTS["Coupon_Low_Barrier"]),
    textarea("coupon_mem_cutoff_dates", "Coupon_Memory_Cutoff_Dates", DEFAULTS["Coupon_Memory_Cutoff_Dates"]),
    textarea("coupon_memory_mult", "Coupon_Memory_Multiplier", DEFAULTS["Coupon_Memory_Multiplier"]),
    text_input("coupon_mult_obs_type", "Coupon_Multiple_Observation_Barrier_Type", DEFAULTS["Coupon_Multiple_Observation_Barrier_Type"]),
    textarea("coupon_pay_dates", "Coupon_Pay_Dates", DEFAULTS["Coupon_Pay_Dates"]),
], title="Coupon")

# Maturity
maturity_group = dbc.AccordionItem([
    text_input("mat_date", "Maturity_Date", DEFAULTS["Maturity_Date"]),
    text_input("mat_barrier", "Maturity_Barrier", DEFAULTS["Maturity_Barrier"], type_="number"),
    text_input("mat_opt_type", "Maturity_Option_Barrier_Type", DEFAULTS["Maturity_Option_Barrier_Type"]),
    text_input("mat_settle_date", "Maturity_Settlement_Date", DEFAULTS["Maturity_Settlement_Date"]),
], title="Maturity")

# Returns & Participation
returns_group = dbc.AccordionItem([
    textarea("participation", "Participation", DEFAULTS["Participation"]),
    textarea("participation_mem", "Participation_With_Memory_Coupons", DEFAULTS["Participation_With_Memory_Coupons"]),
    textarea("variable_coupon_strike", "Variable_Coupon_Strike", DEFAULTS["Variable_Coupon_Strike"]),
    textarea("variable_coupon_strike_mem", "Variable_Coupon_Strike_With_Memory_Coupons", DEFAULTS["Variable_Coupon_Strike_With_Memory_Coupons"]),
    bool_switch("ret_notional", "Return_Notional_At_Recall", DEFAULTS["Return_Notional_At_Recall"] == "yes"),
    text_input("downside_participation", "Downside_Participation", DEFAULTS["Downside_Participation"], type_="number"),
    textarea("fixed_return", "Fixed_Return", DEFAULTS["Fixed_Return"]),
    text_input("floating_payment_mult", "Floating_Payment_Multiplier", DEFAULTS["Floating_Payment_Multiplier"], type_="number"),
    text_input("gmmr", "Guaranteed_Minimum_Maturity_Return", DEFAULTS["Guaranteed_Minimum_Maturity_Return"], type_="number"),
    textarea("init_levels", "Initial_Levels", DEFAULTS["Initial_Levels"]),
], title="Returns & Participation")

# Barrier Shift Parameters
bsp_group = dbc.AccordionItem([
    textarea("bsp_autocall_shift", "Autocall Abs Shift", DEFAULTS["BSP_Autocall_Absolute_Shift"]),
    textarea("bsp_autocall_dates", "Autocall Shift Dates", DEFAULTS["BSP_Autocall_Shift_Dates"]),
    textarea("bsp_coupon_shift", "Coupon Abs Shift", DEFAULTS["BSP_Coupon_Absolute_Shift"]),
    textarea("bsp_coupon_spread", "Coupon Abs Spread", DEFAULTS["BSP_Coupon_Absolute_Spread"]),
    textarea("bsp_coupon_dates", "Coupon Shift Dates", DEFAULTS["BSP_Coupon_Shift_Dates"]),
    text_input("bsp_mat_shift", "Maturity Barrier Abs Shift", DEFAULTS["BSP_Maturity_Barrier_Absolute_Shift"], type_="number"),
    text_input("bsp_mat_spread", "Maturity Barrier Abs Spread", DEFAULTS["BSP_Maturity_Barrier_Absolute_Spread"], type_="number"),
    textarea("bsp_mat_ko_shift", "Maturity KO Abs Shift", DEFAULTS["BSP_Maturity_Barrier_Knock_Out_Levels_Absolute_Shift"]),
], title="Barrier Shift Parameters")

# Bump Settings
bump_group = dbc.AccordionItem([
    textarea("bump_stock_ids", "Bump Stock IDs", DEFAULTS["Bump_Stock_IDs"]),
    textarea("bump_sizes", "Bump Sizes", DEFAULTS["Bump_Sizes"]),
], title="Bump Settings")

# Build accordion and layout
accordion = dbc.Accordion([
    general_group,
    basket_group,
    autocall_group,
    coupon_group,
    maturity_group,
    returns_group,
    bsp_group,
    bump_group,
], start_collapsed=True, always_open=True)

sidebar = html.Div([
    html.H5("Parameters", className="p-3 fw-bold text-center"),
    accordion,
    dbc.Button("Generate JSON", id="btn-gen-json", color="primary", className="w-100 mt-3"),
], style=dict(position="fixed", top="56px", bottom="0", left="0", width="350px", padding="10px", overflow="auto", backgroundColor="#f8f9fa", borderRight="1px solid #ddd"))

content = html.Div([
    dcc.Tabs([
        dcc.Tab(label="TermSheet JSON", children=[html.Pre(id="json-preview", className="small")]),
    ]),
], style={"marginLeft": "360px", "padding": "20px"})

navbar = dbc.Navbar(
    dbc.Container([
        html.Img(id="logo", src="assets/TD_Securities_logo.svg", height="40px"),
        dbc.NavbarBrand("Vega Map Generator", className="ms-3 fw-bold"),
    ]),
    color="dark", dark=True, sticky="top")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([navbar, sidebar, content])

# ---------------------------------------------------------------------------
#  Callback – build TermSheet JSON from user inputs
# ---------------------------------------------------------------------------
_all_state_ids = [
    "acc_when", "daycount_basis", "pay_id", "stock_ids", "strike_setting_date", "premium_settle_date", "is_note",
    "basket_level_type", "basket_weights",
    "autocall_barrier", "autocall_dates", "autocall_ex_dates", "autocall_pay_dates",
    "coupon_det_dates", "coupon_det_ex_dates", "coupon_low_barrier", "coupon_mem_cutoff_dates",
    "coupon_memory_mult", "coupon_mult_obs_type", "coupon_pay_dates",
    "mat_date", "mat_barrier", "mat_opt_type", "mat_settle_date",
    "participation", "participation_mem", "variable_coupon_strike", "variable_coupon_strike_mem",
    "ret_notional", "downside_participation", "fixed_return", "floating_payment_mult", "gmmr", "init_levels",
    "bsp_autocall_shift", "bsp_autocall_dates", "bsp_coupon_shift", "bsp_coupon_spread", "bsp_coupon_dates",
    "bsp_mat_shift", "bsp_mat_spread", "bsp_mat_ko_shift",
    "bump_stock_ids", "bump_sizes",
]

@callback(Output("json-preview", "children"),
          Input("btn-gen-json", "n_clicks"),
          [State(i, "value") for i in _all_state_ids],
          prevent_initial_call=True)
def build_termsheet(n_clicks, *values):
    vals = dict(zip(_all_state_ids, values))

    # ---------------- BarrierShiftParameters ----------------
    bsp = BarrierShiftParameters(
        Autocall_Absolute_Shift=_parse_list(vals["bsp_autocall_shift"]),
        Autocall_Shift_Dates=_parse_list(vals["bsp_autocall_dates"], str),
        Coupon_Absolute_Shift=_parse_list(vals["bsp_coupon_shift"]),
        Coupon_Absolute_Spread=_parse_list(vals["bsp_coupon_spread"]),
        Coupon_Shift_Dates=_parse_list(vals["bsp_coupon_dates"], str),
        Maturity_Barrier_Absolute_Shift=_parse_float(vals["bsp_mat_shift"]),
        Maturity_Barrier_Absolute_Spread=_parse_float(vals["bsp_mat_spread"]),
        Maturity_Barrier_Knock_Out_Levels_Absolute_Shift=_parse_list(vals["bsp_mat_ko_shift"]),
    )

    # ---------------- TermSheet ----------------
    ts = TermSheet(
        Accrues_When=vals["acc_when"],
        Autocall_Barrier=_parse_list(vals["autocall_barrier"]),
        Autocall_Dates=_parse_list(vals["autocall_dates"], str),
        Autocall_Ex_Dates=_parse_list(vals["autocall_ex_dates"], str),
        Autocall_Pay_Dates=_parse_list(vals["autocall_pay_dates"], str),
        Basket_Level_Type=vals["basket_level_type"],
        Basket_Weights=_parse_list(vals["basket_weights"]),
        Coupon_Determination_Dates=_parse_list(vals["coupon_det_dates"], str),
        Coupon_Determination_Ex_Dates=_parse_list(vals["coupon_det_ex_dates"], str),
        Coupon_Low_Barrier=_parse_list(vals["coupon_low_barrier"]),
        Coupon_Memory_Cutoff_Dates=_parse_list(vals["coupon_mem_cutoff_dates"], str),
        Coupon_Memory_Multiplier=_parse_list(vals["coupon_memory_mult"]),
        Coupon_Multiple_Observation_Barrier_Type=vals["coupon_mult_obs_type"],
        Coupon_Pay_Dates=_parse_list(vals["coupon_pay_dates"], str),
        Daycount_Basis=vals["daycount_basis"],
        Downside_Participation=_parse_float(vals["downside_participation"]),
        Fixed_Return=_parse_list(vals["fixed_return"]),
        Floating_Payment_Multiplier=_parse_float(vals["floating_payment_mult"]),
        Guaranteed_Minimum_Maturity_Return=_parse_float(vals["gmmr"]),
        Initial_Levels=_parse_list(vals["init_levels"]),
        Is_Note=_parse_bool(vals["is_note"]),
        Maturity_Barrier=_parse_float(vals["mat_barrier"]),
        Maturity_Date=vals["mat_date"],
        Maturity_Option_Barrier_Type=vals["mat_opt_type"],
        Maturity_Settlement_Date=vals["mat_settle_date"],
        Participation=_parse_list(vals["participation"]),
        Participation_With_Memory_Coupons=_parse_list(vals["participation_mem"]),
        Pay_ID=vals["pay_id"],
        Premium_Settlement_Date=vals["premium_settle_date"],
        Return_Notional_At_Recall=_parse_bool(vals["ret_notional"]),
        Stock_IDs=_parse_list(vals["stock_ids"], str),
        Strike_Setting_Date=_parse_list(vals["strike_setting_date"], str),
        Variable_Coupon_Strike=_parse_list(vals["variable_coupon_strike"]),
        Variable_Coupon_Strike_With_Memory_Coupons=_parse_list(vals["variable_coupon_strike_mem"]),
        Barrier_Shift_Parameters=bsp,
    )

    return json.dumps(ts.to_dict(), indent=2)


if __name__ == "__main__":
    app.run(debug=True, port=8052)

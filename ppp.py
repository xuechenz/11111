"""
Dash App – Vega Map Generator  (UI v3 – Bump Tab added)
========================================================
* Sidebar (Accordion)  ➜ TermSheet inputs
* **NEW Tab ‑ “Bump Settings”** on the main panel  
  • input **Stock IDs**  
  • input **Bump Sizes** (comma‑sep floats)  
  • placeholder button “Save Bump Settings”
* Other tabs unchanged: TermSheet JSON | Vega Map

Run: `python term sheet_dashboard.py` → http://localhost:8052
Place logo at `assets/company_logo.png`
"""

import json
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
from autocall_pricer import TermSheet, BarrierShiftParameters

# ---------------------------------------------------------------------
# Default demo values + bump defaults
# ---------------------------------------------------------------------
DEFAULTS = dict(
    # ------- TermSheet core -------
    Accrues_When="Inside Range",
    Autocall_Barrier="1, 1, 1, 1",
    Autocall_Dates="2025-11-07, 2026-02-09, 2026-05-07, 2026-08-07",
    Autocall_Pay_Dates="2025-11-12, 2026-02-12, 2026-05-12, 2026-08-12",
    Basket_Level_Type="Weighted Sum of Asset Returns",
    Basket_Weights="1",
    Coupon_Determination_Dates="2025-11-10, 2026-02-09, 2026-05-07, 2026-08-07",
    Coupon_Low_Barrier="0.7, 0.7, 0.7, 0.7",
    Coupon_Pay_Dates="2025-11-12, 2026-02-12, 2026-05-12, 2026-08-12",
    Coupon_Memory_Multiplier="1, 1, 1, 1",
    Daycount_Basis="ACT/365",
    Downside_Participation="1",
    Fixed_Return="0, 0, 0, 0",
    Floating_Payment_Multiplier="1",
    Guaranteed_Minimum_Maturity_Return="0",
    Initial_Levels="22726.012561114654",
    Is_Note=True,
    Maturity_Barrier="0.7",
    Maturity_Date="2026-08-07",
    Maturity_Option_Barrier_Type="Knock-In",
    Maturity_Settlement_Date="2026-08-12",
    Participation="0, 0, 0, 0",
    Participation_With_Memory_Coupons="0, 0, 0, 0",
    Pay_ID="USD",
    Premium_Settlement_Date="2025-07-10",
    Return_Notional_At_Recall=True,
    Stock_IDs="NDX.IDX",
    Strike_Setting_Date="2025-07-07",
    Variable_Coupon_Strike="1, 1, 1, 1",

    # ------- Barrier shifts -------
    BSP_Autocall_Absolute_Shift="-0.0087, -0.0087, -0.0087, -0.0087",
    BSP_Autocall_Shift_Dates="2025-11-07, 2026-02-09, 2026-05-07, 2026-08-07",
    BSP_Coupon_Absolute_Shift="-0.0087, -0.0087, -0.0087, -0.0087",
    BSP_Coupon_Absolute_Spread="0.0174, 0.0174, 0.0174, 0.0174",
    BSP_Coupon_Shift_Dates="2025-11-07, 2026-02-09, 2026-05-07, 2026-08-07",
    BSP_Maturity_Barrier_Absolute_Shift="-0.0087",
    BSP_Maturity_Barrier_Absolute_Spread="0.0174",
    BSP_Maturity_Barrier_Knock_Out_Levels_Absolute_Shift="-0.0087",

    # ------- Bump defaults -------
    Bump_Stock_IDs="NDX.IDX",
    Bump_Sizes="0.0025"
)

# -------------------- helper factory --------------------

def text_input(id_, label, value, type_="text"):
    return dbc.FormFloating([
        dbc.Input(id=id_, value=value, type=type_, placeholder=" "),
        dbc.Label(label)
    ], className="mb-2")


def textarea(id_, label, value, rows=2):
    return dbc.FormFloating([
        dbc.Textarea(id=id_, value=value, placeholder=" ", style={"height": f"{rows*30}px"}),
        dbc.Label(label)
    ], className="mb-2")


def bool_switch(id_, label, checked):
    return dbc.Checklist(
        id=id_,
        options=[{"label": label, "value": "yes"}],
        value=["yes"] if checked else [],
        switch=True,
        className="mb-2")

# -------------------- form groups --------------------

general_group = dbc.AccordionItem([
    text_input("acc_when", "Accrues_When", DEFAULTS["Accrues_When"]),
    text_input("daycount_basis", "Daycount_Basis", DEFAULTS["Daycount_Basis"]),
    text_input("pay_id", "Pay_ID", DEFAULTS["Pay_ID"]),
    textarea("stock_ids", "Stock_IDs", DEFAULTS["Stock_IDs"]),
], title="General")

autocall_group = dbc.AccordionItem([
    textarea("autocall_barrier", "Autocall_Barrier", DEFAULTS["Autocall_Barrier"]),
    textarea("autocall_dates", "Autocall_Dates", DEFAULTS["Autocall_Dates"]),
    textarea("autocall_pay_dates", "Autocall_Pay_Dates", DEFAULTS["Autocall_Pay_Dates"]),
], title="Autocall")

coupon_group = dbc.AccordionItem([
    textarea("coupon_det_dates", "Coupon_Determination_Dates", DEFAULTS["Coupon_Determination_Dates"]),
    textarea("coupon_low_barrier", "Coupon_Low_Barrier", DEFAULTS["Coupon_Low_Barrier"]),
    textarea("coupon_memory_mult", "Coupon_Memory_Multiplier", DEFAULTS["Coupon_Memory_Multiplier"]),
    textarea("coupon_pay_dates", "Coupon_Pay_Dates", DEFAULTS["Coupon_Pay_Dates"]),
], title="Coupon")

maturity_group = dbc.AccordionItem([
    text_input("mat_date", "Maturity_Date", DEFAULTS["Maturity_Date"]),
    text_input("mat_barrier", "Maturity_Barrier", DEFAULTS["Maturity_Barrier"], type_="number"),
    text_input("mat_opt_type", "Maturity_Option_Barrier_Type", DEFAULTS["Maturity_Option_Barrier_Type"]),
    text_input("mat_settle_date", "Maturity_Settlement_Date", DEFAULTS["Maturity_Settlement_Date"]),
], title="Maturity")

return_group = dbc.AccordionItem([
    textarea("participation", "Participation", DEFAULTS["Participation"]),
    bool_switch("ret_notional", "Return_Notional_At_Recall", DEFAULTS["Return_Notional_At_Recall"]),
    textarea("variable_coupon_strike", "Variable_Coupon_Strike", DEFAULTS["Variable_Coupon_Strike"]),
], title="Returns & Participation")

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

accordion = dbc.Accordion([
    general_group, autocall_group, coupon_group, maturity_group, return_group, bsp_group
], start_collapsed=True, always_open=True)

sidebar = html.Div([
    html.H5("Parameters", className="p-3 fw-bold text-center"),
    accordion,
    dbc.Button("Generate JSON", id="btn-gen-json", color="primary", className="w-100 mt-3"),
    dbc.Button("Generate Vega Map", id="btn-gen-vega", color="success", className="w-100 mt-2"),
], style={"position": "fixed", "top": "56px", "bottom": 0, "left": 0, "width": "340px", "padding": "10px", "overflowY": "auto", "backgroundColor": "#f8f9fa", "borderRight": "1px solid #ddd"})

# -------------------- Main content --------------------

bump_tab = dcc.Tab(label="Bump Settings", children=[
    dbc.Container([
        textarea("bump_stock_ids", "Bump Stock IDs", DEFAULTS["Bump_Stock_IDs"]),
        textarea("bump_sizes", "Bump Sizes", DEFAULTS["Bump_Sizes"]),
        dbc.Button("Save Bump Settings", id="btn-save-bump", color="primary", className="mt-2"),
    ], className="p-3")
])

content_style = {"marginLeft": "350px", "padding": "20px"}
# -------------------- Main content --------------------

# Bump Settings tab defined above

content_style = {"marginLeft": "350px", "padding": "20px"}
content = html.Div([
    dcc.Tabs([
        dcc.Tab(label="TermSheet JSON", children=[html.Pre(id="json-preview", className="small")]),
        bump_tab,
        dcc.Tab(label="Vega Map", children=[dcc.Graph(id="vega-graph", style={"height": "600px"})]),
    ]),
    dbc.Row([
        dbc.Col(dbc.Button("Download Heatmap PNG", id="btn-dl-png", color="secondary", disabled=True), width="auto"),
        dbc.Col(dbc.Button("Download Vega CSV", id="btn-dl-csv", color="secondary", disabled=True), width="auto"),
    ], className="mt-3 g-2"),
], style=content_style)

# ----------------------- Callbacks -----------------------

@callback(Output("json-preview", "children"), Input("btn-gen-json", "n_clicks"), prevent_initial_call=True)
def build_json(_):
    return "（待接入 TermSheet 构造逻辑）"

@callback(Output("bump_stock_ids", "value"), Input("btn-save-bump", "n_clicks"),
          State("bump_stock_ids", "value"), State("bump_sizes", "value"), prevent_initial_call=True)
def save_bump(_, ids, sizes):
    # placeholder for saving bump configuration
    return ids  # simply echo back

# ---------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True, port=8052)

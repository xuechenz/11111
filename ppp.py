"""
Dash App: TermSheet Builder (UI only – no pricing call yet)
-----------------------------------------------------------
* default values taken from the hard-coded example you sent (2025–2026 NDX.IDX note)
* every TermSheet field is represented by an input component
  - strings / floats → `dcc.Input`
  - lists           → `dcc.Textarea`  (comma-separated)
  - booleans        → `dcc.Checklist` (single check)
  - dates           → just keep them as strings in `YYYY-MM-DD` (same Textarea)
* BarrierShiftParameters 放在一个可折叠 `dbc.Collapse` 区块，默认展开
* 右侧实时 JSON 预览（`dcc.Graph` 里用 `pre` 渲染，后续可替换成美化组件）

下一步（⚠️暂未实现）：把“Generate”按钮的 callback 连接到 build_pricer_request 并允许下载 JSON。
"""

import json
from dash import Dash, html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
from autocall_pricer import TermSheet, BarrierShiftParameters

# --------------------------------------------------
# 1. Default values
# --------------------------------------------------
DEFAULTS = dict(
    Accrues_When="Inside Range",
    Autocall_Barrier="1, 1, 1, 1",
    Autocall_Dates="2025-11-07, 2026-02-09, 2026-05-07, 2026-08-07",
    Autocall_Ex_Dates="2025-11-07, 2026-02-09, 2026-05-07, 2026-08-07",
    Autocall_Pay_Dates="2025-11-12, 2026-02-12, 2026-05-12, 2026-08-12",
    Basket_Level_Type="Weighted Sum of Asset Returns",
    Basket_Weights="1",
    Coupon_Determination_Dates="2025-11-10, 2026-02-09, 2026-05-07, 2026-08-07",
    Coupon_Determination_Ex_Dates="2025-11-10, 2026-02-09, 2026-05-07, 2026-08-07",
    Coupon_Low_Barrier="0.7, 0.7, 0.7, 0.7",
    Coupon_Memory_Cutoff_Dates="2026-08-07, 2026-08-07, 2026-08-07, 2026-08-07",
    Coupon_Memory_Multiplier="1, 1, 1, 1",
    Coupon_Multiple_Observation_Barrier_Type="Knock-Out",
    Coupon_Pay_Dates="2025-11-12, 2026-02-12, 2026-05-12, 2026-08-12",
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
    Variable_Coupon_Strike_With_Memory_Coupons="0, 0, 0, 0",

    # --- BarrierShiftParameters ---
    BSP_Autocall_Absolute_Shift="-0.0087, -0.0087, -0.0087, -0.0087",
    BSP_Autocall_Shift_Dates="2025-11-07, 2026-02-09, 2026-05-07, 2026-08-07",
    BSP_Coupon_Absolute_Shift="-0.0087, -0.0087, -0.0087, -0.0087",
    BSP_Coupon_Absolute_Spread="0.0174, 0.0174, 0.0174, 0.0174",
    BSP_Coupon_Shift_Dates="2025-11-07, 2026-02-09, 2026-05-07, 2026-08-07",
    BSP_Maturity_Barrier_Absolute_Shift="-0.0087",
    BSP_Maturity_Barrier_Absolute_Spread="0.0174",
    BSP_Maturity_Barrier_Knock_Out_Levels_Absolute_Shift="-0.0087",
)

# Helper to create textarea input
def textarea(id_, label, default, **style):
    return html.Div([
        html.Label(label),
        dcc.Textarea(id=id_, value=default, style={"width": "100%", "height": "60px", **style}),
    ], className="mb-2")

# Helper to create simple input
def textinput(id_, label, default, type_="text"):
    return html.Div([
        html.Label(label),
        dcc.Input(id=id_, value=default, type=type_, style={"width": "100%"}),
    ], className="mb-2")

# Helper to create checkbox

def boolcheck(id_, label, default):
    return html.Div([
        dcc.Checklist(id=id_, options=[{"label": label, "value": "yes"}], value=["yes"] if default else []),
    ], className="mb-2")

# --------------------------------------------------
# 2. Build Layout
# --------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

left_col = dbc.Card([
    dbc.CardHeader("TermSheet Parameters"),
    dbc.CardBody([
        textinput("acc_when", "Accrues_When", DEFAULTS["Accrues_When"]),
        textarea("autocall_barrier", "Autocall_Barrier", DEFAULTS["Autocall_Barrier"]),
        textarea("autocall_dates", "Autocall_Dates", DEFAULTS["Autocall_Dates"]),
        textarea("autocall_pay_dates", "Autocall_Pay_Dates", DEFAULTS["Autocall_Pay_Dates"]),
        textinput("basket_level_type", "Basket_Level_Type", DEFAULTS["Basket_Level_Type"]),
        textarea("basket_weights", "Basket_Weights", DEFAULTS["Basket_Weights"]),
        textarea("coupon_det_dates", "Coupon_Determination_Dates", DEFAULTS["Coupon_Determination_Dates"]),
        textarea("coupon_low_barrier", "Coupon_Low_Barrier", DEFAULTS["Coupon_Low_Barrier"]),
        textarea("coupon_memory_dates", "Coupon_Memory_Cutoff_Dates", DEFAULTS["Coupon_Memory_Cutoff_Dates"]),
        textarea("coupon_memory_mult", "Coupon_Memory_Multiplier", DEFAULTS["Coupon_Memory_Multiplier"]),
        textinput("coupon_multi_obs_type", "Coupon_Multiple_Observation_Barrier_Type", DEFAULTS["Coupon_Multiple_Observation_Barrier_Type"]),
        textarea("coupon_pay_dates", "Coupon_Pay_Dates", DEFAULTS["Coupon_Pay_Dates"]),
        textinput("daycount_basis", "Daycount_Basis", DEFAULTS["Daycount_Basis"]),
        textinput("downside_part", "Downside_Participation", DEFAULTS["Downside_Participation"], type_="number"),
        textarea("fixed_return", "Fixed_Return", DEFAULTS["Fixed_Return"]),
        textinput("floating_mult", "Floating_Payment_Multiplier", DEFAULTS["Floating_Payment_Multiplier"], type_="number"),
        textinput("gmmr", "Guaranteed_Minimum_Maturity_Return", DEFAULTS["Guaranteed_Minimum_Maturity_Return"], type_="number"),
        textarea("initial_levels", "Initial_Levels", DEFAULTS["Initial_Levels"]),
        boolcheck("is_note", "Is_Note", DEFAULTS["Is_Note"]),
        textinput("mat_barrier", "Maturity_Barrier", DEFAULTS["Maturity_Barrier"], type_="number"),
        textinput("mat_date", "Maturity_Date", DEFAULTS["Maturity_Date"]),
        textinput("mat_opt_type", "Maturity_Option_Barrier_Type", DEFAULTS["Maturity_Option_Barrier_Type"]),
        textinput("mat_settle_date", "Maturity_Settlement_Date", DEFAULTS["Maturity_Settlement_Date"]),
        textarea("participation", "Participation", DEFAULTS["Participation"]),
        textarea("part_mem_coupon", "Participation_With_Memory_Coupons", DEFAULTS["Participation_With_Memory_Coupons"]),
        textinput("pay_id", "Pay_ID", DEFAULTS["Pay_ID"]),
        textinput("prem_settle", "Premium_Settlement_Date", DEFAULTS["Premium_Settlement_Date"]),
        boolcheck("ret_notional", "Return_Notional_At_Recall", DEFAULTS["Return_Notional_At_Recall"]),
        textarea("stock_ids", "Stock_IDs", DEFAULTS["Stock_IDs"]),
        textinput("strike_set_date", "Strike_Setting_Date", DEFAULTS["Strike_Setting_Date"]),
        textarea("var_coupon_strike", "Variable_Coupon_Strike", DEFAULTS["Variable_Coupon_Strike"]),
        textarea("var_coupon_strike_mem", "Variable_Coupon_Strike_With_Memory_Coupons", DEFAULTS["Variable_Coupon_Strike_With_Memory_Coupons"]),
        html.Hr(),
        # -------- Barrier Shift Params collapsible ---------
        dbc.Button("Barrier Shift Parameters", id="bsp-toggle", className="mb-2", color="secondary"),
        dbc.Collapse([
            textarea("bsp_autocall_shift", "Autocall_Absolute_Shift", DEFAULTS["BSP_Autocall_Absolute_Shift"]),
            textarea("bsp_autocall_dates", "Autocall_Shift_Dates", DEFAULTS["BSP_Autocall_Shift_Dates"]),
            textarea("bsp_coupon_shift", "Coupon_Absolute_Shift", DEFAULTS["BSP_Coupon_Absolute_Shift"]),
            textarea("bsp_coupon_spread", "Coupon_Absolute_Spread", DEFAULTS["BSP_Coupon_Absolute_Spread"]),
            textarea("bsp_coupon_dates", "Coupon_Shift_Dates", DEFAULTS["BSP_Coupon_Shift_Dates"]),
            textinput("bsp_mat_shift", "Maturity_Barrier_Absolute_Shift", DEFAULTS["BSP_Maturity_Barrier_Absolute_Shift"], type_="number"),
            textinput("bsp_mat_spread", "Maturity_Barrier_Absolute_Spread", DEFAULTS["BSP_Maturity_Barrier_Absolute_Spread"], type_="number"),
            textarea("bsp_mat_knock_shift", "Maturity_Barrier_Knock_Out_Levels_Absolute_Shift", DEFAULTS["BSP_Maturity_Barrier_Knock_Out_Levels_Absolute_Shift"]),
        ], id="bsp-collapse", is_open=True),

        html.Hr(),
        dbc.Button("Generate JSON", id="btn-generate", color="primary"),
    ])
], body=True, style={"maxHeight": "90vh", "overflowY": "scroll"})

right_col = dbc.Card([
    dbc.CardHeader("Live JSON Preview"),
    dbc.CardBody([
        html.Pre(id="preview", style={"whiteSpace": "pre-wrap", "fontFamily": "monospace"})
    ])
], body=True)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(left_col, width=5),
        dbc.Col(right_col, width=7)
    ], className="mt-3")
], fluid=True)

# --------------------------------------------------
# 3. Callbacks
# --------------------------------------------------

@callback(
    Output("bsp-collapse", "is_open"),
    Input("bsp-toggle", "n_clicks"),
    State("bsp-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_bsp(n, is_open):
    return not is_open

@callback(
    Output("preview", "children"),
    Input("btn-generate", "n_clicks"),
    [State("acc_when", "value"),
     State("autocall_barrier", "value"),
     State("autocall_dates", "value"),
     State("autocall_pay_dates", "value"),
     State("basket_level_type", "value"),
     State("basket_weights", "value"),
     State("coupon_det_dates", "value"),
     State("coupon_low_barrier", "value"),
     State("coupon_memory_dates", "value"),
     State("coupon_memory_mult", "value"),
     State("coupon_multi_obs_type", "value"),
     State("coupon_pay_dates", "value"),
     State("daycount_basis", "value"),
     State("downside_part", "value"),
     State("fixed_return", "value"),
     State("floating_mult", "value"),
     State("gmmr", "value"),
     State("initial_levels", "value"),
     State("is_note", "value"),
     State("mat_barrier", "value"),
     State("mat_date", "value"),
     State("mat_opt_type", "value"),
     State("mat_settle_date", "value"),
     State("participation", "value"),
     State("part_mem_coupon", "value"),
     State("pay_id", "value"),
     State("prem_settle", "value"),
     State("ret_notional", "value"),
     State("stock_ids", "value"),
     State("strike_set_date", "value"),
     State("var_coupon_strike", "value"),
     State("var_coupon_strike_mem", "value"),
     # Barrier shift parameters
     State("bsp_autocall_shift", "value"),
     State("bsp_autocall_dates", "value"),
     State("bsp_coupon_shift", "value"),
     State("bsp_coupon_spread", "value"),
     State("bsp_coupon_dates", "value"),
     State("bsp_mat_shift", "value"),
     State("bsp_mat_spread", "value"),
     State("bsp_mat_knock_shift", "value"),])

def build_preview(n_clicks, *vals):
    if n_clicks is None:
        return "← 点击左侧 Generate JSON 按钮"

    (
        accrues_when, autocall_barrier, autocall_dates, autocall_pay_dates, basket_level_type, basket_weights,
        coupon_det_dates, coupon_low_barrier, coupon_memory_dates, coupon_memory_mult,
        coupon_multi_obs_type, coupon_pay_dates, daycount_basis, downside_part, fixed_return,
        floating_mult, gmmr, initial_levels, is_note, mat_barrier, mat_date, mat_opt_type,
        mat_settle_date, participation, part_mem_coupon, pay_id, prem_settle, ret_notional,
        stock_ids, strike_set_date, var_coupon_strike, var_coupon_strike_mem,
        bsp_autocall_shift, bsp_autocall_dates, bsp_coupon_shift, bsp_coupon_spread,
        bsp_coupon_dates, bsp_mat_shift, bsp_mat_spread, bsp_mat_knock_shift
    ) = vals

    try:
        bsp = BarrierShiftParameters(
            Autocall_Absolute_Shift=[float(x) for x in bsp_autocall_shift.split(',') if x.strip()],
            Autocall_Shift_Dates=[x.strip() for x in bsp_autocall_dates.split(',') if x.strip()],
            Coupon_Absolute_Shift=[float(x) for x in bsp_coupon_shift.split(',') if x.strip()],
            Coupon_Absolute_Spread=[float(x) for x in bsp_coupon_spread.split(',') if x.strip()],
            Coupon_Shift_Dates=[x.strip() for x in bsp_coupon_dates.split(',') if x.strip()],
            Maturity_Barrier_Absolute_Shift=float(bsp_mat_shift),
            Maturity_Barrier_Absolute_Spread=float(bsp_mat_spread),
            Maturity_Barrier_Knock_Out_Levels_Absolute_Shift=[float(x) for x in bsp_mat_knock_shift.split(',') if x.strip()],
        )
        ts = TermSheet(
            Accrues_When=accrues_when,
            Autocall_Barrier=[float(x) for x in autocall_barrier.split(',') if x.strip()],
            Autocall_Dates=[x.strip() for x in autocall_dates.split(',') if x.strip()],
            Autocall_Pay_Dates=[x.strip() for x in autocall_pay_dates.split(',') if x.strip()],
            Basket_Level_Type=basket_level_type,
            Basket_Weights=[float(x) for x in basket_weights.split(',') if x.strip()],
            Coupon_Determination_Dates=[x.strip() for x in coupon_det_dates.split(',') if x.strip()],
            Coupon_Low_Barrier=[float(x) for x in coupon_low_barrier.split(',') if x.strip()],
            Coupon_Memory_Cutoff_Dates=[x.strip() for x in coupon_memory_dates.split(',') if x.strip()],
            Coupon_Memory_Multiplier=[float(x) for x in coupon_memory_mult.split(',') if x.strip()],
            Coupon_Multiple_Observation_Barrier_Type=coupon_multi_obs_type,
            Coupon_Pay_Dates=[x.strip() for x in coupon_pay_dates.split(',') if x.strip()],
            Daycount_Basis=daycount_basis,
            Downside_Participation=float(downside_part),
            Fixed_Return=[float(x) for x in fixed_return.split(',') if x.strip()],
            Floating_Payment_Multiplier=float(floating_mult),
            Guaranteed_Minimum_Maturity_Return=float(gmmr),
            Initial_Levels=[float(x) for x in initial_levels.split(',') if x.strip()],
            Is_Note=(is_note == ["yes"]),
            Maturity_Barrier=float(mat_barrier),
            Maturity_Date=mat_date,
            Maturity_Option_Barrier_Type=mat_opt_type,
            Maturity_Settlement_Date=mat_settle_date,
            Participation=[float(x) for x in participation.split(',') if x.strip()],
            Participation_With_Memory_Coupons=[float(x) for x in part_mem_coupon.split(',') if x.strip()],
            Pay_ID=pay_id,
            Premium_Settlement_Date=prem_settle,
            Return_Notional_At_Recall=(ret_notional == ["yes"]),
            Stock_IDs=[x.strip() for x in stock_ids.split(',') if x.strip()],
            Strike_Setting_Date=strike_set_date,
            Variable_Coupon_Strike=[float(x) for x in var_coupon_strike.split(',') if x.strip()],
            Variable_Coupon_Strike_With_Memory_Coupons=[float(x) for x in var_coupon_strike_mem.split(',') if x.strip()],
            Barrier_Shift_Parameters=bsp,
        )
        return json.dumps(ts.to_dict(), indent=2)
    except Exception as e:
        return f"Error building TermSheet: {e}"

# --------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True, port=8052)

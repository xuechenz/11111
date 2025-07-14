@callback(
    Output("json-preview", "children"),
    Input("btn-gen-json", "n_clicks"),
    # State for all inputs omitted for brevity...
    prevent_initial_call=True
)
def build_json(
    _,
    acc_when, daycount_basis, pay_id, stock_ids,
    autocall_barrier, autocall_dates, autocall_pay_dates, autocall_ex_dates,
    coupon_det_dates, coupon_low_barrier, coupon_pay_dates, coupon_memory_mult,
    coupon_ex_dates, coupon_cutoff_dates, coupon_obs_type,
    mat_date, mat_barrier, mat_opt_type, mat_settle_date,
    participation, ret_notional, variable_coupon_strike, variable_coupon_mem_strike,
    bsp_autocall_shift, bsp_autocall_dates, bsp_coupon_shift, bsp_coupon_spread, bsp_coupon_dates,
    bsp_mat_shift, bsp_mat_spread, bsp_mat_ko_shift,
    bump_stock_ids, bump_sizes
):
    # parse common lists
    def parse_list(s, cast=str):
        return [cast(x.strip()) for x in s.split(",") if x.strip()]

    # build TermSheet with all required args
    ts = TermSheet(
        Accrues_When=acc_when,
        Autocall_Barrier=parse_list(autocall_barrier, float),
        Autocall_Dates=parse_list(autocall_dates),
        Autocall_Ex_Dates=parse_list(autocall_ex_dates),
        Autocall_Pay_Dates=parse_list(autocall_pay_dates),
        Basket_Level_Type=DEFAULTS['Basket_Level_Type'],
        Basket_Weights=parse_list(DEFAULTS['Basket_Weights'], float),
        Coupon_Determination_Dates=parse_list(coupon_det_dates),
        Coupon_Determination_Ex_Dates=parse_list(coupon_ex_dates),
        Coupon_Low_Barrier=parse_list(coupon_low_barrier, float),
        Coupon_Memory_Cutoff_Dates=parse_list(coupon_cutoff_dates),
        Coupon_Memory_Multiplier=parse_list(coupon_memory_mult, float),
        Coupon_Multiple_Observation_Barrier_Type=coupon_obs_type,
        Coupon_Pay_Dates=parse_list(coupon_pay_dates),
        Daycount_Basis=daycount_basis,
        Downside_Participation=float(DEFAULTS['Downside_Participation']),
        Fixed_Return=parse_list(DEFAULTS['Fixed_Return'], float),
        Floating_Payment_Multiplier=float(DEFAULTS['Floating_Payment_Multiplier']),
        Guaranteed_Minimum_Maturity_Return=float(DEFAULTS['Guaranteed_Minimum_Maturity_Return']),
        Initial_Levels=parse_list(DEFAULTS['Initial_Levels'], float),
        Is_Note=DEFAULTS['Is_Note'],
        Maturity_Barrier=float(mat_barrier),
        Maturity_Date=mat_date,
        Maturity_Option_Barrier_Type=mat_opt_type,
        Maturity_Settlement_Date=mat_settle_date,
        Participation=parse_list(participation, float),
        Participation_With_Memory_Coupons=parse_list(DEFAULTS['Participation_With_Memory_Coupons'], float),
        Pay_ID=pay_id,
        Premium_Settlement_Date=DEFAULTS['Premium_Settlement_Date'],
        Return_Notional_At_Recall=('yes' in ret_notional),
        Stock_IDs=parse_list(stock_ids),
        Strike_Setting_Date=DEFAULTS['Strike_Setting_Date'],
        Variable_Coupon_Strike=parse_list(variable_coupon_strike, float),
        Variable_Coupon_Strike_With_Memory_Coupons=parse_list(variable_coupon_mem_strike, float),
        Barrier_Shift_Parameters=bsp  # from state
    )

    # build BarrierShiftParameters
    bsp = BarrierShiftParameters(
        Autocall_Absolute_Shift=parse_list(bsp_autocall_shift, float),
        Autocall_Shift_Dates=parse_list(bsp_autocall_dates),
        Coupon_Absolute_Shift=parse_list(bsp_coupon_shift, float),
        Coupon_Absolute_Spread=parse_list(bsp_coupon_spread, float),
        Coupon_Shift_Dates=parse_list(bsp_coupon_dates),
        Maturity_Barrier_Absolute_Shift=float(bsp_mat_shift),
        Maturity_Barrier_Absolute_Spread=float(bsp_mat_spread),
        Maturity_Barrier_Knock_Out_Levels_Absolute_Shift=parse_list(bsp_mat_ko_shift, float)
    )

    # build request dict
    req = build_pricer_request(
        term_sheet=ts,
        strikes=0,  # placeholder
        tenors=[], tenor_bump_sizes=[],
        bump_size_abs=float(bump_sizes),
        stock_ids=parse_list(bump_stock_ids),
        max_paths=100000
    )
    return json.dumps(req, indent=2)

### PATCH P2: on_generate_vega 支持多资产 ###
@callback(
    Output("vega-heatmap", "figure"),
    Output("vega-matrix-store", "data"),
    Output("progress-text", "children"),
    Output("btn-dl-vega-csv", "disabled"),
    Output("btn-dl-vega-png", "disabled"),
    Output("vega-extra-container", "children"),   # <--- 新增
    Input("btn-gen-vega", "n_clicks"),
    State("spot-store", "data"),
    State("strikes-store", "data"),
    State("avg-life-store", "data"),
    [State(i, "value") for i in _all_state_ids],
    prevent_initial_call=True,
)
def on_generate_vega(n_clicks, spot_store, strikes_store, avg_life, *values):
    if not n_clicks:
        raise dash.no_update

    vals = dict(zip(_all_state_ids, values))

    # ---- 输入格式假设 ----
    # spot_store: List[float]  (len = n_assets)
    # strikes_store: List[List[float]]  (outer = n_assets)
    spots = spot_store
    strikes_2d = strikes_store

    stock_ids = _parse_list(vals["stock_ids"], str)
    if not stock_ids:
        return dash.no_update

    n_assets = len(stock_ids)

    # --------- rebuild basket TermSheet (原逻辑，一行没动，唯独 Initial_Levels/Stock_IDs 传 lists) ---------
    bsp = BarrierShiftParameters(
        Autocall_Absolute_Shift                  = _parse_list(vals["bsp_autocall_shift"]),
        Autocall_Shift_Dates                     = _parse_list(vals["bsp_autocall_dates"], str),
        Coupon_Absolute_Shift                    = _parse_list(vals["bsp_coupon_shift"]),
        Coupon_Absolute_Spread                   = _parse_list(vals["bsp_coupon_spread"]),
        Coupon_Shift_Dates                       = _parse_list(vals["bsp_coupon_dates"], str),
        Maturity_Barrier_Absolute_Shift          = _parse_float(vals["bsp_mat_shift"]),
        Maturity_Barrier_Absolute_Spread         = _parse_float(vals["bsp_mat_spread"]),
        Maturity_Barrier_Knock_Out_Levels_Absolute_Shift =
            _parse_list(vals["bsp_mat_ko_shift"]),
    )

    ts = TermSheet(
        Accrues_When                              = vals["acc_when"],
        Autocall_Barrier                          = _parse_list(vals["autocall_barrier"]),
        Autocall_Dates                            = _parse_list(vals["autocall_dates"], str),
        Autocall_Ex_Dates                         = _parse_list(vals["autocall_ex_dates"], str),
        Autocall_Pay_Dates                        = _parse_list(vals["autocall_pay_dates"], str),
        Basket_Level_Type                         = vals["basket_level_type"],
        Basket_Weights                            = _parse_list(vals["basket_weights"]),
        Coupon_Determination_Dates                = _parse_list(vals["coupon_det_dates"], str),
        Coupon_Determination_Ex_Dates             = _parse_list(vals["coupon_det_ex_dates"], str),
        Coupon_Low_Barrier                        = _parse_list(vals["coupon_low_barrier"]),
        Coupon_Memory_Cutoff_Dates                = _parse_list(vals["coupon_mem_cutoff_dates"], str),
        Coupon_Memory_Multiplier                  = _parse_float(vals["coupon_memory_mult"]),
        Coupon_Mult_Obs_Type                      = vals["coupon_mult_obs_type"],
        Coupon_Pay_Dates                          = _parse_list(vals["coupon_pay_dates"], str),
        Daycount_Basis                            = vals["daycount_basis"],
        Downside_Participation                    = _parse_float(vals["downside_participation"]),
        Fixed_Return                              = _parse_list(vals["fixed_return"]),
        Floating_Payment_Multiplier               = _parse_float(vals["floating_payment_mult"]),
        Guaranteed_Minimum_Maturity_Return        = _parse_float(vals["gmmr"]),
        Initial_Levels                            = spots,          # <--- 现在是 list
        Is_Note                                   = _parse_bool(vals["is_note"]),
        Maturity_Barrier                          = _parse_float(vals["mat_barrier"]),
        Maturity_Date                             = vals["mat_date"],
        Maturity_Option_Barrier_Type              = vals["mat_opt_type"],
        Maturity_Settlement_Date                  = vals["mat_settle_date"],
        Participation                             = _parse_list(vals["participation"]),
        Participation_With_Memory_Coupons         = _parse_list(vals["participation_mem"]),
        Pay_ID                                    = vals["pay_id"],
        Premium_Settlement_Date                   = vals["premium_settle_date"],
        Return_Notional_At_Recall                 = _parse_bool(vals["ret_notional"]),
        Stock_IDs                                 = stock_ids,      # <--- list
        Strike_Setting_Date                       = _parse_list(vals["strike_setting_date"], str),
        Variable_Coupon_Strike_With_Memory_Coupons= _parse_list(vals["variable_coupon_strike_mem"]),
        Barrier_Shift_Parameters                  = bsp,
    )

    # -----------------------------------
    #   跑所有资产 Vega Map
    # -----------------------------------
    tenors = [f"{m}m" for m in range(0, 61, 3)]
    bump_size = _parse_float(vals["bump_sizes"])
    max_paths = 100_000

    matrices = []
    figs = []
    progress_bits = []

    for i, sid in enumerate(stock_ids):
        ks = strikes_2d[i]
        sp = float(spots[i])
        # 多线程跑整行（内部 bump sid）
        matrix_i = []
        with ThreadPoolExecutor(max_workers=10) as exe:
            futs = {
                exe.submit(compute_vega_row, ts, strike, tenors, bump_size, sid, max_paths): strike
                for strike in ks
            }
            for fut in as_completed(futs):
                strike, row = fut.result()
                idx = ks.index(strike)
                # 确保 matrix_i 有长度
                if len(matrix_i) < len(ks):
                    matrix_i = [[0.0] * len(tenors) for _ in ks]
                matrix_i[idx] = row

        matrices.append(matrix_i)

        # 图
        fig_i = make_heatmap(
            ks, sp, matrix_i, tenors, avg_life, _parse_float(vals["mat_barrier"]), sid
        )
        figs.append(fig_i)
        progress_bits.append(f"{sid}: {len(ks)} strikes")

    # 主图 = 第一个资产
    main_fig = figs[0] if figs else go.Figure()

    # 其它资产 children
    extra_children = []
    for sid, fig_i in zip(stock_ids[1:], figs[1:]):
        extra_children.extend([
            html.Hr(),
            html.H5(f"Vega Map: {sid}"),
            dcc.Graph(figure=fig_i, id={"type": "vega-subfig", "sid": sid}),
        ])

    prog = " | ".join(progress_bits)

    # 缓存到 vega-matrix-store（供下载）
    store_data = {
        "tenors": tenors,
        "stock_ids": stock_ids,
        "spots": spots,
        "strikes": strikes_2d,
        "matrices": matrices,
        "avg_life": avg_life,
        "mat_barrier": _parse_float(vals["mat_barrier"]),
        "timestamp": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
    }

    # 启用下载按钮（有结果即启）
    return main_fig, store_data, prog, False, False, extra_children
### PATCH P2 END ###


### PATCH P3: download_vega_csv 支持多资产 (ZIP) ###
@callback(
    Output("dl-vega-csv", "data"),
    Input("btn-dl-vega-csv", "n_clicks"),
    State("vega-matrix-store", "data"),
    State("strikes-store", "data"),  # 未用，仅保持兼容
    prevent_initial_call=True,
)
def download_vega_csv(n_clicks, store_data, _legacy_strikes):
    if not n_clicks:
        raise dash.no_update
    if not store_data:
        raise dash.no_update

    tenors = store_data["tenors"]
    stock_ids = store_data["stock_ids"]
    strikes_2d = store_data["strikes"]
    matrices = store_data["matrices"]
    ts_tag = store_data.get("timestamp", datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))

    # 单资产：保持原行为（矩阵 -> CSV）
    if len(stock_ids) == 1:
        ks = strikes_2d[0]
        mtx = matrices[0]
        df = pd.DataFrame(mtx, index=ks, columns=tenors)
        filename = f"vega_map_{stock_ids[0]}_{ts_tag}.csv"
        return dict(content=df.to_csv(), filename=filename)

    # 多资产：ZIP 多个 heatmap CSV
    def write_zip(buf):
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for sid, ks, mtx in zip(stock_ids, strikes_2d, matrices):
                df = pd.DataFrame(mtx, index=ks, columns=tenors)
                zf.writestr(f"vega_map_{sid}.csv", df.to_csv())
    zip_name = f"vega_maps_{len(stock_ids)}_{ts_tag}.zip"
    return dcc.send_bytes(write_zip, zip_name)
### PATCH P3 END ###


### PATCH P4: download_vega_png 支持多资产 (ZIP) ###
@callback(
    Output("dl-vega-png", "data"),
    Input("btn-dl-vega-png", "n_clicks"),
    State("vega-matrix-store", "data"),
    State("strikes-store", "data"),   # legacy unused
    State("avg-life-store", "data"),  # legacy unused (我们用 store_data 内的 avg_life, barrier)
    State("spot-store", "data"),      # legacy unused
    [State(i, "value") for i in _all_state_ids],
    prevent_initial_call=True,
)
def download_vega_png(n_clicks, store_data, _legacy_strikes, _avg_life, _spots, *values):
    if not n_clicks:
        raise dash.no_update
    if not store_data:
        raise dash.no_update

    vals = dict(zip(_all_state_ids, values))  # 仅为取 barrier 兼容；我们也存了
    mat_barrier = store_data.get("mat_barrier", _parse_float(vals["mat_barrier"]))
    avg_life = store_data.get("avg_life", _avg_life)

    tenors = store_data["tenors"]
    stock_ids = store_data["stock_ids"]
    spots = store_data["spots"]
    strikes_2d = store_data["strikes"]
    matrices = store_data["matrices"]
    ts_tag = store_data.get("timestamp", datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))

    # 单资产：原行为
    if len(stock_ids) == 1:
        sid = stock_ids[0]
        fig = make_heatmap(strikes_2d[0], float(spots[0]), matrices[0], tenors, avg_life, mat_barrier, sid)
        png_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        fname = f"vega_map_{sid}_{ts_tag}.png"
        return dict(content=png_bytes, filename=fname, type="image/png")

    # 多资产：打 ZIP
    def write_zip(buf):
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for sid, ks, sp, mtx in zip(stock_ids, strikes_2d, spots, matrices):
                fig = make_heatmap(ks, float(sp), mtx, tenors, avg_life, mat_barrier, sid)
                png_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
                zf.writestr(f"vega_map_{sid}.png", png_bytes)
    zip_name = f"vega_maps_{len(stock_ids)}_{ts_tag}.zip"
    return dcc.send_bytes(write_zip, zip_name)
### PATCH P4 END ###

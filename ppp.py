for i, strike_abs in enumerate(strikes_abs):
    # Compute the baseline PV (M2M) for this strike with no volatility bump
    zero_bump_list = [0.0] * n_tenor
    req_base = build_pricer_request(
        term_sheet       = ts,             
        strikes          = strike_abs,     
        tenors           = tenor_grid,    
        tenor_bump_sizes = zero_bump_list, 
        max_paths        = 100_000,        
    )
    resp_base = fpf(req_base)             
    pv_before = float(resp_base["M2M Value"])  
    print(f"Strike {strike_abs:.2f} baseline M2M = {pv_before:.6f}")

    # For each tenor, apply a small vol bump and compute finite-difference Vega
    for j, tenor in enumerate(tenor_grid):
        # bump only the j-th tenor by BUMP_SIZE (e.g. 0.0025 = 0.25%)
        bump_list = [BUMP_SIZE if k == j else 0.0 for k in range(n_tenor)]

        req = build_pricer_request(
            term_sheet       = ts,
            strikes          = strike_abs,
            tenors           = tenor_grid,
            tenor_bump_sizes = bump_list,
            max_paths        = 100_000,
        )
        resp     = fpf(req)               # send bumped request
        pv_after = float(resp["M2M Value"])  

        # Vega (pv_after - pv_before)/bump_size
        vega_matrix[i, j] = (pv_after - pv_before) / BUMP_SIZE
        print(f"  Tenor {tenor}: Vega = {vega_matrix[i, j]:.4f}")

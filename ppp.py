from concurrent.futures import ThreadPoolExecutor, as_completed

def compute_vega(strike_abs):
    req_base = build_pricer_request(
        term_sheet      = ts,
        strikes         = strike_abs,
        tenors          = tenor_grid,
        tenor_bump_sizes= zero_bump_list,
        max_paths       = 100_000,
    )
    pv_before = float(fpf(req_base)["M2M Value"])

    vega_row = []
    for j, tenor in enumerate(tenor_grid):
        bump_list = [BUMP_SIZE if k == j else 0.0 for k in range(n_tenor)]
        req = build_pricer_request(
            term_sheet       = ts,
            strikes          = strike_abs,
            tenors           = tenor_grid,
            tenor_bump_sizes = bump_list,
            max_paths        = 100_000,
        )
        pv_after = float(fpf(req)["M2M Value"])
        vega_row.append((pv_after - pv_before) / BUMP_SIZE)
    return strike_abs, vega_row

# Run with threading
with ThreadPoolExecutor(max_workers=8) as executor:  # Adjust workers
    futures = [executor.submit(compute_vega, strike) for strike in strikes_abs]

    for future in as_completed(futures):
        strike_abs, vega_row = future.result()
        idx = strikes_abs.index(strike_abs)
        vega_matrix[idx, :] = vega_row

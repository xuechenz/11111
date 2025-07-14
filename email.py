tenor_grid      = [f"{m}m" for m in tenor_months]
zero_bump_list  = [0.0] * len(tenor_grid)

strike_a = strikes_abs[0]
strike_b = strikes_abs[-1]

def fetch_baseline(strike_abs: float):
    req  = build_pricer_request(
        term_sheet       = ts,
        strikes          = strike_abs,
        tenors           = tenor_grid,
        tenor_bump_sizes = zero_bump_list,
        max_paths        = 100_000,
    )
    resp = fpf(req)
    premium   = float(resp["Premium Price"])
    raw_vega  = resp["Vega"]  
    return premium, raw_vega

for strike_abs in (strike_a, strike_b):
    prem, raw_v = fetch_baseline(strike_abs)
    print(f"[Strike = {strike_abs:,.2f}]  Premium Price = {prem:.6f} ,  Vega(raw) = {raw_v}")

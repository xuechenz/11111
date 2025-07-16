row = []
for i in range(len(tenors)):
    bump_list = [bump if k == i else 0.0 for k in range(len(tenors))]
    req = build_pricer_request(ts, strike, tenors, bump_list, max_paths=max_paths)
    resp = fpf(req)
    print(f"bumped tenor={tenors[i]} resp keys:", resp.keys())
    print(f"bumped tenor={tenors[i]} full resp:", resp)
    pv = float(resp["M2M Value"])
    row.append((pv - pv0) / bump)
return strike, row

vol_handle = fpf({
    "get": {
        "what": "volatility index",
        "id": "NDX.IDX"
    }
})["top"][0]
strike_meta = fpf({ "get": vol_handle })
strikes_abs = strike_meta["strikes"]
strike_spot = strike_meta["spot"]
percent_strikes = [strike / strike_spot for strike in strikes_abs]
filtered_strikes = []
for strike, pct in zip(strikes_abs, percent_strikes):
    if 0.5 <= pct <= 1.5:
        if 0.9 <= pct <= 1.1:
            filtered_strikes.append(strike)
        else:
            rounded_pct = round(pct * 100)  
            if rounded_pct % 10 == 0: 
                filtered_strikes.append(strike)
strikes_abs = filtered_strikes
print(strikes_abs)

spot_handle = fpf({
    "get": {
        "what": "spot index",
        "id": "NDX.IDX"
    }
})["top"][0]

spot_meta = fpf({ "get": spot_handle })
spot        = spot_meta["last"]

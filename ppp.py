if __name__ == "__main__":
    ENV = {"name": "111", "password": "11"}
    HOST, PORT = "11", 11
    DATES = ["2025-11-07", "2026-02-09", "2026-05-07", "2026-08-07"]
    INITIAL_LEVEL = 22726.012561111645
    # Send request
    res = price_autocall(
        host=HOST,
        port=PORT,
        env=ENV,
        underlying_id="NDX.IDX",
        autocall_dates=DATES,
        initial_level=INITIAL_LEVEL,
    )
    out = Path("outputs"); out.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file = out / f"single_request_{ts}.json"
    json.dump(res, file.open("w"), indent=2)
    print(f"Pricing Complete→ {file}")

@app.callback(
    Output("iv-summary-container", "children"),
    Input("btn-refresh-iv-summary", "n_clicks"),
    State("TD_minus_concensus_date", "date"),
    State("iv-summary-tenor", "value"),
    State("iv-summary-strike", "value"),
    State("iv-summary-neigh", "value"),
    State("iv-summary-page-size", "value"),
    prevent_initial_call=True,
)
def build_iv_summary(_, val_date_str, tenor_m, strike_pct, n_neigh, page_size):
    if val_date_str is None:
        return "Select a valuation date."
    tenor_m   = int(tenor_m or 0)
    strike_pct= float(strike_pct or 100)
    n_neigh   = max(0, int(n_neigh or 1))

    val_date = date.fromisoformat(val_date_str)
    target_dt = val_date + relativedelta(months=+tenor_m)

    cache = diff_cache(val_date_str)
    rows = []

    for tk, (mtx, Ks, dts) in cache.items():
        col_idx = int(np.argmin(np.abs(np.asarray(Ks) - (strike_pct / 100))))

        if isinstance(dts[0], (float, int)):
            tgt_year = tenor_m / 12.0
            dist_arr = np.abs(np.asarray(dts) - tgt_year)
            date_labels = [
                (val_date + relativedelta(days=int(y * 365))).strftime("%Y/%m/%d")
                for y in dts
            ]
        else:
            dist_arr = np.abs(np.asarray(dts) - target_dt)
            date_labels = [dt.strftime("%Y/%m/%d") for dt in dts]

        num = max(1, n_neigh)
        idx_sorted = dist_arr.argsort()[:num]


        for idx in idx_sorted:
            diff_val = mtx[idx, col_idx]
            if np.isnan(diff_val):
                continue
            rows.append(
                {
                    "Ticker": tk,
                    "Diff": round(float(diff_val), 2),
                    "Date": date_labels[idx],
                    "TICKER_RAW": tk,
                }
            )

    if not rows:
        return "No data available for the chosen inputs."

    rows.sort(key=lambda r: -abs(r["Diff"]))
    df = pd.DataFrame(rows)

    return html.Div(
        [
            dcc.Store(id="iv-summary-df",
                      data=df.to_json(date_format="iso", orient="split")),
            dash_table.DataTable(
                id="iv-summary-table",
                data=df.to_dict("records"),
                columns=[
                    {"name": "Ticker", "id": "Ticker", "presentation": "markdown"},
                    {"name": "Diff Annualized(%)", "id": "Diff", "type": "numeric"},
                    {"name": "Date", "id": "Date"},
                ],
                row_selectable="single",
                page_current=0,
                page_size=page_size,
                sort_action="native",
                style_cell={"textAlign": "center", "padding": "0.15rem"},
                style_data_conditional=[
                    {"if": {"filter_query": "{Diff} > 0"}, "color": "blue"},
                    {"if": {"filter_query": "{Diff} < 0"}, "color": "red"},
                ],
            ),
        ]
    )

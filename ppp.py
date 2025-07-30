def write_csv_zip(buf, stock_ids, matrices, strike_centers, tenor_centers_m, ts_tag):
    cols = [f"{m}m" for m in tenor_centers_m]
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for sid, mtx in zip(stock_ids, matrices):
            df = pd.DataFrame(mtx, index=strike_centers, columns=cols)
            zf.writestr(f"vega_map_{sid}.csv", df.to_csv())

@callback(
    Output("dl-vega-csv", "data"),
    Input("btn-dl-vega-csv", "n_clicks"),
    State("vega-matrix-store", "data"),
    prevent_initial_call=True,
)
def download_vega_csv(n_clicks, store_data):
    if not n_clicks or not store_data:
        raise dash.no_update

    strike_centers    = store_data["strike_centers"]
    tenor_centers_m   = store_data["tenor_centers_m"]
    stock_ids         = store_data["stock_ids"]
    matrices          = store_data["matrices"]
    ts_tag            = store_data["timestamp"]

    if len(stock_ids) == 1:
        df = pd.DataFrame(matrices[0], index=strike_centers,
                          columns=[f"{m}m" for m in tenor_centers_m])
        return dcc.send_bytes(df.to_csv, f"vega_map_{stock_ids[0]}_{ts_tag}.csv")

    buf = io.BytesIO()
    write_csv_zip(buf, stock_ids, matrices, strike_centers, tenor_centers_m, ts_tag)
    zip_name = f"vega_maps_{len(stock_ids)}_{ts_tag}.zip"
    return dcc.send_bytes(lambda f: f.write(buf.getvalue()), zip_name)

def write_png_zip(buf, stock_ids, matrices, strike_centers, tenor_centers_m,
                  avg_life, mat_barrier, ts_tag):
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for sid, mtx in zip(stock_ids, matrices):
            fig = make_heatmap(strike_centers, tenor_centers_m,
                               mtx, avg_life, mat_barrier, sid)
            img = fig.to_image(format="png", width=800, height=600, scale=2)
            zf.writestr(f"vega_map_{sid}.png", img)


@callback(
    Output("dl-vega-png", "data"),
    Input("btn-dl-vega-png", "n_clicks"),
    State("vega-matrix-store", "data"),
    prevent_initial_call=True,
)
def download_vega_png(n_clicks, store_data):
    if not n_clicks or not store_data:
        raise dash.no_update

    strike_centers   = store_data["strike_centers"]
    tenor_centers_m  = store_data["tenor_centers_m"]
    stock_ids        = store_data["stock_ids"]
    matrices         = store_data["matrices"]
    avg_life         = store_data["avg_life"]
    mat_barrier      = store_data["mat_barrier"]
    ts_tag           = store_data["timestamp"]

    if len(stock_ids) == 1:
        fig = make_heatmap(strike_centers, tenor_centers_m,
                           matrices[0], avg_life, mat_barrier, stock_ids[0])
        img = fig.to_image(format="png", width=800, height=600, scale=2)
        return dcc.send_bytes(lambda f: f.write(img), f"vega_map_{stock_ids[0]}_{ts_tag}.png")

    buf = io.BytesIO()
    write_png_zip(buf, stock_ids, matrices, strike_centers,
                  tenor_centers_m, avg_life, mat_barrier, ts_tag)
    zip_name = f"vega_maps_{len(stock_ids)}_{ts_tag}.zip"
    return dcc.send_bytes(lambda f: f.write(buf.getvalue()), zip_name)

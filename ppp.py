from datetime import datetime, UTC

store_data = {
    "strike_centers": strike_centers,          
    "tenor_centers_m": tenor_centers_m,        
    "stock_ids": stock_ids,
    "matrices": matrices,                      
    "avg_life": avg_life,
    "mat_barrier": _parse_float(vals["mat_barrier"]),
    "timestamp": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
}

@callback(
    Output("dl-vega-csv", "data"),
    Input("btn-dl-vega-csv", "n_clicks"),
    State("vega-matrix-store", "data"),
    prevent_initial_call=True,
)
def download_vega_csv(n_clicks, store_data):
    if not n_clicks or not store_data:
        raise dash.no_update

    k_centers   = store_data["strike_centers"]       
    t_centers_m = store_data["tenor_centers_m"]      
    cols        = [f"{m}m" for m in t_centers_m]

    stock_ids   = store_data["stock_ids"]
    matrices    = store_data["matrices"]
    ts_tag      = store_data["timestamp"]

    if len(stock_ids) == 1:
        df  = pd.DataFrame(matrices[0], index=k_centers, columns=cols)
        fname = f"vega_map_{stock_ids[0]}_{ts_tag}.csv"
        return dcc.send_data_frame(df.to_csv, fname)

    import zipfile, io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for sid, mtx in zip(stock_ids, matrices):
            df = pd.DataFrame(mtx, index=k_centers, columns=cols)
            csv_bytes = df.to_csv().encode()
            zf.writestr(f"vega_map_{sid}.csv", csv_bytes)
    buf.seek(0)
    return dict(content=buf.read(), filename=f"vega_maps_{len(stock_ids)}_{ts_tag}.zip")

@callback(
    Output("dl-vega-png", "data"),
    Input("btn-dl-vega-png", "n_clicks"),
    State("vega-matrix-store", "data"),
    prevent_initial_call=True,
)
def download_vega_png(n_clicks, store_data):
    if not n_clicks or not store_data:
        raise dash.no_update

    k_centers   = store_data["strike_centers"]
    t_centers_m = store_data["tenor_centers_m"]
    stock_ids   = store_data["stock_ids"]
    matrices    = store_data["matrices"]
    avg_life    = store_data["avg_life"]
    mat_barrier = store_data["mat_barrier"]
    ts_tag      = store_data["timestamp"]

    if len(stock_ids) == 1:
        sid = stock_ids[0]
        fig = make_heatmap(k_centers, t_centers_m, matrices[0],
                           avg_life, mat_barrier, sid)
        png_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        fname = f"vega_map_{sid}_{ts_tag}.png"
        return dict(content=png_bytes, filename=fname, type="image/png")

    import zipfile, io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for sid, mtx in zip(stock_ids, matrices):
            fig = make_heatmap(k_centers, t_centers_m, mtx,
                               avg_life, mat_barrier, sid)
            png_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
            zf.writestr(f"vega_map_{sid}.png", png_bytes)
    buf.seek(0)
    return dict(content=buf.read(), filename=f"vega_maps_{len(stock_ids)}_{ts_tag}.zip")

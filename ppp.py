import pandas as pd
from dash import send_bytes
from datetime import datetime

@callback(
    Output("dl-vega-csv", "data"),
    Input("btn-dl-vega-csv", "n_clicks"),
    State("vega-matrix-store", "data"),
    State("strikes-store", "data"),
    prevent_initial_call=True
)
def download_vega_csv(n_clicks, matrix, strikes):
    tenors = [f"{m}m" for m in range(0, 61, 3)]
    df = pd.DataFrame(matrix, index=strikes, columns=tenors)

    csv_string = df.to_csv()
    filename = f"vega_map_{datetime.utcnow():%Y%m%dT%H%M%S}.csv"
    return dict(content=csv_string, filename=filename)


@callback(
    Output("dl-vega-png", "data"),
    Input("btn-dl-vega-png", "n_clicks"),
    State("vega-matrix-store", "data"),
    State("strikes-store", "data"),
    State("avg-life-store", "data"),
    State("ts-store", "data"),
    prevent_initial_call=True
)
def download_vega_png(n_clicks, matrix, strikes, avg_life, ts_dict):
    bsp = BarrierShiftParameters(**ts_dict["Barrier Shift Parameters"])
    ts = TermSheet(**{k:v for k,v in ts_dict.items() if k!="Barrier Shift Parameters"},
                   Barrier_Shift_Parameters=bsp)

    tenors = [f"{m}m" for m in range(0, 61, 3)]
    spot, _ = fetch_spot_and_strikes(ts_dict["Stock IDs"][0])

    fig = make_heatmap(strikes, spot, matrix, tenors,
                       avg_life,
                       ts_dict["Maturity Barrier"],
                       ts_dict["Stock IDs"][0])

    img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)

    filename = f"vega_map_{datetime.utcnow():%Y%m%dT%H%M%S}.png"
    return dict(content=img_bytes, filename=filename)

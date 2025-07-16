def download_vega_png(n_clicks, matrix, strikes, avg_life, ts_dict):
    import matplotlib.pyplot as plt
    import numpy as np
    from io import BytesIO
    from datetime import datetime

    # regenerate data
    spot, _ = fetch_spot_and_strikes(ts_dict["Stock IDs"][0])
    barrier = ts_dict["Maturity Barrier"]
    tenors = list(range(0, 61, 3))
    vega_mat = np.array(matrix)
    strikes_pct = [s/spot for s in strikes]

    # plot with matplotlib
    fig, ax = plt.subplots(figsize=(8, 6))
    mesh = ax.pcolormesh(tenors, strikes_pct, vega_mat, cmap="RdYlGn", shading="auto")
    fig.colorbar(mesh, ax=ax, label="Vega")
    ax.set_xlabel("Tenor (months)")
    ax.set_ylabel("Strike / Spot")
    ax.set_title(f"{ts_dict['Stock IDs'][0]} Vega Map")
    avg_m = int(round(avg_life * 12))
    ax.axvline(avg_m, color="red", linestyle="--")
    ax.axhline(barrier, color="red", linestyle="--")
    ax.plot(avg_m, barrier, "ro")

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img_bytes = buf.getvalue()

    filename = f"vega_map_{datetime.utcnow():%Y%m%dT%H%M%S}.png"
    return {"content": img_bytes, "filename": filename}

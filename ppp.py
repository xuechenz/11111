buf = BytesIO()
    fig = make_heatmap(
        strikes=matrix and list(ts_dict['Stock IDs']),
        spot=fetch_spot_and_strikes(ts_dict['Stock IDs'][0])[0],
        matrix=matrix,
        tenors=[f"{m}m" for m in range(0, 61, 3)],
        avg_life=avg_life,
        barrier=ts_dict['Maturity Barrier'],
        stock=ts_dict['Stock IDs'][0]
    )
    # Render to PNG bytes
    fig.write_image(buf, format='png', width=800, height=600, scale=2)
    buf.seek(0)
    # Use send_bytes to stream bytes directly
    filename = f"vega_map_{datetime.utcnow():%Y%m%dT%H%M%S}.png"
    return send_bytes(lambda out: out.write(buf.read()), filename)

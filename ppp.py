@dash.callback(
    Output("upload-status", "children"),
    Output("edited-json-store", "data"),
    Output("json-preview", "children"),
    Output("btn-gen-vega", "disabled"),
    Input("upload-json-file", "contents"),
    State("upload-json-file", "filename"),
    prevent_initial_call=True,
)
def parse_and_override(contents, filename):
    if not contents:
        return "No file uploaded.", dash.no_update, dash.no_update, True

    # ---- Decode --------------------------------------------------------------------
    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        data = json.load(io.StringIO(decoded.decode("utf-8")))
    except Exception as e:
        return f"Error reading {filename}: {e}", None, "", True

    # ---- ✏️  Override logic happens *here* -----------------------------------------
    # (1) Initial Levels -------------------------------------------------------------
    data["Initial Levels"] = [4321.55, 18_345.67]  # TODO: replace with live spots

    # (2) Replace bumps completely ---------------------------------------------------
    new_bumps = [{
        "Type": "Volatility Bump",
        "Bump Method": "Absolute",
        "Stock IDs": [data.get("Stock IDs", ["UNDL.IDX"])[0]],
        "Strike": 1.0,
        "Tenor Bump Sizes": [[0.00, 0.0025, 0.00, 0.00]],
        "Tenors": ["3m", "6m", "9m", "12m"],
    }]
    data["bumps"] = new_bumps

    preview = _safe_json_pretty(data)
    status = f"Loaded {filename} & overrides applied"
    return status, data, preview, False  # enable Generate button

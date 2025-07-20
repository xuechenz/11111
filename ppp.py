import base64
import io
import json
from typing import Any, Dict

import dash
from dash import Dash, html, dcc, Input, Output, State, callback_context as ctx
import dash_bootstrap_components as dbc


def _safe_json_pretty(data: Any, max_chars: int = 200_000) -> str:
    try:
        s = json.dumps(data, indent=2, sort_keys=False)
    except Exception as e:
        s = f"<JSON serialization error: {e}>"
    if len(s) > max_chars:
        s = s[:max_chars] + "\n... <truncated> ..."
    return s

sidebar = html.Div([
    html.H5("Upload & Settings", className="p-3 fw-bold text-center"),

    dbc.Label("Quote ID", html_for="quote-id", className="small fw-semibold"),
    dbc.Input(id="quote-id", type="text", size="sm", placeholder="(optional)"),

    dbc.Label("Iteration Number", html_for="iteration-num", className="small fw-semibold mt-2"),
    dbc.Input(id="iteration-num", type="text", size="sm", placeholder="(optional)"),

    dcc.Upload(
        id="upload-json-file",
        children=html.Div(["Drag & Drop or ", html.A("Select JSON File")]),
        style={
            "width": "100%", "height": "70px", "lineHeight": "70px",
            "borderWidth": "1px", "borderStyle": "dashed", "borderRadius": "5px",
            "textAlign": "center", "margin": "10px 0", "fontSize": "12px",
        },
        multiple=False,
    ),
    html.Div(id="upload-status", className="small text-muted mb-2", style={"minHeight": "1.2em"}),

    dbc.Button("Generate Vega Map", id="btn-gen-vega", color="success", className="w-100 mt-2", disabled=True),
], style={
    "position": "fixed", "top": "56px", "bottom": "0", "left": "0", "width": "300px",
    "padding": "10px", "overflow": "auto", "backgroundColor": "#f8f9fa",
})


content = html.Div([
    dcc.Store(id="uploaded-json-store"),
    dcc.Store(id="edited-json-store"),
    dcc.Store(id="spot-store"),
    dcc.Store(id="strikes-store"),
    dcc.Store(id="avg-life-store"),
    dcc.Store(id="vega-matrix-store"),

    dcc.Tabs([
        dcc.Tab(label="Uploaded JSON", children=[html.Pre(id="json-preview", className="small")]),
        dcc.Tab(label="Vega Map", children=[
            html.Div(id="progress-text", style={"margin": "10px 0"}),
            dcc.Loading(dcc.Graph(id="vega-heatmap", className="circle")),
            dbc.Button("Download Vega CSV", id="btn-dl-vega-csv", color="secondary", className="mt-3 me-2", disabled=True),
            dbc.Button("Download Vega Map", id="btn-dl-vega-png", color="secondary", className="mt-3", disabled=True),
            dcc.Download(id="dl-vega-csv"),
            dcc.Download(id="dl-vega-png"),
        ]),
    ])
], style={"marginLeft": "300px", "padding": "20px"})


navbar = dbc.Navbar([
    dbc.Container([
        html.Img(src="/assets/TD_Securities_logo.svg", height="40px"),
        dbc.NavbarBrand("Vega Map Generator", className="ms-3 fw-bold"),
    ])
], color="dark", dark=True, sticky="top", style={"paddingLeft": "8px"})


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Vega Map Generator"
app.layout = html.Div([navbar, sidebar, content])
server = app.server


@dash.callback(
    Output("upload-status", "children"),
    Output("uploaded-json-store", "data"),
    Output("json-preview", "children"),
    Output("btn-gen-vega", "disabled"),
    Input("upload-json-file", "contents"),
    State("upload-json-file", "filename"),
    prevent_initial_call=True,
)
def parse_uploaded_json(contents, filename):
    if not contents:
        return "No file uploaded.", dash.no_update, dash.no_update, True
    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        data = json.load(io.StringIO(decoded.decode("utf-8")))
    except Exception as e:
        return f"Error reading {filename}: {e}", None, "", True
    return f"Loaded {filename} (OK)", data, _safe_json_pretty(data), False


@dash.callback(
    Output("progress-text", "children"),
    Output("edited-json-store", "data"),
    Input("btn-gen-vega", "n_clicks"),
    State("uploaded-json-store", "data"),
    prevent_initial_call=True,
)
def run_vega_map(n, uploaded_json):
    if not n:
        raise dash.exceptions.PreventUpdate
    if not uploaded_json:
        return "Upload a JSON first …", dash.no_update
    # TODO – integrate pricer / Vega calc here
    return "Pricing submitted … (stub)", uploaded_json


if __name__ == "__main__":
    app.run(debug=True, port=8050)

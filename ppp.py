import dash, pandas as pd
from datetime import date
from pandas.tseries.offsets import BDay
from dash import html, dcc
import dash_bootstrap_components as dbc

external = [dbc.themes.LUX,
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css"]

app = dash.Dash(__name__, external_stylesheets=external)
app.title = "GED Manager"


def placeholder(label):
    return dbc.Alert(f"{label} – replace with real content", color="secondary", className="mb-3")

main_keys = ["vol", "div", "repo", "rate", "corr", "spot"]
sub_names = ["Data", "Visualization", "Analysis", "Benchmark", "Fitter", "Spread"]

content_map = {}
for m in main_keys:
    for i, lbl in enumerate(sub_names, 1):
        key = (m, str(i))
        content_map[key] = lambda l=lbl, m=m: placeholder(f"{m.upper()} – {l}")


def make_subtabs(main_key):
    children = []
    for idx, lbl in enumerate(sub_names, 1):
        tab_val = f"{main_key}-sub{idx}"
        pg      = content_map[(main_key, str(idx))]
        children.append(
            dcc.Tab(label=lbl, value=tab_val, children=pg())
        )
    return dcc.Tabs(id=f"{main_key}-subtabs", value=f"{main_key}-sub1",
                    children=children, className="mb-4")


navbar = dbc.NavbarSimple(
    brand=html.Span([
        html.Img(src="assets/TD_Securities_logo.svg", height="32px", className="me-2"),
        "GED MANAGER"
    ], className="d-flex align-items-center"),
    color="light", className="mb-4 shadow-sm",
    brand_style={"fontWeight":"bold","fontSize":"20px","color":"black"}
)


main_labels = dict(zip(
    main_keys,
    ["Volatility","Dividend","Repo","Rate","Correlation","Spot"]
))
app.layout = dbc.Container([
    navbar,
    dcc.Tabs(id="main-tabs", value="vol",
             children=[dcc.Tab(label=lab, value=key) for key,lab in main_labels.items()],
             colors={"border":"transparent","primary":"#0defd","background":"#f8f9fa"},
             className="mb-4"),
    html.Div(id="main-content")
], fluid=True, className="px-4")

@app.callback(Output("main-content","children"),
              Input("main-tabs","value"))
def display_subtabs(main_key):
    return make_subtabs(main_key)


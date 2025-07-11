import io, requests, pandas as pd, datetime as dt
import win32com.client

HOST    = "https://dashboard.td.com/dash/GED_Manager_Summary_New"
PARAMS  = {"fmt": "csv"}
VERIFY  = False

ENDPOINTS = {
    "iv"  : "/api/iv-summary",
    "div" : "/api/div-summary",
    "repo": "/api/repo-summary",
}

HEADERS = {
    "iv"  : "Implied Volatility Difference (12 m 80 % Strike, |diff| > 0.5)",
    "div" : "Dividend Difference (12 m, |diff| > 0.5)",
    "repo": "Forward (Repo) Difference (12 m, |diff| > 0.5)",
}

def fetch_df(url: str) -> pd.DataFrame:
    r = requests.get(url, params=PARAMS, verify=VERIFY, timeout=30)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))

def df_to_html(df: pd.DataFrame) -> str:
    return (
        df.to_html(index=False, border=0, justify="center")
          .replace("<table", '<table style="border-collapse:collapse;font-family:Segoe UI;font-size:12px"')
          .replace("<th",    '<th style="padding:4px 8px;background:#f9f9f9;border:1px solid #ddd"')
          .replace("<td",    '<td style="padding:4px 8px;border:1px solid #ddd;text-align:center"')
    )

def send_outlook_email(to_addr: list[str], subject: str, html_body: str) -> None:
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail    = outlook.CreateItem(0)                
    mail.To = "; ".join(to_addr)                
    mail.Subject  = subject
    mail.HTMLBody = html_body
    mail.Send()

if __name__ == "__main__":
    tables_html_ca  = []
    tables_html_oth = []
    today_str = dt.date.today().strftime("%Y-%m-%d")

    for key, ep in ENDPOINTS.items():
        try:
            full_df = fetch_df(HOST + ep)
        except Exception as e:
            err = f"<p><i>Error: {e}</i></p>"
            tables_html_ca.append(f"<h3>{HEADERS[key]}</h3>{err}")
            tables_html_oth.append(f"<h3>{HEADERS[key]}</h3>{err}")
            continue

        df_ca  = full_df[ full_df["Ticker"].str.endswith(".CA") ].copy()
        df_oth = full_df[~full_df["Ticker"].str.endswith(".CA") ].copy()

        for df_part, bucket in ((df_ca, tables_html_ca), (df_oth, tables_html_oth)):
            if df_part.empty:
                bucket.append(f"<h3>{HEADERS[key]}</h3><p><i>No records</i></p>")
            else:
                bucket.append(f"<h3>{HEADERS[key]}</h3>{df_to_html(df_part)}")

    BODY_TMPL = """
    <html><body>
    <p>Hi&nbsp;team,</p>
    <p>{universe} − TD&nbsp;minus&nbsp;Consensus summary as of <b>{date}</b></p>
    {tables}
    <p>Best,<br>Automated&nbsp;Benchmark&nbsp;Bot</p>
    </body></html>"""

    send_outlook_email(
        to_addr = ["Annie.Zhang2@tdsecurities.com", "joyce.chen@tdsecurities.com"],
        subject = f"[Auto-Bench] TD vs Consensus ⋅ CA tickers ({today_str})",
        html_body = BODY_TMPL.format(
            universe="Canadian Universe (.CA tickers)",
            date=today_str,
            tables="".join(tables_html_ca),
        ),
    )

    send_outlook_email(
        to_addr = ["Annie.Zhang2@tdsecurities.com", "joyce.chen@tdsecurities.com"],
        subject = f"[Auto-Bench] TD vs Consensus ⋅ Non-CA tickers ({today_str})",
        html_body = BODY_TMPL.format(
            universe="Global Universe (non-CA tickers)",
            date=today_str,
            tables="".join(tables_html_oth),
        ),
    )

    print("Two emails sent.")

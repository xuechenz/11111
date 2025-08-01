import os
import pandas as pd
import datetime as dt
from pandas.tseries.offsets import BDay
import pyodbc

BASE_DIR = os.path.join(os.getcwd(), "Spot_data")
os.makedirs(BASE_DIR, exist_ok=True)

TICKERS = ["PCG.US"]  

CONN_STR = (
    "DRIVER={SQL Server};"
    "SERVER=***,3341;"
    "DATABASE=**;"
    "UID=**;"
    "PWD=******"          
)

def fetch_daily_spot(conn, ticker, start_date, end_date_excl):

    sql = """
    WITH d AS (
        SELECT 
            BloombergTicker,
            CAST([timestamp] AS date) AS dte,
            [timestamp],
            [Last],
            ROW_NUMBER() OVER (
                PARTITION BY CAST([timestamp] AS date)
                ORDER BY [timestamp] DESC
            ) AS rn
        FROM Prices_SN_BMBG
        WHERE BloombergTicker = ?
          AND [timestamp] >= ? AND [timestamp] < ?
    )
    SELECT dte AS [Date], CAST(Last AS float) AS Spot
    FROM d WHERE rn = 1
    ORDER BY dte;
    """
    return pd.read_sql(sql, conn, params=[ticker, start_date, end_date_excl])

def fetch_intraday_hi_lo(conn, ticker, start_date, end_date_excl):
    sql = """
    SELECT 
        CAST([timestamp] AS date) AS [Date],
        CAST(MIN([Last]) AS float) AS Low,
        CAST(MAX([Last]) AS float) AS High
    FROM Prices_SN_BMBG
    WHERE BloombergTicker = ?
      AND [timestamp] >= ? AND [timestamp] < ?
    GROUP BY CAST([timestamp] AS date)
    ORDER BY [Date];
    """
    df = pd.read_sql(sql, conn, params=[ticker, start_date, end_date_excl])
    if not df.empty:
        df["RangePct"] = (df["High"] - df["Low"]) / df["Low"]
    return df

def process_ticker(ticker: str):
    end_bday = (pd.Timestamp.today().normalize() if pd.Timestamp.today().weekday() < 5 
                else (pd.Timestamp.today().normalize() - BDay(1)))
    start_bday = end_bday - BDay(252*5)
    start_date = start_bday.date()
    end_date_excl = (end_bday + BDay(1)).date()

    with pyodbc.connect(CONN_STR) as conn:
        spot = fetch_daily_spot(conn, ticker, start_date, end_date_excl)
        hilo = fetch_intraday_hi_lo(conn, ticker, start_date, end_date_excl)

    bdays = pd.date_range(start=start_bday, end=end_bday, freq="B").date
    spot = spot[spot["Date"].isin(bdays)].reset_index(drop=True)
    hilo = hilo[hilo["Date"].isin(bdays)].reset_index(drop=True)

    out_dir = os.path.join(BASE_DIR, ticker)
    os.makedirs(out_dir, exist_ok=True)
    spot_path = os.path.join(out_dir, "spot_5y.csv")
    spot.to_csv(spot_path, index=False)

    merged = pd.merge(hilo, spot, on="Date", how="inner")
    gt10 = merged[merged["RangePct"] >= 0.10].copy()
    gt10 = gt10[["Date", "Spot", "Low", "High", "RangePct"]]
    gt10_path = os.path.join(out_dir, "intraday_gt10pct.csv")
    gt10.to_csv(gt10_path, index=False)

    print(f"[{ticker}] spot saved to: {spot_path}")
    print(f"[{ticker}] ≥10% intraday: {gt10_path}")

if __name__ == "__main__":
    for t in TICKERS:
        process_ticker(t)

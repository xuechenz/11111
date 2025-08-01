import os
import pandas as pd
from pandas.tseries.offsets import BDay
from xbbg import blp

BASE = os.path.join(os.getcwd(), "Spot_data")
TICKERS = ["TTD US Equity"]         

def fetch_bbg_px_last_adj(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = blp.bdh(
        tickers=ticker,
        flds='px_last',
        start_date=start,
        end_date=end,
        adjust='all', 
        Fill='P',    
        Days='A',  
        Per='D',
    )
    df = df.reset_index().rename(columns={'index': 'Date', ('px_last', ticker): 'BBG_PX_LAST_ADJ'})
    if 'Date' not in df.columns:
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    if 'BBG_PX_LAST_ADJ' not in df.columns:
        last_col = [c for c in df.columns if isinstance(c, tuple) and c[0].lower() in ('px_last','last_price')]
        if last_col:
            df['BBG_PX_LAST_ADJ'] = df[last_col[0]]
        elif 'px_last' in df.columns:
            df['BBG_PX_LAST_ADJ'] = df['px_last']
        elif 'last_price' in df.columns:
            df['BBG_PX_LAST_ADJ'] = df['last_price']
    return df[['Date', 'BBG_PX_LAST_ADJ']]

def compare_one_ticker(bbg_ticker: str):
    td_ticker_folder = bbg_ticker.replace(' ', '_').replace('/', '-')  
    folder = os.path.join(BASE, td_ticker_folder)
    spot_path = os.path.join(folder, "spot_5y.csv")
    gt10_path = os.path.join(folder, "intraday_gt10pct.csv")
    out_path  = os.path.join(folder, "bbg_compare.csv")
    os.makedirs(folder, exist_ok=True)

    spot = pd.read_csv(spot_path, parse_dates=['Date'])
    gt10  = pd.read_csv(gt10_path, parse_dates=['Date'])

    start = spot['Date'].min().date().strftime('%Y-%m-%d')
    end   = spot['Date'].max().date().strftime('%Y-%m-%d')
    bbg = fetch_bbg_px_last_adj(bbg_ticker, start, end)

    bdays = pd.date_range(spot['Date'].min(), spot['Date'].max(), freq='B')
    spot = spot.set_index('Date').reindex(bdays).rename_axis('Date').reset_index()
    bbg  = bbg.set_index('Date').reindex(bdays).rename_axis('Date').reset_index()

    df = spot.merge(bbg, on='Date', how='left')
    df['TD_Spot_ret']  = df['Spot'].pct_change()
    df['BBG_ret']      = df['BBG_PX_LAST_ADJ'].pct_change()

    gt10_flag = set(pd.to_datetime(gt10['Date']).date)
    df['Is_IntradayMove_GT10'] = df['Date'].dt.date.isin(gt10_flag)

    def label_row(x, td_thr=0.10, bbg_thr=0.03):
        if not x['Is_IntradayMove_GT10']:
            return ''
        td_ok  = pd.notna(x['TD_Spot_ret'])
        bbg_ok = pd.notna(x['BBG_ret'])
        if not bbg_ok:
            return 'DataGap_BBG'
        if abs(x['TD_Spot_ret']) >= td_thr and abs(x['BBG_ret']) < bbg_thr:
            return 'Missing_Adjustment_Suspect'
        if abs(x['TD_Spot_ret']) >= td_thr and abs(x['BBG_ret']) >= td_thr:
            return 'True_Move'
        return 'Check'

    df['Label'] = df.apply(label_row, axis=1)

    out = df[df['Is_IntradayMove_GT10']].copy()
    out = out[['Date','Spot','BBG_PX_LAST_ADJ','TD_Spot_ret','BBG_ret','Label']]
    out.to_csv(out_path, index=False)
    print(f"[{bbg_ticker}] Result → {out_path}")

if __name__ == "__main__":
    for tk in TICKERS:
        compare_one_ticker(tk)

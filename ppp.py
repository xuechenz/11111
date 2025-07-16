today = pd.Timestamp.today()  
yesterday_bd = (today - pd.tseries.offsets.BDay(1)).date()
today_str = yesterday_bd.strftime("%Y-%m-%d")

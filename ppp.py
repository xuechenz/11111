def main():
    ENV = {
        "name": "111",
        "password": "1111"
    }
    HOST = "111"
    PORT = 111

    AUTOCALL_DATES = ["2025-11-07", "2026-02-09", "2026-05-07", "2026-08-07"]
    
    STRIKE = 1.0         
    TENOR = "3m"       

    result = price_autocall(
        host=HOST,
        port=PORT,
        env=ENV,
        autocall_dates=AUTOCALL_DATES,
        strike=STRIKE,
        tenors=[TENOR]
    )
    print(result)

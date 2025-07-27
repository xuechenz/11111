from datetime import datetime, timedelta

def get_latest_workday(today=None):
    if today is None:
        today = datetime.today()
    
    weekday = today.weekday()
    
    if weekday >= 5:
        days_to_subtract = weekday - 4 
        latest_workday = today - timedelta(days=days_to_subtract)
    else:
        latest_workday = today
    
    return latest_workday.date()

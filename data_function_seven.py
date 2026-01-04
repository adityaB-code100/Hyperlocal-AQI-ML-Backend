from datetime import datetime, timedelta

def next_seven_days(start_date_str):
    # Try multiple formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            start_date = datetime.strptime(start_date_str, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError("Date format must be YYYY-MM-DD or DD-MM-YYYY")

    # Always return in DD-MM-YYYY format
    return [(start_date + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(15)]

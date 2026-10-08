from datetime import datetime, timedelta
from typing import List

def parse_date(date_str: str) -> datetime:
    """Parse date from common string formats (YYYY-MM-DD or DD-MM-YYYY)."""
    if not date_str:
        raise ValueError("Date string cannot be empty")
    cleaned = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date format must be YYYY-MM-DD or DD-MM-YYYY, got: {date_str}")

def get_current_date() -> str:
    """Get current date formatted as DD-MM-YYYY."""
    return datetime.now().strftime("%d-%m-%Y")

def next_days(start_date_str: str, n_days: int = 7) -> List[str]:
    """Generate n consecutive dates starting from start_date_str in DD-MM-YYYY format."""
    start_date = parse_date(start_date_str)
    return [(start_date + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(n_days)]

def next_seven_days(start_date_str: str) -> List[str]:
    """
    Generate exactly seven consecutive days starting from start_date_str.
    Returns list of 7 dates in DD-MM-YYYY format.
    """
    return next_days(start_date_str, n_days=7)

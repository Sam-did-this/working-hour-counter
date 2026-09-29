# timesheet.py — time parsing and pay math

def parse_time(text):
    """'7:30 AM' or '19:30' -> minutes since midnight."""
    text = text.strip().upper()
    is_pm = "PM" in text
    is_am = "AM" in text
    text = text.replace("AM", "").replace("PM", "").strip()

    if ":" in text:
        h, m = text.split(":")
        hours = int(h)
        minutes = int(m)
    else:
        hours = int(text)
        minutes = 0

    if is_pm and hours != 12:
        hours += 12
    if is_am and hours == 12:
        hours = 0

    return hours * 60 + minutes


def shift_hours(start_str, end_str):
    """Full-precision hours between two times (handles midnight wrap)."""
    start = parse_time(start_str)
    end = parse_time(end_str)
    diff = end - start
    if diff < 0:
        diff += 24 * 60
    return diff / 60


def daily_pay(start_str, end_str, rate):
    """Pay for one shift: unrounded hours * rate, rounded to 2 decimals."""
    hours = shift_hours(start_str, end_str)
    return round(hours * rate, 2)


def display_hours(hours):
    """Round hours for display only."""
    return round(hours, 2)

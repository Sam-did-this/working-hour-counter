# report.py — group entries by week and export to Excel

from datetime import date, datetime, timedelta
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

from transfer_data import load_entries
from settings import HOURLY_RATE, CURRENCY


def week_key(fecha_str):
    """'2026-09-29' -> '2026-W39' (ISO week identifier)."""
    d = date.fromisoformat(fecha_str)
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def week_start(fecha_str):
    """'2026-09-29' -> '2026-09-28' (Monday of that week)."""
    d = date.fromisoformat(fecha_str)
    return (d - timedelta(days=d.weekday())).isoformat()


def group_by_week(entries):
    """Return {week_key: [entries sorted by date]}."""
    groups = {}
    for e in entries:
        if "fecha" not in e:
            continue #This is for skipping old formats
        key = week_key(e["fecha"])
        groups.setdefault(key, []).append(e)

    # sort each week's entries by fecha
    for key in groups:
        groups[key].sort(key=lambda x: x["fecha"])

    return groups


def write_week_sheet(wb, week_key_str, entries):
    """Create one sheet for one week."""
    ws = wb.create_sheet(title=week_key_str)

    # --- Header ---
    headers = ["Date", "Day", "Start", "End", "Hours", "Rate", "Daily Total"]
    ws.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="2F4F4F")
    for col, _ in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # --- Rows ---
    total_h = 0
    total_p = 0
    for e in entries:
        d = date.fromisoformat(e["fecha"])
        ws.append([
            e["fecha"],                    # 2026-09-21
            d.strftime("%A"),              # Monday
            e["entrada"],                  # 7:30 AM
            e["salida"],                   # 8:07 PM
            round(e["horas"], 2),
            HOURLY_RATE,
            round(e["pago"], 2),
        ])
        total_h += e["horas"]
        total_p += e["pago"]

    # --- Totals row ---
    ws.append([])   # blank row
    ws.append(["Total Weekly Hours:", "", "", "", round(total_h, 2)])
    ws.append(["Total Weekly Payment:", "", "", "", "", "", round(total_p, 2)])

    # --- Column widths ---
    widths = [12, 12, 12, 12, 10, 10, 14]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w

    return ws

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)   # create it if it doesn't exist


def week_range(week_key_str):
    """
    Given '2026-W39', return ('2026-09-21', '2026-09-27').
    """
    # ISO week format: '2026-W39'
    year, week = week_key_str.split("-W")
    year = int(year)
    week = int(week)

    # Monday of that ISO week
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)

    return monday.isoformat(), sunday.isoformat()


def export_week(week_key_str, entries):
    """Write one week to its own file. Returns the path."""
    start, end = week_range(week_key_str)
    filename = f"{start}_to_{end}.xlsx"
    output_path = OUTPUT_DIR / filename

    wb = Workbook()
    wb.remove(wb.active)
    write_week_sheet(wb, week_key_str, entries)
    wb.save(output_path)

    print(f"Saved: {output_path}")
    return output_path


def export_all():
    """Group entries by week, write one file per week."""
    entries = load_entries()
    if not entries:
        print("No entries to export.")
        return []

    groups = group_by_week(entries)
    if not groups:
        print("No valid entries (all missing 'fecha').")
        return []

    paths = []
    for week_key_str in sorted(groups.keys()):
        path = export_week(week_key_str, groups[week_key_str])
        paths.append(path)

    return paths

if __name__ == "__main__":
    export_all()

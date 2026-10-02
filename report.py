# report.py — build a single Excel file with two sheets:
#              "Semana Anterior" (last completed Mon–Sun)
#              "Semana Actual"   (this Mon -> today)

from datetime import date, timedelta
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from transfer_data import load_entries, append_log
from settings import HOURLY_RATE, CURRENCY


OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "timesheet.xlsx"


# ---------- date helpers ----------

def week_key(fecha_str):
    """'2026-09-29' -> '2026-W39' (ISO week identifier)."""
    d = date.fromisoformat(fecha_str)
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def week_range(week_key_str):
    """'2026-W39' -> ('2026-09-21', '2026-09-27')."""
    year, week = week_key_str.split("-W")
    year, week = int(year), int(week)
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def monday_of(d):
    return d - timedelta(days=d.weekday())


def display_date(iso_str):
    """'2026-09-29' -> '09/29/2026'."""
    d = date.fromisoformat(iso_str)
    return d.strftime("%m/%d/%Y")


# ---------- entry filtering ----------

def split_weeks(entries, today=None):
    """
    Return (prev_entries, curr_entries, prev_bounds, curr_bounds).

    prev_bounds / curr_bounds = (start_iso, end_iso).
    """
    today = today or date.today()

    curr_start = monday_of(today)
    curr_end   = today                       # current week ends today
    prev_start = curr_start - timedelta(days=7)
    prev_end   = curr_start - timedelta(days=1)

    prev_entries, curr_entries = [], []

    for e in entries:
        if "fecha" not in e:
            continue  # skip legacy entries
        d = date.fromisoformat(e["fecha"])
        if prev_start <= d <= prev_end:
            prev_entries.append(e)
        elif curr_start <= d <= curr_end:
            curr_entries.append(e)

    prev_entries.sort(key=lambda x: x["fecha"])
    curr_entries.sort(key=lambda x: x["fecha"])

    return (
        prev_entries, curr_entries,
        (prev_start.isoformat(), prev_end.isoformat()),
        (curr_start.isoformat(), curr_end.isoformat()),
    )


def weekly_totals(entries):
    return {
        "hours": round(sum(e.get("horas", 0) for e in entries), 2),
        "pay":   round(sum(e.get("pago",  0) for e in entries), 2),
    }


# ---------- sheet writer ----------

HEADERS = ["Date", "Day", "Start", "End", "Hours", "Rate", "Daily Total"]
WIDTHS  = [12, 12, 12, 12, 10, 10, 14]

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="2F4F4F")
TITLE_FONT  = Font(bold=True, size=12)
TOTAL_FONT  = Font(bold=True)


def write_week_sheet(wb, tab_name, title_text, entries):
    """Create one sheet with a title row, header row, entries, and totals."""
    ws = wb.create_sheet(title=tab_name)

    # Title row (merged across all columns)
    ws.append([title_text])
    ws.merge_cells(
        start_row=1, start_column=1,
        end_row=1,   end_column=len(HEADERS),
    )
    ws.cell(row=1, column=1).font = TITLE_FONT
    ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
    ws.append([])  # blank spacer

    # Header row
    ws.append(HEADERS)
    header_row_idx = ws.max_row
    for col in range(1, len(HEADERS) + 1):
        c = ws.cell(row=header_row_idx, column=col)
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.alignment = Alignment(horizontal="center")

    # Entry rows
    total_h = 0.0
    total_p = 0.0
    for e in entries:
        d = date.fromisoformat(e["fecha"])
        ws.append([
            display_date(e["fecha"]),
            d.strftime("%A"),
            e.get("entrada", ""),
            e.get("salida",  ""),
            round(e.get("horas", 0), 2),
            HOURLY_RATE,
            round(e.get("pago",  0), 2),
        ])
        total_h += e.get("horas", 0)
        total_p += e.get("pago",  0)

    # Totals
    ws.append([])
    ws.append(["Total semanal (horas):", "", "", "",
               round(total_h, 2)])
    ws.append(["Total semanal (pago):",  "", "", "", "", "",
               f"{CURRENCY}{round(total_p, 2)}"])

    last = ws.max_row
    for row in (last - 1, last):
        for col in range(1, len(HEADERS) + 1):
            ws.cell(row=row, column=col).font = TOTAL_FONT

    # Column widths
    for i, w in enumerate(WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    return ws


# ---------- public entry point ----------

def export_weekly_report():
    """
    Build reports/timesheet.xlsx with exactly two sheets.
    Logs an 'export_report' event with the full entries for both weeks.
    Returns the output path.
    """
    entries = load_entries()

    (prev_entries, curr_entries,
     prev_bounds, curr_bounds) = split_weeks(entries)

    prev_totals = weekly_totals(prev_entries)
    curr_totals = weekly_totals(curr_entries)

    wb = Workbook()
    wb.remove(wb.active)  # drop the default empty sheet

    write_week_sheet(
        wb,
        tab_name="Semana Anterior",
        title_text=f"Semana del {display_date(prev_bounds[0])} "
                   f"al {display_date(prev_bounds[1])}",
        entries=prev_entries,
    )
    write_week_sheet(
        wb,
        tab_name="Semana Actual",
        title_text=f"Semana del {display_date(curr_bounds[0])} "
                   f"al {display_date(curr_bounds[1])}",
        entries=curr_entries,
    )

    wb.save(OUTPUT_FILE)

    append_log({
        "action": "export_report",
        "file":   str(OUTPUT_FILE),
        "prev_week": {
            "start":   prev_bounds[0],
            "end":     prev_bounds[1],
            "hours":   prev_totals["hours"],
            "pay":     prev_totals["pay"],
            "entries": prev_entries,
        },
        "curr_week": {
            "start":   curr_bounds[0],
            "end":     curr_bounds[1],
            "hours":   curr_totals["hours"],
            "pay":     curr_totals["pay"],
            "entries": curr_entries,
        },
    })

    return OUTPUT_FILE


if __name__ == "__main__":
    path = export_weekly_report()
    print(f"Saved: {path}")

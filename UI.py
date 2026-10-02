# UI.py — minimal App for Dad window

import tkinter as tk
from tkinter import messagebox
from datetime import date

from transfer_data import save_entry, append_log
from settings import HOURLY_RATE
from timesheet import shift_hours, daily_pay
from report import export_weekly_report


INSTRUCTION = (
    "Por favor ingresa tu hora de entrada y de salida.\n"
    "Usa formato AM/PM (ejemplo: 7:30 AM, 8:07 PM)."
)

WARNING = (
    "No te preocupes si ingresas mal el horario, solo sigue intentando "
    "hasta que lo ingreses bien, luego me comunicas para arreglarlo.\n"
    "Cualquier cosa que escribas en el Excel se borrará sin poder ser guardada."
)


def run():
    """Launch the App for Dad window."""

    def set_status(text, ok=True):
        status_var.set(text)
        status_label.config(fg="#2E7D32" if ok else "#C62828")

    def submit():
        start = entry_in.get().strip()
        end   = entry_out.get().strip()

        if not start or not end:
            set_status("Faltan datos: ingresa hora de entrada y de salida.", ok=False)
            return

        try:
            h = shift_hours(start, end)
            p = daily_pay(start, end, HOURLY_RATE)
        except ValueError:
            set_status("Formato inválido. Usa algo como 7:30 AM o 19:30.", ok=False)
            return

        entry = {
            "fecha":   date.today().isoformat(),
            "entrada": start,
            "salida":  end,
            "horas":   round(h, 2),
            "pago":    p,
        }
        save_entry(entry)
        append_log({"action": "add_entry", "entry": entry})

        entry_in.delete(0, tk.END)
        entry_out.delete(0, tk.END)
        entry_in.focus_set()

        set_status("✓ Guardado. Revisa tu reporte en el archivo Excel.", ok=True)

    def generate_excel():
        try:
            path = export_weekly_report()
            set_status(f"✓ Excel actualizado: {path.name}", ok=True)
        except PermissionError:
            set_status(
                "No se puede guardar el Excel. Por favor cierra el documento si es que lo tienes abierto. Gracias.",
                ok=False,
            )
        except Exception as e:
            set_status(f"Error al generar Excel: {type(e).__name__}: {e}", ok=False)
            messagebox.showerror("Error", f"{type(e).__name__}: {e}")

    # --- window ---
    root = tk.Tk()
    root.title("App for Dad")
    root.geometry("560x480")

    tk.Label(
        root, text=INSTRUCTION,
        justify="center", wraplength=500,
    ).pack(pady=(20, 15))

    tk.Label(root, text="Hora de entrada:").pack(pady=(10, 3))
    entry_in = tk.Entry(root, width=20, justify="center")
    entry_in.pack(pady=3)

    tk.Label(root, text="Hora de salida:").pack(pady=(10, 3))
    entry_out = tk.Entry(root, width=20, justify="center")
    entry_out.pack(pady=3)

    tk.Button(root, text="Guardar", width=18, command=submit).pack(pady=(15, 5))

    tk.Label(
        root, text=WARNING,
        justify="center", wraplength=500,
        fg="gray", font=("TkDefaultFont", 9, "italic"),
    ).pack(pady=(10, 10))

    status_var = tk.StringVar(value="")
    status_label = tk.Label(
        root, textvariable=status_var,
        justify="center", wraplength=500,
    )
    status_label.pack(pady=(5, 15))

    tk.Button(root, text="Generar Excel", width=18, command=generate_excel).pack(pady=3)
    tk.Button(root, text="Cerrar",       width=18, command=root.destroy).pack(pady=3)

    entry_in.focus_set()
    root.bind("<Return>", lambda e: submit())
    root.mainloop()

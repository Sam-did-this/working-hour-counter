import tkinter as tk
from tkinter import messagebox
from datetime import date

from transfer_data import save_entry, load_entries
from settings import HOURLY_RATE, CURRENCY
from timesheet import shift_hours, daily_pay
from report import export_all


def run():
    """Launch the App for Dad window."""

    def refresh_list():
    try:
        entries = load_entries()
    except Exception as e:
        messagebox.showerror(
            "Error al leer los datos",
            f"{type(e).__name__}: {e}\n\nRevisa target.json"
        )
        return

    listbox.delete(0, tk.END)
    for item in entries:
        fecha   = item.get("fecha", "?")
        entrada = item.get("entrada", "?")
        salida  = item.get("salida", "?")
        listbox.insert(tk.END, f"{fecha}  {entrada} -> {salida}")

    def submit():
        start = entry_in.get().strip()
        end   = entry_out.get().strip()

        if not start or not end:
            messagebox.showwarning("Faltan datos", "Ingresa hora de entrada y salida.")
            return

        try:
            h = shift_hours(start, end)
            p = daily_pay(start, end, HOURLY_RATE)
        except ValueError:
            messagebox.showerror("Formato inválido", "Usa formato como 7:30 AM o 19:30")
            return

        save_entry({
            "fecha":   date.today().isoformat(),
            "entrada": start,
            "salida":  end,
            "horas":   round(h, 2),
            "pago":    p,
        })

        entry_in.delete(0, tk.END)
        entry_out.delete(0, tk.END)
        refresh_list()

    def generate_excel():
        try:
            paths = export_all()
            if not paths:
                messagebox.showinfo("Nada", "No hay entradas para exportar.")
                return
            msg = "\n".join(str(p) for p in paths)
            messagebox.showinfo("Listo", f"Excel generado:\n{msg}")
        except Exception as e:
            messagebox.showerror("Error", f"{type(e).__name__}: {e}")

    # --- Window ---
    root = tk.Tk()
    root.title("App for Dad")
    root.geometry("700x550")

    tk.Label(root, text="Hora de entrada:").pack(pady=(15, 5))
    entry_in = tk.Entry(root, width=20)
    entry_in.pack(pady=5)

    tk.Label(root, text="Hora de salida:").pack(pady=(10, 5))
    entry_out = tk.Entry(root, width=20)
    entry_out.pack(pady=5)

    tk.Button(root, text="Guardar", command=submit).pack(pady=10)

    tk.Label(root, text="Registros:").pack(pady=(10, 5))
    listbox = tk.Listbox(root, width=80, height=12)
    listbox.pack(pady=5, padx=15, fill=tk.BOTH, expand=True)

    tk.Label(
    root,
    text="No edites report.xlsx — se sobrescribe. Edita target.json solo si sabes qué haces.",
    fg="gray",
    font=("TkDefaultFont", 9, "italic")
).pack(pady=5)

    tk.Button(root, text="Generar Excel", command=generate_excel).pack(pady=5)
    tk.Button(root, text="Cerrar", command=root.destroy).pack(pady=5)

    entry_in.focus_set()
    root.bind("<Return>", lambda e: submit())
    refresh_list()
    root.mainloop()

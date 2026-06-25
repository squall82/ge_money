"""Module 4 - UI laporan.

Berisi 3 sub-laporan dalam inner notebook:
- 4a. Transaksi + sisa saldo pada satu titik tanggal.
- 4b. Pie chart kategori terbesar berdasarkan periode.
- 4c. Cashflow harian agregat (incoming/outgoing/net + saldo).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..config import TRANSACTION_TYPES
from ..services import running_balance_report, category_breakdown, daily_cashflow
from ..utils import format_currency, parse_date, today_str


class ReportView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=8)
        self.app = app
        self._build()

    def _build(self) -> None:
        self.inner = ttk.Notebook(self)
        self.inner.pack(fill="both", expand=True)

        self.tab_balance = ttk.Frame(self.inner, padding=8)
        self.tab_pie = ttk.Frame(self.inner, padding=8)
        self.tab_cashflow = ttk.Frame(self.inner, padding=8)

        self.inner.add(self.tab_balance, text="4a. Transaksi & Sisa Saldo")
        self.inner.add(self.tab_pie, text="4b. Kategori Terbesar (Pie)")
        self.inner.add(self.tab_cashflow, text="4c. Cashflow Harian")

        self._build_balance_tab()
        self._build_pie_tab()
        self._build_cashflow_tab()

    # ----------------------------------------------------------- 4a
    def _build_balance_tab(self) -> None:
        bar = ttk.Frame(self.tab_balance)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Posisi s/d tanggal:").pack(side="left")
        self.bal_date_var = tk.StringVar(value=today_str())
        ttk.Entry(bar, textvariable=self.bal_date_var, width=14).pack(side="left", padx=4)
        ttk.Label(bar, text="Rekening:").pack(side="left")
        self.bal_acc_var = tk.StringVar(value="(semua)")
        self.bal_acc_combo = ttk.Combobox(bar, textvariable=self.bal_acc_var,
                                          state="readonly", width=20)
        self.bal_acc_combo.pack(side="left", padx=4)
        ttk.Button(bar, text="Tampilkan", command=self._run_balance).pack(side="left", padx=4)

        cols = ("date", "type", "category", "account", "amount", "balance")
        self.bal_tree = ttk.Treeview(self.tab_balance, columns=cols, show="headings")
        headers = {"date": "Tanggal", "type": "Tipe", "category": "Kategori",
                   "account": "Rekening", "amount": "Nominal", "balance": "Saldo Berjalan"}
        for c in cols:
            self.bal_tree.heading(c, text=headers[c])
            self.bal_tree.column(c, width=120, anchor="e" if c in ("amount", "balance") else "w")
        self.bal_tree.pack(fill="both", expand=True)
        self.bal_tree.tag_configure("incoming", foreground="#1a7f37")
        self.bal_tree.tag_configure("outgoing", foreground="#c1121f")

        self.bal_summary = ttk.Label(self.tab_balance, text="", font=("", 10, "bold"))
        self.bal_summary.pack(anchor="w", pady=(6, 0))

    def _run_balance(self) -> None:
        try:
            parse_date(self.bal_date_var.get())
        except ValueError:
            messagebox.showerror("Gagal", "Format tanggal harus YYYY-MM-DD.")
            return
        as_of = self.bal_date_var.get().strip()
        accounts = self.app.accounts.list()
        txs = self.app.transactions.list()
        acc_filter = None if self.bal_acc_var.get() == "(semua)" else self.bal_acc_var.get()
        rows, balances = running_balance_report(txs, accounts, as_of, acc_filter)

        self.bal_tree.delete(*self.bal_tree.get_children())
        for r in rows:
            self.bal_tree.insert(
                "", "end",
                values=(r.date, r.type, r.category, r.account,
                        format_currency(r.signed), format_currency(r.balance)),
                tags=(r.type,),
            )
        total = sum(balances.values())
        parts = "  |  ".join(f"{n}: {format_currency(v)}" for n, v in balances.items())
        self.bal_summary.config(
            text=f"Sisa saldo per {as_of}  ->  Total: {format_currency(total)}    {parts}"
        )

    # ----------------------------------------------------------- 4b
    def _build_pie_tab(self) -> None:
        bar = ttk.Frame(self.tab_pie)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Dari:").pack(side="left")
        self.pie_start_var = tk.StringVar(value=self._month_start())
        ttk.Entry(bar, textvariable=self.pie_start_var, width=12).pack(side="left", padx=4)
        ttk.Label(bar, text="s/d:").pack(side="left")
        self.pie_end_var = tk.StringVar(value=today_str())
        ttk.Entry(bar, textvariable=self.pie_end_var, width=12).pack(side="left", padx=4)
        ttk.Label(bar, text="Tipe:").pack(side="left")
        self.pie_type_var = tk.StringVar(value="outgoing")
        ttk.Combobox(bar, textvariable=self.pie_type_var, values=list(TRANSACTION_TYPES),
                     state="readonly", width=12).pack(side="left", padx=4)
        ttk.Button(bar, text="Tampilkan", command=self._run_pie).pack(side="left", padx=4)

        self.pie_fig = Figure(figsize=(6, 4.4), dpi=100)
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, master=self.tab_pie)
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _run_pie(self) -> None:
        try:
            start = self.pie_start_var.get().strip()
            end = self.pie_end_var.get().strip()
            parse_date(start)
            parse_date(end)
        except ValueError:
            messagebox.showerror("Gagal", "Format tanggal harus YYYY-MM-DD.")
            return
        txs = self.app.transactions.list()
        data = category_breakdown(txs, start, end, self.pie_type_var.get())
        self.pie_ax.clear()
        if not data:
            self.pie_ax.text(0.5, 0.5, "Tidak ada data pada periode ini",
                             ha="center", va="center")
        else:
            labels = list(data.keys())
            values = list(data.values())
            total = sum(values)

            def autopct(pct):
                return f"{pct:.1f}%\n{format_currency(pct/100*total)}"

            self.pie_ax.pie(values, labels=labels, autopct=autopct, startangle=90,
                            textprops={"fontsize": 8})
            self.pie_ax.set_title(
                f"{self.pie_type_var.get().capitalize()} per kategori "
                f"({start} s/d {end}) - Total {format_currency(total)}"
            )
            self.pie_ax.axis("equal")
        self.pie_fig.tight_layout()
        self.pie_canvas.draw()

    # ----------------------------------------------------------- 4c
    def _build_cashflow_tab(self) -> None:
        bar = ttk.Frame(self.tab_cashflow)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Dari:").pack(side="left")
        self.cf_start_var = tk.StringVar(value=self._month_start())
        ttk.Entry(bar, textvariable=self.cf_start_var, width=12).pack(side="left", padx=4)
        ttk.Label(bar, text="s/d:").pack(side="left")
        self.cf_end_var = tk.StringVar(value=today_str())
        ttk.Entry(bar, textvariable=self.cf_end_var, width=12).pack(side="left", padx=4)
        ttk.Label(bar, text="Rekening:").pack(side="left")
        self.cf_acc_var = tk.StringVar(value="(semua)")
        self.cf_acc_combo = ttk.Combobox(bar, textvariable=self.cf_acc_var,
                                         state="readonly", width=18)
        self.cf_acc_combo.pack(side="left", padx=4)
        ttk.Button(bar, text="Tampilkan", command=self._run_cashflow).pack(side="left", padx=4)

        body = ttk.Frame(self.tab_cashflow)
        body.pack(fill="both", expand=True)

        cols = ("date", "incoming", "outgoing", "net", "balance")
        self.cf_tree = ttk.Treeview(body, columns=cols, show="headings", height=10)
        headers = {"date": "Tanggal", "incoming": "Incoming", "outgoing": "Outgoing",
                   "net": "Net", "balance": "Saldo"}
        for c in cols:
            self.cf_tree.heading(c, text=headers[c])
            self.cf_tree.column(c, width=110, anchor="e" if c != "date" else "w")
        self.cf_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(body, orient="vertical", command=self.cf_tree.yview)
        sb.pack(side="left", fill="y")
        self.cf_tree.configure(yscrollcommand=sb.set)

        self.cf_fig = Figure(figsize=(6, 3.2), dpi=100)
        self.cf_ax = self.cf_fig.add_subplot(111)
        self.cf_canvas = FigureCanvasTkAgg(self.cf_fig, master=self.tab_cashflow)
        self.cf_canvas.get_tk_widget().pack(fill="both", expand=True, pady=(6, 0))

    def _run_cashflow(self) -> None:
        try:
            start = self.cf_start_var.get().strip()
            end = self.cf_end_var.get().strip()
            parse_date(start)
            parse_date(end)
        except ValueError:
            messagebox.showerror("Gagal", "Format tanggal harus YYYY-MM-DD.")
            return
        accounts = self.app.accounts.list()
        txs = self.app.transactions.list()
        acc_filter = None if self.cf_acc_var.get() == "(semua)" else self.cf_acc_var.get()
        rows = daily_cashflow(txs, accounts, start, end, acc_filter, hide_zero_net=True)

        self.cf_tree.delete(*self.cf_tree.get_children())
        for r in rows:
            self.cf_tree.insert(
                "", "end",
                values=(r.date, format_currency(r.incoming), format_currency(r.outgoing),
                        format_currency(r.net), format_currency(r.balance)),
            )

        self.cf_ax.clear()
        if rows:
            dates = [r.date for r in rows]
            x = range(len(dates))
            self.cf_ax.bar([i - 0.2 for i in x], [r.incoming for r in rows],
                           width=0.4, label="Incoming", color="#1a7f37")
            self.cf_ax.bar([i + 0.2 for i in x], [r.outgoing for r in rows],
                           width=0.4, label="Outgoing", color="#c1121f")
            self.cf_ax.plot(list(x), [r.balance for r in rows], marker="o",
                            label="Saldo", color="#1f4e79")
            step = max(1, len(dates) // 12)
            self.cf_ax.set_xticks(list(x)[::step])
            self.cf_ax.set_xticklabels(dates[::step], rotation=45, ha="right", fontsize=7)
            self.cf_ax.legend(fontsize=8)
            self.cf_ax.set_title(f"Cashflow harian agregat ({start} s/d {end})")
            self.cf_ax.grid(True, axis="y", alpha=0.3)
        else:
            self.cf_ax.text(0.5, 0.5, "Tidak ada data pada periode ini",
                            ha="center", va="center")
        self.cf_fig.tight_layout()
        self.cf_canvas.draw()

    # ----------------------------------------------------------- shared
    @staticmethod
    def _month_start() -> str:
        from datetime import date
        d = date.today()
        return d.replace(day=1).strftime("%Y-%m-%d")

    def on_show(self) -> None:
        accounts = ["(semua)"] + self.app.accounts.names()
        for combo in (self.bal_acc_combo, self.cf_acc_combo):
            combo["values"] = accounts

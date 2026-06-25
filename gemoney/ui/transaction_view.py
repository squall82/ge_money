"""Module 3 - UI input transaksi.

Form input transaksi (tanggal, tipe, kategori level 2, rekening, nominal,
deskripsi) di bagian atas, daftar transaksi di bagian bawah.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from ..config import TRANSACTION_TYPES
from ..models import Transaction
from ..utils import (
    format_currency,
    parse_amount,
    parse_date,
    today_str,
    recurrence_dates,
    format_date,
    RECURRENCE_FREQUENCIES,
    FREQ_DAILY,
)


class TransactionView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=10)
        self.app = app
        self.repo = app.transactions
        self._editing_id: str | None = None
        self._build()
        self.on_show()

    def _build(self) -> None:
        self._build_tx_form()
        self._build_tx_list()

    # ------------------------------------------------ form transaksi
    def _build_tx_form(self) -> None:
        form = ttk.LabelFrame(self, text="Input Transaksi", padding=12)
        form.pack(fill="x")

        # Dua kolom field agar ringkas & rapi.
        # Kolom kiri
        ttk.Label(form, text="Tanggal").grid(row=0, column=0, sticky="w", padx=4, pady=5)
        self.date_var = tk.StringVar(value=today_str())
        ttk.Entry(form, textvariable=self.date_var, width=24).grid(
            row=0, column=1, sticky="w", padx=4, pady=5)
        ttk.Label(form, text="(YYYY-MM-DD)", foreground="gray").grid(
            row=0, column=2, sticky="w")

        ttk.Label(form, text="Kategori (level 2)").grid(row=1, column=0, sticky="w", padx=4, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form, textvariable=self.category_var,
                                            state="readonly", width=22)
        self.category_combo.grid(row=1, column=1, sticky="w", padx=4, pady=5)

        ttk.Label(form, text="Nominal").grid(row=2, column=0, sticky="w", padx=4, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_var, width=24).grid(
            row=2, column=1, sticky="w", padx=4, pady=5)

        # Kolom kanan
        ttk.Label(form, text="Tipe").grid(row=0, column=3, sticky="w", padx=(20, 4), pady=5)
        self.type_var = tk.StringVar(value="outgoing")
        ttk.Combobox(form, textvariable=self.type_var, values=list(TRANSACTION_TYPES),
                     state="readonly", width=22).grid(row=0, column=4, sticky="w", padx=4, pady=5)

        ttk.Label(form, text="Rekening").grid(row=1, column=3, sticky="w", padx=(20, 4), pady=5)
        self.account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(form, textvariable=self.account_var,
                                          state="readonly", width=22)
        self.account_combo.grid(row=1, column=4, sticky="w", padx=4, pady=5)

        ttk.Label(form, text="Deskripsi").grid(row=2, column=3, sticky="nw", padx=(20, 4), pady=5)
        self.desc_text = tk.Text(form, width=26, height=3)
        self.desc_text.grid(row=2, column=4, sticky="w", padx=4, pady=5)

        # Baris perulangan (recurrence)
        self.recur_frame = ttk.Frame(form)
        self.recur_frame.grid(row=3, column=0, columnspan=5, sticky="w", pady=(8, 0))
        ttk.Label(self.recur_frame, text="Ulangi").pack(side="left", padx=(4, 4))
        self.repeat_var = tk.StringVar(value="1")
        tk.Spinbox(self.recur_frame, from_=1, to=999, width=5,
                   textvariable=self.repeat_var).pack(side="left")
        ttk.Label(self.recur_frame, text="kali, frekuensi").pack(side="left", padx=(6, 4))
        self.freq_var = tk.StringVar(value=FREQ_DAILY)
        ttk.Combobox(self.recur_frame, textvariable=self.freq_var,
                     values=list(RECURRENCE_FREQUENCIES), state="readonly",
                     width=10).pack(side="left")
        ttk.Label(self.recur_frame, text="(isi 1 = tanpa perulangan)",
                  foreground="gray").pack(side="left", padx=(6, 0))

        # Tombol aksi
        btns = ttk.Frame(form)
        btns.grid(row=4, column=0, columnspan=5, pady=(10, 0), sticky="w")
        self.save_btn = ttk.Button(btns, text="Simpan transaksi", command=self._save_tx)
        self.save_btn.pack(side="left", padx=4)
        ttk.Button(btns, text="Bersihkan", command=self._clear_tx_form).pack(side="left", padx=4)

    # ------------------------------------------------ daftar transaksi
    def _build_tx_list(self) -> None:
        wrap = ttk.LabelFrame(self, text="Daftar Transaksi", padding=8)
        wrap.pack(fill="both", expand=True, pady=(10, 0))

        cols = ("date", "type", "category", "account", "amount", "description")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        headers = {"date": "Tanggal", "type": "Tipe", "category": "Kategori",
                   "account": "Rekening", "amount": "Nominal", "description": "Deskripsi"}
        widths = {"date": 95, "type": 90, "category": 150, "account": 160,
                  "amount": 130, "description": 260}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            anchor = "e" if c == "amount" else "w"
            self.tree.column(c, width=widths[c], anchor=anchor)
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.tag_configure("incoming", foreground="#1a7f37")
        self.tree.tag_configure("outgoing", foreground="#c1121f")
        self.tree.bind("<Double-1>", lambda _e: self._edit_selected())

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(6, 0))
        ttk.Button(bar, text="Edit terpilih", command=self._edit_selected).pack(side="left", padx=2)
        ttk.Button(bar, text="Hapus terpilih", command=self._delete_selected).pack(side="left", padx=2)
        ttk.Label(bar, text="(klik dua kali baris untuk edit)",
                  foreground="gray").pack(side="left", padx=8)

    # --------------------------------------------------------------- logic
    def on_show(self) -> None:
        cats = self.app.categories.list()
        cat_display = [c.display for c in sorted(cats, key=lambda x: x.display)]
        self._cat_lookup = {c.display: c.name for c in cats}
        self.category_combo["values"] = cat_display

        self.account_combo["values"] = self.app.accounts.names()
        self._refresh_list()

    def _refresh_list(self) -> None:
        self.tree.delete(*self.tree.get_children())
        txs = sorted(self.repo.list(), key=lambda t: (t.date, t.id), reverse=True)
        for t in txs:
            self.tree.insert(
                "", "end", iid=t.id,
                values=(t.date, t.type, t.category, t.account,
                        format_currency(t.amount), t.description),
                tags=(t.type,),
            )

    def _save_tx(self) -> None:
        try:
            base_date = parse_date(self.date_var.get())
        except ValueError:
            messagebox.showerror("Gagal", "Format tanggal harus YYYY-MM-DD.")
            return
        category_display = self.category_var.get()
        category = self._cat_lookup.get(category_display, category_display)
        try:
            amount = parse_amount(self.amount_var.get())
        except ValueError as e:
            messagebox.showerror("Gagal", f"Nominal tidak valid: {e}")
            return

        tx_type = self.type_var.get()
        account = self.account_var.get()
        description = self.desc_text.get("1.0", "end").strip()

        # Mode edit: selalu satu transaksi (perulangan diabaikan).
        if self._editing_id:
            tx = Transaction(date=self.date_var.get().strip(), type=tx_type,
                             category=category, account=account, amount=amount,
                             description=description)
            tx.id = self._editing_id
            try:
                self.repo.update(tx)
            except ValueError as e:
                messagebox.showerror("Gagal", str(e))
                return
            self._clear_tx_form()
            self._refresh_list()
            return

        # Mode tambah: dukung perulangan.
        try:
            count = int(self.repeat_var.get())
            if count < 1:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Gagal", "Jumlah perulangan harus angka >= 1.")
            return

        dates = recurrence_dates(base_date, count, self.freq_var.get())
        try:
            for d in dates:
                self.repo.add(Transaction(
                    date=format_date(d), type=tx_type, category=category,
                    account=account, amount=amount, description=description,
                ))
        except ValueError as e:
            messagebox.showerror("Gagal", str(e))
            self._refresh_list()
            return

        if len(dates) > 1:
            messagebox.showinfo(
                "Tersimpan",
                f"{len(dates)} transaksi dibuat ({self.freq_var.get().lower()}): "
                f"{format_date(dates[0])} s/d {format_date(dates[-1])}.",
            )
        self._clear_tx_form()
        self._refresh_list()

    def _edit_selected(self) -> None:
        item = self.tree.focus()
        if not item:
            return
        tx = next((t for t in self.repo.list() if t.id == item), None)
        if not tx:
            return
        self._editing_id = tx.id
        self.date_var.set(tx.date)
        self.type_var.set(tx.type)
        display = next((d for d, n in self._cat_lookup.items() if n == tx.category), tx.category)
        self.category_var.set(display)
        self.account_var.set(tx.account)
        self.amount_var.set(str(int(tx.amount)) if tx.amount == int(tx.amount) else str(tx.amount))
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", tx.description)
        # Perulangan tidak berlaku saat edit.
        self.repeat_var.set("1")
        self.freq_var.set(FREQ_DAILY)
        self.save_btn.config(text="Perbarui transaksi")

    def _delete_selected(self) -> None:
        item = self.tree.focus()
        if not item:
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus transaksi terpilih?"):
            return
        self.repo.delete(item)
        self._clear_tx_form()
        self._refresh_list()

    def _clear_tx_form(self) -> None:
        self._editing_id = None
        self.date_var.set(today_str())
        self.type_var.set("outgoing")
        self.category_var.set("")
        self.account_var.set("")
        self.amount_var.set("")
        self.desc_text.delete("1.0", "end")
        self.repeat_var.set("1")
        self.freq_var.set(FREQ_DAILY)
        self.save_btn.config(text="Simpan transaksi")

"""Module 2 - UI manajemen rekening + rekonsiliasi.

Tabel rekonsiliasi membandingkan saldo awal dengan saldo hasil pencatatan
transaksi. Selisih dihitung otomatis = Saldo Awal - Saldo Pencatatan.
Saldo bank tidak diinput terpisah; cukup catat lewat transaksi pada rekening
bank yang bersangkutan.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from ..models import Account
from ..services import computed_balance
from ..utils import format_currency, parse_amount


class AccountView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=10)
        self.app = app
        self.repo = app.accounts
        self._editing_name: str | None = None
        self._build()
        self.on_show()

    def _build(self) -> None:
        # Kolom kiri: form rekening
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(0, 10))

        form = ttk.LabelFrame(left, text="Tambah / Ubah Rekening", padding=10)
        form.pack(fill="x")

        ttk.Label(form, text="Nama rekening").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=24).grid(row=0, column=1, pady=4)

        ttk.Label(form, text="Saldo rekening").grid(row=1, column=0, sticky="w", pady=4)
        self.opening_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.opening_var, width=24).grid(row=1, column=1, pady=4)
        ttk.Label(form, text="(saldo bank, tidak memengaruhi transaksi)",
                  foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w")

        btns = ttk.Frame(form)
        btns.grid(row=3, column=0, columnspan=2, pady=10, sticky="we")
        self.save_btn = ttk.Button(btns, text="Simpan", command=self._save)
        self.save_btn.pack(side="left", padx=2)
        ttk.Button(btns, text="Bersihkan", command=self._clear_form).pack(side="left", padx=2)
        ttk.Button(btns, text="Edit terpilih", command=self._edit_selected).pack(side="left", padx=2)
        ttk.Button(btns, text="Hapus terpilih", command=self._delete_selected).pack(side="left", padx=2)

        # Kolom kanan: tabel rekonsiliasi
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(right, text="Rekonsiliasi Saldo", font=("", 10, "bold")).pack(anchor="w")

        cols = ("account", "opening", "recorded", "diff")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", height=18)
        headers = {
            "account": "Rekening",
            "opening": "Saldo Rekening",
            "recorded": "Saldo Pencatatan",
            "diff": "Selisih",
        }
        widths = {"account": 170, "opening": 140, "recorded": 150, "diff": 130}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            anchor = "w" if c == "account" else "e"
            self.tree.column(c, width=widths[c], anchor=anchor)
        self.tree.pack(fill="both", expand=True, pady=4)

        self.tree.tag_configure("match", foreground="#1a7f37")
        self.tree.tag_configure("mismatch", foreground="#c1121f")
        self.tree.bind("<Double-1>", lambda _e: self._edit_selected())

        ttk.Label(
            right,
            text="Selisih = Saldo Rekening - Saldo Pencatatan.  "
                 "Saldo Pencatatan = total incoming - total outgoing (dari transaksi).",
            foreground="gray",
        ).pack(anchor="w")

    # --------------------------------------------------------------- logic
    def on_show(self) -> None:
        self.tree.delete(*self.tree.get_children())
        accounts = self.repo.list()
        txs = self.app.transactions.list()
        for a in accounts:
            recorded = computed_balance(txs, a)
            diff = a.account_balance - recorded
            tag = "match" if abs(diff) < 0.005 else "mismatch"
            self.tree.insert(
                "", "end",
                values=(a.name, format_currency(a.account_balance),
                        format_currency(recorded), format_currency(diff)),
                tags=(tag,),
            )

    def _save(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Validasi", "Nama rekening wajib diisi.")
            return
        try:
            opening = parse_amount(self.opening_var.get() or "0")
        except ValueError as e:
            messagebox.showerror("Gagal", f"Saldo rekening tidak valid: {e}")
            return
        account = Account(name=name, account_balance=opening)
        try:
            if self._editing_name:
                self.repo.update(self._editing_name, account)
            else:
                self.repo.add(account)
        except ValueError as e:
            messagebox.showerror("Gagal", str(e))
            return
        self._clear_form()
        self.on_show()
        self.app.broadcast_refresh()

    def _selected_account(self) -> str | None:
        item = self.tree.focus()
        if not item:
            return None
        values = self.tree.item(item, "values")
        return values[0] if values else None

    def _edit_selected(self) -> None:
        name = self._selected_account()
        if not name:
            return
        acc = self.repo.get(name)
        if not acc:
            return
        self._editing_name = acc.name
        self.name_var.set(acc.name)
        self.opening_var.set(
            str(int(acc.account_balance))
            if acc.account_balance == int(acc.account_balance)
            else str(acc.account_balance)
        )
        self.save_btn.config(text="Perbarui")

    def _delete_selected(self) -> None:
        name = self._selected_account()
        if not name:
            return
        if not messagebox.askyesno("Konfirmasi", f"Hapus rekening '{name}'?"):
            return
        self.repo.delete(name)
        self._clear_form()
        self.on_show()
        self.app.broadcast_refresh()

    def _clear_form(self) -> None:
        self._editing_name = None
        self.name_var.set("")
        self.opening_var.set("0")
        self.save_btn.config(text="Simpan")

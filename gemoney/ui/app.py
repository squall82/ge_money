"""Jendela utama aplikasi: menggabungkan ke-4 module dalam bentuk tab.

Repository dibuat sekali di sini lalu dibagikan (shared) ke seluruh view,
sehingga perubahan data di satu module langsung dipakai module lain melalui
mekanisme refresh.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..models import (
    CategoryRepository,
    AccountRepository,
    TransactionRepository,
    BalanceRepository,
)
from .category_view import CategoryView
from .account_view import AccountView
from .transaction_view import TransactionView
from .report_view import ReportView
from .branding import BrandingFooter


class GeMoneyApp(tk.Tk):
    """Aplikasi GUI pencatatan keuangan pribadi."""

    def __init__(self):
        super().__init__()
        self.title("GE Money - Pencatatan Keuangan Pribadi")
        self.geometry("1024x680")
        self.minsize(900, 600)
        # Mulai dalam keadaan maximize.
        try:
            self.state("zoomed")
        except tk.TclError:
            # Fallback untuk platform yang tidak mendukung 'zoomed'.
            self.attributes("-zoomed", True)

        # Repository bersama untuk semua module.
        self.categories = CategoryRepository()
        self.accounts = AccountRepository()
        self.transactions = TransactionRepository()
        self.balances = BalanceRepository()

        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        self.category_view = CategoryView(notebook, self)
        self.account_view = AccountView(notebook, self)
        self.transaction_view = TransactionView(notebook, self)
        self.report_view = ReportView(notebook, self)

        notebook.add(self.category_view, text="1. Kategori")
        notebook.add(self.account_view, text="2. Rekening")
        notebook.add(self.transaction_view, text="3. Transaksi")
        notebook.add(self.report_view, text="4. Laporan")

        # Saat berpindah tab, segarkan data yang mungkin berubah dari tab lain.
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._notebook = notebook

        # Footer call sign (Made by BijiBTC + QR).
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=8)
        BrandingFooter(self).pack(fill="x", side="bottom", anchor="w")

    def _on_tab_changed(self, _event) -> None:
        current = self._notebook.nametowidget(self._notebook.select())
        if hasattr(current, "on_show"):
            current.on_show()

    def broadcast_refresh(self) -> None:
        """Minta semua view memperbarui daftar pilihannya (kategori/rekening)."""
        for view in (
            self.transaction_view,
            self.account_view,
            self.report_view,
            self.category_view,
        ):
            if hasattr(view, "on_show"):
                view.on_show()

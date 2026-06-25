"""Konfigurasi path & konstanta aplikasi.

Semua data disimpan dalam file JSON di dalam folder ``data`` agar tidak
membutuhkan database eksternal. Module lain cukup mengimport konstanta dari
sini sehingga lokasi penyimpanan terpusat di satu tempat.
"""

import sys
from pathlib import Path

# Root aplikasi:
# - Saat dijalankan sebagai .exe (PyInstaller), data & assets disimpan di
#   folder tempat file .exe berada agar portable dan datanya persisten.
# - Saat dijalankan sebagai script Python biasa, memakai folder project
#   (folder yang berisi paket ``gemoney``).
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

# File penyimpanan per-module.
CATEGORIES_FILE = DATA_DIR / "categories.json"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
TRANSACTIONS_FILE = DATA_DIR / "transactions.json"
BALANCES_FILE = DATA_DIR / "balances.json"

# Tipe transaksi yang diizinkan.
TYPE_INCOMING = "incoming"
TYPE_OUTGOING = "outgoing"
TRANSACTION_TYPES = (TYPE_INCOMING, TYPE_OUTGOING)

# Format tanggal standar yang dipakai di seluruh aplikasi.
DATE_FORMAT = "%Y-%m-%d"

# Simbol mata uang untuk tampilan.
CURRENCY_PREFIX = "Rp"


def ensure_data_dir() -> None:
    """Pastikan folder data tersedia sebelum membaca/menulis file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

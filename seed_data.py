"""Isi data awal kategori & rekening sesuai contoh.

Jalankan sekali untuk mengisi data contoh:  python seed_data.py
Script ini aman dijalankan ulang (hanya menambah yang belum ada).
"""

from gemoney.models import (
    Category,
    CategoryRepository,
    Account,
    AccountRepository,
)

# (nama, induk). Induk "" berarti kategori level 1 (root).
CATEGORIES = [
    ("Family", ""),
    ("Home", ""),
    ("Bills", ""),
    ("Income", ""),
    ("Loan & Debt", ""),
    ("Operational", ""),
    ("Gikhes", "Family"),
    ("Bae", "Family"),
    ("Abiel", "Bae"),
    ("Egu", "Gikhes"),
    ("Tata", "Family"),
    ("Groceries", "Home"),
    ("Foods & Drinks", "Home"),
    ("Lending", "Loan & Debt"),
    ("Debt", "Loan & Debt"),
    ("Home Maintenance", "Home"),
    ("Electricity", "Bills"),
    ("Gas", "Bills"),
    ("Phone", "Bills"),
    ("Internet", "Bills"),
    ("Water", "Bills"),
    ("Security", "Bills"),
    ("Garbage", "Bills"),
    ("Petrol", "Bills"),
    ("Update Balance", "Operational"),
    ("Payroll", "Income"),
    ("THR", "Income"),
    ("Gift", "Income"),
    ("Credit Card", "Debt"),
    ("Home Improvement", "Home"),
]

ACCOUNTS = [
    "Bank Mandiri Gikhes",
    "Bank Mandiri Bae",
    "Bank BCA Gikhes",
    "Bank BCA Bae",
    "Bank Lampung Gikhes",
    "Bank Lampung Bae",
    "Bank BII Gikhes",
    "Cash Gikhes",
    "Cash Bae",
]


def seed() -> None:
    crepo = CategoryRepository()
    arepo = AccountRepository()

    added_c = 0
    for name, parent in CATEGORIES:
        if not crepo.exists(name):
            crepo.add(Category(name=name, parent=parent))
            added_c += 1

    added_a = 0
    for name in ACCOUNTS:
        if not arepo.exists(name):
            arepo.add(Account(name=name, account_balance=0.0))
            added_a += 1

    print(f"Selesai. Kategori baru: {added_c}, Rekening baru: {added_a}.")


if __name__ == "__main__":
    seed()

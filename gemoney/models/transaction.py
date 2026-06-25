"""Module 3a - Transaksi keuangan."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from ..config import TRANSACTIONS_FILE, TRANSACTION_TYPES
from ..storage import JsonStore
from ..utils import new_id


@dataclass
class Transaction:
    """Satu transaksi.

    Field sesuai kebutuhan: tanggal, tipe (incoming/outgoing), kategori,
    nominal, deskripsi. ``account`` ditambahkan agar saldo per rekening bisa
    dihitung untuk laporan "sisa saldo" dan rekonsiliasi (Module 2 & 4).
    """

    date: str
    type: str
    category: str
    amount: float
    description: str = ""
    account: str = ""
    id: str = field(default_factory=new_id)

    @property
    def signed_amount(self) -> float:
        """Nominal bertanda: positif untuk incoming, negatif untuk outgoing."""
        return self.amount if self.type == "incoming" else -self.amount

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            id=data.get("id") or new_id(),
            date=data.get("date", ""),
            type=data.get("type", "outgoing"),
            category=data.get("category", ""),
            amount=float(data.get("amount", 0.0) or 0.0),
            description=data.get("description", ""),
            account=data.get("account", ""),
        )


class TransactionRepository:
    """CRUD transaksi. ``id`` dipakai sebagai kunci unik."""

    def __init__(self, store: JsonStore | None = None):
        self.store = store or JsonStore(TRANSACTIONS_FILE)

    def list(self) -> list[Transaction]:
        return [Transaction.from_dict(d) for d in self.store.load()]

    def _save(self, items: list[Transaction]) -> None:
        self.store.save([t.to_dict() for t in items])

    @staticmethod
    def _validate(t: Transaction) -> None:
        if t.type not in TRANSACTION_TYPES:
            raise ValueError(f"Tipe transaksi tidak valid: {t.type}")
        if not t.date:
            raise ValueError("Tanggal transaksi wajib diisi")
        if not t.category:
            raise ValueError("Kategori wajib dipilih")
        if t.amount <= 0:
            raise ValueError("Nominal harus lebih besar dari 0")

    def add(self, t: Transaction) -> Transaction:
        self._validate(t)
        items = self.list()
        items.append(t)
        self._save(items)
        return t

    def update(self, t: Transaction) -> None:
        self._validate(t)
        items = self.list()
        for i, existing in enumerate(items):
            if existing.id == t.id:
                items[i] = t
                self._save(items)
                return
        raise ValueError("Transaksi tidak ditemukan")

    def delete(self, transaction_id: str) -> None:
        items = [t for t in self.list() if t.id != transaction_id]
        self._save(items)

    def count_by_category(self, category: str) -> int:
        return sum(1 for t in self.list() if t.category == category)

    def rename_category(self, old_name: str, new_name: str) -> int:
        """Ganti nama kategori pada semua transaksi. Mengembalikan jumlah yang diubah."""
        items = self.list()
        changed = 0
        for t in items:
            if t.category == old_name:
                t.category = new_name
                changed += 1
        if changed:
            self._save(items)
        return changed

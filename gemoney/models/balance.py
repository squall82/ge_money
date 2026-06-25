"""Module 3b - Catatan saldo bank (untuk rekonsiliasi vs pencatatan)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from ..config import BALANCES_FILE
from ..storage import JsonStore
from ..utils import new_id


@dataclass
class BalanceSnapshot:
    """Saldo aktual rekening pada tanggal tertentu (mis. dari mutasi bank).

    Dibandingkan dengan saldo hasil pencatatan transaksi untuk rekonsiliasi.
    """

    account: str
    date: str
    amount: float
    note: str = ""
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BalanceSnapshot":
        return cls(
            id=data.get("id") or new_id(),
            account=data.get("account", ""),
            date=data.get("date", ""),
            amount=float(data.get("amount", 0.0) or 0.0),
            note=data.get("note", ""),
        )


class BalanceRepository:
    """CRUD snapshot saldo rekening."""

    def __init__(self, store: JsonStore | None = None):
        self.store = store or JsonStore(BALANCES_FILE)

    def list(self) -> list[BalanceSnapshot]:
        return [BalanceSnapshot.from_dict(d) for d in self.store.load()]

    def _save(self, items: list[BalanceSnapshot]) -> None:
        self.store.save([b.to_dict() for b in items])

    def add(self, b: BalanceSnapshot) -> BalanceSnapshot:
        if not b.account:
            raise ValueError("Rekening wajib dipilih")
        if not b.date:
            raise ValueError("Tanggal wajib diisi")
        items = self.list()
        items.append(b)
        self._save(items)
        return b

    def delete(self, balance_id: str) -> None:
        items = [b for b in self.list() if b.id != balance_id]
        self._save(items)

    def latest_for(self, account: str, as_of: str | None = None) -> BalanceSnapshot | None:
        """Snapshot terbaru untuk satu rekening (opsional hingga tanggal ``as_of``)."""
        candidates = [b for b in self.list() if b.account == account]
        if as_of:
            candidates = [b for b in candidates if b.date <= as_of]
        if not candidates:
            return None
        return max(candidates, key=lambda b: b.date)

"""Module 2 - Manajemen rekening (untuk rekonsiliasi saldo)."""

from __future__ import annotations

from dataclasses import dataclass, asdict

from ..config import ACCOUNTS_FILE
from ..storage import JsonStore


@dataclass
class Account:
    """Satu rekening / kantong uang (bank atau cash).

    ``account_balance`` adalah saldo rekening (saldo bank) sebagai referensi
    untuk rekonsiliasi. Nilai ini TIDAK ikut dihitung sebagai transaksi; ia
    hanya dibandingkan dengan saldo hasil pencatatan transaksi.
    """

    name: str
    account_balance: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        # Backward-compat: file lama memakai kunci "opening_balance".
        raw = data.get("account_balance", data.get("opening_balance", 0.0))
        return cls(
            name=data.get("name", ""),
            account_balance=float(raw or 0.0),
        )


class AccountRepository:
    """CRUD rekening. Nama rekening dipakai sebagai kunci unik."""

    def __init__(self, store: JsonStore | None = None):
        self.store = store or JsonStore(ACCOUNTS_FILE)

    def list(self) -> list[Account]:
        return [Account.from_dict(d) for d in self.store.load()]

    def _save(self, items: list[Account]) -> None:
        self.store.save([a.to_dict() for a in items])

    def names(self) -> list[str]:
        return [a.name for a in self.list()]

    def exists(self, name: str) -> bool:
        return any(a.name.lower() == name.lower() for a in self.list())

    def get(self, name: str) -> Account | None:
        for a in self.list():
            if a.name.lower() == name.lower():
                return a
        return None

    def add(self, account: Account) -> Account:
        name = account.name.strip()
        if not name:
            raise ValueError("Nama rekening tidak boleh kosong")
        if self.exists(name):
            raise ValueError(f"Rekening '{name}' sudah ada")
        items = self.list()
        items.append(account)
        self._save(items)
        return account

    def update(self, original_name: str, account: Account) -> None:
        items = self.list()
        for i, a in enumerate(items):
            if a.name.lower() == original_name.lower():
                items[i] = account
                self._save(items)
                return
        raise ValueError(f"Rekening '{original_name}' tidak ditemukan")

    def delete(self, name: str) -> None:
        items = [a for a in self.list() if a.name.lower() != name.lower()]
        self._save(items)

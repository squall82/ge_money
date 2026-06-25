"""Module 1 - Manajemen kategori (2 level: parent -> child)."""

from __future__ import annotations

from dataclasses import dataclass, asdict

from ..config import CATEGORIES_FILE
from ..storage import JsonStore


@dataclass
class Category:
    """Satu kategori.

    ``parent`` berisi nama kategori induk. Untuk kategori level teratas
    (root), ``parent`` boleh sama dengan ``name`` atau dikosongkan.
    """

    name: str
    parent: str = ""

    def is_root(self) -> bool:
        return not self.parent or self.parent == self.name

    @property
    def display(self) -> str:
        """Tampilan 'Parent > Nama' untuk dropdown transaksi."""
        if self.is_root():
            return self.name
        return f"{self.parent} > {self.name}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(name=data.get("name", ""), parent=data.get("parent", ""))


class CategoryRepository:
    """CRUD kategori. Nama kategori dipakai sebagai kunci unik."""

    def __init__(self, store: JsonStore | None = None):
        self.store = store or JsonStore(CATEGORIES_FILE)

    def list(self) -> list[Category]:
        return [Category.from_dict(d) for d in self.store.load()]

    def _save(self, items: list[Category]) -> None:
        self.store.save([c.to_dict() for c in items])

    def exists(self, name: str) -> bool:
        return any(c.name.lower() == name.lower() for c in self.list())

    def get(self, name: str) -> Category | None:
        for c in self.list():
            if c.name.lower() == name.lower():
                return c
        return None

    def add(self, category: Category) -> Category:
        name = category.name.strip()
        if not name:
            raise ValueError("Nama kategori tidak boleh kosong")
        if self.exists(name):
            raise ValueError(f"Kategori '{name}' sudah ada")
        items = self.list()
        items.append(category)
        self._save(items)
        return category

    def update(self, original_name: str, category: Category) -> None:
        items = self.list()
        for i, c in enumerate(items):
            if c.name.lower() == original_name.lower():
                items[i] = category
                self._save(items)
                return
        raise ValueError(f"Kategori '{original_name}' tidak ditemukan")

    def delete(self, name: str) -> None:
        items = [c for c in self.list() if c.name.lower() != name.lower()]
        self._save(items)

    def descendants(self, name: str) -> list[Category]:
        """Semua keturunan (anak, cucu, dst.) dari sebuah kategori, rekursif."""
        items = self.list()
        result: list[Category] = []
        frontier = [name.lower()]
        seen = {name.lower()}
        while frontier:
            current = frontier.pop()
            for c in items:
                if c.is_root():
                    continue
                if c.parent.lower() == current and c.name.lower() not in seen:
                    result.append(c)
                    seen.add(c.name.lower())
                    frontier.append(c.name.lower())
        return result

    def delete_cascade(self, name: str) -> list[str]:
        """Hapus kategori beserta seluruh keturunannya.

        Mengembalikan daftar nama kategori yang terhapus (termasuk induknya).
        """
        to_remove = {name.lower()}
        to_remove.update(c.name.lower() for c in self.descendants(name))
        items = [c for c in self.list() if c.name.lower() not in to_remove]
        self._save(items)
        return sorted(to_remove)

    def rename(self, old_name: str, new_name: str, new_parent: str) -> None:
        """Ubah nama/induk sebuah kategori sekaligus perbaiki referensi anak.

        Anak yang induknya menunjuk ``old_name`` otomatis diarahkan ke
        ``new_name`` agar hirarki tetap konsisten.
        """
        if new_name.lower() != old_name.lower() and self.exists(new_name):
            raise ValueError(f"Kategori '{new_name}' sudah ada")
        if new_parent.lower() == new_name.lower():
            new_parent = ""  # root

        items = self.list()
        found = False
        for i, c in enumerate(items):
            if c.name.lower() == old_name.lower():
                items[i] = Category(name=new_name, parent=new_parent)
                found = True
            elif not c.is_root() and c.parent.lower() == old_name.lower():
                # repoint anak ke nama induk yang baru
                items[i] = Category(name=c.name, parent=new_name)
        if not found:
            raise ValueError(f"Kategori '{old_name}' tidak ditemukan")
        self._save(items)

    # --- helper hirarki ---
    def roots(self) -> list[Category]:
        return [c for c in self.list() if c.is_root()]

    def children_of(self, parent_name: str) -> list[Category]:
        return [
            c
            for c in self.list()
            if not c.is_root() and c.parent.lower() == parent_name.lower()
        ]

    def parents(self) -> list[str]:
        """Daftar nama kategori yang dipakai sebagai induk + root."""
        names = {c.parent for c in self.list() if c.parent}
        names.update(c.name for c in self.roots())
        return sorted(names)

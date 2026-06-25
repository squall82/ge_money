"""Module 1 - UI manajemen kategori (2 level: parent -> child)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from ..models import Category


class CategoryView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=10)
        self.app = app
        self.repo = app.categories
        self._editing_name: str | None = None
        self._build()
        self.on_show()

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        # Panel form (kiri)
        form = ttk.LabelFrame(self, text="Tambah / Ubah Kategori", padding=10)
        form.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(form, text="Nama kategori").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=24).grid(row=0, column=1, pady=4)

        ttk.Label(form, text="Kategori induk").grid(row=1, column=0, sticky="w", pady=4)
        self.parent_var = tk.StringVar()
        self.parent_combo = ttk.Combobox(
            form, textvariable=self.parent_var, width=22, state="normal"
        )
        self.parent_combo.grid(row=1, column=1, pady=4)
        ttk.Label(
            form,
            text="(kosongkan bila ini kategori induk/level 1)",
            foreground="gray",
        ).grid(row=2, column=0, columnspan=2, sticky="w")

        btns = ttk.Frame(form)
        btns.grid(row=3, column=0, columnspan=2, pady=10, sticky="we")
        self.save_btn = ttk.Button(btns, text="Simpan", command=self._save)
        self.save_btn.pack(side="left", padx=2)
        ttk.Button(btns, text="Bersihkan", command=self._clear_form).pack(side="left", padx=2)

        # Panel daftar (kanan)
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        cols = ("name", "parent")
        self.tree = ttk.Treeview(right, columns=cols, show="tree headings", height=20)
        self.tree.heading("#0", text="Hirarki")
        self.tree.heading("name", text="Kategori")
        self.tree.heading("parent", text="Induk")
        self.tree.column("#0", width=220)
        self.tree.column("name", width=160)
        self.tree.column("parent", width=140)
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        sb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", lambda _e: self._edit_selected())

        action = ttk.Frame(self)
        # action bar di bawah kanan
        bottom = ttk.Frame(right)
        bottom.pack(side="bottom", fill="x", pady=(6, 0))
        ttk.Button(bottom, text="Edit terpilih", command=self._edit_selected).pack(side="left", padx=2)
        ttk.Button(bottom, text="Hapus terpilih", command=self._delete_selected).pack(side="left", padx=2)

    # --------------------------------------------------------------- logic
    def on_show(self) -> None:
        self._refresh_parent_options()
        self._refresh_tree()

    def _refresh_parent_options(self) -> None:
        names = sorted(c.name for c in self.repo.list())
        self.parent_combo["values"] = names

    def _refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        cats = self.repo.list()
        roots = sorted({c.parent for c in cats if c.parent} | {c.name for c in cats if c.is_root()})

        # Bangun tampilan pohon: induk -> anak. Induk bisa berupa nama yang
        # muncul sebagai parent walau tidak terdaftar sebagai record sendiri.
        children_map: dict[str, list[Category]] = {}
        for c in cats:
            if not c.is_root():
                children_map.setdefault(c.parent, []).append(c)

        added = set()
        for root in roots:
            node = self.tree.insert("", "end", text=root, values=(root, ""), open=True)
            added.add(root.lower())
            for child in sorted(children_map.get(root, []), key=lambda x: x.name):
                self.tree.insert(node, "end", text="", values=(child.name, child.parent))

        # Tampilkan kategori anak yang induknya tidak termasuk root (mis. 2 level
        # bertingkat seperti Abiel -> Bae).
        for parent, kids in children_map.items():
            if parent.lower() in added:
                continue
            # cari apakah parent ada sebagai child di tempat lain -> nested
            node = self.tree.insert("", "end", text=parent, values=(parent, ""), open=True)
            for child in sorted(kids, key=lambda x: x.name):
                self.tree.insert(node, "end", text="", values=(child.name, child.parent))

    def _save(self) -> None:
        name = self.name_var.get().strip()
        parent = self.parent_var.get().strip()
        if not name:
            messagebox.showwarning("Validasi", "Nama kategori wajib diisi.")
            return
        if parent.lower() == name.lower():
            parent = ""  # root

        try:
            if self._editing_name:
                old = self._editing_name
                self.repo.rename(old, name, parent)
                # Jika nama berubah, ikut perbarui transaksi yang memakainya.
                if old != name:
                    n = self.app.transactions.rename_category(old, name)
                    if n:
                        messagebox.showinfo(
                            "Info", f"{n} transaksi ikut diperbarui ke kategori '{name}'."
                        )
            else:
                self.repo.add(Category(name=name, parent=parent))
        except ValueError as e:
            messagebox.showerror("Gagal", str(e))
            return
        self._clear_form()
        self.on_show()
        self.app.broadcast_refresh()

    def _edit_selected(self) -> None:
        item = self.tree.focus()
        if not item:
            return
        values = self.tree.item(item, "values")
        if not values or not values[0]:
            return
        self._editing_name = values[0]
        self.name_var.set(values[0])
        self.parent_var.set(values[1] if len(values) > 1 else "")
        self.save_btn.config(text="Perbarui")

    def _delete_selected(self) -> None:
        item = self.tree.focus()
        if not item:
            return
        values = self.tree.item(item, "values")
        if not values or not values[0]:
            return
        name = values[0]

        children = self.repo.descendants(name)
        tx_repo = self.app.transactions
        affected_cats = [name] + [c.name for c in children]
        tx_count = sum(tx_repo.count_by_category(c) for c in affected_cats)

        if children:
            child_names = ", ".join(c.name for c in children)
            msg = (
                f"Kategori '{name}' punya {len(children)} sub-kategori:\n"
                f"{child_names}\n\n"
                f"Menghapus induk akan menghapus SEMUA sub-kategori tersebut."
            )
        else:
            msg = f"Hapus kategori '{name}'?"
        if tx_count:
            msg += (
                f"\n\nAda {tx_count} transaksi yang memakai kategori ini "
                f"(atau sub-kategorinya). Transaksi tidak ikut terhapus, "
                f"tetapi kategorinya menjadi tidak terdaftar."
            )

        if not messagebox.askyesno("Konfirmasi hapus", msg):
            return

        self.repo.delete_cascade(name)
        self._clear_form()
        self.on_show()
        self.app.broadcast_refresh()

    def _clear_form(self) -> None:
        self._editing_name = None
        self.name_var.set("")
        self.parent_var.set("")
        self.save_btn.config(text="Simpan")

"""Footer call sign 'Made by Biji' + QR + tombol About + versi aplikasi.

QR dibuat sekali memakai library ``qrcode`` lalu disimpan ke folder ``assets``
sehingga tidak perlu di-generate ulang setiap aplikasi dibuka.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from .. import __version__
from ..config import BASE_DIR

BTC_ADDRESS = "13EALQHMdTBKXsM74rjmbQTJmmL2RTHfjE"
CREDIT_TEXT = "Made by Biji"

ASSETS_DIR = BASE_DIR / "assets"
QR_PATH = ASSETS_DIR / "bijibtc_qr.png"

ABOUT_TEXT = (
    "GE Money membantu Anda mencatat keuangan pribadi sehari-hari secara "
    "sederhana: input transaksi pemasukan/pengeluaran, kelompokkan dengan "
    "kategori dua tingkat, dan pantau saldo tiap rekening.\n\n"
    "Fitur utama:\n"
    "  - Manajemen kategori (induk dan sub-kategori)\n"
    "  - Manajemen rekening dan rekonsiliasi saldo\n"
    "  - Input transaksi dengan opsi perulangan (harian/bulanan/tahunan)\n"
    "  - Laporan: sisa saldo per tanggal, kategori terbesar (pie chart),\n"
    "    dan arus kas harian\n\n"
    "Privasi & data:\n"
    "Seluruh data disimpan lokal dalam file JSON di folder \"data\" di sebelah "
    "aplikasi. Tidak ada data yang dikirim ke mana pun. Untuk backup, cukup "
    "salin folder \"data\".\n\n"
    "Dibuat dengan Python + Tkinter.\n\n"
    "Catatan: aplikasi ini untuk pencatatan pribadi, bukan nasihat keuangan. "
)


def ensure_qr(box_size: int = 2, border: int = 2) -> Path | None:
    """Pastikan file QR tersedia; buat bila belum ada. Return path atau None."""
    if QR_PATH.exists():
        return QR_PATH
    try:
        import qrcode

        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        qr = qrcode.QRCode(box_size=box_size, border=border)
        qr.add_data(BTC_ADDRESS)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(QR_PATH)
        return QR_PATH
    except Exception:
        return None


def show_about(parent: tk.Misc) -> None:
    """Tampilkan dialog 'Tentang GE Money'."""
    win = tk.Toplevel(parent)
    win.title("Tentang GE Money")
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()

    container = ttk.Frame(win, padding=16)
    container.pack(fill="both", expand=True)

    # Header: QR + judul
    header = ttk.Frame(container)
    header.pack(fill="x", pady=(0, 10))

    qr_path = ensure_qr()
    if qr_path and qr_path.exists():
        try:
            win._qr_img = tk.PhotoImage(file=str(qr_path))  # type: ignore[attr-defined]
            ttk.Label(header, image=win._qr_img).pack(side="left", padx=(0, 12))
        except Exception:
            pass

    title_box = ttk.Frame(header)
    title_box.pack(side="left", anchor="n")
    ttk.Label(title_box, text="GE Money", font=("", 16, "bold")).pack(anchor="w")
    ttk.Label(title_box, text=f"versi {__version__}", foreground="gray").pack(anchor="w")
    ttk.Label(title_box, text="Aplikasi pencatatan keuangan pribadi").pack(anchor="w")

    # Body
    body = tk.Text(container, width=64, height=18, wrap="word",
                   font=("", 9), relief="flat", background=win.cget("background"))
    body.pack(fill="both", expand=True)
    body.insert("1.0", ABOUT_TEXT)
    body.configure(state="disabled")

    ttk.Separator(container, orient="horizontal").pack(fill="x", pady=8)

    # Footer: tombol Tutup + "made by Biji" di kanan bawah.
    footer = ttk.Frame(container)
    footer.pack(fill="x")
    ttk.Button(footer, text="Tutup", command=win.destroy).pack(side="left")
    ttk.Label(footer, text="made by Biji", foreground="gray").pack(side="right")

    # Posisikan di tengah parent.
    win.update_idletasks()
    try:
        px = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(px, 0)}+{max(py, 0)}")
    except Exception:
        pass


class BrandingFooter(ttk.Frame):
    """Footer: kiri = QR + credit + BTC; kanan = tombol About + versi."""

    def __init__(self, master):
        super().__init__(master, padding=(8, 4))
        self._qr_image: tk.PhotoImage | None = None

        # ---- kanan: tombol About + versi (kecil) ----
        right = ttk.Frame(self)
        right.pack(side="right", anchor="se")
        ttk.Button(right, text="About", width=8,
                   command=lambda: show_about(self.winfo_toplevel())).pack(anchor="e")
        ttk.Label(right, text=f"v{__version__}", foreground="gray",
                  font=("", 7)).pack(anchor="e")

        # ---- kiri: QR + credit ----
        path = ensure_qr()
        if path and path.exists():
            try:
                self._qr_image = tk.PhotoImage(file=str(path))
                ttk.Label(self, image=self._qr_image).pack(side="left", padx=(0, 8))
            except Exception:
                self._qr_image = None

        text = ttk.Frame(self)
        text.pack(side="left", fill="y")

        ttk.Label(text, text=CREDIT_TEXT, font=("", 9, "bold")).pack(anchor="w")
        ttk.Label(text, text="BTC", font=("", 8)).pack(anchor="w")

        addr_row = ttk.Frame(text)
        addr_row.pack(anchor="w", pady=(2, 0))
        self.addr_var = tk.StringVar(value=BTC_ADDRESS)
        addr_entry = ttk.Entry(addr_row, textvariable=self.addr_var,
                               width=len(BTC_ADDRESS) + 2, font=("Consolas", 8))
        addr_entry.pack(side="left")
        addr_entry.configure(state="readonly")
        ttk.Button(addr_row, text="Copy", width=6,
                   command=self._copy_address).pack(side="left", padx=(4, 0))

    def _copy_address(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(BTC_ADDRESS)

# GE Money - Pencatatan Keuangan Pribadi

Aplikasi GUI (Tkinter) untuk mencatat transaksi keuangan pribadi. Data disimpan
dalam file JSON (tanpa database eksternal), sehingga mudah dibackup dan dibawa.

Desain dibuat **modular** agar tiap bagian bisa diubah/di-update terpisah.

## Module

1. **Kategori** (`gemoney/ui/category_view.py`) - manajemen kategori 2 level
   (induk -> anak), mis. `Family > Gikhes`. Mendukung edit dan hapus; menghapus
   induk akan ikut menghapus seluruh sub-kategorinya (cascade) dengan konfirmasi.
2. **Rekening** (`gemoney/ui/account_view.py`) - manajemen rekening + tabel
   **rekonsiliasi**. Setiap rekening punya **Saldo Rekening** (saldo bank,
   sebagai referensi; tidak memengaruhi transaksi). Selisih dihitung otomatis:
   - `Saldo Pencatatan = total incoming - total outgoing` (murni dari transaksi)
   - `Selisih = Saldo Rekening - Saldo Pencatatan`
   Saldo bank cukup dicatat lewat transaksi pada rekening bank yang bersangkutan.
3. **Transaksi** (`gemoney/ui/transaction_view.py`) - input transaksi: tanggal,
   tipe (`incoming`/`outgoing`), kategori (level 2), rekening, nominal, deskripsi.
   Tanggal boleh masa lalu/masa depan. Daftar transaksi bisa di-edit
   (klik dua kali baris) dan dihapus.
4. **Laporan** (`gemoney/ui/report_view.py`)
   - 4a. Daftar transaksi + sisa saldo pada satu titik tanggal.
   - 4b. Pie chart kategori terbesar berdasarkan periode tanggal.
   - 4c. Cashflow harian agregat (incoming/outgoing/net + saldo).

> Catatan: semua agregat berupa **nominal** (jumlah uang), bukan frekuensi
> transaksi.

## Struktur Proyek

```
ge_money/
  main.py                # titik masuk aplikasi
  seed_data.py           # isi data contoh (kategori & rekening)
  requirements.txt
  data/                  # file JSON (dibuat otomatis)
  gemoney/
    config.py            # path & konstanta
    storage.py           # baca/tulis JSON (atomik)
    utils.py             # format mata uang, tanggal, id
    models/              # model + repository per module
      category.py  account.py  transaction.py  balance.py
    services/
      reports.py         # logika laporan & rekonsiliasi
    ui/
      app.py             # jendela utama (tab)
      category_view.py   account_view.py
      transaction_view.py report_view.py
```

Tiap lapisan terpisah: **model/repository** (data) -> **services** (logika
laporan) -> **ui** (tampilan). Mengubah satu module tidak memengaruhi yang lain.

## Cara Menjalankan

```bash
# 1. Pasang dependency (sekali saja)
pip install -r requirements.txt

# 2. (opsional) isi data contoh kategori & rekening
python seed_data.py

# 3. jalankan aplikasi
python main.py
```

## Format Data

- `data/categories.json`  : `[{ "name", "parent" }]`
- `data/accounts.json`    : `[{ "name", "account_balance" }]`
- `data/transactions.json`: `[{ "id", "date", "type", "category", "amount", "description", "account" }]`

Tanggal memakai format `YYYY-MM-DD`. Nominal disimpan sebagai angka.

## Build .exe Portable (Windows)

Aplikasi bisa dibungkus menjadi satu file `.exe` portable (tanpa perlu Python):

```bash
pip install pyinstaller
build_exe.bat
```

Hasilnya ada di folder `GeMoney_Portable/`:
- `GeMoney.exe`  - aplikasi (double-click untuk jalan)
- `data/`        - file JSON penyimpanan (di sebelah exe, persisten & portable)
- `assets/`      - gambar QR footer (dibuat otomatis)

Seluruh folder `GeMoney_Portable` bisa dipindah ke PC/flashdisk lain. Pastikan
folder `data` ikut dibawa agar transaksi tidak hilang.

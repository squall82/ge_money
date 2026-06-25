"""Fungsi bantu umum: format mata uang, parsing/validasi tanggal, dan id."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from . import config


def new_id() -> str:
    """Buat id unik untuk record baru."""
    return uuid.uuid4().hex[:12]


def format_currency(amount: float) -> str:
    """Format angka menjadi string Rupiah, mis. 1500000 -> 'Rp 1.500.000'."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        value = 0.0
    sign = "-" if value < 0 else ""
    whole = abs(int(round(value)))
    grouped = f"{whole:,}".replace(",", ".")
    return f"{sign}{config.CURRENCY_PREFIX} {grouped}"


def parse_amount(text: str) -> float:
    """Ubah input teks nominal menjadi float.

    Menerima format umum: '1.500.000', '1500000', '1,500,000', '15000.50'.
    """
    if text is None:
        raise ValueError("Nominal kosong")
    cleaned = str(text).strip().replace(config.CURRENCY_PREFIX, "").strip()
    if not cleaned:
        raise ValueError("Nominal kosong")

    # Hilangkan spasi.
    cleaned = cleaned.replace(" ", "")

    # Tentukan pemisah desimal. Bila ada ',' dan '.', pemisah desimal adalah
    # karakter yang muncul paling akhir.
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Anggap ',' sebagai pemisah ribuan (umum di Indonesia) kecuali
        # tampak seperti desimal (mis. '1500,50').
        if cleaned.count(",") == 1 and len(cleaned.split(",")[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        # Hanya ada '.'. Bila terlihat sebagai ribuan (mis. '1.500.000'),
        # buang titiknya.
        parts = cleaned.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            cleaned = cleaned.replace(".", "")

    value = float(cleaned)
    if value < 0:
        raise ValueError("Nominal tidak boleh negatif")
    return value


def parse_date(text: str) -> date:
    """Parse string 'YYYY-MM-DD' menjadi objek date."""
    return datetime.strptime(str(text).strip(), config.DATE_FORMAT).date()


def format_date(value: date) -> str:
    """Format objek date menjadi string 'YYYY-MM-DD'."""
    return value.strftime(config.DATE_FORMAT)


def today_str() -> str:
    """Tanggal hari ini sebagai string standar."""
    return format_date(date.today())


def add_months(d: date, months: int) -> date:
    """Tambah ``months`` bulan ke tanggal, dengan clamp ke akhir bulan.

    Mis. 31 Jan + 1 bulan -> 28/29 Feb (hari disesuaikan ke hari terakhir bulan).
    """
    import calendar

    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def add_years(d: date, years: int) -> date:
    """Tambah ``years`` tahun, dengan penyesuaian 29 Feb -> 28 Feb bila perlu."""
    return add_months(d, years * 12)


# Pemetaan label frekuensi (Indonesia) -> langkah perulangan.
FREQ_DAILY = "Harian"
FREQ_MONTHLY = "Bulanan"
FREQ_YEARLY = "Tahunan"
RECURRENCE_FREQUENCIES = (FREQ_DAILY, FREQ_MONTHLY, FREQ_YEARLY)


def recurrence_dates(start: date, count: int, freq: str) -> list[date]:
    """Hasilkan daftar tanggal perulangan, dimulai dari ``start``.

    ``count`` termasuk kejadian pertama (tanggal start itu sendiri).
    Contoh start=25-Jun-2026, count=2:
      - Harian  -> [25-Jun, 26-Jun]
      - Bulanan -> [25-Jun-2026, 25-Jul-2026]
      - Tahunan -> [25-Jun-2026, 25-Jun-2027]
    """
    count = max(1, int(count))
    f = (freq or "").strip().lower()
    out: list[date] = []
    for i in range(count):
        if f in ("harian", "daily"):
            out.append(start + timedelta(days=i))
        elif f in ("bulanan", "monthly"):
            out.append(add_months(start, i))
        elif f in ("tahunan", "yearly"):
            out.append(add_years(start, i))
        else:
            out.append(start)
    return out

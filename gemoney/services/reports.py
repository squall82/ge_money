"""Module 4 - logika laporan.

Semua agregasi dihitung berdasarkan NOMINAL (jumlah uang), bukan frekuensi
transaksi, sesuai kebutuhan.

Berisi:
- ``computed_balance``       : saldo hasil pencatatan transaksi per rekening.
- ``running_balance_report`` : 4a. daftar transaksi + sisa saldo s/d tanggal.
- ``category_breakdown``     : 4b. total nominal per kategori (untuk pie chart).
- ``daily_cashflow``         : 4c. arus kas harian agregat + saldo + net.
- ``reconciliation``         : Module 2. saldo bank vs saldo pencatatan.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from ..models import Account, Transaction, BalanceSnapshot
from ..utils import parse_date


# --------------------------------------------------------------------------- #
# Saldo hasil pencatatan
# --------------------------------------------------------------------------- #
def computed_balance(
    transactions: list[Transaction],
    account: Account,
    as_of: str | None = None,
) -> float:
    """Saldo hasil pencatatan transaksi = Σ(incoming) - Σ(outgoing).

    Saldo rekening (saldo bank) TIDAK termasuk di sini; nilai ini murni dari
    transaksi. Bila ``as_of`` diisi, hanya transaksi sampai tanggal tersebut
    yang dihitung.
    """
    total = 0.0
    for t in transactions:
        if t.account != account.name:
            continue
        if as_of and t.date > as_of:
            continue
        total += t.signed_amount
    return total


# --------------------------------------------------------------------------- #
# 4a. Laporan transaksi + sisa saldo pada satu titik tanggal
# --------------------------------------------------------------------------- #
@dataclass
class RunningRow:
    date: str
    type: str
    category: str
    account: str
    description: str
    amount: float
    signed: float
    balance: float  # saldo berjalan setelah transaksi ini


def running_balance_report(
    transactions: list[Transaction],
    accounts: list[Account],
    as_of: str,
    account_name: str | None = None,
) -> tuple[list[RunningRow], dict[str, float]]:
    """Daftar transaksi (urut tanggal) dengan saldo berjalan, s/d ``as_of``.

    Mengembalikan (baris, saldo_akhir_per_rekening). Bila ``account_name``
    diisi, hanya rekening itu yang dihitung; selain itu seluruh rekening.
    """
    acc_map = {a.name: a for a in accounts}
    selected = (
        [account_name] if account_name else [a.name for a in accounts]
    )

    # Saldo berjalan per rekening dari pencatatan transaksi (mulai dari 0).
    balances: dict[str, float] = {
        name: 0.0 for name in selected if name in acc_map
    }

    relevant = [
        t
        for t in transactions
        if t.date <= as_of and t.account in balances
    ]
    relevant.sort(key=lambda t: (t.date, t.id))

    rows: list[RunningRow] = []
    for t in relevant:
        balances[t.account] += t.signed_amount
        rows.append(
            RunningRow(
                date=t.date,
                type=t.type,
                category=t.category,
                account=t.account,
                description=t.description,
                amount=t.amount,
                signed=t.signed_amount,
                balance=balances[t.account],
            )
        )
    return rows, balances


# --------------------------------------------------------------------------- #
# 4b. Breakdown kategori (pie chart) berdasarkan periode
# --------------------------------------------------------------------------- #
def category_breakdown(
    transactions: list[Transaction],
    start: str,
    end: str,
    tx_type: str = "outgoing",
) -> dict[str, float]:
    """Total NOMINAL per kategori untuk periode [start, end] dan tipe tertentu.

    Diurutkan dari nominal terbesar ke terkecil.
    """
    totals: dict[str, float] = defaultdict(float)
    for t in transactions:
        if t.type != tx_type:
            continue
        if not (start <= t.date <= end):
            continue
        totals[t.category] += t.amount
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


# --------------------------------------------------------------------------- #
# 4c. Cashflow harian agregat
# --------------------------------------------------------------------------- #
@dataclass
class CashflowRow:
    date: str
    incoming: float
    outgoing: float
    net: float       # incoming - outgoing (arus kas hari itu)
    balance: float   # saldo kumulatif s/d akhir hari itu


def daily_cashflow(
    transactions: list[Transaction],
    accounts: list[Account],
    start: str,
    end: str,
    account_name: str | None = None,
    hide_zero_net: bool = False,
) -> list[CashflowRow]:
    """Arus kas harian agregat untuk periode [start, end].

    Tiap hari menampilkan total incoming, total outgoing, net (incoming -
    outgoing), dan saldo kumulatif. Saldo memperhitungkan saldo awal +
    seluruh transaksi sebelum ``start`` agar nilai saldo berkesinambungan.

    Bila ``hide_zero_net`` True, hari dengan net = 0 tidak dimasukkan ke hasil
    (saldo tetap berkesinambungan karena net 0 tidak mengubah saldo).
    """
    if account_name:
        relevant_accounts = [a for a in accounts if a.name == account_name]
    else:
        relevant_accounts = list(accounts)
    acc_names = {a.name for a in relevant_accounts}

    start_d = parse_date(start)
    end_d = parse_date(end)
    if end_d < start_d:
        return []

    # Saldo pembuka periode = akumulasi transaksi sebelum ``start`` (saldo
    # rekening/bank tidak diperhitungkan, murni dari pencatatan transaksi).
    opening = 0.0
    for t in transactions:
        if t.account in acc_names and t.date < start:
            opening += t.signed_amount

    # Agregasi per hari di dalam periode.
    inc: dict[str, float] = defaultdict(float)
    out: dict[str, float] = defaultdict(float)
    for t in transactions:
        if t.account not in acc_names:
            continue
        if not (start <= t.date <= end):
            continue
        if t.type == "incoming":
            inc[t.date] += t.amount
        else:
            out[t.date] += t.amount

    rows: list[CashflowRow] = []
    running = opening
    current = start_d
    while current <= end_d:
        d = current.strftime("%Y-%m-%d")
        i = inc.get(d, 0.0)
        o = out.get(d, 0.0)
        net = i - o
        running += net
        if hide_zero_net and abs(net) < 0.005:
            current += timedelta(days=1)
            continue
        rows.append(CashflowRow(date=d, incoming=i, outgoing=o, net=net, balance=running))
        current += timedelta(days=1)
    return rows


# --------------------------------------------------------------------------- #
# Module 2. Rekonsiliasi saldo bank vs pencatatan
# --------------------------------------------------------------------------- #
@dataclass
class ReconRow:
    account: str
    recorded: float          # saldo dari pencatatan transaksi
    bank: float | None       # saldo bank (snapshot terakhir), None bila belum ada
    bank_date: str | None
    difference: float | None  # bank - recorded


def reconciliation(
    transactions: list[Transaction],
    accounts: list[Account],
    balances: list[BalanceSnapshot],
    as_of: str | None = None,
) -> list[ReconRow]:
    """Bandingkan saldo pencatatan dengan snapshot saldo bank terakhir."""
    rows: list[ReconRow] = []
    for a in accounts:
        recorded = computed_balance(transactions, a, as_of=as_of)
        snaps = [b for b in balances if b.account == a.name]
        if as_of:
            snaps = [b for b in snaps if b.date <= as_of]
        latest = max(snaps, key=lambda b: b.date) if snaps else None
        bank = latest.amount if latest else None
        diff = (bank - recorded) if bank is not None else None
        rows.append(
            ReconRow(
                account=a.name,
                recorded=recorded,
                bank=bank,
                bank_date=latest.date if latest else None,
                difference=diff,
            )
        )
    return rows

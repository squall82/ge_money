"""Lapisan penyimpanan JSON sederhana (tanpa database).

``JsonStore`` membungkus operasi baca/tulis sebuah file JSON yang berisi list
of dict. Penulisan dilakukan secara atomik (tulis ke file sementara lalu
``replace``) supaya data tidak rusak bila proses terganggu di tengah jalan.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from . import config


class JsonStore:
    """Penyimpanan untuk satu koleksi (list of dict) dalam file JSON."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        """Baca seluruh isi koleksi. Mengembalikan list kosong bila belum ada."""
        config.ensure_data_dir()
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            # File rusak/kosong: jangan menghentikan aplikasi.
            return []
        if not isinstance(data, list):
            return []
        return data

    def save(self, items: list[dict[str, Any]]) -> None:
        """Tulis seluruh koleksi secara atomik."""
        config.ensure_data_dir()
        directory = self.path.parent
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(items, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

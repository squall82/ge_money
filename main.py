"""Titik masuk aplikasi GE Money.

Jalankan dengan:  python main.py
"""

from gemoney.ui import GeMoneyApp


def main() -> None:
    app = GeMoneyApp()
    app.mainloop()


if __name__ == "__main__":
    main()

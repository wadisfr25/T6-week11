"""
Nama  : Wadis Freandly
NIM   : F1D02310094
Kelas : Pemvis D
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from post_manager_app.ui import PostManagerWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = PostManagerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

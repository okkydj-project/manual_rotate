#!/usr/bin/env python3
"""Screen Rotate - Manual display rotation for Ubuntu Wayland."""

import sys

from PySide6.QtWidgets import QApplication

from .gui import ScreenRotateWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Screen Rotate")
    app.setOrganizationName("screen-rotate")
    app.setDesktopFileName("screen-rotate")

    window = ScreenRotateWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

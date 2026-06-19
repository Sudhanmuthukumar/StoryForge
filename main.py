"""
main.py — Entry point for StoryForge AI.

Creates the QApplication, applies the global dark-theme stylesheet,
instantiates the main window, and starts the event loop.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that ``from core import …``
# and ``from models import …`` resolve correctly regardless of how the
# script is launched.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from ui.main_window import MainWindow
from ui.styles import DARK_THEME
from utils.constants import APP_NAME


def main() -> None:
    """Launch StoryForge AI."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Apply global stylesheet
    app.setStyleSheet(DARK_THEME)

    # Prefer Segoe UI on Windows, fall back gracefully
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""
styles.py — QSS dark-theme stylesheet for StoryForge AI.

Colour palette
──────────────
  Background   #0f0f1a  (deep void)
  Surface      #12121f  (sidebar)  /  #15152a  (editor card)
  Border       #2a2a4a
  Text primary #e0e0ff
  Text muted   #6c6c8a  /  #8888aa
  Accent       #6c63ff  (indigo)
  Success      #1a9a5a
  Danger       #ff6b6b
"""

DARK_THEME: str = """

/* ── Global ───────────────────────────────────────────────────────── */
* {
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #0f0f1a;
}

QToolTip {
    background-color: #1e1e38;
    color: #e0e0ff;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 12px;
}

/* ── Status Bar ───────────────────────────────────────────────────── */
QStatusBar {
    background-color: #0a0a14;
    color: #8888aa;
    border-top: 1px solid #2a2a4a;
    padding: 4px 12px;
    font-size: 12px;
}

/* ── Splitter handle ──────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #2a2a4a;
    width: 1px;
}

/* ── Sidebar ──────────────────────────────────────────────────────── */
QWidget#sidebar {
    background-color: #12121f;
    border-right: 1px solid #2a2a4a;
}

QLabel#sidebarTitle {
    color: #e0e0ff;
    font-size: 18px;
    font-weight: 700;
    padding: 22px 16px 4px 16px;
    letter-spacing: 0.5px;
}

QLabel#sidebarSubtitle {
    color: #6c6c8a;
    font-size: 11px;
    padding: 0 16px 14px 16px;
}

/* Story list */
QListWidget#storyList {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px 8px;
    color: #c0c0dd;
    font-size: 13px;
}

QListWidget#storyList::item {
    padding: 10px 12px;
    border-radius: 8px;
    margin: 2px 0;
}

QListWidget#storyList::item:hover {
    background-color: rgba(108, 99, 255, 0.08);
    color: #e0e0ff;
}

QListWidget#storyList::item:selected {
    background-color: rgba(108, 99, 255, 0.18);
    color: #ffffff;
    border-left: 3px solid #6c63ff;
}

/* ── Sidebar buttons ──────────────────────────────────────────────── */
QPushButton#btnCreate {
    background-color: #6c63ff;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
    font-size: 13px;
    margin: 4px 12px;
}
QPushButton#btnCreate:hover  { background-color: #7b73ff; }
QPushButton#btnCreate:pressed { background-color: #5a52e0; }

QPushButton#btnOpen {
    background-color: transparent;
    color: #a0a0cc;
    border: 1px solid #3a3a5a;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 500;
    font-size: 13px;
    margin: 4px 12px;
}
QPushButton#btnOpen:hover {
    background-color: rgba(108, 99, 255, 0.08);
    color: #c0c0ff;
    border-color: #6c63ff;
}
QPushButton#btnOpen:pressed {
    background-color: rgba(108, 99, 255, 0.15);
}

QPushButton#btnDelete {
    background-color: transparent;
    color: #ff6b6b;
    border: 1px solid #4a2a2a;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 500;
    font-size: 13px;
    margin: 4px 12px;
}
QPushButton#btnDelete:hover {
    background-color: rgba(255, 107, 107, 0.08);
    border-color: #ff6b6b;
}
QPushButton#btnDelete:pressed {
    background-color: rgba(255, 107, 107, 0.15);
}

/* ── Editor area ──────────────────────────────────────────────────── */
QWidget#editorArea {
    background-color: #0f0f1a;
}

QLabel#editorTitle {
    color: #e0e0ff;
    font-size: 22px;
    font-weight: 700;
    padding: 24px 32px 4px 32px;
}

QLabel#editorGenre {
    color: #6c63ff;
    font-size: 12px;
    font-weight: 500;
    padding: 0 32px 16px 32px;
    letter-spacing: 1px;
}

QTextEdit#storyTextEdit {
    background-color: #15152a;
    color: #d0d0e8;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px 24px;
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: 15px;
    selection-background-color: rgba(108, 99, 255, 0.30);
    selection-color: #ffffff;
}

QTextEdit#storyTextEdit:focus {
    border-color: #6c63ff;
}

/* Save button */
QPushButton#btnSave {
    background-color: #1a9a5a;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 32px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton#btnSave:hover   { background-color: #1fb86c; }
QPushButton#btnSave:pressed { background-color: #158a4e; }
QPushButton#btnSave:disabled {
    background-color: #2a2a4a;
    color: #5a5a7a;
}

/* ── Welcome / empty state ────────────────────────────────────────── */
QLabel#welcomeIcon {
    color: #2a2a4a;
    font-size: 56px;
}

QLabel#welcomeTitle {
    color: #4a4a6a;
    font-size: 26px;
    font-weight: 700;
}

QLabel#welcomeSubtitle {
    color: #3a3a5a;
    font-size: 14px;
}

/* ── Scrollbars ───────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3a3a5a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #6c63ff; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
    border: none;
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #3a3a5a;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #6c63ff; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
    width: 0;
}

/* ── Dialog overrides ─────────────────────────────────────────────── */
QDialog, QInputDialog, QMessageBox {
    background-color: #16213e;
    color: #e0e0ff;
}

QDialog QLabel, QInputDialog QLabel, QMessageBox QLabel {
    color: #e0e0ff;
}

QDialog QLineEdit, QInputDialog QLineEdit {
    background-color: #1a1a2e;
    color: #e0e0ff;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: rgba(108, 99, 255, 0.30);
}

QDialog QLineEdit:focus, QInputDialog QLineEdit:focus {
    border-color: #6c63ff;
}

QMessageBox QPushButton,
QDialog QPushButton,
QInputDialog QPushButton {
    background-color: #6c63ff;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 600;
    min-width: 80px;
}
QMessageBox QPushButton:hover,
QDialog QPushButton:hover,
QInputDialog QPushButton:hover {
    background-color: #7b73ff;
}

/* ── Tabs ─────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    border-top: 1px solid #2a2a4a;
}
QTabBar::tab {
    background: #0f0f1a;
    color: #8888aa;
    padding: 10px 20px;
    border: none;
    font-size: 14px;
    font-weight: 500;
}
QTabBar::tab:selected {
    color: #e0e0ff;
    border-bottom: 3px solid #6c63ff;
}
QTabBar::tab:hover {
    color: #e0e0ff;
    background: #15152a;
}

/* ── Stat Cards ───────────────────────────────────────────────────── */
QFrame#statCard {
    background-color: #15152a;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 16px;
}
QLabel#statIcon {
    font-size: 24px;
}
QLabel#statCount {
    font-size: 28px;
    color: #6c63ff;
    font-weight: 700;
}
QLabel#statLabel {
    color: #8888aa;
    font-size: 13px;
    font-weight: 500;
}
QLabel#sectionTitle {
    color: #e0e0ff;
    font-size: 18px;
    font-weight: 700;
    padding-bottom: 16px;
}

/* ── Chat ─────────────────────────────────────────────────────────── */
QFrame#chatBubbleUser {
    background-color: #6c63ff;
    border-radius: 12px;
    border-top-right-radius: 2px;
}
QFrame#chatBubbleAssistant {
    background-color: #1e1e38;
    border-radius: 12px;
    border-top-left-radius: 2px;
}
QLabel#chatSender {
    color: #6c63ff;
    font-size: 11px;
    font-weight: 600;
}
QLabel#chatTimestamp {
    color: #6c6c8a;
    font-size: 10px;
}
QLineEdit#chatInput {
    background-color: #15152a;
    color: #e0e0ff;
    border: 1px solid #2a2a4a;
    border-radius: 20px;
    padding: 10px 16px;
    font-size: 14px;
}
QLineEdit#chatInput:focus {
    border-color: #6c63ff;
}
QPushButton#btnSend {
    background-color: #6c63ff;
    color: #ffffff;
    border: none;
    border-radius: 20px;
    padding: 10px 24px;
    font-weight: 600;
}
QPushButton#btnSend:hover {
    background-color: #7b73ff;
}
QPushButton#btnSend:disabled {
    background-color: #2a2a4a;
    color: #5a5a7a;
}
"""

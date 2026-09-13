"""Dark and Light theme stylesheets for PixForge.

QSS constraints:
- NO letter-spacing (not valid in Qt QSS)
- All braces must be balanced
- Descendant selectors like QWidget QFrame are unreliable; use objectName
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Shared colour tokens
# ---------------------------------------------------------------------------
DARK_BG = "#1a1a2e"
DARK_SURFACE = "#16213e"
DARK_CARD = "#0f3460"
DARK_ACCENT = "#e94560"
DARK_ACCENT_HOVER = "#ff6b6b"
DARK_TEXT = "#eaeaea"
DARK_MUTED = "#8892a4"
DARK_BORDER = "#2a2a4a"
DARK_INPUT_BG = "#1e1e3a"
DARK_SUCCESS = "#4caf50"
DARK_ERROR = "#f44336"
DARK_WARNING = "#ff9800"
DARK_CONVERTING = "#2196f3"

LIGHT_BG = "#f5f6fa"
LIGHT_SURFACE = "#ffffff"
LIGHT_CARD = "#e8eaf6"
LIGHT_ACCENT = "#3f51b5"
LIGHT_ACCENT_HOVER = "#5c6bc0"
LIGHT_TEXT = "#1a1a2e"
LIGHT_MUTED = "#666680"
LIGHT_BORDER = "#c5cae9"
LIGHT_INPUT_BG = "#ffffff"


def _build_stylesheet(
    bg: str, surface: str, card: str, accent: str, accent_hover: str,
    text: str, muted: str, border: str, input_bg: str,
) -> str:
    return f"""
/* ── Base ─────────────────────────────────────────────────────────── */
QMainWindow, QDialog {{
    background-color: {bg};
    color: {text};
}}
QWidget {{
    color: {text};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

/* ── Cards ─────────────────────────────────────────────────────────── */
QFrame#card {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 10px;
}}
QFrame#dropZone {{
    background-color: {surface};
    border: 2px dashed {border};
    border-radius: 12px;
}}
QFrame#dropZoneActive {{
    background-color: {card};
    border: 2px dashed {accent};
    border-radius: 12px;
}}
QFrame#thumbnailBox {{
    background-color: {card};
    border: 1px solid {border};
    border-radius: 6px;
}}
QFrame#row {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
}}
QFrame#row:hover {{
    background-color: {card};
}}
QFrame#rowActive {{
    background-color: {card};
    border: 1px solid {accent};
    border-radius: 6px;
}}
QFrame#header {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {surface}, stop:1 {bg}
    );
    border-bottom: 1px solid {border};
    border-radius: 0px;
}}

/* ── Labels ─────────────────────────────────────────────────────────── */
QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    color: {text};
}}
QLabel#subtitle {{
    font-size: 12px;
    color: {muted};
}}
QLabel#section {{
    font-size: 11px;
    font-weight: 600;
    color: {muted};
    text-transform: uppercase;
}}
QLabel#muted {{
    color: {muted};
    font-size: 12px;
}}
QLabel#dropHint {{
    font-size: 15px;
    font-weight: 600;
    color: {muted};
}}
QLabel#dropSub {{
    font-size: 12px;
    color: {muted};
}}

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {card};
    border-color: {accent};
}}
QPushButton:pressed {{
    background-color: {accent};
    color: #ffffff;
}}
QPushButton:disabled {{
    color: {muted};
    border-color: {border};
    background-color: {surface};
}}
QPushButton#primary {{
    background-color: {accent};
    color: #ffffff;
    border: none;
    font-size: 14px;
    font-weight: 700;
    padding: 10px 28px;
    border-radius: 8px;
}}
QPushButton#primary:hover {{
    background-color: {accent_hover};
}}
QPushButton#primary:pressed {{
    background-color: {accent};
}}
QPushButton#primary:disabled {{
    background-color: {muted};
    color: {surface};
}}
QPushButton#danger {{
    background-color: #c0392b;
    color: #ffffff;
    border: none;
    font-size: 14px;
    font-weight: 700;
    padding: 10px 24px;
    border-radius: 8px;
}}
QPushButton#danger:hover {{
    background-color: #e74c3c;
}}
QPushButton#iconButton {{
    background-color: transparent;
    border: none;
    color: {muted};
    padding: 4px;
    font-size: 12px;
    border-radius: 4px;
}}
QPushButton#iconButton:hover {{
    color: {text};
    background-color: {card};
}}
QPushButton#linkButton {{
    background-color: transparent;
    border: none;
    color: {accent};
    font-size: 12px;
    padding: 2px 0px;
    text-decoration: underline;
}}
QPushButton#linkButton:hover {{
    color: {accent_hover};
}}

/* ── Inputs ─────────────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
    selection-background-color: {accent};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    selection-background-color: {accent};
}}

/* ── Sliders ─────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {border};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {accent};
    border: none;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}}
QSlider::sub-page:horizontal {{
    background: {accent};
    border-radius: 2px;
}}

/* ── Progress Bar ─────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {border};
    border-radius: 4px;
    height: 8px;
    text-align: center;
    font-size: 11px;
    color: transparent;
    border: none;
}}
QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 4px;
}}

/* ── List / Scroll ─────────────────────────────────────────────────────── */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background: {bg};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {muted};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {bg};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {border};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Checkboxes ─────────────────────────────────────────────────────── */
QCheckBox {{
    color: {text};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border};
    border-radius: 4px;
    background-color: {input_bg};
}}
QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

/* ── Group Box ─────────────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 8px;
    font-size: 12px;
    font-weight: 600;
    color: {muted};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 12px;
}}

/* ── Status badges ─────────────────────────────────────────────────── */
QLabel#statusWaiting {{
    color: {muted};
    font-size: 11px;
}}
QLabel#statusConverting {{
    color: {DARK_CONVERTING};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#statusCompleted {{
    color: {DARK_SUCCESS};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#statusFailed {{
    color: {DARK_ERROR};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#statusSkipped {{
    color: {DARK_WARNING};
    font-size: 11px;
}}

/* ── Stacked / Tab widget ─────────────────────────────────────────── */
QTabBar::tab {{
    background: {surface};
    color: {muted};
    padding: 6px 14px;
    border: 1px solid {border};
    border-bottom: none;
    border-radius: 4px 4px 0 0;
}}
QTabBar::tab:selected {{
    color: {text};
    background: {card};
}}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 0 6px 6px 6px;
    background: {surface};
}}

/* ── Tooltip ─────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    padding: 4px 8px;
    border-radius: 4px;
}}
"""


# Dark theme (default)
DARK_STYLESHEET = _build_stylesheet(
    bg=DARK_BG, surface=DARK_SURFACE, card=DARK_CARD,
    accent=DARK_ACCENT, accent_hover=DARK_ACCENT_HOVER,
    text=DARK_TEXT, muted=DARK_MUTED, border=DARK_BORDER,
    input_bg=DARK_INPUT_BG,
)

# Light theme
LIGHT_STYLESHEET = _build_stylesheet(
    bg=LIGHT_BG, surface=LIGHT_SURFACE, card=LIGHT_CARD,
    accent=LIGHT_ACCENT, accent_hover=LIGHT_ACCENT_HOVER,
    text=LIGHT_TEXT, muted=LIGHT_MUTED, border=LIGHT_BORDER,
    input_bg=LIGHT_INPUT_BG,
)

# Default export
APP_STYLESHEET = DARK_STYLESHEET


def get_stylesheet(theme: str = "dark") -> str:
    """Return stylesheet for *theme* ('dark' or 'light')."""
    return LIGHT_STYLESHEET if theme.lower() == "light" else DARK_STYLESHEET

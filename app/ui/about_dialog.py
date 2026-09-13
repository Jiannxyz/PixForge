"""About / Credits dialog for PixForge."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QFrame,
)

from app.config import APP_NAME, APP_VERSION, LOGO_TRANSPARENT_PATH, LOGO_BACKGROUND_PATH

_GITHUB_URL = "https://github.com/Jiannxyz"
_DEVELOPER = "Jian Alvarez"


class AboutDialog(QDialog):
    """Minimal, polished About / Credits dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(420, 340)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        if LOGO_TRANSPARENT_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_TRANSPARENT_PATH)))
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = (
            LOGO_TRANSPARENT_PATH
            if LOGO_TRANSPARENT_PATH.exists()
            else LOGO_BACKGROUND_PATH
        )
        if logo_path.exists():
            logo_lbl = QLabel(self)
            pix = QPixmap(str(logo_path)).scaled(
                80, 80,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_lbl.setPixmap(pix)
            logo_lbl.setFixedSize(80, 80)
            logo_row.addWidget(logo_lbl)

        root.addLayout(logo_row)
        root.addSpacing(14)

        # ── App name & version ────────────────────────────────────────
        name_lbl = QLabel(APP_NAME, self)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("font-size: 22px; font-weight: 700;")
        root.addWidget(name_lbl)

        tagline_lbl = QLabel("Offline Batch Image Converter", self)
        tagline_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline_lbl.setObjectName("muted")
        tagline_lbl.setStyleSheet("font-size: 12px;")
        root.addWidget(tagline_lbl)

        root.addSpacing(6)

        version_lbl = QLabel(f"Version {APP_VERSION}", self)
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setStyleSheet("font-size: 11px; font-weight: 600; opacity: 0.7;")
        root.addWidget(version_lbl)

        root.addSpacing(18)

        # ── Divider ───────────────────────────────────────────────────
        divider = QFrame(self)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("muted")
        root.addWidget(divider)

        root.addSpacing(16)

        # ── Credits ───────────────────────────────────────────────────
        credit_lbl = QLabel("Developed by", self)
        credit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit_lbl.setObjectName("muted")
        credit_lbl.setStyleSheet("font-size: 12px;")
        root.addWidget(credit_lbl)

        dev_lbl = QLabel(f"<b>{_DEVELOPER}</b>", self)
        dev_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_lbl.setStyleSheet("font-size: 15px;")
        root.addWidget(dev_lbl)

        root.addSpacing(10)

        # ── GitHub button ─────────────────────────────────────────────
        gh_row = QHBoxLayout()
        gh_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gh_btn = QPushButton("⬡  GitHub", self)
        gh_btn.setObjectName("linkButton")
        gh_btn.setToolTip(_GITHUB_URL)
        gh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_GITHUB_URL)))
        gh_row.addWidget(gh_btn)

        root.addLayout(gh_row)
        root.addStretch()

        # ── Close button ──────────────────────────────────────────────
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close", self)
        close_btn.setFixedWidth(90)
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        root.addLayout(close_row)

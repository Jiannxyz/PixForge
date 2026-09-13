"""Shared helper widgets and formatting utilities."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from app.models import FileStatus


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_bytes(n: int) -> str:
    """Return a human-readable file size string."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    if n < 1024 ** 3:
        return f"{n / 1024 ** 2:.1f} MB"
    return f"{n / 1024 ** 3:.2f} GB"


def format_dimensions(w: int, h: int) -> str:
    if w and h:
        return f"{w} × {h}"
    return ""


# ---------------------------------------------------------------------------
# Styled label helpers
# ---------------------------------------------------------------------------

class TitleLabel(QLabel):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("title")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)


class SubtitleLabel(QLabel):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("subtitle")


class SectionLabel(QLabel):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text.upper(), parent)
        self.setObjectName("section")


class MutedLabel(QLabel):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("muted")


class PrimaryButton(QPushButton):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("primary")


# ---------------------------------------------------------------------------
# Status badge
# ---------------------------------------------------------------------------

STATUS_OBJECT_NAMES = {
    FileStatus.WAITING: "statusWaiting",
    FileStatus.CONVERTING: "statusConverting",
    FileStatus.COMPLETED: "statusCompleted",
    FileStatus.FAILED: "statusFailed",
    FileStatus.SKIPPED: "statusSkipped",
}

STATUS_ICONS = {
    FileStatus.WAITING: "◦",
    FileStatus.CONVERTING: "↻",
    FileStatus.COMPLETED: "✓",
    FileStatus.FAILED: "✗",
    FileStatus.SKIPPED: "⊘",
}


def make_status_label(status: FileStatus, parent=None) -> QLabel:
    icon = STATUS_ICONS.get(status, "")
    lbl = QLabel(f"{icon} {status.value}", parent)
    lbl.setObjectName(STATUS_OBJECT_NAMES.get(status, "muted"))
    return lbl


def update_status_label(label: QLabel, status: FileStatus) -> None:
    icon = STATUS_ICONS.get(status, "")
    label.setText(f"{icon} {status.value}")
    label.setObjectName(STATUS_OBJECT_NAMES.get(status, "muted"))
    # Force stylesheet re-evaluation
    label.style().unpolish(label)
    label.style().polish(label)

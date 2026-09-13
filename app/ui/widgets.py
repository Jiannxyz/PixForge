"""Shared widgets and display helpers."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def format_dimensions(width: int | None, height: int | None) -> str:
    if width is None or height is None:
        return "—"
    return f"{width} × {height}"


def status_label(status: str) -> str:
    mapping = {
        "WAITING": "Ready",
        "CONVERTING": "Converting",
        "COMPLETED": "Completed",
        "FAILED": "Failed",
        "SKIPPED": "Skipped",
    }
    return mapping.get(status, status.title())


class MutedLabel(QLabel):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("muted")


class TitleLabel(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("title")


class SubtitleLabel(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("subtitle")


class SectionLabel(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text.upper(), parent)
        self.setObjectName("section")


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("primary")

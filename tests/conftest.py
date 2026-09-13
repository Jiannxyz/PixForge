"""Pytest configuration and session fixtures."""
from __future__ import annotations

import os
import sys

# Ensure offscreen rendering for Qt tests in CI / headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtWidgets import QApplication
from pillow_heif import register_heif_opener

register_heif_opener()


@pytest.fixture(scope="session")
def qapp():
    """Create a single shared QApplication instance for all UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

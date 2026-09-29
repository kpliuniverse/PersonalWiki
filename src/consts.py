"""
    A collection of consts.
"""

from PyQt6.QtCore import Qt
# DO NOT MOVE THIS FILE
import pathlib
from pathlib import Path


ITEM_DATA_ROLE = Qt.ItemDataRole.UserRole + 1
WIKI_ENCODING = "utf-8"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESOURCE_PATH = PROJECT_ROOT / "resources"

LOOPBACK_IP_ADD = "127.0.0.1"

SAVE_DELAY_MS = 500
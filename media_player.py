#!/usr/bin/env python3
"""Lumina Media Player

A desktop video player for local video files with a Kodi Estuary-inspired GUI.
Built with PyQt5 and Qt Multimedia.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence, QPixmap
from PyQt5.QtMultimedia import QAudio, QAudioDeviceInfo, QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStackedWidget,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QMainWindow,
)

# ---------------------------------------------------------------------------
# Supported video file extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".m2ts", ".vob",
        ".ogv", ".mxf", ".asf", ".rm", ".rmvb",
    }
)

VIDEO_FILTER = (
    "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm "
    "*.m4v *.mpg *.mpeg *.3gp *.ts *.m2ts *.vob *.ogv *.mxf "
    "*.asf *.rm *.rmvb);;All Files (*)"
)

# ---------------------------------------------------------------------------
# Supported image file extensions
# ---------------------------------------------------------------------------
SUPPORTED_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
)

IMAGE_FILTER = (
    "Image Files (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff *.tif);;All Files (*)"
)

# Path to persist the media library between sessions
LIBRARY_FILE = os.path.join(
    os.path.expanduser("~"), ".lumina_media_library.json"
)

# Path to persist user settings between sessions
_SETTINGS_FILE = os.path.join(
    os.path.expanduser("~"), ".lumina_settings.json"
)

# Default settings values
_DEFAULT_SETTINGS: dict = {
    "volume": 80,
    "audio_device": "",
    "display_index": 0,
    "window_mode": "windowed",
    "resolution": [1280, 720],
}

# Selectable window resolutions
_RESOLUTIONS = [
    ("640 × 360",   640,  360),
    ("854 × 480",   854,  480),
    ("1280 × 720",  1280, 720),
    ("1600 × 900",  1600, 900),
    ("1920 × 1080", 1920, 1080),
    ("2560 × 1440", 2560, 1440),
]

# ---------------------------------------------------------------------------
# Kodi Estuary-inspired stylesheet
# ---------------------------------------------------------------------------
ESTUARY_STYLESHEET = """
* {
    font-family: "Open Sans", "Segoe UI", "Ubuntu", Arial, sans-serif;
}

QMainWindow, QWidget {
    background-color: #0f0f13;
    color: #dddddd;
}

/* ── Header ─────────────────────────────────────────────────────────────── */
QFrame#headerBar {
    background-color: #0a0a10;
    border-bottom: 2px solid #1c1c28;
    min-height: 48px;
    max-height: 48px;
}

QLabel#appTitle {
    color: #2d7ae0;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 3px;
    padding-left: 16px;
}

QLabel#nowPlaying {
    color: #9898a0;
    font-size: 12px;
    padding-right: 16px;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
QFrame#sidebar {
    background-color: #13131b;
    border-right: 1px solid #1c1c28;
}

QLabel#sidebarTitle {
    color: #2d7ae0;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 10px 12px 8px;
    border-bottom: 1px solid #1c1c28;
    background-color: #0f0f18;
}

QListWidget#playlist {
    background-color: transparent;
    border: none;
    outline: 0;
    color: #c0c0d0;
    font-size: 13px;
}

QListWidget#playlist::item {
    padding: 9px 12px;
    border-radius: 3px;
    margin: 2px 4px;
}

QListWidget#playlist::item:selected {
    background-color: #2d7ae0;
    color: #ffffff;
}

QListWidget#playlist::item:hover:!selected {
    background-color: #1e1e2e;
    color: #ffffff;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 5px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #2a2a3a;
    border-radius: 2px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #2d7ae0;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Sidebar buttons ─────────────────────────────────────────────────────── */
QPushButton#sidebarBtn {
    background-color: #1a1a28;
    color: #9898a0;
    border: 1px solid #1c1c28;
    border-radius: 3px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
}

QPushButton#sidebarBtn:hover {
    background-color: #2d7ae0;
    color: #ffffff;
    border-color: #2d7ae0;
}

QPushButton#sidebarBtn:pressed {
    background-color: #1d6ad0;
}

/* ── Video area ──────────────────────────────────────────────────────────── */
QVideoWidget {
    background-color: #000000;
}

QWidget#videoContainer {
    background-color: #000000;
}

/* ── Control bar ─────────────────────────────────────────────────────────── */
QFrame#controlBar {
    background-color: #13131b;
    border-top: 1px solid #1c1c28;
    min-height: 84px;
}

/* ── Seek slider ─────────────────────────────────────────────────────────── */
QSlider#seekSlider::groove:horizontal {
    height: 4px;
    background: #2a2a3a;
    border-radius: 2px;
}

QSlider#seekSlider::sub-page:horizontal {
    background: #2d7ae0;
    border-radius: 2px;
}

QSlider#seekSlider::handle:horizontal {
    background: #5097f2;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider#seekSlider::handle:horizontal:hover {
    background: #7ab3ff;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

/* ── Volume slider ───────────────────────────────────────────────────────── */
QSlider#volumeSlider::groove:horizontal {
    height: 3px;
    background: #2a2a3a;
    border-radius: 1px;
}

QSlider#volumeSlider::sub-page:horizontal {
    background: #5097f2;
    border-radius: 1px;
}

QSlider#volumeSlider::handle:horizontal {
    background: #5097f2;
    width: 10px;
    height: 10px;
    margin: -4px 0;
    border-radius: 5px;
}

/* ── Transport control buttons ───────────────────────────────────────────── */
QPushButton#controlBtn {
    background-color: transparent;
    color: #9898a0;
    border: none;
    border-radius: 4px;
    font-size: 18px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
}

QPushButton#controlBtn:hover {
    color: #ffffff;
    background-color: #1e1e2e;
}

QPushButton#controlBtn:pressed {
    color: #2d7ae0;
}

/* ── Play / Pause button (accent circle) ────────────────────────────────── */
QPushButton#playBtn {
    background-color: #2d7ae0;
    color: #ffffff;
    border: none;
    border-radius: 25px;
    font-size: 20px;
    min-width: 50px;
    min-height: 50px;
    max-width: 50px;
    max-height: 50px;
}

QPushButton#playBtn:hover {
    background-color: #3d8af0;
}

QPushButton#playBtn:pressed {
    background-color: #1d6ad0;
}

/* ── Time label ──────────────────────────────────────────────────────────── */
QLabel#timeLabel {
    color: #9898a0;
    font-size: 11px;
    font-family: "Courier New", "Consolas", monospace;
    min-width: 100px;
}

/* ── Volume icon label ───────────────────────────────────────────────────── */
QLabel#volumeIcon {
    color: #9898a0;
    font-size: 14px;
    padding: 0 4px;
}

/* ── Sidebar tabs ─────────────────────────────────────────────────────────── */
QTabWidget#sidebarTabs::pane {
    border: none;
    background-color: #13131b;
}

QTabWidget#sidebarTabs > QTabBar::tab {
    background-color: #0f0f18;
    color: #9898a0;
    padding: 7px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabWidget#sidebarTabs > QTabBar::tab:selected {
    color: #2d7ae0;
    border-bottom: 2px solid #2d7ae0;
    background-color: #13131b;
}

QTabWidget#sidebarTabs > QTabBar::tab:hover:!selected {
    color: #dddddd;
    background-color: #1a1a28;
}

/* ── Library list ────────────────────────────────────────────────────────── */
QListWidget#library {
    background-color: transparent;
    border: none;
    outline: 0;
    color: #c0c0d0;
    font-size: 13px;
}

QListWidget#library::item {
    padding: 9px 12px;
    border-radius: 3px;
    margin: 2px 4px;
}

QListWidget#library::item:selected {
    background-color: #2d7ae0;
    color: #ffffff;
}

QListWidget#library::item:hover:!selected {
    background-color: #1e1e2e;
    color: #ffffff;
}

/* ── Home page ────────────────────────────────────────────────────────────── */
QWidget#homePage {
    background-color: #0f0f13;
}

QLabel#homeTitle {
    color: #2d7ae0;
    font-size: 36px;
    font-weight: 700;
    letter-spacing: 6px;
}

QLabel#homeSubtitle {
    color: #9898a0;
    font-size: 14px;
    letter-spacing: 1px;
}

QPushButton#homeNavBtn {
    background-color: #13131b;
    color: #dddddd;
    border: 1px solid #1c1c28;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    min-width: 160px;
    min-height: 130px;
    padding: 16px 24px;
}

QPushButton#homeNavBtn:hover {
    background-color: #1a1a2e;
    border-color: #2d7ae0;
    color: #ffffff;
}

QPushButton#homeNavBtn:pressed {
    background-color: #2d7ae0;
    color: #ffffff;
    border-color: #2d7ae0;
}

/* ── Home button in header ────────────────────────────────────────────────── */
QPushButton#homeBtn {
    background-color: transparent;
    color: #9898a0;
    border: 1px solid #1c1c28;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    min-height: 28px;
    padding: 0 12px;
    margin-left: 8px;
}

QPushButton#homeBtn:hover {
    color: #ffffff;
    background-color: #1e1e2e;
    border-color: #2d7ae0;
}

QPushButton#homeBtn:pressed {
    color: #2d7ae0;
}

/* ── Settings page ────────────────────────────────────────────────────────── */
QWidget#settingsPage {
    background-color: #0f0f13;
}

QLabel#settingsTitle {
    color: #2d7ae0;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 4px;
}

QScrollArea#settingsScroll {
    background-color: transparent;
    border: none;
}

QWidget#settingsContent {
    background-color: transparent;
}

QGroupBox#settingsGroup {
    color: #2d7ae0;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    border: 1px solid #1c1c28;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 8px;
}

QGroupBox#settingsGroup::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 14px;
}

QLabel#settingLabel {
    color: #dddddd;
    font-size: 13px;
    min-width: 170px;
}

QLabel#settingsValueLabel {
    color: #9898a0;
    font-size: 12px;
    min-width: 36px;
}

QComboBox#settingsCombo {
    background-color: #1a1a28;
    color: #dddddd;
    border: 1px solid #1c1c28;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 13px;
    min-width: 220px;
    min-height: 32px;
}

QComboBox#settingsCombo:hover {
    border-color: #2d7ae0;
}

QComboBox#settingsCombo:disabled {
    color: #505060;
    background-color: #141420;
    border-color: #141420;
}

QComboBox#settingsCombo::drop-down {
    border: none;
    width: 20px;
}

QComboBox#settingsCombo QAbstractItemView {
    background-color: #1a1a28;
    color: #dddddd;
    border: 1px solid #2d7ae0;
    selection-background-color: #2d7ae0;
    outline: none;
}

QSlider#settingsSlider::groove:horizontal {
    height: 4px;
    background: #2a2a3a;
    border-radius: 2px;
}

QSlider#settingsSlider::sub-page:horizontal {
    background: #2d7ae0;
    border-radius: 2px;
}

QSlider#settingsSlider::handle:horizontal {
    background: #5097f2;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider#settingsSlider::handle:horizontal:hover {
    background: #7ab3ff;
}

QPushButton#settingsApplyBtn {
    background-color: #2d7ae0;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 10px 40px;
    min-width: 160px;
}

QPushButton#settingsApplyBtn:hover {
    background-color: #3d8af0;
}

QPushButton#settingsApplyBtn:pressed {
    background-color: #1d6ad0;
}

/* ── Library sub-tabs ─────────────────────────────────────────────────────── */
QTabWidget#librarySubTabs::pane {
    border: none;
    background-color: #13131b;
}

QTabWidget#librarySubTabs > QTabBar::tab {
    background-color: #0f0f18;
    color: #9898a0;
    padding: 5px 8px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabWidget#librarySubTabs > QTabBar::tab:selected {
    color: #2d7ae0;
    border-bottom: 2px solid #2d7ae0;
    background-color: #13131b;
}

QTabWidget#librarySubTabs > QTabBar::tab:hover:!selected {
    color: #dddddd;
    background-color: #1a1a28;
}

/* ── Picture viewer ──────────────────────────────────────────────────────── */
QWidget#pictureViewer {
    background-color: #000000;
}

QLabel#pictureLabel {
    background-color: #000000;
}

/* ── YouTube search dialog ───────────────────────────────────────────────── */
QDialog {
    background-color: #0f0f13;
    color: #dddddd;
}

QLineEdit#ytSearchInput {
    background-color: #1a1a28;
    color: #dddddd;
    border: 1px solid #1c1c28;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit#ytSearchInput:focus {
    border-color: #2d7ae0;
}

QListWidget#ytResultsList {
    background-color: #13131b;
    border: 1px solid #1c1c28;
    border-radius: 4px;
    color: #c0c0d0;
    font-size: 12px;
    outline: 0;
}

QListWidget#ytResultsList::item {
    padding: 8px 12px;
    border-radius: 3px;
    margin: 2px 4px;
}

QListWidget#ytResultsList::item:selected {
    background-color: #2d7ae0;
    color: #ffffff;
}

QListWidget#ytResultsList::item:hover:!selected {
    background-color: #1e1e2e;
    color: #ffffff;
}

QLabel#ytStatusLabel {
    color: #9898a0;
    font-size: 11px;
    padding: 4px 0;
}

QPushButton#ytActionBtn {
    background-color: #2d7ae0;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

QPushButton#ytActionBtn:hover {
    background-color: #3d8af0;
}

QPushButton#ytActionBtn:pressed {
    background-color: #1d6ad0;
}

QPushButton#ytActionBtn:disabled {
    background-color: #1a1a28;
    color: #505060;
}

QPushButton#ytCancelBtn {
    background-color: #1a1a28;
    color: #9898a0;
    border: 1px solid #1c1c28;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

QPushButton#ytCancelBtn:hover {
    background-color: #2a2a3a;
    color: #dddddd;
}
"""


# ---------------------------------------------------------------------------
# Helper: format milliseconds → "H:MM:SS" or "M:SS"
# ---------------------------------------------------------------------------
def _format_time(ms: int) -> str:
    if ms <= 0:
        return "0:00"
    total_s = ms // 1000
    h, remainder = divmod(total_s, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ---------------------------------------------------------------------------
# Helper: create a styled label for a settings form row
# ---------------------------------------------------------------------------
def _settings_lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("settingLabel")
    return lbl


# ---------------------------------------------------------------------------
# Background worker: yt-dlp search
# ---------------------------------------------------------------------------
class _YTSearchWorker(QThread):
    """Runs yt-dlp search in a background thread."""
    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, query: str, max_results: int = 10) -> None:
        super().__init__()
        self._query = query
        self._max_results = max_results

    def run(self) -> None:
        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    f"ytsearch{self._max_results}:{self._query}",
                    "--dump-json",
                    "--no-download",
                    "--no-playlist",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError:
            self.error.emit(
                "yt-dlp not found. Install it with: pip install yt-dlp"
            )
            return
        except subprocess.TimeoutExpired:
            self.error.emit("Search timed out")
            return
        except Exception as exc:
            self.error.emit(str(exc))
            return

        if result.returncode != 0:
            self.error.emit(result.stderr.strip() or "yt-dlp search failed")
            return

        entries: list[dict] = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            try:
                data = json.loads(line)
                duration_val = data.get("duration")
                entries.append(
                    {
                        "title": data.get("title", "Unknown"),
                        "url": data.get(
                            "webpage_url", data.get("url", "")
                        ),
                        "duration": int(duration_val)
                        if duration_val is not None
                        else None,
                        "channel": data.get(
                            "uploader", data.get("channel", "")
                        ),
                    }
                )
            except (json.JSONDecodeError, ValueError):
                pass
        self.results_ready.emit(entries)


# ---------------------------------------------------------------------------
# Background worker: yt-dlp stream URL fetcher
# ---------------------------------------------------------------------------
class _YTStreamWorker(QThread):
    """Fetches the best direct stream URL for a YouTube video via yt-dlp."""
    stream_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url

    def run(self) -> None:
        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--format",
                    "best[ext=mp4]/best",
                    "--get-url",
                    self._url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            self.error.emit(
                "yt-dlp not found. Install it with: pip install yt-dlp"
            )
            return
        except subprocess.TimeoutExpired:
            self.error.emit("Timed out while fetching stream URL")
            return
        except Exception as exc:
            self.error.emit(str(exc))
            return

        if result.returncode == 0:
            lines = [ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()]
            if lines:
                self.stream_ready.emit(lines[0])
            else:
                self.error.emit("No stream URL returned by yt-dlp")
        else:
            self.error.emit(result.stderr.strip() or "Failed to get stream URL")


# ---------------------------------------------------------------------------
# YouTube search / add dialog
# ---------------------------------------------------------------------------
_RESULT_ROLE = Qt.UserRole


def _fmt_yt_duration(seconds: int | None) -> str:
    """Format a duration in seconds to M:SS or H:MM:SS."""
    if seconds is None:
        return ""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class _YouTubeSearchDialog(QDialog):
    """Dialog for searching YouTube and selecting videos to add."""

    # Signals emitted when the user confirms a selection:
    # add_to_library(entries)  – caller should add to YouTube library
    # add_to_playlist(entries) – caller should add to playlist directly
    add_to_library = pyqtSignal(list)
    add_to_playlist = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("YouTube Search")
        self.setMinimumSize(660, 480)
        self._worker: _YTSearchWorker | None = None
        self._results: list[dict] = []
        self._build_ui()
        self.setStyleSheet(parent.styleSheet() if parent else "")

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)
        v.setSpacing(10)
        v.setContentsMargins(16, 16, 16, 16)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self._search_input = QLineEdit()
        self._search_input.setObjectName("ytSearchInput")
        self._search_input.setPlaceholderText("Search YouTube…")
        self._search_input.returnPressed.connect(self._do_search)
        search_row.addWidget(self._search_input, 1)

        self._search_btn = QPushButton("🔍  SEARCH")
        self._search_btn.setObjectName("ytActionBtn")
        self._search_btn.clicked.connect(self._do_search)
        search_row.addWidget(self._search_btn)
        v.addLayout(search_row)

        # Status label
        self._status_lbl = QLabel("Enter a search term and press Search")
        self._status_lbl.setObjectName("ytStatusLabel")
        v.addWidget(self._status_lbl)

        # Results list
        self._results_list = QListWidget()
        self._results_list.setObjectName("ytResultsList")
        self._results_list.setSelectionMode(QListWidget.ExtendedSelection)
        v.addWidget(self._results_list, 1)

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._add_lib_btn = QPushButton("📚  ADD TO LIBRARY")
        self._add_lib_btn.setObjectName("ytActionBtn")
        self._add_lib_btn.setToolTip("Save selected videos to the YouTube library")
        self._add_lib_btn.clicked.connect(self._emit_add_to_library)

        self._add_play_btn = QPushButton("▶  ADD TO PLAYLIST")
        self._add_play_btn.setObjectName("ytActionBtn")
        self._add_play_btn.setToolTip("Add selected videos to the current playlist")
        self._add_play_btn.clicked.connect(self._emit_add_to_playlist)

        close_btn = QPushButton("CLOSE")
        close_btn.setObjectName("ytCancelBtn")
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(self._add_lib_btn)
        btn_row.addWidget(self._add_play_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        v.addLayout(btn_row)

    def _do_search(self) -> None:
        query = self._search_input.text().strip()
        if not query:
            return
        self._search_btn.setEnabled(False)
        self._add_lib_btn.setEnabled(False)
        self._add_play_btn.setEnabled(False)
        self._status_lbl.setText("Searching…")
        self._results_list.clear()
        self._results = []

        self._worker = _YTSearchWorker(query)
        self._worker.results_ready.connect(self._on_results)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_results(self, entries: list[dict]) -> None:
        self._results = entries
        self._results_list.clear()
        for entry in entries:
            dur = _fmt_yt_duration(entry.get("duration"))
            dur_str = f"  [{dur}]" if dur else ""
            channel = entry.get("channel", "")
            line1 = f"{entry['title']}{dur_str}"
            line2 = f"  {channel}" if channel else ""
            text = line1 + ("\n" + line2 if line2 else "")
            item = QListWidgetItem(text)
            item.setData(_RESULT_ROLE, entry)
            self._results_list.addItem(item)
        self._status_lbl.setText(
            f"Found {len(entries)} result(s). Select one or more, then choose an action."
        )
        self._search_btn.setEnabled(True)
        self._add_lib_btn.setEnabled(True)
        self._add_play_btn.setEnabled(True)

    def _on_error(self, msg: str) -> None:
        self._status_lbl.setText(f"Error: {msg}")
        self._search_btn.setEnabled(True)
        self._add_lib_btn.setEnabled(True)
        self._add_play_btn.setEnabled(True)

    def _selected_entries(self) -> list[dict]:
        return [
            item.data(_RESULT_ROLE)
            for item in self._results_list.selectedItems()
            if item.data(_RESULT_ROLE)
        ]

    def _emit_add_to_library(self) -> None:
        entries = self._selected_entries()
        if not entries:
            QMessageBox.information(self, "No Selection", "Please select one or more videos first.")
            return
        self.add_to_library.emit(entries)

    def _emit_add_to_playlist(self) -> None:
        entries = self._selected_entries()
        if not entries:
            QMessageBox.information(self, "No Selection", "Please select one or more videos first.")
            return
        self.add_to_playlist.emit(entries)



class _ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            value = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(), event.x(), self.width()
            )
            self.setValue(value)
            self.sliderMoved.emit(value)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# QVideoWidget with double-click fullscreen signal
# ---------------------------------------------------------------------------
class _VideoWidget(QVideoWidget):
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MediaPlayer(QMainWindow):
    """Lumina media player window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lumina Media Player")
        self.setMinimumSize(900, 580)
        self.resize(1280, 720)

        # Internal state
        self._playlist_paths: list[str] = []
        self._playlist_types: list[str] = []   # "video" | "image" | "youtube"
        self._current_index: int = -1
        self._seek_dragging: bool = False
        self._is_fullscreen: bool = False

        # Media library
        self._library_folders: list[str] = []
        self._library_paths: list[str] = []          # video files
        self._picture_library_paths: list[str] = []  # image files
        self._youtube_library: list[dict] = []        # YouTube entries

        # Active yt-dlp stream worker (kept alive until thread finishes)
        self._yt_stream_worker: _YTStreamWorker | None = None
        # Original full-resolution pixmap for the currently displayed image
        self._current_pixmap: QPixmap | None = None

        # Auto-hide cursor in fullscreen
        self._cursor_timer = QTimer(self)
        self._cursor_timer.setSingleShot(True)
        self._cursor_timer.timeout.connect(self._hide_cursor)

        # Load persisted settings before building the UI so the settings page
        # can initialise its widgets with the saved values.
        self._settings: dict = self._load_settings()

        # Media engine
        self.player = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        self.player.stateChanged.connect(self._on_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.error.connect(self._on_error)

        self._build_ui()
        self._setup_shortcuts()
        self.setStyleSheet(ESTUARY_STYLESHEET)

        # Wire video output after widget exists, then apply saved settings
        self.player.setVideoOutput(self._video_widget)
        self._apply_initial_settings()

        # Load persisted library
        self._load_library()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._make_header())

        self._stack = QStackedWidget()
        self._stack.addWidget(self._make_home_page())     # index 0 – home
        self._stack.addWidget(self._make_player_page())   # index 1 – player
        self._stack.addWidget(self._make_settings_page()) # index 2 – settings
        layout.addWidget(self._stack, 1)

    def _make_home_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("homePage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        # Title
        title_lbl = QLabel("LUMINA")
        title_lbl.setObjectName("homeTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(title_lbl)

        subtitle_lbl = QLabel("Your personal media player")
        subtitle_lbl.setObjectName("homeSubtitle")
        subtitle_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(subtitle_lbl)

        outer.addSpacing(48)

        # Navigation cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(24)
        cards_row.setContentsMargins(80, 0, 80, 0)

        cards = [
            ("▶\n\nVideo Player", "Open the video player", self._go_to_player),
            ("🗂\n\nLibrary",     "Browse your media library", self._go_to_library),
            ("⚙\n\nSettings",    "Configure application settings", self._go_to_settings),
        ]

        for label_text, tooltip, slot in cards:
            btn = QPushButton(label_text)
            btn.setObjectName("homeNavBtn")
            btn.setToolTip(tooltip)
            btn.clicked.connect(slot)
            cards_row.addWidget(btn)

        outer.addLayout(cards_row)
        outer.addStretch(2)
        return page

    def _make_player_page(self) -> QWidget:
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._make_sidebar())
        splitter.addWidget(self._make_video_area())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 1040])
        v.addWidget(splitter, 1)

        v.addWidget(self._make_control_bar())
        return container

    def _make_settings_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title_lbl = QLabel("SETTINGS")
        title_lbl.setObjectName("settingsTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setContentsMargins(0, 28, 0, 20)
        outer.addWidget(title_lbl)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("settingsContent")
        vlay = QVBoxLayout(content)
        vlay.setContentsMargins(80, 8, 80, 32)
        vlay.setSpacing(20)

        # ── Audio ─────────────────────────────────────────────────────────
        audio_grp = QGroupBox("AUDIO")
        audio_grp.setObjectName("settingsGroup")
        audio_form = QFormLayout(audio_grp)
        audio_form.setSpacing(14)
        audio_form.setContentsMargins(16, 20, 16, 16)
        audio_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Audio output device
        self._audio_device_combo = QComboBox()
        self._audio_device_combo.setObjectName("settingsCombo")
        try:
            devices = QAudioDeviceInfo.availableDevices(QAudio.AudioOutput)
        except Exception:
            devices = []
        for dev in devices:
            self._audio_device_combo.addItem(dev.deviceName(), dev.deviceName())
        if self._audio_device_combo.count() == 0:
            self._audio_device_combo.addItem("System Default", "")
        saved_audio = self._settings.get("audio_device", "")
        if saved_audio:
            idx = self._audio_device_combo.findData(saved_audio)
            if idx >= 0:
                self._audio_device_combo.setCurrentIndex(idx)
        audio_form.addRow(_settings_lbl("Audio Output Device"), self._audio_device_combo)

        # Default volume
        vol_container = QWidget()
        vol_layout = QHBoxLayout(vol_container)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.setSpacing(10)

        self._settings_vol_slider = _ClickableSlider(Qt.Horizontal)
        self._settings_vol_slider.setObjectName("settingsSlider")
        self._settings_vol_slider.setRange(0, 100)
        self._settings_vol_slider.setValue(self._settings.get("volume", 80))
        self._settings_vol_slider.setFixedWidth(180)
        vol_layout.addWidget(self._settings_vol_slider)

        self._settings_vol_label = QLabel(f"{self._settings.get('volume', 80)}%")
        self._settings_vol_label.setObjectName("settingsValueLabel")
        self._settings_vol_label.setMinimumWidth(36)
        self._settings_vol_slider.valueChanged.connect(
            lambda v: self._settings_vol_label.setText(f"{v}%")
        )
        vol_layout.addWidget(self._settings_vol_label)
        vol_layout.addStretch()
        audio_form.addRow(_settings_lbl("Default Volume"), vol_container)

        vlay.addWidget(audio_grp)

        # ── Display ───────────────────────────────────────────────────────
        disp_grp = QGroupBox("DISPLAY")
        disp_grp.setObjectName("settingsGroup")
        disp_form = QFormLayout(disp_grp)
        disp_form.setSpacing(14)
        disp_form.setContentsMargins(16, 20, 16, 16)
        disp_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Monitor selection
        self._display_combo = QComboBox()
        self._display_combo.setObjectName("settingsCombo")
        for i, scr in enumerate(QApplication.screens()):
            geo = scr.geometry()
            self._display_combo.addItem(
                f"Display {i + 1}  –  {scr.name()}  ({geo.width()} × {geo.height()})",
                i,
            )
        saved_display = self._settings.get("display_index", 0)
        if isinstance(saved_display, int) and 0 <= saved_display < self._display_combo.count():
            self._display_combo.setCurrentIndex(saved_display)
        disp_form.addRow(_settings_lbl("Monitor"), self._display_combo)

        # Window mode
        self._window_mode_combo = QComboBox()
        self._window_mode_combo.setObjectName("settingsCombo")
        self._window_mode_combo.addItem("Windowed", "windowed")
        self._window_mode_combo.addItem("Fullscreen", "fullscreen")
        saved_mode = self._settings.get("window_mode", "windowed")
        self._window_mode_combo.setCurrentIndex(1 if saved_mode == "fullscreen" else 0)
        self._window_mode_combo.currentIndexChanged.connect(self._on_window_mode_changed)
        disp_form.addRow(_settings_lbl("Window Mode"), self._window_mode_combo)

        # Resolution (disabled in fullscreen)
        self._resolution_combo = QComboBox()
        self._resolution_combo.setObjectName("settingsCombo")
        for lbl_text, w, h in _RESOLUTIONS:
            self._resolution_combo.addItem(lbl_text, (w, h))
        saved_res = list(self._settings.get("resolution", [1280, 720]))
        for i, (_, w, h) in enumerate(_RESOLUTIONS):
            if saved_res == [w, h]:
                self._resolution_combo.setCurrentIndex(i)
                break
        self._resolution_combo.setEnabled(saved_mode != "fullscreen")
        disp_form.addRow(_settings_lbl("Resolution"), self._resolution_combo)

        vlay.addWidget(disp_grp)
        vlay.addStretch()

        # Apply button
        apply_btn = QPushButton("APPLY")
        apply_btn.setObjectName("settingsApplyBtn")
        apply_btn.setToolTip("Apply and save settings")
        apply_btn.clicked.connect(self._apply_settings)
        vlay.addWidget(apply_btn, 0, Qt.AlignCenter)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        return page

    # ── Navigation ─────────────────────────────────────────────────────────

    def _go_home(self) -> None:
        self._stack.setCurrentIndex(0)
        self._home_btn.hide()

    def _go_to_player(self) -> None:
        self._stack.setCurrentIndex(1)
        self._home_btn.show()

    def _go_to_library(self) -> None:
        self._stack.setCurrentIndex(1)
        self._sidebar_tabs.setCurrentIndex(1)
        self._home_btn.show()

    def _go_to_settings(self) -> None:
        # Sync live state into the settings widgets before showing the page
        self._settings_vol_slider.setValue(self.player.volume())
        self._window_mode_combo.setCurrentIndex(1 if self._is_fullscreen else 0)
        self._resolution_combo.setEnabled(not self._is_fullscreen)
        self._stack.setCurrentIndex(2)
        self._home_btn.show()

    def _make_header(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("headerBar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)

        self._home_btn = QPushButton("HOME")
        self._home_btn.setObjectName("homeBtn")
        self._home_btn.setToolTip("Home  (Alt+Home)")
        self._home_btn.clicked.connect(self._go_home)
        self._home_btn.hide()
        h.addWidget(self._home_btn)

        logo = QLabel("LUMINA")
        logo.setObjectName("appTitle")
        h.addWidget(logo)

        h.addStretch()

        self._now_playing_lbl = QLabel("No media loaded")
        self._now_playing_lbl.setObjectName("nowPlaying")
        h.addWidget(self._now_playing_lbl)

        return bar

    def _make_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        v = QVBoxLayout(sidebar)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._sidebar_tabs = QTabWidget()
        self._sidebar_tabs.setObjectName("sidebarTabs")
        self._sidebar_tabs.addTab(self._make_playlist_tab(), "PLAYLIST")
        self._sidebar_tabs.addTab(self._make_library_tab(), "LIBRARY")
        v.addWidget(self._sidebar_tabs, 1)

        return sidebar

    def _make_playlist_tab(self) -> QWidget:
        widget = QWidget()
        v = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._playlist_widget = QListWidget()
        self._playlist_widget.setObjectName("playlist")
        self._playlist_widget.itemDoubleClicked.connect(
            self._on_playlist_double_click
        )
        v.addWidget(self._playlist_widget, 1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(8, 8, 8, 8)
        btn_row.setSpacing(6)

        add_btn = QPushButton("＋  ADD")
        add_btn.setObjectName("sidebarBtn")
        add_btn.setToolTip("Open video files")
        add_btn.clicked.connect(self._open_files)

        clear_btn = QPushButton("✕  CLEAR")
        clear_btn.setObjectName("sidebarBtn")
        clear_btn.setToolTip("Clear playlist")
        clear_btn.clicked.connect(self._clear_playlist)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(clear_btn)
        v.addLayout(btn_row)

        return widget

    def _make_library_tab(self) -> QWidget:
        widget = QWidget()
        v = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._library_subtabs = QTabWidget()
        self._library_subtabs.setObjectName("librarySubTabs")
        self._library_subtabs.addTab(self._make_video_library_subtab(), "VIDEOS")
        self._library_subtabs.addTab(self._make_picture_library_subtab(), "PICTURES")
        self._library_subtabs.addTab(self._make_youtube_library_subtab(), "YOUTUBE")
        v.addWidget(self._library_subtabs, 1)

        return widget

    def _make_video_library_subtab(self) -> QWidget:
        widget = QWidget()
        v = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._library_widget = QListWidget()
        self._library_widget.setObjectName("library")
        self._library_widget.itemDoubleClicked.connect(
            self._on_library_double_click
        )
        v.addWidget(self._library_widget, 1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(8, 8, 8, 8)
        btn_row.setSpacing(6)

        scan_btn = QPushButton("📁  SCAN")
        scan_btn.setObjectName("sidebarBtn")
        scan_btn.setToolTip("Scan a folder for video files")
        scan_btn.clicked.connect(self._scan_folder)

        add_all_btn = QPushButton("▶  ALL")
        add_all_btn.setObjectName("sidebarBtn")
        add_all_btn.setToolTip("Add all video library items to playlist")
        add_all_btn.clicked.connect(self._library_add_all)

        clear_lib_btn = QPushButton("✕")
        clear_lib_btn.setObjectName("sidebarBtn")
        clear_lib_btn.setToolTip("Clear video library")
        clear_lib_btn.clicked.connect(self._clear_library)

        btn_row.addWidget(scan_btn)
        btn_row.addWidget(add_all_btn)
        btn_row.addWidget(clear_lib_btn)
        v.addLayout(btn_row)

        return widget

    def _make_picture_library_subtab(self) -> QWidget:
        widget = QWidget()
        v = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._picture_library_widget = QListWidget()
        self._picture_library_widget.setObjectName("library")
        self._picture_library_widget.itemDoubleClicked.connect(
            self._on_picture_library_double_click
        )
        v.addWidget(self._picture_library_widget, 1)

        # Row 1: Scan folder + Add files
        btn_row1 = QHBoxLayout()
        btn_row1.setContentsMargins(8, 8, 8, 2)
        btn_row1.setSpacing(6)

        scan_btn = QPushButton("📁  SCAN")
        scan_btn.setObjectName("sidebarBtn")
        scan_btn.setToolTip("Scan a folder for image files")
        scan_btn.clicked.connect(self._scan_folder)

        add_pics_btn = QPushButton("🖼  ADD FILES")
        add_pics_btn.setObjectName("sidebarBtn")
        add_pics_btn.setToolTip("Add image files from a file dialog")
        add_pics_btn.clicked.connect(self._add_pictures)

        btn_row1.addWidget(scan_btn)
        btn_row1.addWidget(add_pics_btn)
        v.addLayout(btn_row1)

        # Row 2: Add all + Clear
        btn_row2 = QHBoxLayout()
        btn_row2.setContentsMargins(8, 2, 8, 8)
        btn_row2.setSpacing(6)

        add_all_btn = QPushButton("▶  ADD ALL")
        add_all_btn.setObjectName("sidebarBtn")
        add_all_btn.setToolTip("Add all pictures to playlist")
        add_all_btn.clicked.connect(self._picture_library_add_all)

        clear_btn = QPushButton("✕  CLEAR")
        clear_btn.setObjectName("sidebarBtn")
        clear_btn.setToolTip("Clear picture library")
        clear_btn.clicked.connect(self._clear_picture_library)

        btn_row2.addWidget(add_all_btn)
        btn_row2.addWidget(clear_btn)
        v.addLayout(btn_row2)

        return widget

    def _make_youtube_library_subtab(self) -> QWidget:
        widget = QWidget()
        v = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._youtube_library_widget = QListWidget()
        self._youtube_library_widget.setObjectName("library")
        self._youtube_library_widget.itemDoubleClicked.connect(
            self._on_youtube_library_double_click
        )
        v.addWidget(self._youtube_library_widget, 1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(8, 8, 8, 8)
        btn_row.setSpacing(6)

        search_btn = QPushButton("🔍  SEARCH")
        search_btn.setObjectName("sidebarBtn")
        search_btn.setToolTip("Search YouTube and add videos")
        search_btn.clicked.connect(self._youtube_search)

        add_all_btn = QPushButton("▶  ALL")
        add_all_btn.setObjectName("sidebarBtn")
        add_all_btn.setToolTip("Add all YouTube library items to playlist")
        add_all_btn.clicked.connect(self._youtube_library_add_all)

        clear_btn = QPushButton("✕")
        clear_btn.setObjectName("sidebarBtn")
        clear_btn.setToolTip("Clear YouTube library")
        clear_btn.clicked.connect(self._clear_youtube_library)

        btn_row.addWidget(search_btn)
        btn_row.addWidget(add_all_btn)
        btn_row.addWidget(clear_btn)
        v.addLayout(btn_row)

        return widget

    def _make_video_area(self) -> QWidget:
        container = QWidget()
        container.setObjectName("videoContainer")
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Stack: index 0 = video, index 1 = picture viewer
        self._media_stack = QStackedWidget()

        self._video_widget = _VideoWidget()
        self._video_widget.double_clicked.connect(self._toggle_fullscreen)
        self._video_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self._media_stack.addWidget(self._video_widget)  # index 0

        # Picture viewer page
        self._picture_scroll = QScrollArea()
        self._picture_scroll.setObjectName("pictureViewer")
        self._picture_scroll.setAlignment(Qt.AlignCenter)
        self._picture_scroll.setWidgetResizable(False)
        self._picture_scroll.setFrameShape(QFrame.NoFrame)
        self._picture_label = QLabel()
        self._picture_label.setObjectName("pictureLabel")
        self._picture_label.setAlignment(Qt.AlignCenter)
        self._picture_scroll.setWidget(self._picture_label)
        self._media_stack.addWidget(self._picture_scroll)  # index 1

        v.addWidget(self._media_stack, 1)
        return container

    def _make_control_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("controlBar")
        v = QVBoxLayout(bar)
        v.setContentsMargins(16, 8, 16, 10)
        v.setSpacing(6)

        # ── Seek row ──────────────────────────────────────────────────────
        seek_row = QHBoxLayout()
        seek_row.setSpacing(10)

        self._time_lbl = QLabel("0:00 / 0:00")
        self._time_lbl.setObjectName("timeLabel")
        seek_row.addWidget(self._time_lbl)

        self._seek_slider = _ClickableSlider(Qt.Horizontal)
        self._seek_slider.setObjectName("seekSlider")
        self._seek_slider.setRange(0, 0)
        self._seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self._seek_slider.sliderReleased.connect(self._on_seek_released)
        self._seek_slider.sliderMoved.connect(self._on_seek_moved)
        seek_row.addWidget(self._seek_slider, 1)

        v.addLayout(seek_row)

        # ── Buttons row ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self._prev_btn = self._transport_btn("⏮", "Previous  (Ctrl+Left)", self._prev_track)
        self._rew_btn  = self._transport_btn("⏪", "Rewind 10 s  (←)",     self._rewind)

        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("playBtn")
        self._play_btn.setToolTip("Play / Pause  (Space)")
        self._play_btn.clicked.connect(self._toggle_play)

        self._fwd_btn  = self._transport_btn("⏩", "Forward 10 s  (→)",    self._forward)
        self._next_btn = self._transport_btn("⏭", "Next  (Ctrl+Right)",    self._next_track)

        btn_row.addStretch()
        for w in (self._prev_btn, self._rew_btn, self._play_btn,
                  self._fwd_btn, self._next_btn):
            btn_row.addWidget(w)
        btn_row.addStretch()

        # Volume
        vol_icon = QLabel("🔊")
        vol_icon.setObjectName("volumeIcon")

        self._vol_slider = _ClickableSlider(Qt.Horizontal)
        self._vol_slider.setObjectName("volumeSlider")
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(90)
        self._vol_slider.setToolTip("Volume  (↑ / ↓)")
        self._vol_slider.valueChanged.connect(self.player.setVolume)

        # Open / Fullscreen
        open_btn = self._transport_btn("📂", "Open files  (O)",          self._open_files)
        self._fs_btn = self._transport_btn("⛶",  "Fullscreen  (F)",       self._toggle_fullscreen)

        btn_row.addWidget(vol_icon)
        btn_row.addWidget(self._vol_slider)
        btn_row.addSpacing(8)
        btn_row.addWidget(open_btn)
        btn_row.addWidget(self._fs_btn)

        v.addLayout(btn_row)

        return bar

    @staticmethod
    def _transport_btn(icon: str, tooltip: str, slot) -> QPushButton:
        btn = QPushButton(icon)
        btn.setObjectName("controlBtn")
        btn.setToolTip(tooltip)
        btn.clicked.connect(slot)
        return btn

    # ── Keyboard shortcuts ─────────────────────────────────────────────────

    def _setup_shortcuts(self) -> None:
        bindings = [
            (Qt.Key_Space,                  self._toggle_play),
            (Qt.Key_F,                      self._toggle_fullscreen),
            (Qt.Key_Escape,                 self._exit_fullscreen),
            (Qt.Key_Left,                   self._rewind),
            (Qt.Key_Right,                  self._forward),
            (Qt.CTRL + Qt.Key_Left,         self._prev_track),
            (Qt.CTRL + Qt.Key_Right,        self._next_track),
            (Qt.Key_Up,                     self._volume_up),
            (Qt.Key_Down,                   self._volume_down),
            (Qt.Key_M,                      self._toggle_mute),
            (Qt.Key_O,                      self._open_files),
            (Qt.ALT + Qt.Key_Home,          self._go_home),
        ]
        for key, slot in bindings:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(slot)

    # ── Playback control ───────────────────────────────────────────────────

    def _toggle_play(self) -> None:
        state = self.player.state()
        if state == QMediaPlayer.PlayingState:
            self.player.pause()
        elif state == QMediaPlayer.PausedState:
            self.player.play()
        elif self._playlist_paths:
            self._play_index(max(self._current_index, 0))

    def _play_index(self, index: int) -> None:
        if not (0 <= index < len(self._playlist_paths)):
            return
        self._current_index = index
        path = self._playlist_paths[index]
        media_type = self._playlist_types[index] if index < len(self._playlist_types) else "video"
        self._playlist_widget.setCurrentRow(index)

        if media_type == "image":
            self._show_picture(path)
        elif media_type == "youtube":
            self._play_youtube(path, index)
        else:
            # Local video
            self._media_stack.setCurrentIndex(0)
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            self.player.play()
            name = os.path.basename(path)
            self._now_playing_lbl.setText(name)
            self.setWindowTitle(f"{name} — Lumina Media Player")

    def _prev_track(self) -> None:
        if self._current_index > 0:
            self._play_index(self._current_index - 1)

    def _next_track(self) -> None:
        if self._current_index < len(self._playlist_paths) - 1:
            self._play_index(self._current_index + 1)

    def _rewind(self) -> None:
        self.player.setPosition(max(0, self.player.position() - 10_000))

    def _forward(self) -> None:
        self.player.setPosition(
            min(self.player.duration(), self.player.position() + 10_000)
        )

    def _volume_up(self) -> None:
        self._vol_slider.setValue(min(100, self.player.volume() + 5))

    def _volume_down(self) -> None:
        self._vol_slider.setValue(max(0, self.player.volume() - 5))

    def _toggle_mute(self) -> None:
        self.player.setMuted(not self.player.isMuted())

    # ── File / playlist operations ─────────────────────────────────────────

    def _open_files(self) -> None:
        combined_filter = (
            "Media Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm "
            "*.m4v *.mpg *.mpeg *.3gp *.ts *.m2ts *.vob *.ogv *.mxf "
            "*.asf *.rm *.rmvb "
            "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff *.tif);;"
            + VIDEO_FILTER + ";;" + IMAGE_FILTER
        )
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Media Files", "", combined_filter
        )
        if paths:
            start = len(self._playlist_paths)
            for p in paths:
                ext = os.path.splitext(p)[1].lower()
                if ext in SUPPORTED_IMAGE_EXTENSIONS:
                    self._add_to_playlist(p, "image")
                else:
                    self._add_to_playlist(p, "video")
            self._play_index(start)

    def _add_to_playlist(self, path: str, media_type: str = "video", title: str = "") -> None:
        display = title or os.path.basename(path)
        item = QListWidgetItem(display)
        item.setToolTip(path)
        self._playlist_widget.addItem(item)
        self._playlist_paths.append(path)
        self._playlist_types.append(media_type)

    def _clear_playlist(self) -> None:
        self.player.stop()
        self._playlist_widget.clear()
        self._playlist_paths.clear()
        self._playlist_types.clear()
        self._current_index = -1
        self._now_playing_lbl.setText("No media loaded")
        self.setWindowTitle("Lumina Media Player")
        self._seek_slider.setValue(0)
        self._time_lbl.setText("0:00 / 0:00")

    def _on_playlist_double_click(self, item: QListWidgetItem) -> None:
        self._play_index(self._playlist_widget.row(item))

    # ── Media library operations ───────────────────────────────────────────

    def _scan_folder(self) -> None:
        """Open a directory dialog and recursively scan for video and image files."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder to Scan", os.path.expanduser("~")
        )
        if not folder:
            return

        found_videos: list[str] = []
        found_images: list[str] = []
        for dirpath, _dirnames, filenames in os.walk(folder):
            for fname in sorted(filenames):
                ext = os.path.splitext(fname)[1].lower()
                full_path = os.path.join(dirpath, fname)
                if ext in SUPPORTED_EXTENSIONS:
                    found_videos.append(full_path)
                elif ext in SUPPORTED_IMAGE_EXTENSIONS:
                    found_images.append(full_path)

        if not found_videos and not found_images:
            QMessageBox.information(
                self,
                "No Media Found",
                f"No supported video or image files were found in:\n{folder}",
            )
            return

        # Track the scanned folder
        if folder not in self._library_folders:
            self._library_folders.append(folder)

        # Merge videos (avoid duplicates)
        existing_videos = set(self._library_paths)
        new_videos = [p for p in found_videos if p not in existing_videos]
        if new_videos:
            self._library_paths.extend(new_videos)
            self._library_paths.sort(key=lambda p: os.path.basename(p).lower())

        # Merge images (avoid duplicates)
        existing_images = set(self._picture_library_paths)
        new_images = [p for p in found_images if p not in existing_images]
        if new_images:
            self._picture_library_paths.extend(new_images)
            self._picture_library_paths.sort(key=lambda p: os.path.basename(p).lower())

        if new_videos or new_images:
            self._refresh_library_widget()
            self._save_library()

    def _refresh_library_widget(self) -> None:
        self._refresh_video_library_widget()
        self._refresh_picture_library_widget()
        self._refresh_youtube_library_widget()

    def _refresh_video_library_widget(self) -> None:
        self._library_widget.clear()
        for path in self._library_paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            self._library_widget.addItem(item)

    def _refresh_picture_library_widget(self) -> None:
        self._picture_library_widget.clear()
        for path in self._picture_library_paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            self._picture_library_widget.addItem(item)

    def _refresh_youtube_library_widget(self) -> None:
        self._youtube_library_widget.clear()
        for entry in self._youtube_library:
            dur = _fmt_yt_duration(entry.get("duration"))
            dur_str = f"  [{dur}]" if dur else ""
            title = entry.get("title", entry.get("url", "Unknown"))
            item = QListWidgetItem(f"{title}{dur_str}")
            item.setToolTip(entry.get("url", ""))
            item.setData(Qt.UserRole, entry)
            self._youtube_library_widget.addItem(item)

    def _on_library_double_click(self, item: QListWidgetItem) -> None:
        """Add the double-clicked video library item to the playlist and play it."""
        path = item.toolTip()
        if path not in self._playlist_paths:
            self._add_to_playlist(path, "video")
        index = self._playlist_paths.index(path)
        self._play_index(index)

    def _on_picture_library_double_click(self, item: QListWidgetItem) -> None:
        """Add the double-clicked picture to the playlist and display it."""
        path = item.toolTip()
        if path not in self._playlist_paths:
            self._add_to_playlist(path, "image")
        index = self._playlist_paths.index(path)
        self._play_index(index)

    def _on_youtube_library_double_click(self, item: QListWidgetItem) -> None:
        """Add the double-clicked YouTube entry to the playlist and play it."""
        entry = item.data(Qt.UserRole)
        if not entry:
            return
        url = entry.get("url", "")
        title = entry.get("title", url)
        if url not in self._playlist_paths:
            self._add_to_playlist(url, "youtube", title)
        index = self._playlist_paths.index(url)
        self._play_index(index)

    def _library_add_all(self) -> None:
        """Append all video library items to the current playlist."""
        if not self._library_paths:
            return
        start = len(self._playlist_paths)
        for path in self._library_paths:
            if path not in self._playlist_paths:
                self._add_to_playlist(path, "video")
        if self._current_index < 0 and self._playlist_paths:
            self._play_index(start)

    def _picture_library_add_all(self) -> None:
        """Append all picture library items to the current playlist."""
        if not self._picture_library_paths:
            return
        start = len(self._playlist_paths)
        for path in self._picture_library_paths:
            if path not in self._playlist_paths:
                self._add_to_playlist(path, "image")
        if self._current_index < 0 and self._playlist_paths:
            self._play_index(start)

    def _youtube_library_add_all(self) -> None:
        """Append all YouTube library items to the current playlist."""
        if not self._youtube_library:
            return
        start = len(self._playlist_paths)
        for entry in self._youtube_library:
            url = entry.get("url", "")
            title = entry.get("title", url)
            if url and url not in self._playlist_paths:
                self._add_to_playlist(url, "youtube", title)
        if self._current_index < 0 and self._playlist_paths:
            self._play_index(start)

    def _clear_library(self) -> None:
        self._library_folders.clear()
        self._library_paths.clear()
        self._library_widget.clear()
        self._save_library()

    def _clear_picture_library(self) -> None:
        self._picture_library_paths.clear()
        self._picture_library_widget.clear()
        self._save_library()

    def _clear_youtube_library(self) -> None:
        self._youtube_library.clear()
        self._youtube_library_widget.clear()
        self._save_library()

    def _save_library(self) -> None:
        """Persist the library to a JSON file."""
        data = {
            "folders": self._library_folders,
            "files": self._library_paths,
            "pictures": self._picture_library_paths,
            "youtube": self._youtube_library,
        }
        try:
            with open(LIBRARY_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except OSError:
            pass

    def _load_library(self) -> None:
        """Load the persisted library from disk (if it exists)."""
        if not os.path.isfile(LIBRARY_FILE):
            return
        try:
            with open(LIBRARY_FILE, encoding="utf-8") as fh:
                data = json.load(fh)
            self._library_folders = [
                f for f in data.get("folders", []) if isinstance(f, str)
            ]
            # Only keep video files that still exist on disk
            self._library_paths = [
                p
                for p in data.get("files", [])
                if isinstance(p, str) and os.path.isfile(p)
            ]
            # Only keep image files that still exist on disk
            self._picture_library_paths = [
                p
                for p in data.get("pictures", [])
                if isinstance(p, str) and os.path.isfile(p)
            ]
            # Load YouTube entries (URL-based, no disk check)
            self._youtube_library = [
                e
                for e in data.get("youtube", [])
                if isinstance(e, dict) and e.get("url")
            ]
            self._refresh_library_widget()
        except (OSError, json.JSONDecodeError):
            pass

    # ── Settings persistence ───────────────────────────────────────────────

    def _load_settings(self) -> dict:
        """Load settings from disk, filling in defaults for missing keys."""
        defaults = dict(_DEFAULT_SETTINGS)
        if not os.path.isfile(_SETTINGS_FILE):
            return defaults
        try:
            with open(_SETTINGS_FILE, encoding="utf-8") as fh:
                data = json.load(fh)
            for key, default_val in defaults.items():
                if key not in data:
                    data[key] = default_val
            return data
        except (OSError, json.JSONDecodeError):
            return defaults

    def _save_settings(self) -> None:
        """Persist current settings to disk."""
        try:
            with open(_SETTINGS_FILE, "w", encoding="utf-8") as fh:
                json.dump(self._settings, fh, indent=2)
        except OSError:
            pass

    def _apply_initial_settings(self) -> None:
        """Apply saved settings on startup (volume and window size only;
        display placement and fullscreen are deferred to showEvent)."""
        vol = self._settings.get("volume", 80)
        self.player.setVolume(vol)
        self._vol_slider.setValue(vol)

        # Apply window size only in windowed mode
        if self._settings.get("window_mode", "windowed") != "fullscreen":
            res = self._settings.get("resolution", [1280, 720])
            if isinstance(res, (list, tuple)) and len(res) == 2:
                self.resize(int(res[0]), int(res[1]))

    def _apply_settings(self) -> None:
        """Read settings widgets, apply all changes, and persist to disk."""
        # Volume
        vol = self._settings_vol_slider.value()
        self._settings["volume"] = vol
        self.player.setVolume(vol)
        self._vol_slider.setValue(vol)

        # Audio device (stored for backends that support device selection)
        self._settings["audio_device"] = self._audio_device_combo.currentData() or ""

        # Monitor – move window to selected screen
        display_idx = self._display_combo.currentData()
        if not isinstance(display_idx, int):
            display_idx = 0
        self._settings["display_index"] = display_idx
        screens = QApplication.screens()
        if 0 <= display_idx < len(screens):
            scr = screens[display_idx]
            geo = scr.availableGeometry()
            self.move(
                geo.x() + max(0, (geo.width() - self.width()) // 2),
                geo.y() + max(0, (geo.height() - self.height()) // 2),
            )

        # Window mode
        mode = self._window_mode_combo.currentData()
        self._settings["window_mode"] = mode
        if mode == "fullscreen" and not self._is_fullscreen:
            self._toggle_fullscreen()
        elif mode == "windowed" and self._is_fullscreen:
            self._exit_fullscreen()

        # Resolution (only meaningful in windowed mode)
        if mode == "windowed":
            res = self._resolution_combo.currentData()
            if res:
                self._settings["resolution"] = list(res)
                self.resize(res[0], res[1])

        self._save_settings()

    def _on_window_mode_changed(self, _index: int) -> None:
        """Enable or disable the resolution selector based on the chosen mode."""
        self._resolution_combo.setEnabled(
            self._window_mode_combo.currentData() == "windowed"
        )

    # ── Fullscreen ─────────────────────────────────────────────────────────

    def _toggle_fullscreen(self) -> None:
        if self._is_fullscreen:
            self._exit_fullscreen()
        else:
            self._is_fullscreen = True
            self.showFullScreen()
            self._fs_btn.setToolTip("Exit Fullscreen  (F / Esc)")
            self._cursor_timer.start(3000)

    def _exit_fullscreen(self) -> None:
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.showNormal()
            self._fs_btn.setToolTip("Fullscreen  (F)")
            self.unsetCursor()
            self._cursor_timer.stop()

    def _hide_cursor(self) -> None:
        if self._is_fullscreen:
            self.setCursor(Qt.BlankCursor)

    def mouseMoveEvent(self, event) -> None:
        if self._is_fullscreen:
            self.unsetCursor()
            self._cursor_timer.start(3000)
        super().mouseMoveEvent(event)

    def showEvent(self, event) -> None:
        """On first show: move to saved display and apply fullscreen if needed."""
        super().showEvent(event)
        if not getattr(self, "_initial_layout_applied", False):
            self._initial_layout_applied = True
            display_idx = self._settings.get("display_index", 0)
            screens = QApplication.screens()
            if isinstance(display_idx, int) and 0 <= display_idx < len(screens):
                scr = screens[display_idx]
                geo = scr.availableGeometry()
                self.move(
                    geo.x() + max(0, (geo.width() - self.width()) // 2),
                    geo.y() + max(0, (geo.height() - self.height()) // 2),
                )
            if self._settings.get("window_mode") == "fullscreen":
                QTimer.singleShot(0, self._toggle_fullscreen)

    def closeEvent(self, event) -> None:
        """Auto-save current volume and window state on exit."""
        self._settings["volume"] = self.player.volume()
        self._settings["window_mode"] = "fullscreen" if self._is_fullscreen else "windowed"
        if not self._is_fullscreen:
            sz = self.size()
            self._settings["resolution"] = [sz.width(), sz.height()]
        self._save_settings()
        super().closeEvent(event)

    # ── Player signals ─────────────────────────────────────────────────────

    def _on_state_changed(self, state: QMediaPlayer.State) -> None:
        self._play_btn.setText("⏸" if state == QMediaPlayer.PlayingState else "▶")

    def _on_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.EndOfMedia:
            # Auto-advance to next track
            if self._current_index < len(self._playlist_paths) - 1:
                self._next_track()

    def _on_position_changed(self, pos: int) -> None:
        if not self._seek_dragging:
            self._seek_slider.setValue(pos)
        self._time_lbl.setText(
            f"{_format_time(pos)} / {_format_time(self.player.duration())}"
        )

    def _on_duration_changed(self, duration: int) -> None:
        self._seek_slider.setRange(0, duration)

    def _on_error(self, error: QMediaPlayer.Error) -> None:
        if error != QMediaPlayer.NoError:
            self._now_playing_lbl.setText(f"Error: {self.player.errorString()}")

    # ── Seek slider events ─────────────────────────────────────────────────

    def _on_seek_pressed(self) -> None:
        self._seek_dragging = True

    def _on_seek_released(self) -> None:
        self._seek_dragging = False
        self.player.setPosition(self._seek_slider.value())

    def _on_seek_moved(self, value: int) -> None:
        self._time_lbl.setText(
            f"{_format_time(value)} / {_format_time(self.player.duration())}"
        )

    # ── Drag and drop ──────────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        start = len(self._playlist_paths)
        added = 0
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                ext = os.path.splitext(path)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    self._add_to_playlist(path, "video")
                    added += 1
                elif ext in SUPPORTED_IMAGE_EXTENSIONS:
                    self._add_to_playlist(path, "image")
                    added += 1
        if added:
            self._play_index(start)

    # ── Picture support ────────────────────────────────────────────────────

    def _add_pictures(self) -> None:
        """Open a file dialog to pick image files and add them to the picture library."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add Image Files", "", IMAGE_FILTER
        )
        if not paths:
            return
        existing = set(self._picture_library_paths)
        new_paths = [p for p in paths if p not in existing]
        if new_paths:
            self._picture_library_paths.extend(new_paths)
            self._picture_library_paths.sort(
                key=lambda p: os.path.basename(p).lower()
            )
            self._refresh_picture_library_widget()
            self._save_library()

    def _show_picture(self, path: str) -> None:
        """Display an image file in the picture viewer area."""
        self.player.stop()
        self._media_stack.setCurrentIndex(1)
        name = os.path.basename(path)
        self._now_playing_lbl.setText(name)
        self.setWindowTitle(f"{name} — Lumina Media Player")
        self._seek_slider.setValue(0)
        self._seek_slider.setRange(0, 0)
        self._time_lbl.setText("Image")

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._picture_label.setText(f"Cannot load image:\n{path}")
            self._current_pixmap = None
            return

        # Store the original full-resolution pixmap so resizing always scales from it
        self._current_pixmap = pixmap

        # Scale to fit the available viewport while keeping aspect ratio
        view_size = self._picture_scroll.viewport().size()
        scaled = pixmap.scaled(
            view_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self._picture_label.setPixmap(scaled)
        self._picture_label.resize(scaled.size())

    def resizeEvent(self, event) -> None:
        """Re-scale the current picture when the window is resized."""
        super().resizeEvent(event)
        if (
            self._media_stack.currentIndex() == 1
            and getattr(self, "_current_pixmap", None) is not None
            and not self._current_pixmap.isNull()
        ):
            view_size = self._picture_scroll.viewport().size()
            scaled = self._current_pixmap.scaled(
                view_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._picture_label.setPixmap(scaled)
            self._picture_label.resize(scaled.size())

    # ── YouTube support ────────────────────────────────────────────────────

    def _youtube_search(self) -> None:
        """Open the YouTube search dialog."""
        dlg = _YouTubeSearchDialog(self)
        dlg.add_to_library.connect(self._on_yt_add_to_library)
        dlg.add_to_playlist.connect(self._on_yt_add_to_playlist)
        dlg.exec_()

    def _on_yt_add_to_library(self, entries: list) -> None:
        """Add YouTube search results to the YouTube library."""
        existing_urls = {e.get("url") for e in self._youtube_library}
        added = 0
        for entry in entries:
            if entry.get("url") and entry["url"] not in existing_urls:
                self._youtube_library.append(entry)
                existing_urls.add(entry["url"])
                added += 1
        if added:
            self._refresh_youtube_library_widget()
            self._save_library()
            # Switch to YouTube sub-tab so the user sees the result
            self._library_subtabs.setCurrentIndex(2)

    def _on_yt_add_to_playlist(self, entries: list) -> None:
        """Add YouTube search results directly to the playlist."""
        start = len(self._playlist_paths)
        for entry in entries:
            url = entry.get("url", "")
            title = entry.get("title", url)
            if url and url not in self._playlist_paths:
                self._add_to_playlist(url, "youtube", title)
        if self._current_index < 0 and self._playlist_paths:
            self._play_index(start)
        # Navigate to the player page
        self._go_to_player()

    def _play_youtube(self, url: str, index: int) -> None:
        """Start a yt-dlp worker to resolve the stream URL, then play it."""
        self._media_stack.setCurrentIndex(0)
        self.player.stop()

        # Display a placeholder title while resolving
        title = ""
        if index < len(self._playlist_types):
            item = self._playlist_widget.item(index)
            if item:
                title = item.text()
        display = title or url
        self._now_playing_lbl.setText(f"⏳ Loading: {display}")
        self.setWindowTitle(f"Loading… — Lumina Media Player")

        # Cancel any previous worker — quit the thread gracefully and wait for it
        if self._yt_stream_worker is not None:
            self._yt_stream_worker.quit()
            self._yt_stream_worker.wait()
            self._yt_stream_worker = None

        self._yt_stream_worker = _YTStreamWorker(url)
        self._yt_stream_worker.stream_ready.connect(
            lambda stream_url, t=display: self._on_yt_stream_ready(stream_url, t)
        )
        self._yt_stream_worker.error.connect(self._on_yt_stream_error)
        self._yt_stream_worker.start()

    def _on_yt_stream_ready(self, stream_url: str, title: str) -> None:
        """Called when yt-dlp has resolved the YouTube stream URL."""
        self.player.setMedia(QMediaContent(QUrl(stream_url)))
        self.player.play()
        self._now_playing_lbl.setText(title)
        self.setWindowTitle(f"{title} — Lumina Media Player")

    def _on_yt_stream_error(self, msg: str) -> None:
        """Called when yt-dlp fails to resolve the stream URL."""
        self._now_playing_lbl.setText(f"YouTube error: {msg}")
        self.setWindowTitle("Lumina Media Player")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    # Enable HiDPI support (must be set before QApplication is created)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Lumina Media Player")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Lumina")

    window = MediaPlayer()
    window.setAcceptDrops(True)
    window.show()

    # If a file path is passed on the command line, open it immediately
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            path = os.path.abspath(arg)
            if os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    window._add_to_playlist(path, "video")
                elif ext in SUPPORTED_IMAGE_EXTENSIONS:
                    window._add_to_playlist(path, "image")
        if window._playlist_paths:
            window._play_index(0)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

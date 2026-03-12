#!/usr/bin/env python3
"""Lumina Media Player

A desktop video player for local video files with a Kodi Estuary-inspired GUI.
Built with PyQt5 and Qt Multimedia.
"""

from __future__ import annotations

import json
import os
import sys

from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtMultimedia import QAudio, QAudioDeviceInfo, QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
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
# Slider that jumps to the clicked position (instead of stepping)
# ---------------------------------------------------------------------------
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
        self._current_index: int = -1
        self._seek_dragging: bool = False
        self._is_fullscreen: bool = False

        # Media library: list of scanned folder paths and discovered video files
        self._library_folders: list[str] = []
        self._library_paths: list[str] = []

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

        add_all_btn = QPushButton("▶  ADD ALL")
        add_all_btn.setObjectName("sidebarBtn")
        add_all_btn.setToolTip("Add all library items to playlist")
        add_all_btn.clicked.connect(self._library_add_all)

        clear_lib_btn = QPushButton("✕")
        clear_lib_btn.setObjectName("sidebarBtn")
        clear_lib_btn.setToolTip("Clear library")
        clear_lib_btn.clicked.connect(self._clear_library)

        btn_row.addWidget(scan_btn)
        btn_row.addWidget(add_all_btn)
        btn_row.addWidget(clear_lib_btn)
        v.addLayout(btn_row)

        return widget

    def _make_video_area(self) -> QWidget:
        container = QWidget()
        container.setObjectName("videoContainer")
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._video_widget = _VideoWidget()
        self._video_widget.double_clicked.connect(self._toggle_fullscreen)
        self._video_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        v.addWidget(self._video_widget, 1)

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
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.player.play()
        self._playlist_widget.setCurrentRow(index)
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
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Video Files", "", VIDEO_FILTER
        )
        if paths:
            start = len(self._playlist_paths)
            for p in paths:
                self._add_to_playlist(p)
            self._play_index(start)

    def _add_to_playlist(self, path: str) -> None:
        name = os.path.basename(path)
        item = QListWidgetItem(name)
        item.setToolTip(path)
        self._playlist_widget.addItem(item)
        self._playlist_paths.append(path)

    def _clear_playlist(self) -> None:
        self.player.stop()
        self._playlist_widget.clear()
        self._playlist_paths.clear()
        self._current_index = -1
        self._now_playing_lbl.setText("No media loaded")
        self.setWindowTitle("Lumina Media Player")
        self._seek_slider.setValue(0)
        self._time_lbl.setText("0:00 / 0:00")

    def _on_playlist_double_click(self, item: QListWidgetItem) -> None:
        self._play_index(self._playlist_widget.row(item))

    # ── Media library operations ───────────────────────────────────────────

    def _scan_folder(self) -> None:
        """Open a directory dialog and recursively scan for video files."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder to Scan", os.path.expanduser("~")
        )
        if not folder:
            return

        found: list[str] = []
        for dirpath, _dirnames, filenames in os.walk(folder):
            for fname in sorted(filenames):
                if os.path.splitext(fname)[1].lower() in SUPPORTED_EXTENSIONS:
                    found.append(os.path.join(dirpath, fname))

        if not found:
            QMessageBox.information(
                self,
                "No Videos Found",
                f"No supported video files were found in:\n{folder}",
            )
            return

        # Add folder to tracked folders and merge new paths (avoid duplicates)
        if folder not in self._library_folders:
            self._library_folders.append(folder)

        existing = set(self._library_paths)
        new_paths = [p for p in found if p not in existing]
        if new_paths:
            self._library_paths.extend(new_paths)
            self._library_paths.sort(key=lambda p: os.path.basename(p).lower())
            self._refresh_library_widget()
            self._save_library()

    def _refresh_library_widget(self) -> None:
        self._library_widget.clear()
        for path in self._library_paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            self._library_widget.addItem(item)

    def _on_library_double_click(self, item: QListWidgetItem) -> None:
        """Add the double-clicked library item to the playlist and play it."""
        path = item.toolTip()
        if path not in self._playlist_paths:
            self._add_to_playlist(path)
        index = self._playlist_paths.index(path)
        self._play_index(index)

    def _library_add_all(self) -> None:
        """Append all library items to the current playlist."""
        if not self._library_paths:
            return
        start = len(self._playlist_paths)
        for path in self._library_paths:
            if path not in self._playlist_paths:
                self._add_to_playlist(path)
        if self._current_index < 0 and self._playlist_paths:
            self._play_index(start)

    def _clear_library(self) -> None:
        self._library_folders.clear()
        self._library_paths.clear()
        self._library_widget.clear()
        self._save_library()

    def _save_library(self) -> None:
        """Persist the library to a JSON file."""
        data = {
            "folders": self._library_folders,
            "files": self._library_paths,
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
            # Only keep files that still exist on disk
            self._library_paths = [
                p
                for p in data.get("files", [])
                if isinstance(p, str) and os.path.isfile(p)
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
                if os.path.splitext(path)[1].lower() in SUPPORTED_EXTENSIONS:
                    self._add_to_playlist(path)
                    added += 1
        if added:
            self._play_index(start)


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
                    window._add_to_playlist(path)
        if window._playlist_paths:
            window._play_index(0)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

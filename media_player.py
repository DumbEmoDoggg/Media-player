#!/usr/bin/env python3
"""Lumina Media Player

A desktop video player for local video files with a Kodi Estuary-inspired GUI.
Built with PyQt5 and Qt Multimedia.
"""

from __future__ import annotations

import os
import sys

from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStyle,
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

        # Auto-hide cursor in fullscreen
        self._cursor_timer = QTimer(self)
        self._cursor_timer.setSingleShot(True)
        self._cursor_timer.timeout.connect(self._hide_cursor)

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

        # Wire video output after widget exists
        self.player.setVideoOutput(self._video_widget)
        self.player.setVolume(80)

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._make_header())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._make_sidebar())
        splitter.addWidget(self._make_video_area())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 1040])
        layout.addWidget(splitter, 1)

        layout.addWidget(self._make_control_bar())

    def _make_header(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("headerBar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)

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

        heading = QLabel("PLAYLIST")
        heading.setObjectName("sidebarTitle")
        v.addWidget(heading)

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

        return sidebar

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

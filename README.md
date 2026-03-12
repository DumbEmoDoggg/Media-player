# Lumina Media Player

A desktop video player for local video files with a **Kodi Estuary-inspired** dark GUI, built with Python and PyQt5.

---

## Features

- 🎬 Play local video files (MP4, AVI, MKV, MOV, WMV, FLV, WebM, and more)
- 📋 Playlist with auto-advance to the next file
- 🎨 Kodi Estuary-inspired dark theme with blue accents
- ⌨️ Keyboard shortcuts for all common actions
- 🖱️ Drag and drop video files directly onto the window
- 🔊 Volume control with mute toggle
- ⏩ Seek bar, rewind, and fast-forward (±10 s)
- ⛶ Fullscreen mode with auto-hiding cursor
- 🖥️ Cross-platform: Linux and Windows

---

## Running from Source

### Prerequisites

| Platform | Requirement |
|----------|-------------|
| **Linux**   | Python 3.9+, GStreamer (`gstreamer1.0-plugins-good` and friends) |
| **Windows** | Python 3.9+, Windows 10 or later (uses Windows Media Foundation) |

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run

```bash
python media_player.py
# or pass a file directly:
python media_player.py /path/to/video.mp4
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `←` / `→` | Rewind / Forward 10 s |
| `Ctrl+←` / `Ctrl+→` | Previous / Next track |
| `↑` / `↓` | Volume up / down |
| `M` | Toggle mute |
| `F` | Toggle fullscreen |
| `Esc` | Exit fullscreen |
| `O` | Open file(s) |

---

## Building Executables

Executables are built automatically via GitHub Actions on every push to `main`/`master`.

### Download artifacts

After a successful workflow run, download the executable from the **Actions** tab
in GitHub → select the workflow run → **Artifacts** section.

| Artifact | Platform |
|----------|----------|
| `MediaPlayer-Linux` | Ubuntu/Linux (x86-64) |
| `MediaPlayer-Windows` | Windows 10+ (x86-64) |

### Build locally

```bash
pip install pyinstaller
pyinstaller --name=MediaPlayer --onefile --windowed media_player.py
# output: dist/MediaPlayer  (Linux) or dist/MediaPlayer.exe  (Windows)
```

> **Linux note:** The resulting binary relies on the system's GStreamer libraries
> for video decoding.  Install them with:
> ```bash
> sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
>                      gstreamer1.0-plugins-ugly gstreamer1.0-libav
> ```

---

## Project Structure

```
.
├── media_player.py               # Main application
├── requirements.txt              # Python dependencies
└── .github/workflows/
    ├── build-linux.yml           # Linux executable workflow
    └── build-windows.yml         # Windows executable workflow
```

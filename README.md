<p align="center">
  <img src="public/icon.svg" alt="Écrit" width="80" height="80">
</p>

<h1 align="center">Écrit</h1>

<p align="center">
  <strong>A cross-platform desktop screenplay writing app for Fountain and Fountain-derived dialects.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#building-from-source">Building</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <a href="https://github.com/FlintWave/Ecrit/actions/workflows/ci.yml"><img src="https://github.com/FlintWave/Ecrit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/FlintWave/Ecrit/releases/latest"><img src="https://img.shields.io/github/v/release/FlintWave/Ecrit" alt="Latest Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/FlintWave/Ecrit" alt="License: GPL-3.0"></a>
</p>

---

## Features

### Five-Phase Editor

Écrit guides your screenplay through five distinct phases, each with a focused workspace:

- **Plan** — Prose editor for treatments, logline builder, and story notes
- **Outline** — Visual node graph with drag-and-drop scene cards, act breaks, and structure templates (Save the Cat, Hero's Journey, Three-Act, and more)
- **Manuscript** — Courier Prime script editor with full Fountain syntax highlighting, typewriter scrolling, auto-save, and scene numbering
- **Proofread** — Read-only view with an issues rail for flagging problems
- **Deliver** — Preview with PDF/ODT/Fountain export, WGA revision tracking, and contest preset validation

### Writing Tools

- **Command Palette** (Ctrl+K) — Fuzzy search across 29 commands
- **Sprint Timer** — Timed writing sessions with 15/25/45/60-minute presets
- **Reading Mode** — Distraction-free full-screen reading
- **Scratchpad** — Clipboard for cut text with paste-back
- **Find & Replace** — Regex support, match case, replace all
- **Compare Drafts** — Side-by-side and inline diff between snapshots
- **Statistics** — Word counts, page counts, character/scene breakdowns
- **Character Sheets** — Name, occupation, wants/needs/flaw, arc, moodboard

### Screenplay Features

- **Scene Numbers** — Lock, unlock, renumber, A-numbers for inserts
- **WGA Revisions** — Full 19-color revision sequence with history tracking
- **Logline Builder** — Five madlibs-style templates with live preview
- **Structure Templates** — Seven storytelling frameworks to scaffold your outline
- **Contest Presets** — Validation for Nicholl, BBC Writersroom, Austin, PAGE, BlueCat, Sundance, Final Draft
- **Production Reports** — Scene, cast, location, day/night, and one-liner reports

### Series & Collaboration

- **Series Manager** — Multi-episode/season management with a shared series bible (characters, locations, props, themes, backstory)
- **Git Snapshots** — Local version control with create, list, and restore
- **Remote Sync** — Push/pull to GitHub, GitLab, or Codeberg
- **Cloud Export** — Export to Google Drive, iCloud, Dropbox, OneDrive, or Nextcloud
- **Share for Review** — Generate self-contained, watermarked HTML files for confidential review

### Export Formats

| Format | Details |
|--------|---------|
| **PDF** | QPrinter-based, US Letter or A4, optional title page |
| **ODT** | ODF-spec compliant for LibreOffice/Word |
| **Fountain** | Plain `.fountain` text |
| **HTML** | Watermarked review copies with dark mode |

### Themes

Switch between **Nocturne** (dark) and **Organic** (light) with a single command. Both themes are built from a shared design token system for consistent styling.

---

## Installation

### From Releases (Recommended)

Download the latest release for your platform from the [Releases page](https://github.com/FlintWave/Ecrit/releases/latest):

| Platform | Download |
|----------|----------|
| **Windows** | `Ecrit-x.x.x-win64.zip` |
| **macOS (Intel)** | `Ecrit-x.x.x-macos-x86_64.dmg` |
| **macOS (Apple Silicon)** | `Ecrit-x.x.x-macos-arm64.dmg` |
| **Linux (AppImage)** | `Ecrit-x.x.x-linux-x86_64.AppImage` |
| **Linux (.deb)** | `Ecrit-x.x.x-amd64.deb` |
| **Linux (.rpm)** | `Ecrit-x.x.x-x86_64.rpm` |

### From PyPI (coming soon)

```bash
pip install ecrit
ecrit
```

---

## Usage

### Quick Start

1. Launch Écrit
2. Click **New Project** on the Dashboard
3. Enter a title, choose a screenplay format
4. Start writing in the Manuscript phase

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Command Palette |
| `Ctrl+S` | Save |
| `Ctrl+F` | Find & Replace |
| `Ctrl+Shift+X` | Scratchpad |
| `Escape` | Exit Reading Mode |
| `Tab` | Cycle element types (in Manuscript) |

### Importing Existing Scripts

Use **Import Script** from the Dashboard or Command Palette to open any `.fountain` file as a new project.

---

## Building from Source

### Prerequisites

- **Python 3.10+**
- **Rust 1.70+** (for the native core)
- **Qt 6** (installed via PySide6)

### Setup

```bash
# Clone the repository
git clone https://github.com/FlintWave/Ecrit.git
cd Ecrit

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install Python dependencies
pip install -e ".[dev]"

# Build the Rust core
cd src-tauri
cargo build --release
cd ..

# Run the app
python -m ecrit
```

### Running Tests

```bash
# Run the full test suite (headless Qt)
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v

# Run a specific test file
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_new_features.py -v
```

On Windows, set the environment variable differently:
```powershell
$env:QT_QPA_PLATFORM="offscreen"; python -m pytest tests/ -v
```

### Project Structure

```
Ecrit/
├── ecrit/                  # Python application
│   ├── main.py             # App entry point and MainWindow
│   ├── ui/                 # PySide6 UI layer
│   │   ├── components/     # Reusable widgets (title bar, buttons, etc.)
│   │   ├── screens/        # Dashboard, Editor, New Project wizard
│   │   ├── overlays/       # Dialogs (settings, stats, command palette, etc.)
│   │   ├── styles/         # Theme tokens and stylesheet generation
│   │   └── assets/         # Fonts, icons
│   ├── screenplay/         # Screenplay domain logic
│   │   ├── scene_numbers.py
│   │   ├── revisions.py
│   │   ├── series_projects.py
│   │   └── ...
│   ├── export/             # PDF, ODT, Fountain, HTML exporters
│   ├── sync/               # Remote sync and cloud export
│   └── stores/             # Application state management
├── src-tauri/              # Rust core (PyO3)
│   └── src/
│       ├── fountain/       # Fountain parser
│       ├── project/        # Project file management
│       └── lib.rs          # PyO3 module
├── tests/                  # Test suite (517 tests)
├── openspec/               # Feature tracking and roadmap
└── public/                 # Static assets
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Overview

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the test suite (`QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## Roadmap

The full feature roadmap is tracked in [`openspec/roadmap.yaml`](openspec/roadmap.yaml). All v1.0 milestone features are implemented. Future plans include:

- Android companion app
- Real-time collaboration
- AI-assisted writing tools
- Plugin marketplace
- Localization (i18n)

---

## License

Écrit is licensed under the [GNU General Public License v3.0](LICENSE).

---

<p align="center">
  Made with ❤️ for screenwriters everywhere
</p>

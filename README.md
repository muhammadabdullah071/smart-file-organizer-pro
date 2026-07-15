# Smart File Organizer Pro

A production-grade CLI tool that **automatically organizes messy folders** into structured categories. Perfect for taming your Downloads folder, desktop, or any chaotic directory.

## Features

- **Automatic Organization** — Sort files into Images, Documents, Videos, Music, Archives, Code, and Others based on file extension
- **Safe by Default** — Dry-run mode shows a preview before making any changes
- **Duplicate Detection** — Rename conflicting filenames (`file_1.ext`, `file_2.ext`) and detect content duplicates via SHA-256 hashing
- **Configurable** — Custom categories, extensions, and behavior via `config.json`
- **Watch Mode** — Automatically organize new files as they arrive
- **Undo Support** — Revert the last organization operation
- **Rich CLI** — Colored tables, progress bars, and summary dashboards

## 💡 Why Smart File Organizer?

Managing a cluttered Downloads folder can be frustrating. Smart File Organizer automates the process by sorting files into meaningful categories while keeping every operation safe through dry-run previews and undo support.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-file-organizer-pro.git
cd smart-file-organizer-pro

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Preview what would happen (safe — no files are moved)
python main.py preview --path ~/Downloads

# Organize for real
python main.py organize --path ~/Downloads --apply

# Show statistics for a folder
python main.py stats --path ~/Downloads

# Watch a folder and auto-organize new files
python main.py watch --path ~/Downloads
```

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `organize` | Organize files into category folders (dry-run by default) |
| `preview` | Show a preview of what would be organized |
| `report` | Display the last organization report |
| `stats` | Show file statistics for a directory |
| `watch` | Watch a directory and auto-organize new files |
| `undo` | Revert the last organization operation |
| `init` | Create a default `config.json` |

### Options

```bash
python main.py organize --help
```

| Option | Description |
|--------|-------------|
| `--path, -p` | Directory to organize (overrides config) |
| `--apply, -a` | Actually move files (default is dry-run) |
| `--recursive, -r` | Scan subdirectories recursively |
| `--no-logs` | Disable logging for this run |
| `--config, -c` | Path to custom config.json |

### Examples

```bash
# Dry-run organize your Downloads folder
python main.py organize --path ~/Downloads

# Actually organize recursively
python main.py organize --path ~/Downloads --recursive --apply

# Oversized report
python main.py report

# Folder statistics
python main.py stats --path ~/Documents --recursive

# Auto-organize new files
python main.py watch --path ~/Downloads

# Undo the last organization
python main.py undo
```

## Configuration

Create a `config.json` in the project root or pass a custom path with `--config`:

```json
{
  "base_path": ".",
  "dry_run": true,
  "recursive": false,
  "create_logs": true,
  "log_level": "DEBUG",
  "remove_empty_dirs": true,
  "watch_interval": 2,
  "categories": {
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"],
    "Documents": ["pdf", "docx", "doc", "txt", "xlsx", "pptx", "csv"],
    "Videos": ["mp4", "mkv", "avi", "mov", "wmv"],
    "Music": ["mp3", "wav", "flac", "aac", "ogg"],
    "Archives": ["zip", "rar", "7z", "tar", "gz"],
    "Code": ["py", "js", "ts", "java", "cpp", "html", "css"]
  }
}
```

Run `python main.py init` to generate a default config file.

## Project Structure

```
smart-file-organizer-pro/
├── main.py                  # CLI entry point
├── config.json              # Default configuration
├── requirements.txt
├── pyproject.toml
├── core/
│   ├── organizer.py         # Main orchestration engine
│   ├── scanner.py           # File scanning and discovery
│   ├── mover.py             # Safe file moving logic
│   ├── duplicates.py        # SHA-256 hash + conflict resolution
│   ├── reporter.py          # Report generation
│   ├── config.py            # Configuration loading
│   └── categories.py        # File classification
├── utils/
│   ├── logger.py            # Logging setup
│   ├── helpers.py           # Path/size utilities
│   ├── manifest.py          # Undo manifest management
│   └── watcher.py           # Watchdog-based file watcher
├── tests/                   # Pytest test suite (90+ tests)
├── sample_messy_folder/     # Demo folder for testing
├── logs/                    # Runtime logs
└── reports/                 # Runtime reports + manifests
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=core --cov=utils
```

## Sample Output

```
== Smart File Organizer Pro ==
  Path: /Users/name/Downloads
  Mode: DRY RUN
  Recursive: False

                          Preview: 24 files to organize
+----------+----------------------+------------------------------------------+
| Category | File                 | Destination                              |
+----------+----------------------+------------------------------------------+
| Images   | vacation_photo.jpg   | /Users/name/Downloads/Images/            |
| Documents| report.pdf           | /Users/name/Downloads/Documents/         |
| Videos   | tutorial.mp4         | /Users/name/Downloads/Videos/            |
| Music    | song.mp3             | /Users/name/Downloads/Music/             |
| Archives | project.zip          | /Users/name/Downloads/Archives/          |
| Code     | script.py            | /Users/name/Downloads/Code/              |
| Others   | unknown.xyz          | /Users/name/Downloads/Others/            |
+----------+----------------------+------------------------------------------+

Total: 24 files, 156.3 MB

+------------------------- Smart File Organizer Pro --------------------------+
| Summary Dashboard                                                           |
|                                                                             |
| Base path: /Users/name/Downloads                                            |
| Files scanned: 24                                                           |
| Files moved: 24                                                             |
| Files skipped: 0                                                            |
| Duplicates (renamed): 0                                                     |
| Content duplicates: 0                                                       |
| Errors: 0                                                                   |
| Time: 0.15s                                                                 |
+-----------------------------------------------------------------------------+
```

## License

MIT

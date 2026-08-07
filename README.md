# WordBox

A desktop vocabulary trainer built around the Leitner spaced-repetition system. Organize words into folders, review them on a schedule that adapts to how well you know them, and let related "derivation" words unlock automatically once their root word matures.

> 🤖 **Built with vibe-coding.** This app was prompted into existence with Claude Code — a paragraph of spec went in, working code came out, and every feature since was iterated on entirely through conversation. No hand-written boilerplate was harmed in the making of this repo.

## Features

- **Leitner spaced repetition** across 5 levels, with review intervals of 1, 2, 4, 9, and 14 days
- **Independent folders** — organize vocabulary however you like; each folder progresses on its own
- **Derivation words** — attach related words (e.g. `grow` → `grow up`) to a root word at any time; they stay pending until the root reaches Level 4, then activate automatically and progress independently from then on
- **Folder-first daily review** — see how many words are due in each folder before jumping into a review session
- **Known words archive** — words that pass three consecutive reviews at Level 5 graduate out of the review cycle
- Add/delete folders and words, with derivation links preserved (not deleted) when a root word is removed
- Fully local, SQLite-backed — no accounts, no network calls, no telemetry

## Tech Stack

- Python 3.9+
- [PySide6](https://doc.qt.io/qtforpython/) for the desktop UI
- SQLite for local storage

## Getting Started

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
app/
  srs.py           # Leitner level rules and date math (pure, unit-tested)
  database.py      # SQLite schema and CRUD layer
  ui/               # PySide6 widgets and dialogs
tests/              # pytest suite for srs.py and database.py
main.py             # entry point
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/
```

# `stampt`

*A minimal daily notes tool for your terminal.*

---

## ✍️ What is it?

`stampt` is a dead-simple CLI tool for capturing quick thoughts, logs, or ideas. Each note you write gets saved into its own timestamped Markdown file inside a `stampt/` folder — organized, portable, and yours forever.

It’s perfect for journaling, debugging logs, working session notes, or late-night brain dumps.

---

## 🚀 How it works

stampt
→ Opens a clean TUI for writing notes
→ Hit Enter twice to save
→ Press Ctrl+X to keep typing past blank lines

stampt add "note"
→ Instantly adds a one-liner note without opening the TUI

Inside the TUI, type:

`copy
→ Copies your last note to the clipboard

All notes are stored in ./stampt/YYYY-MM-DD_HH-MM-SS.md, right where you run the tool.

## 📦 Installation

[get yanked](https://github.com/codinganovel/yanked)

## 🐌 Performance note (pun intended)

If you end up with hundreds or thousands of notes in the stampt/ folder, the app may start to slow down slightly while looking for the most recent note. That’s because it currently sorts all files by timestamp on each launch.

I plan to add a workaround in a future version (likely using a latest.txt pointer file).
Until then, feel free to clean up your stampt/ folder once in a while.
Or don’t — and accept that a few hundred existential ramblings might slow you down.
That’s life.
## 🛠️ Features (v0.1)

Multi-line note input
Ctrl+X support for inserting blank lines
add command for quick automation
Clipboard copy of your last note
Versioned filenames (no overwrites!)
Cross-platform, zero dependencies (except pyperclip)
🧱 Built with

Python 3.6+
argparse, Pathlib, pyperclip

## 📄 License

under ☕️, check out [the-coffee-license](https://github.com/codinganovel/The-Coffee-License)

I've included both licenses with the repo, do what you know is right. The licensing works by assuming your operating under good faith.

— make it yours, fork it, hack it, ship it. made by sam.

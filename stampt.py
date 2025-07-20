#!/usr/bin/env python3
"""
stampt – timestamped markdown notes CLI
A minimal daily notes tool for your terminal.
"""

# ───────────────────────── Imports & config ─────────────────────────
import argparse
import datetime as _dt
import os
import platform
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

# Handle platform-specific imports
try:
    import termios
    import tty
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False

# Handle optional clipboard dependency
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

VERSION = "0.2.0"
STAMPT_DIRNAME = "stampt"  # folder created in the CWD


# ────────────────── Folder & filename utilities ────────────────────
def ensure_stampt_dir(base: Path) -> Path:
    """Create stampt directory if it doesn't exist."""
    path = base / STAMPT_DIRNAME
    try:
        path.mkdir(exist_ok=True)
        return path
    except PermissionError:
        print(f"❌ Permission denied creating directory: {path}")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Error creating directory {path}: {e}")
        sys.exit(1)


def _now_ts() -> str:
    """Generate current timestamp string."""
    return _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _free_filename(directory: Path, base: str) -> Path:
    """Find available filename with version suffix if needed."""
    path = directory / f"{base}.md"
    if not path.exists():
        return path
    for i in range(1, 1000):
        cand = directory / f"{base}_v{i}.md"
        if not cand.exists():
            return cand
    raise RuntimeError("Too many versions this second!")


def save_note(directory: Path, text: str) -> Path:
    """Save note to timestamped file."""
    if not text or not text.strip():
        print("⚠️  Cannot save empty note.")
        return None
    
    try:
        p = _free_filename(directory, _now_ts())
        p.write_text(text.strip() + "\n", encoding="utf-8")
        return p
    except PermissionError:
        print(f"❌ Permission denied writing to: {p}")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Error writing file: {e}")
        sys.exit(1)


# ─────────────── Cross-platform "newest file" helper ───────────────
_TS = re.compile(r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})")


def _parse_ts(name: str) -> Optional[float]:
    """Parse timestamp from filename."""
    m = _TS.match(name)
    if not m:
        return None
    try:
        return _dt.datetime.strptime(m.group(1), "%Y-%m-%d_%H-%M-%S").timestamp()
    except ValueError:
        return None


def newest_note(directory: Path) -> Optional[Path]:
    """Find the most recent note file."""
    try:
        files = list(directory.glob("*.md"))
        with_ts = [(f, _parse_ts(f.name)) for f in files]
        valid = [(f, ts) for f, ts in with_ts if ts is not None]
        return max(valid, key=lambda x: x[1])[0] if valid else None
    except OSError as e:
        print(f"❌ Error reading directory: {e}")
        return None


def search_notes(directory: Path, query: str) -> List[Path]:
    """Search for notes containing the query string."""
    if not query.strip():
        return []
    
    matching_files = []
    query_lower = query.lower()
    
    try:
        for file_path in directory.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    matching_files.append(file_path)
            except (OSError, UnicodeDecodeError):
                # Skip files we can't read
                continue
    except OSError:
        print("❌ Error searching directory")
        return []
    
    # Sort by timestamp (newest first)
    with_ts = [(f, _parse_ts(f.name)) for f in matching_files]
    valid = [(f, ts) for f, ts in with_ts if ts is not None]
    return [f for f, ts in sorted(valid, key=lambda x: x[1], reverse=True)]


# ───────────────────── Clipboard convenience ───────────────────────
def copy_last(directory: Path) -> None:
    """Copy most recent note to clipboard."""
    if not HAS_CLIPBOARD:
        print("⚠️  Clipboard not available. Install pyperclip: pip install pyperclip")
        return
    
    note = newest_note(directory)
    if not note:
        print("⚠️  No notes yet.")
        return
    
    try:
        content = note.read_text(encoding="utf-8")
        pyperclip.copy(content)
        print(f"📋 Copied {note.name} to clipboard.")
    except Exception as e:
        print(f"❌ Error copying to clipboard: {e}")


# ───────── Ctrl-X / Enter prompt after blank line ─────────
def prompt_blank_line_action() -> str:
    """Prompt user for action after blank line."""
    blue_text = "\033[36m"
    gray_text = "\033[90m"
    reset = "\033[0m"
    print(f"{gray_text}[{blue_text}Enter{gray_text}] to save  •  [{blue_text}Ctrl+X{gray_text}] to keep typing{reset}")
    
    if not HAS_TERMIOS:
        # Fallback for Windows/systems without termios
        try:
            response = input(f"{blue_text}Press Enter to save, or type 'x' to continue: {reset}").strip().lower()
            return "ctrlx" if response == 'x' else "enter"
        except (EOFError, KeyboardInterrupt):
            return "enter"
    
    # Unix-like systems with termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x18":  # Ctrl+X
            return "ctrlx"
        return "enter"
    except (OSError, termios.error):
        return "enter"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ───────────────────────── Screen helpers ─────────────────────────
def clear() -> None:
    """Clear terminal screen."""
    os.system("cls" if platform.system() == "Windows" else "clear")


def show_dashboard(directory: Path) -> None:
    """Display the main dashboard."""
    clear()
    # Blue theme colors
    blue_border = "\033[94m"  # Bright blue
    blue_text = "\033[36m"    # Cyan
    white_text = "\033[97m"   # Bright white
    gray_text = "\033[90m"    # Dark gray
    reset = "\033[0m"         # Reset colors
    
    print(f"{blue_border}╔═ {blue_text}stampt{blue_border} ═════════════════════════════════════════════╗{reset}")
    last = newest_note(directory)
    if last:
        print(f"{blue_border}║{reset} {gray_text}Last note: {last.name}{reset}")
        print(f"{blue_border}╠" + "─" * 55 + f"╗{reset}")
        try:
            content = last.read_text(encoding="utf-8").rstrip()
            # Apply subtle blue tint to content
            print(f"{blue_text}{content}{reset}")
        except (OSError, UnicodeDecodeError):
            print("❌ Error reading note file")
    else:
        print(f"{blue_border}║{reset} {gray_text}(no notes yet){reset}")
    print(f"{blue_border}╚" + "═" * 55 + f"╝{reset}")
    print(f"\n{gray_text}Commands:{reset} {blue_text}copy{reset}  •  {blue_text}list{reset}  •  {blue_text}search <term>{reset}  •  {blue_text}/term{reset}  •  {blue_text}exit{reset}  •  {gray_text}<anything else> = new note{reset}\n")


# ──────────────────────── Command handlers ────────────────────────
def show_last_note(stampt_dir: Path) -> None:
    """Show the most recent note."""
    note = newest_note(stampt_dir)
    if not note:
        print("⚠️  No notes yet.")
        return
    
    blue_text = "\033[36m"
    gray_text = "\033[90m"
    white_text = "\033[97m"
    reset = "\033[0m"
    
    try:
        content = note.read_text(encoding="utf-8")
        print(f"{blue_text}📝 {white_text}{note.name}{reset}")
        print(f"{gray_text}" + "─" * 50 + f"{reset}")
        print(f"{blue_text}{content.rstrip()}{reset}")
    except (OSError, UnicodeDecodeError):
        print(f"❌ Error reading {note.name}")


def list_notes(directory: Path, limit: int = 20) -> None:
    """List recent notes with previews."""
    blue_text = "\033[36m"
    gray_text = "\033[90m"
    white_text = "\033[97m"
    reset = "\033[0m"
    
    try:
        files = list(directory.glob("*.md"))
        with_ts = [(f, _parse_ts(f.name)) for f in files]
        valid = [(f, ts) for f, ts in with_ts if ts is not None]
        sorted_files = [f for f, ts in sorted(valid, key=lambda x: x[1], reverse=True)]
        
        if not sorted_files:
            print("⚠️  No notes yet.")
            return
            
        print(f"{blue_text}📝 {white_text}{len(sorted_files)}{blue_text} note(s) (showing latest {min(limit, len(sorted_files))}){reset}")
        print(f"{gray_text}" + "─" * 60 + f"{reset}")
        
        for note in sorted_files[:limit]:
            try:
                content = note.read_text(encoding="utf-8")
                preview = content.split('\n')[0]
                if len(preview) > 60:
                    preview = preview[:57] + "..."
                print(f"{blue_text}📝 {white_text}{note.name}{reset}")
                print(f"{gray_text}   {preview}{reset}")
                print()
            except (OSError, UnicodeDecodeError):
                print(f"❌ Error reading {note.name}")
    except OSError:
        print("❌ Error listing notes")


def search_and_display(stampt_dir: Path, query: str) -> None:
    """Search notes and display results."""
    matches = search_notes(stampt_dir, query)
    
    blue_text = "\033[36m"
    gray_text = "\033[90m"
    white_text = "\033[97m"
    reset = "\033[0m"
    
    if not matches:
        print(f"{blue_text}🔍 No notes found matching '{white_text}{query}{blue_text}'{reset}")
        return
    
    print(f"{blue_text}🔍 Found {white_text}{len(matches)}{blue_text} note(s) matching '{white_text}{query}{blue_text}':{reset}")
    print(f"{gray_text}" + "─" * 50 + f"{reset}")
    
    for note in matches[:10]:  # Limit to 10 results
        try:
            content = note.read_text(encoding="utf-8")
            # Show first line or first 80 chars
            preview = content.split('\n')[0]
            if len(preview) > 80:
                preview = preview[:77] + "..."
            
            print(f"{blue_text}📝 {white_text}{note.name}{reset}")
            print(f"{gray_text}   {preview}{reset}")
            print()
        except (OSError, UnicodeDecodeError):
            print(f"❌ Error reading {note.name}")


# ──────────────────────── Interactive loop ────────────────────────
def tui_loop(stampt_dir: Path) -> None:
    """Main interactive loop."""
    try:
        while True:
            show_dashboard(stampt_dir)
            try:
                cmd = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Bye!")
                break

            # --- top-level commands ---
            if cmd.lower() in {"exit", "quit", ":q"}:
                print("👋 Bye!")
                break
            if cmd.lower() == "copy":
                copy_last(stampt_dir)
                time.sleep(1)
                continue  # immediate refresh
            if cmd.lower() == "list":
                list_notes(stampt_dir)
                input("\nPress Enter to continue...")
                continue
            
            # Search commands
            if cmd.lower().startswith("search ") or cmd.lower().startswith("/"):
                query = cmd[7:] if cmd.startswith("search ") else cmd[1:]
                if query.strip():
                    search_and_display(stampt_dir, query.strip())
                    input("\nPress Enter to continue...")
                continue

            # --- start multi-line note ---
            lines: List[str] = []
            if cmd:
                lines.append(cmd)

            try:
                while True:
                    line = input()
                    if line.strip() == "":
                        action = prompt_blank_line_action()
                        if action == "ctrlx":
                            lines.append("")
                            continue
                        break
                    lines.append(line)
            except (EOFError, KeyboardInterrupt):
                if lines:
                    print("\n💾 Saving draft...")
                    save_note(stampt_dir, "\n".join(lines))
                print("👋 Bye!")
                break

            if lines:
                saved_path = save_note(stampt_dir, "\n".join(lines))
                if saved_path:
                    blue_text = "\033[36m"
                    white_text = "\033[97m"
                    reset = "\033[0m"
                    print(f"{blue_text}✅ Saved: {white_text}{saved_path.name}{reset}")
                    time.sleep(0.5)
                # immediately loops back for fresh dashboard
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Your notes are safe in the stampt/ folder.")


# ───────────────────────────── CLI entry ───────────────────────────
def make_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    p = argparse.ArgumentParser(
        prog="stampt", 
        description="A minimal daily notes tool for your terminal."
    )
    p.add_argument("--version", action="version", version=f"stampt {VERSION}")
    
    sub = p.add_subparsers(dest="cmd", required=False)

    # Add command
    add = sub.add_parser("add", help="Add one-line note without opening TUI")
    add.add_argument("note", nargs="+", help="Text of the note")

    # Last command
    sub.add_parser("last", help="Show the most recent note")

    # List command
    sub.add_parser("list", help="List all notes (newest first)")

    # Search command
    search = sub.add_parser("search", help="Search through notes")
    search.add_argument("query", help="Search term")
    
    return p


def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point."""
    try:
        ns = make_parser().parse_args(argv)
        dir_ = ensure_stampt_dir(Path.cwd())

        if ns.cmd == "add":
            note_text = " ".join(ns.note)
            saved_path = save_note(dir_, note_text)
            if saved_path:
                blue_text = "\033[36m"
                white_text = "\033[97m"
                reset = "\033[0m"
                print(f"{blue_text}✅ Added: {white_text}{saved_path.name}{reset}")
        elif ns.cmd == "last":
            show_last_note(dir_)
        elif ns.cmd == "list":
            list_notes(dir_)
        elif ns.cmd == "search":
            search_and_display(dir_, ns.query)
        else:
            tui_loop(dir_)
    except KeyboardInterrupt:
        print("\n👋 Bye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
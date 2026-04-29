"""Command-line entry point for ``adr``.

Subcommands:

* ``adr init``                — initialise an ADR directory
* ``adr new "<title>"``       — create a new ADR
* ``adr list``                — list every ADR
* ``adr show <num>``          — print one ADR to stdout
* ``adr supersede <a> <b>``   — mark ADR ``a`` as superseded by ADR ``b``
* ``adr index``               — refresh the directory README
* ``adr graph``               — emit a Mermaid supersession graph
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from .graph import render_mermaid
from .index import render_index
from .parser import (
    Adr,
    discover_adrs,
    find_by_number,
    next_number,
)
from .templates import (
    AdrConfig,
    DEFAULT_FORMAT,
    VALID_FORMATS,
    render_filename,
    render_starter_adr,
    render_template,
    write_template_file,
)


DEFAULT_DIR = Path("docs/adr")


# ---- helpers ----------------------------------------------------------------

def _adr_dir(args: argparse.Namespace) -> Path:
    """Resolve the ADR directory from --dir, $ADR_DIR, or the default."""
    if getattr(args, "dir", None):
        return Path(args.dir)
    env = os.environ.get("ADR_DIR")
    if env:
        return Path(env)
    return DEFAULT_DIR


def _err(msg: str) -> int:
    print(f"adr: error: {msg}", file=sys.stderr)
    return 2


# ---- subcommands ------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
    adr_dir = _adr_dir(args)
    adr_dir.mkdir(parents=True, exist_ok=True)

    fmt = args.format or DEFAULT_FORMAT
    if fmt not in VALID_FORMATS:
        return _err(f"unknown --format {fmt!r}; expected one of {VALID_FORMATS}")

    # Write the template file for reference.
    write_template_file(adr_dir, fmt)

    # Persist the format choice.
    (adr_dir / ".adrconfig").write_text(f"format: {fmt}\n", encoding="utf-8")

    # If the directory already has ADRs, don't write a starter — assume the
    # user is bringing their own.
    existing = discover_adrs(adr_dir)
    if not existing:
        starter = render_starter_adr(fmt=fmt)
        starter_path = adr_dir / render_filename(1, "Record architecture decisions")
        starter_path.write_text(starter, encoding="utf-8")
        print(f"Initialised ADR directory at {adr_dir}")
        print(f"Created {starter_path} (Accepted)")
    else:
        print(f"Refreshed config in {adr_dir} (found {len(existing)} existing ADRs)")

    # Always (re)render the index.
    _write_index(adr_dir)
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    adr_dir = _adr_dir(args)
    if not adr_dir.exists():
        return _err(
            f"ADR directory {adr_dir} does not exist. Run `adr init` first."
        )

    config = AdrConfig.load(adr_dir)
    fmt = args.format or config.format
    if fmt not in VALID_FORMATS:
        return _err(f"unknown --format {fmt!r}; expected one of {VALID_FORMATS}")

    title = " ".join(args.title).strip() if isinstance(args.title, list) else str(args.title).strip()
    if not title:
        return _err("title may not be empty")

    adrs = discover_adrs(adr_dir)
    number = next_number(adrs)
    body = render_template(fmt=fmt, number=number, title=title)
    path = adr_dir / render_filename(number, title)

    if path.exists():
        return _err(f"refusing to overwrite {path}")

    path.write_text(body, encoding="utf-8")
    print(f"Created {path} (Proposed)")
    _write_index(adr_dir)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    adr_dir = _adr_dir(args)
    adrs = discover_adrs(adr_dir)
    if not adrs:
        print(f"No ADRs found in {adr_dir}.")
        return 0
    width = max(len(a.title) for a in adrs)
    for adr in adrs:
        suffix = ""
        if adr.superseded_by is not None:
            suffix = f"  (by {adr.superseded_by:04d})"
        print(f"{adr.number_str}  {adr.status:<10}  {adr.title:<{width}}{suffix}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    adr_dir = _adr_dir(args)
    adrs = discover_adrs(adr_dir)
    target = find_by_number(adrs, int(args.number))
    if target is None:
        return _err(f"no ADR with number {args.number}")
    print(target.path.read_text(encoding="utf-8"))
    return 0


def cmd_supersede(args: argparse.Namespace) -> int:
    adr_dir = _adr_dir(args)
    adrs = discover_adrs(adr_dir)
    old_num, new_num = int(args.old), int(args.new)
    old = find_by_number(adrs, old_num)
    new = find_by_number(adrs, new_num)
    if old is None:
        return _err(f"no ADR with number {old_num}")
    if new is None:
        return _err(
            f"Hold on — {new_num:04d} doesn't exist yet. "
            "Create it first with `adr new`."
        )
    if old_num == new_num:
        return _err("an ADR cannot supersede itself")

    _mark_superseded(old, new)
    _add_supersedes_link(new, old)
    print(f"Marked {old.number_str} as superseded by {new.number_str}.")
    _write_index(adr_dir)
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    adr_dir = _adr_dir(args)
    if not adr_dir.exists():
        return _err(f"ADR directory {adr_dir} does not exist")
    path = _write_index(adr_dir)
    print(f"Wrote {path}")
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    adr_dir = _adr_dir(args)
    adrs = discover_adrs(adr_dir)
    text = render_mermaid(adrs)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        sys.stdout.write(text)
    return 0


# ---- file mutation helpers --------------------------------------------------

def _write_index(adr_dir: Path) -> Path:
    adrs = discover_adrs(adr_dir)
    text = render_index(adrs)
    path = adr_dir / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


_STATUS_BLOCK_RE = re.compile(
    r"(##\s+Status\s*\n+)(?P<body>.+?)(?=\n##\s|\Z)",
    re.DOTALL,
)


def _mark_superseded(old: Adr, new: "Adr") -> None:
    """Update ``old``'s Status section to record the supersession."""
    text = old.path.read_text(encoding="utf-8")
    today = date.today().isoformat()
    new_status = (
        f"Superseded by [{new.number_str}](./{new.path.name}) on {today}\n\n"
    )

    def _replace(match: re.Match) -> str:
        return match.group(1) + new_status

    new_text, n = _STATUS_BLOCK_RE.subn(_replace, text, count=1)
    if n == 0:
        # No status section — append one.
        new_text = text.rstrip() + "\n\n## Status\n\n" + new_status
    old.path.write_text(new_text, encoding="utf-8")


def _add_supersedes_link(new: Adr, old: Adr) -> None:
    """Note in ``new``'s body that it supersedes ``old``."""
    text = new.path.read_text(encoding="utf-8")
    note = f"\nSupersedes [{old.number_str}](./{old.path.name})\n"
    if note.strip() in text:
        return  # already linked
    # Insert just after the Status section, or append at the end.
    if "## Status" in text:
        # Append note inside the Status section.
        def _replace(match: re.Match) -> str:
            existing = match.group("body").rstrip()
            return match.group(1) + existing + "\n" + note + "\n"

        new_text, n = _STATUS_BLOCK_RE.subn(_replace, text, count=1)
        if n == 0:
            new_text = text.rstrip() + "\n" + note
    else:
        new_text = text.rstrip() + "\n" + note
    new.path.write_text(new_text, encoding="utf-8")


# ---- argparse glue ----------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="adr",
        description="Manage Architecture Decision Records (ADRs).",
    )
    p.add_argument("--version", action="version", version=f"adr-toolkit {__version__}")
    p.add_argument(
        "--dir",
        help="ADR directory (default: docs/adr, or $ADR_DIR)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s_init = sub.add_parser("init", help="initialise an ADR directory")
    s_init.add_argument("--format", choices=VALID_FORMATS, help="template format")
    s_init.set_defaults(func=cmd_init)

    s_new = sub.add_parser("new", help="create a new ADR")
    s_new.add_argument("title", nargs="+", help="ADR title (quoted or unquoted)")
    s_new.add_argument("--format", choices=VALID_FORMATS, help="override template format")
    s_new.set_defaults(func=cmd_new)

    s_list = sub.add_parser("list", help="list all ADRs with status")
    s_list.set_defaults(func=cmd_list)

    s_show = sub.add_parser("show", help="print a single ADR to stdout")
    s_show.add_argument("number", help="ADR number, e.g. 7 or 0007")
    s_show.set_defaults(func=cmd_show)

    s_sup = sub.add_parser("supersede", help="mark one ADR as superseded by another")
    s_sup.add_argument("old", help="number of the ADR being superseded")
    s_sup.add_argument("new", help="number of the ADR doing the superseding")
    s_sup.set_defaults(func=cmd_supersede)

    s_idx = sub.add_parser("index", help="regenerate the ADR README index")
    s_idx.set_defaults(func=cmd_index)

    s_graph = sub.add_parser("graph", help="emit a Mermaid supersession graph")
    s_graph.add_argument("--output", "-o", help="write to file instead of stdout")
    s_graph.set_defaults(func=cmd_graph)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

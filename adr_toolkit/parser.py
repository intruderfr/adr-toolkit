"""Parse existing ADR markdown files into a structured ``Adr`` record.

We deliberately avoid any external markdown library — ADRs follow a small
predictable shape, so a few regular expressions get us 99% of the way there
without dragging in a parser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional


VALID_STATUSES = ("Proposed", "Accepted", "Superseded", "Deprecated", "Rejected")

# Filename like "0007-use-postgresql-for-primary-database.md"
_FILENAME_RE = re.compile(r"^(?P<num>\d{3,5})-(?P<slug>[a-z0-9][a-z0-9-]*)\.md$")

# Heading like "# 0007. Use PostgreSQL for primary database"
_HEADING_RE = re.compile(r"^#\s+(?P<num>\d{3,5})\.\s+(?P<title>.+?)\s*$", re.MULTILINE)

# "Superseded by [0010](0010-...)" or "Superseded by 0010"
_SUPERSEDED_BY_RE = re.compile(
    r"[Ss]uperseded\s+by\s+(?:\[)?(?P<num>\d{3,5})", re.MULTILINE
)

# "Supersedes [0003](...)" or "Supersedes 0003"
_SUPERSEDES_RE = re.compile(
    r"[Ss]upersedes\s+(?:\[)?(?P<num>\d{3,5})", re.MULTILINE
)


@dataclass
class Adr:
    """A parsed ADR document."""

    number: int
    title: str
    status: str
    path: Path
    superseded_by: Optional[int] = None
    supersedes: List[int] = field(default_factory=list)

    @property
    def number_str(self) -> str:
        return f"{self.number:04d}"


def _extract_status(body: str) -> str:
    """Pull the value of the ``## Status`` section."""
    m = re.search(r"^##\s+Status\s*\n+(?P<rest>.+?)(?:\n##\s|\Z)", body,
                  re.MULTILINE | re.DOTALL)
    if not m:
        return "Unknown"
    rest = m.group("rest").strip()
    # Status section may be just "Accepted", or "Accepted\n\nSuperseded by 0010"
    first_line = rest.splitlines()[0].strip()
    # Common patterns
    for status in VALID_STATUSES:
        if first_line.lower().startswith(status.lower()):
            return status
    # If the first line says "Superseded by ..." treat as Superseded
    if first_line.lower().startswith("superseded"):
        return "Superseded"
    return first_line or "Unknown"


def parse_adr(path: Path) -> Optional[Adr]:
    """Parse a single ADR file. Returns ``None`` for files that don't match."""
    name = path.name
    m = _FILENAME_RE.match(name)
    if not m:
        return None
    number = int(m.group("num"))

    body = path.read_text(encoding="utf-8")

    title = "(untitled)"
    h = _HEADING_RE.search(body)
    if h:
        title = h.group("title").strip()

    status = _extract_status(body)

    superseded_by: Optional[int] = None
    sb = _SUPERSEDED_BY_RE.search(body)
    if sb:
        superseded_by = int(sb.group("num"))

    supersedes: List[int] = []
    for sm in _SUPERSEDES_RE.finditer(body):
        n = int(sm.group("num"))
        if n not in supersedes:
            supersedes.append(n)

    return Adr(
        number=number,
        title=title,
        status=status,
        path=path,
        superseded_by=superseded_by,
        supersedes=supersedes,
    )


def discover_adrs(adr_dir: Path) -> List[Adr]:
    """Return all parseable ADRs in ``adr_dir``, sorted by number."""
    if not adr_dir.exists():
        return []
    adrs: List[Adr] = []
    for entry in sorted(adr_dir.iterdir()):
        if not entry.is_file():
            continue
        # Skip templates and the generated index
        if entry.name.startswith("template-"):
            continue
        if entry.name.lower() == "readme.md":
            continue
        adr = parse_adr(entry)
        if adr is not None:
            adrs.append(adr)
    adrs.sort(key=lambda a: a.number)
    return adrs


def next_number(adrs: Iterable[Adr]) -> int:
    """Return the next free ADR number (one greater than current max, or 1)."""
    nums = [a.number for a in adrs]
    return max(nums) + 1 if nums else 1


def find_by_number(adrs: Iterable[Adr], number: int) -> Optional[Adr]:
    for a in adrs:
        if a.number == number:
            return a
    return None

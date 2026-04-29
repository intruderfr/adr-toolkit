"""Built-in ADR templates and config helpers.

We support two well-known formats:

* MADR (Markdown ADR) — the modern standard, with explicit sections for
  decision drivers, considered options, and consequences. Default.
* Nygard — the original Michael Nygard format. Terser, four sections.

Both formats produce plain markdown so they render anywhere — GitHub,
Bitbucket, Confluence, mkdocs, you name it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional


VALID_FORMATS = ("madr", "nygard")
DEFAULT_FORMAT = "madr"
CONFIG_FILENAME = ".adrconfig"


@dataclass
class AdrConfig:
    """Per-directory config, read from ``.adrconfig`` if present."""

    format: str = DEFAULT_FORMAT

    @classmethod
    def load(cls, adr_dir: Path) -> "AdrConfig":
        path = adr_dir / CONFIG_FILENAME
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Fall back to a tiny key:value parser so the file can be hand-edited
            data = _parse_simple_config(path.read_text(encoding="utf-8"))
        fmt = str(data.get("format", DEFAULT_FORMAT)).strip().lower()
        if fmt not in VALID_FORMATS:
            fmt = DEFAULT_FORMAT
        return cls(format=fmt)


def _parse_simple_config(text: str) -> dict:
    """Tolerant ``key: value`` / ``key = value`` parser for hand-edited configs."""
    out: dict = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*[:=]\s*(.+?)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip("\"'")
    return out


def slugify(title: str) -> str:
    """Turn a title into a kebab-case slug suitable for a filename."""
    text = title.lower().strip()
    # Replace anything that isn't alnum or whitespace with a space
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    # Collapse whitespace and hyphens to single hyphens
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    return text or "adr"


def render_filename(number: int, title: str) -> str:
    return f"{number:04d}-{slugify(title)}.md"


# ---- Templates --------------------------------------------------------------

_MADR_TEMPLATE = """# {number}. {title}

Date: {date}

## Status

{status}

## Context and problem statement

<!-- Describe the architectural problem and the forces at play. What's the
context? What constraints do we have? Why is this decision worth recording? -->

## Decision drivers

- <!-- driver 1, e.g. operational cost -->
- <!-- driver 2, e.g. team familiarity -->

## Considered options

- <!-- option A -->
- <!-- option B -->

## Decision outcome

Chosen option: "<!-- option -->", because <!-- justification -->.

### Positive consequences

- <!-- e.g. easier to operate -->

### Negative consequences

- <!-- e.g. extra training cost -->

## Links

<!-- Optional: links to PRs, RFCs, related ADRs -->
"""


_NYGARD_TEMPLATE = """# {number}. {title}

Date: {date}

## Status

{status}

## Context

<!-- What is the issue we are facing? -->

## Decision

<!-- What is the change we are making? -->

## Consequences

<!-- What becomes easier or more difficult because of this change? -->
"""


def render_template(
    *,
    fmt: str,
    number: int,
    title: str,
    today: Optional[date] = None,
    status: str = "Proposed",
) -> str:
    """Render a brand new ADR body for the given format."""
    if fmt not in VALID_FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {VALID_FORMATS}")
    template = _MADR_TEMPLATE if fmt == "madr" else _NYGARD_TEMPLATE
    return template.format(
        number=f"{number:04d}",
        title=title,
        date=(today or date.today()).isoformat(),
        status=status,
    )


def render_starter_adr(*, fmt: str, today: Optional[date] = None) -> str:
    """Render the conventional ``0001-record-architecture-decisions.md`` ADR."""
    body = render_template(
        fmt=fmt,
        number=1,
        title="Record architecture decisions",
        today=today,
        status="Accepted",
    )
    # Replace the empty MADR/Nygard body with a real first decision so the
    # repository ships with a meaningful starter ADR.
    starter_body = (
        "## Context and problem statement\n\n"
        "We need a lightweight way to capture significant architectural\n"
        "decisions and the context around them, so that future maintainers\n"
        "(and our future selves) understand *why* the system looks the way\n"
        "it does, not just *what* it looks like.\n\n"
        "## Decision\n\n"
        "We will use Architecture Decision Records (ADRs) stored as plain\n"
        "Markdown in `docs/adr/`. New decisions are added by running\n"
        "`adr new \"<title>\"`. ADRs are immutable once `Accepted` — to\n"
        "change a decision, write a new ADR and supersede the old one with\n"
        "`adr supersede <old> <new>`.\n\n"
        "## Consequences\n\n"
        "- Decisions are versioned alongside the code they describe.\n"
        "- The full historical context is searchable via `git log`.\n"
        "- New engineers can read the ADR log to ramp up faster.\n"
    )
    # Replace everything after the Status section with the starter content.
    head, _, _ = body.partition("## Status")
    head = head + "## Status\n\nAccepted\n\n"
    return head + starter_body


def write_template_file(adr_dir: Path, fmt: str) -> Path:
    """Write a copy of the chosen template to ``template-<fmt>.md`` for reference."""
    body = render_template(
        fmt=fmt, number=0, title="Title", today=date(1970, 1, 1), status="Proposed"
    )
    # Rewrite the heading so it's obviously a template, not a real ADR.
    body = re.sub(
        r"^# 0000\. Title",
        "# Template — copy this when writing a new ADR by hand",
        body,
        count=1,
        flags=re.MULTILINE,
    )
    out = adr_dir / f"template-{fmt}.md"
    out.write_text(body, encoding="utf-8")
    return out

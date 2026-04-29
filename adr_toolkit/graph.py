"""Render a Mermaid graph showing supersession relationships between ADRs."""

from __future__ import annotations

from typing import Iterable

from .parser import Adr


_STATUS_CLASS = {
    "Accepted": "accepted",
    "Proposed": "proposed",
    "Superseded": "superseded",
    "Deprecated": "deprecated",
    "Rejected": "deprecated",
}


_CLASS_DEFS = (
    "classDef accepted fill:#bef5cb,stroke:#1a7f37",
    "classDef proposed fill:#fff8c5,stroke:#9a6700",
    "classDef superseded fill:#ffd8b5,stroke:#9a6700,stroke-dasharray:3",
    "classDef deprecated fill:#ffcecb,stroke:#cf222e",
)


def _escape(label: str) -> str:
    """Escape characters that would break a Mermaid label."""
    return label.replace('"', "'").replace("\n", " ").replace("[", "(").replace("]", ")")


def render_mermaid(adrs: Iterable[Adr]) -> str:
    """Build a Mermaid ``graph LR`` describing the ADR network.

    Nodes are coloured by status, and dashed arrows mark supersession.
    """
    adrs = list(adrs)
    lines = ["graph LR"]

    for adr in adrs:
        klass = _STATUS_CLASS.get(adr.status, "proposed")
        label = f"{adr.number_str} {_escape(adr.title)}"
        lines.append(f'    {adr.number_str}["{label}"]:::{klass}')

    for adr in adrs:
        if adr.superseded_by is not None:
            lines.append(
                f"    {adr.number_str} -.->|superseded by| {adr.superseded_by:04d}"
            )

    lines.extend(f"    {cd}" for cd in _CLASS_DEFS)
    return "\n".join(lines) + "\n"

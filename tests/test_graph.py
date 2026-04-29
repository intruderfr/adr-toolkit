"""Tests for the Mermaid graph renderer."""

from __future__ import annotations

import unittest
from pathlib import Path

from adr_toolkit.graph import render_mermaid
from adr_toolkit.parser import Adr


def _adr(num, title, status, superseded_by=None, supersedes=None):
    return Adr(
        number=num,
        title=title,
        status=status,
        path=Path(f"{num:04d}-{title.lower()}.md"),
        superseded_by=superseded_by,
        supersedes=supersedes or [],
    )


class TestMermaidRendering(unittest.TestCase):
    def test_starts_with_graph_lr(self):
        text = render_mermaid([_adr(1, "Foo", "Accepted")])
        self.assertTrue(text.startswith("graph LR\n"))

    def test_includes_classdefs(self):
        text = render_mermaid([_adr(1, "Foo", "Accepted")])
        self.assertIn("classDef accepted", text)
        self.assertIn("classDef superseded", text)

    def test_supersession_arrow(self):
        adrs = [
            _adr(1, "Old", "Superseded", superseded_by=2),
            _adr(2, "New", "Accepted", supersedes=[1]),
        ]
        text = render_mermaid(adrs)
        self.assertIn("0001 -.->|superseded by| 0002", text)

    def test_status_class_assigned(self):
        adrs = [
            _adr(1, "Old", "Superseded", superseded_by=2),
            _adr(2, "New", "Accepted"),
            _adr(3, "Pending", "Proposed"),
        ]
        text = render_mermaid(adrs)
        self.assertIn(":::superseded", text)
        self.assertIn(":::accepted", text)
        self.assertIn(":::proposed", text)

    def test_label_escapes_quotes(self):
        text = render_mermaid([_adr(1, 'Use "smart" cache', "Accepted")])
        # Inner double-quotes converted to single-quotes for Mermaid safety
        self.assertIn("Use 'smart' cache", text)
        self.assertNotIn('"Use "smart" cache"', text)


if __name__ == "__main__":
    unittest.main()

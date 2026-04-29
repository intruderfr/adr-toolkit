"""Tests for the ADR markdown parser."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from adr_toolkit import parser


SAMPLE_MADR = """# 0007. Use PostgreSQL for primary database

Date: 2026-04-29

## Status

Accepted

## Context and problem statement

We need a relational database.

## Decision outcome

Chosen option: PostgreSQL.
"""

SAMPLE_SUPERSEDED = """# 0003. Use Kafka for event bus

## Status

Superseded by [0004](./0004-use-nats-jetstream-for-event-bus.md) on 2026-04-29

## Context

Background.
"""

SAMPLE_SUPERSEDES = """# 0004. Use NATS JetStream for event bus

## Status

Accepted

Supersedes [0003](./0003-use-kafka-for-event-bus.md)

## Context

Reason for change.
"""


class TestParseAdr(unittest.TestCase):
    def test_basic_madr(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "0007-use-postgresql-for-primary-database.md"
            p.write_text(SAMPLE_MADR, "utf-8")
            adr = parser.parse_adr(p)
            self.assertIsNotNone(adr)
            assert adr is not None
            self.assertEqual(adr.number, 7)
            self.assertEqual(adr.title, "Use PostgreSQL for primary database")
            self.assertEqual(adr.status, "Accepted")
            self.assertIsNone(adr.superseded_by)

    def test_superseded_extraction(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "0003-use-kafka-for-event-bus.md"
            p.write_text(SAMPLE_SUPERSEDED, "utf-8")
            adr = parser.parse_adr(p)
            assert adr is not None
            self.assertEqual(adr.status, "Superseded")
            self.assertEqual(adr.superseded_by, 4)

    def test_supersedes_extraction(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "0004-use-nats-jetstream-for-event-bus.md"
            p.write_text(SAMPLE_SUPERSEDES, "utf-8")
            adr = parser.parse_adr(p)
            assert adr is not None
            self.assertEqual(adr.supersedes, [3])
            self.assertEqual(adr.status, "Accepted")

    def test_non_adr_filename_is_ignored(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "notes.md"
            p.write_text("# Random", "utf-8")
            self.assertIsNone(parser.parse_adr(p))


class TestDiscover(unittest.TestCase):
    def test_returns_sorted_by_number(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "0002-b.md").write_text("# 0002. B\n## Status\nProposed\n", "utf-8")
            (d / "0001-a.md").write_text("# 0001. A\n## Status\nAccepted\n", "utf-8")
            (d / "template-madr.md").write_text("# Template\n", "utf-8")
            (d / "README.md").write_text("# Index\n", "utf-8")
            adrs = parser.discover_adrs(d)
            self.assertEqual([a.number for a in adrs], [1, 2])

    def test_next_number(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.assertEqual(parser.next_number([]), 1)
            (d / "0005-x.md").write_text("# 0005. X\n## Status\nProposed\n", "utf-8")
            adrs = parser.discover_adrs(d)
            self.assertEqual(parser.next_number(adrs), 6)

    def test_missing_dir(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(parser.discover_adrs(Path(tmp) / "missing"), [])


if __name__ == "__main__":
    unittest.main()

"""Tests for the template & config helpers."""

from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from adr_toolkit import templates


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(templates.slugify("Use PostgreSQL"), "use-postgresql")

    def test_punctuation(self):
        self.assertEqual(
            templates.slugify("Adopt CQRS+ES, retire CRUD!"),
            "adopt-cqrs-es-retire-crud",
        )

    def test_collapses_whitespace_and_hyphens(self):
        self.assertEqual(
            templates.slugify("  Use   --  Kafka   "), "use-kafka"
        )

    def test_empty_falls_back(self):
        self.assertEqual(templates.slugify("???"), "adr")

    def test_filename(self):
        self.assertEqual(
            templates.render_filename(7, "Use Redis for Cache"),
            "0007-use-redis-for-cache.md",
        )


class TestRenderTemplate(unittest.TestCase):
    def test_madr_has_all_sections(self):
        body = templates.render_template(
            fmt="madr",
            number=2,
            title="Use PostgreSQL",
            today=date(2026, 4, 29),
        )
        self.assertIn("# 0002. Use PostgreSQL", body)
        self.assertIn("## Status", body)
        self.assertIn("Proposed", body)
        self.assertIn("Decision drivers", body)
        self.assertIn("Considered options", body)
        self.assertIn("Decision outcome", body)
        self.assertIn("2026-04-29", body)

    def test_nygard_has_four_sections(self):
        body = templates.render_template(
            fmt="nygard",
            number=3,
            title="Use Redis",
            today=date(2026, 4, 29),
        )
        self.assertIn("## Status", body)
        self.assertIn("## Context", body)
        self.assertIn("## Decision", body)
        self.assertIn("## Consequences", body)
        # Nygard does not include MADR-specific drivers
        self.assertNotIn("Decision drivers", body)

    def test_unknown_format_raises(self):
        with self.assertRaises(ValueError):
            templates.render_template(
                fmt="bogus", number=1, title="x", today=date(2026, 1, 1)
            )

    def test_starter_adr_is_accepted(self):
        body = templates.render_starter_adr(fmt="madr", today=date(2026, 4, 29))
        self.assertIn("Accepted", body)
        self.assertIn("Record architecture decisions", body)
        # The starter contains a real first decision, not the empty template
        self.assertIn("Decisions are versioned alongside the code", body)


class TestConfig(unittest.TestCase):
    def test_default_when_missing(self):
        with TemporaryDirectory() as tmp:
            cfg = templates.AdrConfig.load(Path(tmp))
            self.assertEqual(cfg.format, templates.DEFAULT_FORMAT)

    def test_loads_simple_kv(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / ".adrconfig").write_text("format: nygard\n", "utf-8")
            cfg = templates.AdrConfig.load(Path(tmp))
            self.assertEqual(cfg.format, "nygard")

    def test_loads_json(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / ".adrconfig").write_text(
                json.dumps({"format": "madr"}), "utf-8"
            )
            cfg = templates.AdrConfig.load(Path(tmp))
            self.assertEqual(cfg.format, "madr")

    def test_falls_back_for_unknown_format(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / ".adrconfig").write_text("format: bogus\n", "utf-8")
            cfg = templates.AdrConfig.load(Path(tmp))
            self.assertEqual(cfg.format, templates.DEFAULT_FORMAT)


class TestWriteTemplateFile(unittest.TestCase):
    def test_writes_madr_template(self):
        with TemporaryDirectory() as tmp:
            out = templates.write_template_file(Path(tmp), "madr")
            self.assertTrue(out.exists())
            text = out.read_text("utf-8")
            self.assertIn("Template", text)
            self.assertIn("Decision drivers", text)


if __name__ == "__main__":
    unittest.main()

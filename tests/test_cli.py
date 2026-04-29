"""End-to-end tests of the ``adr`` CLI exercised via ``main()``.

These tests run real subcommands against temporary directories, so they
catch regressions in the file-mutation helpers (init, new, supersede, index).
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from adr_toolkit.cli import main


class TestCliEndToEnd(unittest.TestCase):
    def _run(self, *args, dirpath: Path, expect_zero=True) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--dir", str(dirpath), *args])
        if expect_zero:
            self.assertEqual(rc, 0, f"command failed: {args} (rc={rc})")
        return buf.getvalue()

    def test_init_creates_starter_and_index(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            self.assertTrue((d / "0001-record-architecture-decisions.md").exists())
            self.assertTrue((d / "README.md").exists())
            self.assertTrue((d / "template-madr.md").exists())
            self.assertTrue((d / ".adrconfig").exists())

    def test_new_creates_proposed_adr(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            self._run("new", "Use", "PostgreSQL", dirpath=d)
            adr_file = d / "0002-use-postgresql.md"
            self.assertTrue(adr_file.exists())
            text = adr_file.read_text("utf-8")
            self.assertIn("# 0002. Use PostgreSQL", text)
            self.assertIn("Proposed", text)

    def test_list_includes_status(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            self._run("new", "Use Redis", dirpath=d)
            output = self._run("list", dirpath=d)
            self.assertIn("0001", output)
            self.assertIn("Accepted", output)
            self.assertIn("0002", output)
            self.assertIn("Proposed", output)
            self.assertIn("Use Redis", output)

    def test_supersede_updates_both_files(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            self._run("new", "Use Kafka for event bus", dirpath=d)
            self._run("new", "Use NATS JetStream", dirpath=d)
            self._run("supersede", "2", "3", dirpath=d)

            old = (d / "0002-use-kafka-for-event-bus.md").read_text("utf-8")
            new = (d / "0003-use-nats-jetstream.md").read_text("utf-8")
            self.assertIn("Superseded by", old)
            self.assertIn("0003", old)
            self.assertIn("Supersedes", new)
            self.assertIn("0002", new)

    def test_supersede_rejects_missing_target(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            self._run("new", "Use Kafka", dirpath=d)
            buf = io.StringIO()
            # Capture stderr is non-trivial; just assert non-zero rc
            rc = main(["--dir", str(d), "supersede", "2", "9"])
            self.assertNotEqual(rc, 0)

    def test_graph_emits_mermaid(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            self._run("new", "Use Redis", dirpath=d)
            output = self._run("graph", dirpath=d)
            self.assertIn("graph LR", output)
            self.assertIn("0001", output)
            self.assertIn("0002", output)

    def test_graph_writes_to_output_file(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            out_file = Path(tmp) / "graph.mmd"
            self._run("graph", "--output", str(out_file), dirpath=d)
            self.assertTrue(out_file.exists())
            self.assertIn("graph LR", out_file.read_text("utf-8"))

    def test_show_prints_one_adr(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "adr"
            self._run("init", dirpath=d)
            output = self._run("show", "1", dirpath=d)
            self.assertIn("Record architecture decisions", output)
            self.assertIn("Accepted", output)


if __name__ == "__main__":
    unittest.main()

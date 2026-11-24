# SPDX-License-Identifier: GPL-3.0-or-later
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import g6x


class ImportComparisonTests(unittest.TestCase):
    def test_dll_case_is_normalized_but_delay_imports_stay_separate(self):
        reports = {
            "leonida": {"imports": [
                {"dll": "Example.DLL", "kind": "normal", "where": "bundled", "functions": ["#4"]},
                {"dll": "example.dll", "kind": "delay", "where": "bundled", "functions": ["#4"]},
            ]},
            "runtime": {"imports": [
                {"dll": "EXAMPLE.dll", "delay": False, "function": "#4", "status": "unresolved"},
            ]},
            "xcl": {"imports": [
                {"dll": "example.dll", "delay": False, "function": "#4", "status": "game DLL"},
                {"dll": "example.dll", "delay": False, "function": "#4", "status": "game DLL"},
            ]},
        }
        report = g6x.compare(Path("probe.dll"), reports)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["image"], "probe.dll")
        self.assertEqual(report["backends"], ["leonida", "runtime", "xcl"])
        self.assertEqual(report["imports"], [
            {"dll": "example.dll", "function": "#4", "kind": "delay", "status": {"leonida": ["bundled"]}},
            {"dll": "example.dll", "function": "#4", "kind": "normal", "status": {
                "leonida": ["bundled"], "runtime": ["unresolved"], "xcl": ["game DLL"],
            }},
        ])

    def test_bad_image_does_not_emit_a_partial_json_report(self):
        if not (g6x.SOURCES["leonida"] / "tools" / "pe_inspect.py").is_file():
            self.skipTest("Leonida submodule is not checked out")
        with tempfile.TemporaryDirectory() as scratch:
            image = Path(scratch) / "invalid image.dll"
            image.write_bytes(b"MZ")
            result = subprocess.run(
                [sys.executable, str(g6x.ROOT / "g6x.py"), "inspect", str(image), "--json"],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("leonida: inspector exited with code 1", result.stderr)

    @unittest.skipUnless(sys.platform == "win32", "requires a Windows PE executable")
    def test_default_inspector_accepts_paths_with_spaces(self):
        if not (g6x.SOURCES["leonida"] / "tools" / "pe_inspect.py").is_file():
            self.skipTest("Leonida submodule is not checked out")
        import os
        import shutil

        with tempfile.TemporaryDirectory() as scratch:
            image = Path(scratch) / "probe with spaces.exe"
            shutil.copyfile(Path(os.environ["SystemRoot"]) / "System32" / "whoami.exe", image)
            result = subprocess.run(
                [sys.executable, str(g6x.ROOT / "g6x.py"), "inspect", str(image), "--json"],
                cwd=scratch,
                capture_output=True,
                check=True,
                text=True,
            )
        report = json.loads(result.stdout)
        self.assertEqual(report["image"], image.name)
        self.assertEqual(report["backends"], ["leonida"])
        self.assertTrue(report["imports"])


if __name__ == "__main__":
    unittest.main()

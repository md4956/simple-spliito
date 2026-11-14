"""Checks that CHANGELOG.md, the README and the release script agree. Run with: python3 -m unittest discover -s tests"""

import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("release", ROOT / "scripts" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def as_tuple(version):
    return tuple(map(int, version.split(".")))


class ReleaseTests(unittest.TestCase):
    def test_every_section_has_notes(self):
        for version, _, notes in release.sections():
            with self.subTest(version=version):
                self.assertTrue(notes, "a release needs notes for its GitHub release page")

    def test_sections_are_listed_newest_first(self):
        versions = [version for version, _, _ in release.sections()]
        self.assertEqual(versions, sorted(versions, key=as_tuple, reverse=True))

    def test_each_version_is_listed_once(self):
        versions = [version for version, _, _ in release.sections()]
        self.assertEqual(len(versions), len(set(versions)))

    def test_latest_is_the_top_section(self):
        self.assertEqual(release.latest(), release.sections()[0][0])

    def test_readme_names_the_latest_version(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        match = re.search(r"This README describes version (\d+\.\d+\.\d+)", readme)
        self.assertIsNotNone(match, "the README should say which version it describes")
        self.assertEqual(match.group(1), release.latest(), "update the README version line with the CHANGELOG")

    def test_notes_command_prints_the_latest_notes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "release.py"), "notes", release.latest()],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), release.notes(release.latest()))

    def test_latest_command_prints_the_latest_version(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "release.py"), "latest"],
                                capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), release.latest())

    def test_workflow_creates_the_release_with_the_script(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/release.py latest", workflow)
        self.assertIn("scripts/release.py notes", workflow)
        self.assertIn("simple-spliito.py", workflow)


if __name__ == "__main__":
    unittest.main()

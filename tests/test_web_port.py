"""Checks that docs/spliito.js prints exactly what simple-spliito.py prints.

Needs Node.js, and is skipped without it. Run with: python3 -m unittest discover -s tests
"""

import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "simple-spliito.py"
WEB_JS = ROOT / "docs" / "spliito.js"
NODE_RUNNER = """
const fs = require('fs');
const { run } = require(process.argv[1]);
const result = run(fs.readFileSync(0, 'utf8'));
process.stdout.write(result.text);
process.exitCode = result.ok ? 0 : 1;
"""


def run_script(content):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "expenses.txt"
        path.write_text(content, encoding="utf-8")
        done = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, encoding="utf-8")
    return done.stdout, done.returncode


def run_web(content):
    done = subprocess.run(["node", "-e", NODE_RUNNER, str(WEB_JS)], input=content, capture_output=True, encoding="utf-8")
    return done.stdout, done.returncode


def random_expenses(seed, people, lines):
    rng = random.Random(seed)
    names = [f"p{i}" for i in range(people)]
    rows = []
    for _ in range(lines):
        payer = rng.choice(names)
        related = rng.sample(names, rng.randint(1, 4))
        rows.append(f"{payer} {rng.randint(1, 2000) / 4} {' '.join(related)}")
    return "\n".join(rows) + "\n"


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to run the web port")
class WebPortMatchesScriptTest(unittest.TestCase):
    def assertSameOutput(self, content):
        script_out, script_code = run_script(content)
        web_out, web_code = run_web(content)
        self.assertEqual(web_out, script_out)
        self.assertEqual(web_code == 0, script_code == 0)

    def test_readme_example(self):
        self.assertSameOutput("# Dinner\nana 60 ana ben cy\nben 30 ben cy\n")

    def test_two_currencies(self):
        self.assertSameOutput("# Trip, two currencies\n@EUR\nnik 50 nik eva\nana 30 ana eva\n@\nbob 40 bob cy\n")

    def test_warnings_and_skipped_lines(self):
        self.assertSameOutput(
            "# Trip_ *x\n"
            "ana 10 ana ben\n"
            "bad\n"
            "ana sixty ana\n"
            "mia#2 5 mia\n"
            "@EUR JPY\n"
            "ben 3 ben ana\n"
            "@\n"
            "\n"
            "cy 7 cy,ben, ana # note\n"
            "zed 1e999 zed\n"
            "_zed 2 ana,, ben_\n"
        )

    def test_name_with_star_stops_the_script(self):
        self.assertSameOutput("# Oops\nana 5 ana *bo\nben 2 ben ana\n")

    def test_empty_inputs(self):
        self.assertSameOutput("")
        self.assertSameOutput("# Only a title\n")

    def test_half_cent_rounds_to_even(self):
        # Each share is 0.125, which Python prints as 0.12
        self.assertSameOutput("ana 1 ana ben cy dan eve fay gus hal\n")

    def test_random_groups(self):
        self.assertSameOutput(random_expenses(seed=7, people=7, lines=40))

    def test_too_many_people_for_exact_search(self):
        self.assertSameOutput(random_expenses(seed=3, people=19, lines=30))


if __name__ == "__main__":
    unittest.main()

"""Tests for simple-spliito.py. Run with: python3 -m unittest discover -s tests"""

import contextlib
import importlib.util
import io
import os
import random
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "simple-spliito.py"
EXAMPLE = ROOT / "example-expenses.txt"

spec = importlib.util.spec_from_file_location("simple_spliito", SCRIPT)
spliito = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spliito)


def run_script(content, suffix=".txt"):
    """Write content to a temporary file, run the script on it, return (stdout, exit code)."""
    mode, data = ("wb", content) if isinstance(content, bytes) else ("w", content)
    with tempfile.NamedTemporaryFile(mode, suffix=suffix, delete=False) as file:
        file.write(data)
    try:
        result = subprocess.run([sys.executable, str(SCRIPT), file.name], capture_output=True, text=True)
    finally:
        os.remove(file.name)
    return result.stdout, result.returncode


def min_payments(values):
    """Exact fewest payments for integer balances: try every way to settle the first person."""
    values = [v for v in values if v != 0]
    if not values:
        return 0
    first, rest = values[0], values[1:]
    best = None
    for i, other in enumerate(rest):
        if (other > 0) != (first > 0):
            merged = rest[:i] + rest[i + 1:] + [first + other]
            count = 1 + min_payments(merged)
            best = count if best is None else min(best, count)
    return best


def net_after(balances, payments):
    """Balances left after applying the payments. Should be zero for everyone."""
    net = dict(balances)
    for payer, receiver, amount in payments:
        net[payer] = net.get(payer, 0) + amount
        net[receiver] = net.get(receiver, 0) - amount
    return net


def random_zero_sum(rng, people):
    values = [rng.randint(-50, 50) for _ in range(people - 1)]
    values.append(-sum(values))
    return values


class SettlementAccuracyTests(unittest.TestCase):
    def test_matches_exact_minimum_on_random_cases(self):
        rng = random.Random(1)
        for case in range(300):
            values = random_zero_sum(rng, rng.randint(2, 7))
            balances = {f"p{i}": float(v) for i, v in enumerate(values)}
            payments = spliito.settle(balances)
            with self.subTest(case=case, values=values):
                self.assertEqual(len(payments), min_payments(values))
                net = net_after(balances, payments)
                self.assertTrue(all(abs(v) < 1e-6 for v in net.values()), net)

    def test_decimal_balances_are_cleared(self):
        rng = random.Random(2)
        for case in range(100):
            people = rng.randint(2, 6)
            values = [round(rng.uniform(-500, 500), 2) for _ in range(people - 1)]
            values.append(round(-sum(values), 2))
            balances = {f"p{i}": v for i, v in enumerate(values)}
            payments = spliito.settle(balances)
            net = net_after(balances, payments)
            with self.subTest(case=case):
                self.assertTrue(all(abs(v) < 0.001 for v in net.values()), net)

    def test_two_payments_instead_of_greedy_three(self):
        payments = spliito.settle({"a": 10.0, "b": 5.0, "c": -10.0, "d": -5.0})
        self.assertEqual(sorted(payments), [("c", "a", 10.0), ("d", "b", 5.0)])

    def test_three_payments_for_four_people(self):
        balances = {"ali": 200000.0, "sara": 150000.0, "mina": -50000.0, "reza": -300000.0}
        payments = spliito.settle(balances)
        self.assertEqual(len(payments), 3)
        self.assertTrue(all(abs(v) < 0.001 for v in net_after(balances, payments).values()))

    def test_nobody_owes_means_no_payments(self):
        self.assertEqual(spliito.settle({"a": 0.0, "b": 0.0}), [])
        self.assertEqual(spliito.settle({}), [])

    def test_groups_cover_every_person_once_and_each_sums_to_zero(self):
        rng = random.Random(3)
        for case in range(100):
            values = random_zero_sum(rng, rng.randint(2, 8))
            groups = spliito.split_into_groups(values)
            indexes = sorted(i for group in groups for i in group)
            with self.subTest(case=case):
                self.assertEqual(indexes, list(range(len(values))))
                for group in groups:
                    self.assertLess(abs(sum(values[i] for i in group)), 1e-6)

    def test_more_than_eighteen_people_prints_note_and_still_clears(self):
        balances = {f"p{i}": 1.0 if i % 2 == 0 else -1.0 for i in range(20)}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            payments = spliito.settle(balances)
        self.assertIn("Note: more than 18 people", output.getvalue())
        self.assertTrue(all(abs(v) < 1e-6 for v in net_after(balances, payments).values()))


class BalanceCalculationTests(unittest.TestCase):
    def test_single_expense_split_between_three(self):
        stdout, _ = run_script("@IRT\nali 900000 ali sara reza\n")
        self.assertIn("ali gets 600,000.00 IRT", stdout)
        self.assertIn("sara owes 300,000.00 IRT", stdout)
        self.assertIn("reza owes 300,000.00 IRT", stdout)

    def test_markdown_file_gives_the_same_report_as_txt(self):
        text = "# Dinner\nana 60 ana ben cy\nben 30 ben cy\n"
        txt_stdout, _ = run_script(text)
        md_stdout, md_code = run_script(text, suffix=".md")
        self.assertEqual(md_code, 0)
        self.assertEqual(md_stdout, txt_stdout)
        self.assertIn("Dinner", md_stdout)

    def test_payer_not_in_list_pays_whole_amount_for_others(self):
        stdout, _ = run_script("tom 415 max\n")
        self.assertIn("tom gets 415.00", stdout)
        self.assertIn("max owes 415.00", stdout)

    def test_name_listed_twice_gets_two_shares(self):
        stdout, _ = run_script("sam 900 sam ana ana lia\n")
        self.assertIn("ana owes 450.00", stdout)
        self.assertIn("lia owes 225.00", stdout)
        self.assertIn("sam gets 675.00", stdout)

    def test_paid_only_for_themselves_has_no_effect(self):
        stdout, _ = run_script("ivy 297 ivy\n")
        self.assertIn("ivy is settled", stdout)

    def test_example_file_matches_independent_calculation(self):
        expected = defaultdict(float)
        for raw in EXAMPLE.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            payer, amount, *names = line.split()
            people = [n for n in ",".join(names).split(",") if n]
            share = float(amount) / len(people)
            expected[payer] += float(amount)
            for person in people:
                expected[person] -= share
        stdout, _ = run_script(EXAMPLE.read_text(encoding="utf-8"))
        for person, balance in expected.items():
            with self.subTest(person=person):
                word = "gets" if balance > 0 else "owes"
                if abs(balance) < 0.005:
                    self.assertIn(f"{person} is settled", stdout)
                else:
                    self.assertIn(f"{person} {word} {abs(balance):,.2f}", stdout)

    def test_total_line_says_zero_for_balanced_input(self):
        stdout, _ = run_script("nik 10 nik eva\n")
        self.assertIn("TOTAL: 0.00 (balances add up to zero", stdout)

    def test_total_line_warns_when_balances_do_not_add_up(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            spliito.print_report({"a": 1.0}, [], "", "")
        self.assertIn("should be 0.00, so the script has a calculation bug", output.getvalue())


class InputParsingTests(unittest.TestCase):
    def test_whole_line_comment_and_blank_lines_are_ignored(self):
        stdout, code = run_script("# note\n\n   # indented\nnik 10 nik eva\n")
        self.assertEqual(code, 0)
        self.assertNotIn("Invalid", stdout)
        self.assertIn("eva pays nik 5.00", stdout)

    def test_inline_comment_after_expense(self):
        stdout, _ = run_script("nik 10 nik eva # lunch\n")
        self.assertIn("eva pays nik 5.00", stdout)
        self.assertNotIn("Warning", stdout)

    def test_hash_inside_comment_does_not_warn(self):
        stdout, _ = run_script("nik 10 nik eva # lunch#2 eva\n")
        self.assertNotIn("Warning", stdout)

    def test_hash_glued_to_name_warns_and_ends_the_name(self):
        stdout, _ = run_script("nik 10 nik eva#\n")
        self.assertIn("Warning: '#' right after a name starts a comment", stdout)
        self.assertIn("eva pays nik 5.00", stdout)

    def test_space_after_comma_does_not_create_empty_name(self):
        stdout, _ = run_script("nik 90 nik, eva, tom\n")
        self.assertIn("nik gets 60.00", stdout)
        self.assertIn("eva owes 30.00", stdout)
        self.assertIn("tom owes 30.00", stdout)

    def test_only_comma_is_an_invalid_related_list(self):
        stdout, _ = run_script("nik 100 ,\n")
        self.assertIn("Invalid related_to list in line: nik 100 ,", stdout)

    def test_non_finite_amounts_are_rejected(self):
        for amount in ["nan", "inf", "-inf", "Infinity", "1e999"]:
            with self.subTest(amount=amount):
                stdout, _ = run_script(f"nik {amount} eva\nlia 30 lia eva\n")
                self.assertIn(f"Invalid amount: {amount}", stdout)
                self.assertIn("eva owes 15.00", stdout)

    def test_too_few_parts_is_an_invalid_line(self):
        stdout, _ = run_script("nik 10\n")
        self.assertIn("Invalid line: nik 10", stdout)

    def test_star_in_a_name_is_an_error_that_stops_the_script(self):
        stdout, code = run_script("a* 10 b\n")
        self.assertEqual(code, 1)
        self.assertIn("Error: '*' and '~' are not allowed in names", stdout)
        self.assertNotIn("SUMMARY", stdout)

    def test_tilde_in_a_name_is_an_error(self):
        stdout, code = run_script("nik 10 ni~k\n")
        self.assertEqual(code, 1)
        self.assertIn("Error: '*' and '~'", stdout)

    def test_underscore_in_a_name_warns_and_keeps_processing(self):
        stdout, code = run_script("ana_b 10 ana_b c\n")
        self.assertEqual(code, 0)
        self.assertIn("Warning: '_' in a name", stdout)
        self.assertIn("c pays ana_b 5.00", stdout)

    def test_missing_file_exits_with_error(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "/no/such/file.txt"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("not found", result.stdout)

    def test_wrong_number_of_arguments_prints_usage(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Usage:", result.stdout)

    def test_empty_file_says_everyone_is_settled(self):
        stdout, code = run_script("")
        self.assertEqual(code, 0)
        self.assertIn("Everyone is settled.", stdout)


class TitleTests(unittest.TestCase):
    def test_first_line_comment_becomes_title(self):
        stdout, _ = run_script("# Weekend trip\nnik 10 nik eva\n")
        self.assertTrue(stdout.startswith("Weekend trip\n"))

    def test_comment_on_another_line_is_not_a_title(self):
        stdout, _ = run_script("nik 10 nik eva\n# not a title\n")
        self.assertTrue(stdout.startswith("SUMMARY"))

    def test_empty_first_comment_gives_no_title(self):
        stdout, _ = run_script("#\nnik 10 nik eva\n")
        self.assertTrue(stdout.startswith("SUMMARY"))

    def test_byte_order_mark_does_not_hide_the_title(self):
        stdout, _ = run_script(b"\xef\xbb\xbf# Byte order\nnik 10 nik eva\n")
        self.assertTrue(stdout.startswith("Byte order\n"))

    def test_special_characters_in_title_warn_but_print(self):
        stdout, code = run_script("# Trip_*2025~\nnik 10 nik eva\n")
        self.assertEqual(code, 0)
        self.assertIn("Warning: '_', '*' and '~' in the title", stdout)
        self.assertIn("Trip_*2025~\n", stdout)


class CurrencyTests(unittest.TestCase):
    def test_at_line_sets_currency_for_following_lines(self):
        stdout, _ = run_script("@EUR\nnik 50 nik eva\n")
        self.assertIn("SUMMARY - EUR: 2 people, 1 payment", stdout)
        self.assertIn("eva pays nik 25.00 EUR", stdout)

    def test_currency_sections_are_separated_by_a_line(self):
        stdout, _ = run_script("@IRT\nali 10 ali sara\n@AMD\nali 10 ali sara\n")
        self.assertEqual(stdout.count("\n-----\n"), 1)

    def test_single_currency_has_no_separator(self):
        stdout, _ = run_script("@IRT\nali 10 ali sara\n")
        self.assertNotIn("-----", stdout)
        self.assertIn("PAYMENTS - IRT", stdout)

    def test_plain_numbers_after_currency_are_labelled_no_currency(self):
        stdout, _ = run_script("@EUR\nnik 50 nik eva\n@\nbob 40 bob cy\n")
        self.assertIn("PAYMENTS - NO CURRENCY", stdout)
        self.assertIn("cy pays bob 20.00\n", stdout)

    def test_plain_numbers_only_have_no_labels(self):
        stdout, _ = run_script("nik 10 nik eva\n")
        self.assertNotIn(" - ", stdout)
        self.assertNotIn("-----", stdout)

    def test_each_currency_settles_on_its_own(self):
        stdout, _ = run_script("@IRT\nali 100 ali sara\n@EUR\nsara 100 sara ali\n")
        self.assertIn("sara pays ali 50.00 IRT", stdout)
        self.assertIn("ali pays sara 50.00 EUR", stdout)

    def test_two_codes_on_one_at_line_is_invalid(self):
        stdout, _ = run_script("@EUR USD\nnik 10 nik eva\n")
        self.assertIn("Invalid currency: @EUR USD", stdout)


class OutputFormatTests(unittest.TestCase):
    def test_payments_for_one_payer_are_one_block_and_singles_come_first(self):
        stdout, _ = run_script("ali 400000 ali reza\nsara 300000 sara mina\nmina 200000 mina reza\n")
        payments = stdout.split("PAYMENTS\n\n")[1].strip().split("\n\n")
        self.assertEqual(payments[0], "mina pays sara 50,000.00")
        self.assertEqual(payments[1], "reza pays ali 200,000.00\nreza pays sara 100,000.00")

    def test_each_multi_payer_gets_its_own_block(self):
        # p1 and p2 each pay two people, so each gets a block of their own
        stdout, _ = run_script("a 200 a p1\nb 200 b p1\nc 200 c p2\nd 200 d p2\n")
        blocks = stdout.split("PAYMENTS\n\n")[1].strip().split("\n\n")
        self.assertEqual(blocks, [
            "p1 pays a 100.00\np1 pays b 100.00",
            "p2 pays c 100.00\np2 pays d 100.00",
        ])

    def test_single_payers_come_first_in_one_block(self):
        stdout, _ = run_script("max 100 max joe\nmax 200 max nik\ntom 100 tom joe\ntom 300 tom nik\nivy 50 ivy sam\n")
        blocks = stdout.split("PAYMENTS\n\n")[1].strip().split("\n\n")
        self.assertEqual(blocks, [
            "joe pays max 100.00\nsam pays ivy 25.00",
            "nik pays tom 200.00\nnik pays max 50.00",
        ])

    def test_payments_are_sorted_by_amount_within_each_block(self):
        stdout, _ = run_script("max 100 max joe\nmax 200 max nik\ntom 100 tom joe\ntom 300 tom nik\nivy 50 ivy sam\n")
        for block in stdout.split("PAYMENTS\n\n")[1].strip().split("\n\n"):
            amounts = [float(line.split()[-1].replace(",", "")) for line in block.splitlines()]
            with self.subTest(block=block):
                self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_headings_are_upper_case(self):
        stdout, _ = run_script("nik 10 nik eva\n")
        for heading in ["SUMMARY:", "BALANCES", "TOTAL:", "PAYMENTS"]:
            self.assertIn(heading, stdout)

    def test_summary_uses_singular_for_one(self):
        stdout, _ = run_script("nik 10 nik eva\n")
        self.assertIn("SUMMARY: 2 people, 1 payment", stdout)

    def test_amounts_have_thousands_separators(self):
        stdout, _ = run_script("ali 2000000 ali bob\n")
        self.assertIn("bob owes 1,000,000.00", stdout)


class GoldenOutputTests(unittest.TestCase):
    """The examples in the README must match what the script prints."""

    def test_quick_start(self):
        stdout, _ = run_script("# Dinner\nana 60 ana ben cy\nben 30 ben cy\n")
        expected = """Dinner

SUMMARY: 3 people, 2 payments

BALANCES

ana gets 40.00
ben owes 5.00
cy owes 35.00

TOTAL: 0.00 (balances add up to zero, so every payment is accounted for)

PAYMENTS

cy pays ana 35.00
ben pays ana 5.00
"""
        self.assertEqual(stdout.strip(), expected.strip())

    def test_example_expenses_file(self):
        stdout, _ = run_script(EXAMPLE.read_text(encoding="utf-8"))
        self.assertIn("Weekend trip expenses\n\nSUMMARY: 10 people, 9 payments", stdout)
        self.assertIn("tom pays lia 1.25", stdout)
        self.assertIn("ivy owes 931.79", stdout)


if __name__ == "__main__":
    unittest.main()

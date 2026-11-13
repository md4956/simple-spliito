# simple-spliito

A small command-line tool for splitting shared expenses. You write down who paid what and who it was for in a text file. It prints each person's balance and the fewest payments that settle everyone up.

> Hobby project, still under development.

## Requirements

Python 3. No external packages.

## Quick start

Save this as `dinner.txt`:

```
# Dinner
ana 60 ana ben cy
ben 30 ben cy
```

Run it:

```bash
python3 simple-spliito.py dinner.txt
```

To run the tests (they only use the Python standard library):

```bash
python3 -m unittest discover -s tests
```

You get:

```
Dinner

SUMMARY: 3 people, 2 payments

BALANCES

ana gets 40.00
ben owes 5.00
cy owes 35.00

TOTAL: 0.00 (balances add up to zero, so every payment is accounted for)

PAYMENTS

cy pays ana 35.00
ben pays ana 5.00
```

- The first line of the file becomes the title.
- `ana gets 40.00` means ana should receive 40.00. `cy owes 35.00` means cy should pay 35.00.
- `cy pays ana 35.00` means cy should pay ana 35.00. The two payments settle everyone.

That's all you need for most trips. The rest of this page covers the other features.

## Input format

One expense per line:

```
<payer> <amount> <person> <person> ...
```

The amount is split equally between the people listed after it. The payer only gets a share if they list themselves. So `ana 60 ana ben cy` splits 60 three ways and includes ana, while `tom 415 max` means tom paid the whole amount for max.

Other rules:

- **Names** can be separated by spaces, commas or both: `nik 640.5 nik eva tom,ivy` and `nik 640.5 nik, eva, tom, ivy` mean the same thing.
- **Repeated names** get more shares. `sam 900 sam ana ana lia` splits 900 into four parts, and ana owes two of them. Numbers are allowed in names, so `mia1 mia2 mia3` are three people.
- **Decimals** work: `362.75`. Amounts that aren't finite numbers (`nan`, `inf`, `1e999`) are rejected.
- **Comments:** `#` starts a comment, and everything after it on that line is ignored. A comment can take a whole line or follow an expense: `dan 210 mia1 mia2 mia3 # mias are cousins`.
- **Blank lines** are ignored.
- **Names can't contain `#`, `*` or `~`.** A `*` or `~` stops the script with an error. A `_` is allowed, but the script prints a warning, because messengers can turn the text between two underscores into italics.
- **A `#` directly after a name**, like `mia#2`, still starts a comment. The script prints a `Warning:` line and reads the name as `mia`.
- **The title** comes from a comment on the first line of the file. `# Weekend trip` at the top makes `Weekend trip` the title. If the first line isn't a comment, there's no title.
- **Currencies** are covered below.
- **Other lines** that don't match the format are skipped, with a short message: `Invalid line: ...`, `Invalid amount: ...` or `Invalid related_to list ...`. Watch out for plain-text notes whose second word is a number, such as `Notes: 100 euros total`, because those are read as an expense.

## Currencies

A line starting with `@` sets the currency for the expenses after it:

- `@EUR` switches to euros.
- `@` on its own switches back to plain numbers.

If a file uses more than one currency, the output has a separate section for each one, divided by a `-----` line. Each section has its own summary, balances, total and payments. Every heading names its currency, and every amount shows it too. A single currency doesn't get the divider. The script never converts between currencies, so each section settles on its own.

```
# Trip, two currencies
@EUR
nik 50 nik eva
ana 30 ana eva
@
bob 40 bob cy
```

```
Trip, two currencies

SUMMARY - EUR: 3 people, 2 payments

BALANCES - EUR

nik gets 25.00 EUR
ana gets 15.00 EUR
eva owes 40.00 EUR

TOTAL - EUR: 0.00 (balances add up to zero, so every payment is accounted for)

PAYMENTS - EUR

eva pays nik 25.00 EUR
eva pays ana 15.00 EUR

-----

SUMMARY - NO CURRENCY: 2 people, 1 payment

BALANCES - NO CURRENCY

bob gets 20.00
cy owes 20.00

TOTAL - NO CURRENCY: 0.00 (balances add up to zero, so every payment is accounted for)

PAYMENTS - NO CURRENCY

cy pays bob 20.00
```

Expenses before the first `@` line, and after an `@` line with nothing after it, use plain numbers. Plain numbers always come last, under the `NO CURRENCY` heading.

## Full example

[`example-expenses.txt`](example-expenses.txt) uses every input feature:

```bash
python3 simple-spliito.py example-expenses.txt
```

```
Weekend trip expenses

SUMMARY: 10 people, 9 payments

BALANCES

sam gets 1,816.58
joe gets 730.67
lia gets 712.50
eva gets 246.54
nik gets 46.96
tom owes 247.79
ana owes 696.67
max owes 834.67
ben owes 842.33
ivy owes 931.79

TOTAL: 0.00 (balances add up to zero, so every payment is accounted for)

PAYMENTS

ivy pays sam 931.79
ben pays sam 842.33
ana pays lia 696.67

max pays joe 730.67
max pays nik 46.96
max pays sam 42.46
max pays lia 14.58

tom pays eva 246.54
tom pays lia 1.25
```

How to read the output:

- **SUMMARY** gives the number of people and payments.
- **BALANCES** lists everyone, largest first. `gets` means the person should receive money, and `owes` means they should pay. A person with nothing to settle shows `is settled`.
- **TOTAL** should always be `0.00`, because every expense takes money from the people who share it and gives it to the payer. If it isn't, the script has a calculation bug, not a problem with your input.
- **PAYMENTS** lists each payment on its own line. The people who pay only once come first, sorted by amount. Each person who pays several times gets their own block, also sorted by amount. Blocks are separated by a blank line, so the payments for one person are easy to find.
- If nothing is owed, the payments section says `Everyone is settled.`

The output is plain text, with no alignment or indentation, so it reads the same when pasted into a messenger or viewed on a narrow phone screen.

## Limitations

- Splits are always equal, apart from naming someone more than once.
- Names are case-sensitive.
- The fewest payments are only guaranteed for up to 18 people with a balance to settle. Above that, the exact search would take too long, so the script prints a note and uses a faster method that may list extra payments.
- Amounts are plain floats, shown rounded to two decimals with thousands separators (`1,816.58`).
- The script doesn't convert between currencies.

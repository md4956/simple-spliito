# simple-spliito

A small command-line tool for splitting shared expenses. You give it a text file listing who paid what and who it was for. It prints each person's balance and the fewest payments that settle everyone up.

> Hobby project, still under development.

## Requirements

Python 3. No external packages.

## Usage

```bash
python3 simple-spliito.py example-expenses.txt
```

## Input format

One expense per line:

```
<payer> <amount> <person> <person> ...
```

- The amount is split equally between everyone listed after it.
- People can be separated by spaces, commas, or both: `nik 640.5 nik eva tom,ivy` and `nik 640.5 nik, eva, tom, ivy` mean the same thing.
- The payer only gets a share if they list themselves: `lia 1250 lia nik sam ben` includes lia, while `tom 415 max` means tom paid the whole amount for max.
- A line with only the payer and amount for themselves (`ivy 297 ivy`) has no effect on anyone's balance.
- Naming someone twice gives them two shares: `sam 900 sam ana ana lia` splits the amount into four parts, and ana owes two of them.
- Names can contain numbers, so repeated people can be `mia1 mia2 mia3`. Names can't contain `#`, `*` or `~`: a `*` or `~` stops the script with an error. A `_` is allowed, but the script prints a warning because messengers can turn the text in between into italics.
- Decimal amounts work (`362.75`).
- Blank lines are ignored.
- `#` starts a comment, and everything after it on that line is ignored. A comment can take a whole line or follow an expense: `dan 210 mia1 mia2 mia3 # mias are cousins`.
- A `#` directly after a name, like `mia#2`, still starts a comment, so the script prints a `Warning:` line and the name is read as `mia`.
- Amounts that aren't finite numbers (`nan`, `inf`, `1e999`) are rejected as invalid.
- Any other line that doesn't match the format is skipped, and the script prints a short message for it (`Invalid line: ...`, `Invalid amount: ...` or `Invalid related_to list ...`). Watch out for plain-text notes whose second word is a number, such as `Notes: 100 euros total`, because those are read as an expense.

See [`example-expenses.txt`](example-expenses.txt) for a file that uses all of this.

## Output

```
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

The output is plain text with no alignment, so it reads the same when pasted into a messenger or onto a narrow phone screen.

- Balances are sorted from largest to smallest. `gets` means the person should receive money, and `owes` means they should pay.
- `TOTAL` should always be `0.00`, because every expense takes money from the people who share it and gives it to the payer. If it isn't, the script has a calculation bug.
- Payments are split into two blocks. People who make one payment come first, then people who make several. Each block is sorted by the amount paid, largest first.
- If nothing is owed, the payments section says `Everyone is settled.`

## Limitations

- Splits are always equal (apart from naming someone more than once).
- Names are case-sensitive.
- The fewest payments are only guaranteed for up to 18 people with a balance to settle. Above that, the exact search would take too long, so the script prints a note and uses a faster method that may list extra payments.
- Amounts are plain floats, shown rounded to two decimals with thousands separators (`1,816.58`).

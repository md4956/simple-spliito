# simple-spliito

A small command-line tool for splitting shared expenses. You give it a text file listing who paid what and who it was for. It prints each person's balance and a short list of payments that settles everyone up.

> Hobby project, still under development.

## Requirements

Python 3. No external packages.

## Usage

```bash
python3 spliter-v0.5.py example-expenses.txt
```

## Input format

One expense per line:

```
<payer> <amount> <person> <person> ...
```

- The amount is split equally between everyone listed after it.
- People can be separated by spaces, commas, or both: `nik 640.5 nik eva tom,ivy`.
- The payer only gets a share if they list themselves: `lia 1250 lia nik sam ben` includes lia, while `tom 415 max` means tom paid the whole amount for max.
- A line with only the payer and amount for themselves (`ivy 297 ivy`) has no effect on anyone's balance.
- Naming someone twice gives them two shares: `sam 900 sam ana ana lia` splits the amount into four parts, and ana owes two of them.
- Decimal amounts work (`362.75`).
- Blank lines are ignored.
- Any line that doesn't match this format is skipped, so you can use such lines as comments. The script prints a short message for each one (`Invalid line: ...` or `Invalid amount: ...`), which is harmless. Start comments with `#` and make sure the second word isn't a number, otherwise the line is read as an expense.

See [`example-expenses.txt`](example-expenses.txt) for a file that uses all of this.

## Output

```
Invalid amount: Weekend in line: # Weekend trip expenses
Invalid amount: Format: in line: # Format: payer amount people (space or comma separated)
Invalid amount: Mixed in line: # Mixed spaces and commas, decimal amount
Invalid amount: Payer in line: # Payer not in the list: tom paid the whole amount for max
Invalid amount: Paid in line: # Paid only for themselves: no effect on balances
Invalid amount: A in line: # A name listed twice gets two shares

Balances:      # negative means should pay, and positive means should receive
lia: 712.50
nik: 46.96
sam: 1816.58
ben: -842.33
eva: 246.54
tom: -247.79
ivy: -931.79
max: -834.67
joe: 730.67
ana: -696.67

Settlements:
tom to sam: 247.79
ana to sam: 696.67
max to sam: 834.67
ben to joe: 730.67
ben to lia: 111.67
ivy to lia: 600.83
ivy to eva: 246.54
ivy to nik: 46.96
ivy to sam: 37.46
```

The `Invalid ...` messages come from the comment lines in the example file and can be ignored. `tom to sam: 247.79` means tom pays sam 247.79.

## Limitations

- Splits are always equal (apart from naming someone more than once).
- Names are case-sensitive.
- Comment lines work, but the script prints a message for each one.
- The settlement list isn't guaranteed to use the fewest possible payments.
- Amounts are plain floats, shown rounded to two decimals.

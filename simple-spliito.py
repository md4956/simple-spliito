EPSILON = 0.0001
# The exact search doubles in cost with every extra person
MAX_EXACT_PEOPLE = 18
# Printed instead of a report when no expense line could be read
HINT = """Nothing to calculate yet. Write one expense per line:
payer amount who shares it

Example:
# Dinner
ana 60 ana ben cy
ben 30 ben cy

The first line can be a # title. The amount is split between the people listed."""


def split_into_groups(amounts):
    """Split amounts into as many groups summing to zero as possible.

    A group of k people settles in k - 1 payments, so the most groups gives
    the fewest payments. Returns the groups as lists of indexes into amounts.
    """
    n = len(amounts)
    size = 1 << n
    totals = [0.0] * size  # sum of the amounts in each subset
    counts = [0] * size    # most zero-sum groups the subset can be built from
    removed = [0] * size   # index to remove to reach the best smaller subset

    for mask in range(1, size):
        best = -1
        for i in range(n):
            if mask & (1 << i):
                rest = mask ^ (1 << i)
                totals[mask] = totals[rest] + amounts[i]
                if counts[rest] > best:
                    best = counts[rest]
                    removed[mask] = i
        counts[mask] = best + (abs(totals[mask]) < EPSILON)

    groups = []
    group = []
    mask = size - 1
    while mask:
        i = removed[mask]
        group.append(i)
        mask ^= 1 << i
        if abs(totals[mask]) < EPSILON:
            groups.append(group)
            group = []
    return groups


def settle(balances, warnings):
    """Return the (payer, receiver, amount) payments that settle the balances."""
    people = [k for k, v in balances.items() if abs(v) >= EPSILON]
    if len(people) > MAX_EXACT_PEOPLE:
        warnings.append(f"Note: more than {MAX_EXACT_PEOPLE} people to settle, so the fewest payments isn't guaranteed.")
        groups = [people]
    else:
        groups = [[people[i] for i in group] for group in split_into_groups([balances[p] for p in people])]

    transactions = []
    for group in groups:
        debtors = {k: balances[k] for k in group if balances[k] > 0}
        creditors = {k: balances[k] for k in group if balances[k] < 0}

        while debtors and creditors:
            debtor = max(debtors.items(), key=lambda x: x[1])[0]
            creditor = min(creditors.items(), key=lambda x: x[1])[0]
            transfer = min(debtors[debtor], abs(creditors[creditor]))

            transactions.append((creditor, debtor, transfer))
            debtors[debtor] -= transfer
            creditors[creditor] += transfer

            if debtors[debtor] < EPSILON:
                del debtors[debtor]
            if creditors[creditor] > -EPSILON:
                del creditors[creditor]
    return transactions


def report_blocks(balances, transactions, unit, label):
    """Return the blocks of one currency section: payments first, then balances and totals.

    unit is the currency code, or '' for plain numbers. It is added after each amount.
    label is the name shown in each heading, or '' when there is nothing to add.
    """
    from collections import defaultdict

    suffix = f" {unit}" if unit else ""
    heading_suffix = f" ({label})" if label else ""

    payments = [f"PAYMENTS{heading_suffix}"]
    if not transactions:
        payments.append("Everyone is settled.")
    else:
        by_payer = defaultdict(list)
        for payer, receiver, amount in transactions:
            by_payer[payer].append((receiver, amount))
        paid = {payer: sum(amount for _, amount in items) for payer, items in by_payer.items()}
        single = sorted((p for p in by_payer if len(by_payer[p]) == 1), key=lambda p: -paid[p])
        multi = sorted((p for p in by_payer if len(by_payer[p]) > 1), key=lambda p: -paid[p])

        # Everyone who pays once comes first, then each person who pays several times
        for payer in single + multi:
            for receiver, amount in sorted(by_payer[payer], key=lambda x: -x[1]):
                payments.append(f"{payer} pays {receiver} {amount:,.2f}{suffix}")

    balance_lines = [f"BALANCES{heading_suffix}"]
    for person, balance in sorted(balances.items(), key=lambda x: -x[1]):
        if abs(balance) < 0.005:
            balance_lines.append(f"{person} is settled")
        elif balance > 0:
            balance_lines.append(f"{person} gets {balance:,.2f}{suffix}")
        else:
            balance_lines.append(f"{person} owes {-balance:,.2f}{suffix}")

    total = sum(balances.values())
    if abs(total) < 0.005:
        total_text = f"0.00{suffix}"
    else:
        total_text = f"{total:,.2f}{suffix} (should be 0.00, calculation bug)"
    people_word = "person" if len(balances) == 1 else "people"
    payment_word = "payment" if len(transactions) == 1 else "payments"
    summary = [f"{len(balances)} {people_word}, {len(transactions)} {payment_word}, total {total_text}"]

    return [payments, balance_lines, summary]


def emit(blocks):
    """Print blocks of lines, with one blank line between blocks."""
    print("\n\n".join("\n".join(block) for block in blocks))


def main():
    import math
    import sys
    from collections import defaultdict

    if len(sys.argv) != 2:
        print("Usage: python3 simple-spliito.py expenses.txt (or expenses.md)")
        sys.exit(1)

    filename = sys.argv[1]
    if not filename.lower().endswith(('.txt', '.md')):
        print(f"Unsupported file type: {filename}. Use a .txt or .md file.")
        sys.exit(1)
    balances = defaultdict(lambda: defaultdict(float))  # currency -> person -> balance
    currency = ''
    title = ''
    warnings = []  # shown in a WARNINGS block after the report

    try:
        # utf-8-sig skips the byte-order mark some editors add at the start of the file
        with open(filename, 'r', encoding='utf-8-sig') as file:
            for index, raw_line in enumerate(file):
                if index == 0 and raw_line.lstrip().startswith('#'):
                    title = raw_line.lstrip()[1:].strip()
                head, comment_start, _ = raw_line.partition('#')
                line = head.strip()
                if comment_start and head[-1:] not in ('', ' ', '\t'):
                    warnings.append(f"Warning: '#' right after a name starts a comment: {raw_line.strip()}")
                if not line:
                    continue
                if line.startswith('@'):
                    codes = line[1:].split()
                    if len(codes) > 1:
                        warnings.append(f"Invalid currency: {line}")
                        continue
                    currency = codes[0] if codes else ''
                    continue

                parts = line.split()
                if len(parts) < 3:
                    warnings.append(f"Invalid line: {line}")
                    continue
                payer = parts[0]
                try:
                    amount = float(parts[1])
                    if not math.isfinite(amount):
                        raise ValueError
                except ValueError:
                    warnings.append(f"Invalid amount: {parts[1]} in line: {line}")
                    continue
                related_to = [p for p in ','.join(parts[2:]).split(',') if p]

                if not related_to:
                    warnings.append(f"Invalid related_to list in line: {line}")
                    continue

                names = [payer, *related_to]
                if any('*' in name or '~' in name for name in names):
                    warnings.append(f"Error: '*' and '~' are not allowed in names: {line}")
                    emit([["WARNINGS", *warnings]])  # no report, because the expenses are incomplete
                    sys.exit(1)
                if any('_' in name for name in names):
                    warnings.append(f"Warning: '_' in a name can turn text italic in messengers: {line}")

                share = amount / len(related_to)
                balances[currency][payer] += amount
                for person in related_to:
                    balances[currency][person] -= share

    except FileNotFoundError:
        print(f"File {filename} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    blocks = []
    if title:
        if any(char in title for char in '_*~'):
            warnings.append(f"Warning: '_', '*' and '~' in the title can change how messengers show it: {title}")
        blocks.append([title])

    if balances:
        # Plain-number expenses come first, then each currency in the order it first appears
        multiple = len(balances) > 1
        for unit, person_balances in balances.items():
            label = unit or ('NO CURRENCY' if multiple else '')
            blocks += report_blocks(person_balances, settle(person_balances, warnings), unit, label)
    else:
        blocks.append([HINT])

    if warnings:
        blocks.append(["WARNINGS", *warnings])
    emit(blocks)


if __name__ == "__main__":
    main()

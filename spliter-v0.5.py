def main():
    import sys
    from collections import defaultdict

    if len(sys.argv) != 2:
        print("Usage: python3 splitter-v0.5.py expenses.txt")
        sys.exit(1)

    filename = sys.argv[1]
    balances = defaultdict(float)
    transactions = []

    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) < 3:
                    print(f"Invalid line: {line}")
                    continue
                payer = parts[0]
                try:
                    amount = float(parts[1])
                except ValueError:
                    print(f"Invalid amount: {parts[1]} in line: {line}")
                    continue
                related_str = parts[2:]
                related_to = ','.join(related_str).split(',')

                if not related_to:
                    print(f"Invalid related_to list in line: {line}")
                    continue

                n = len(related_to)
                share = amount / n

                balances[payer] += amount
                for person in related_to:
                    balances[person] -= share

    except FileNotFoundError:
        print(f"File {filename} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    # Calculate settlements
    debtors = {k: v for k, v in balances.items() if v > 0}
    creditors = {k: v for k, v in balances.items() if v < 0}

    while debtors and creditors:
        debtor = max(debtors.items(), key=lambda x: x[1])[0]
        creditor = max(creditors.items(), key=lambda x: x[1])[0]
        transfer = min(debtors[debtor], abs(creditors[creditor]))

        transactions.append((debtor, creditor, transfer))
        debtors[debtor] -= transfer
        creditors[creditor] += transfer

        if debtors[debtor] < 0.0001:
            del debtors[debtor]
        if creditors[creditor] > -0.0001:
            del creditors[creditor]

    # Output the results
    print("\nBalances:      # negative means should pay, and positive means should receive")
    for person, balance in balances.items():
        print(f"{person}: {balance:.2f}")

    print("\nSettlements:")
    for debtor, creditor, amount in transactions:
        print(f"{creditor} to {debtor}: {amount:.2f}")
    print()

if __name__ == "__main__":
    main()

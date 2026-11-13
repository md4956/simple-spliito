# Weekend trip expenses
# Format: payer amount people (space or comma separated)
lia 1250 lia nik sam ben
# Mixed spaces and commas, decimal amount
nik 640.5 nik eva tom,ivy
sam 2100 sam ivy ben,max # dinner, split with ivy and ben
eva 980 eva joe tom
# Payer not in the list: tom paid the whole amount for max
tom 415 max
ben 362.75 ben nik,sam

joe 1480 joe ben eva ivy max ana
max 528 max tom joe
# Paid only for themselves: no effect on balances
ivy 297 ivy
# A name listed twice gets two shares
sam 900 sam ana ana lia

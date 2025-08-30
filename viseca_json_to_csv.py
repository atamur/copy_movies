import json
import csv
from datetime import datetime

fname = 'asya.json'
fd = open(fname, encoding ="ISO-8859-1")
data = json.load(fd)
transactions = [x for x in data['list'] if x['stateType'] == 'booked' and x['type'] != 'fee']
# print(transactions[0])
transactionsConverted = open(fname + '.csv', 'w', encoding ="ISO-8859-1")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

for row in transactions:
  print(row)
  date = datetime.fromisoformat(row['date']).strftime('%d/%m/%Y') # DD/MM/YYYY
  # Prefer prettyName over merchantName for Payee
  payee = row.get('prettyName') or row.get('merchantName', '')

  # If merchantName starts with a generic prefix, strip it and use the remainder as Payee
  generic_prefixes = ['google', "wp*"]
  merchant_name = row.get('merchantName', '') or ''
  mn_lower = merchant_name.strip().lower()
  for pref in generic_prefixes:
    if mn_lower.startswith(pref):
      remainder = merchant_name[len(pref):]
      # Strip common separators and whitespace from the remainder
      remainder = remainder.lstrip(" .:-_*#").strip()
      if remainder:
        payee = remainder
      break

  category = ''
  # Build memo from an explicit include list of fields
  include_keys = ['merchantName', 'merchantPlace', 'isOnline']
  memo_parts = []
  for k in include_keys:
    if k not in row:
      continue
    memo_parts.append(f"{k}={str(row.get(k))}")
  memo = " | ".join(memo_parts)
  amount = row['amount']

  # Check if the transaction is Debit (outflow) or Credit (inflow)
  if amount >= 0:
    outflow = amount
    inflow = '0'
  else:
    outflow = '0'
    inflow = -1*amount

  writer.writerow([date, payee, category, memo, outflow, inflow])

transactionsConverted.close()
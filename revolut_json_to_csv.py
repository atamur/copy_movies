import json
import csv, datetime

fname = 'revolut_ilya.json'
fd = open(fname, encoding ="ISO-8859-1")
data = json.load(fd)
# print({x['account']['id'] for x in data if x['state'] == 'COMPLETED'})

transactions = [x for x in data if x['state'] == 'COMPLETED']

transactionsConverted = open(fname + '.csv', 'w', encoding ="ISO-8859-1")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

for row in transactions:
  print(row)
  date = datetime.datetime.fromtimestamp(row['createdDate'] / 1000).strftime('%d/%m/%Y') # DD/MM/YYYY
  if 'merchant' in row and 'name' in row['merchant'] and row['merchant']['name'] not in ['Paypal']:
    payee = row['merchant']['name']
  else:
    payee = row['description']
  category = ''
  memo = row['description']

  if row['type'] == 'EXCHANGE':
    if row['counterpart']['currency'] in ['ETH']:
      pass # this is fine, we treat this as spending
    else:
      continue # other exchanges we ignore

  amount = row['amount'] / 100
  if 'fee' in row:
    amount -= row['fee'] / 100
  if row['currency'] != 'CHF':
    raise AssertionError('currency ' + row['currency'])

  amount = round(amount, 2)

  if amount == 0:
    continue # skip empty

  # Check if the transaction is Debit (outflow) or Credit (inflow)
  if amount >= 0:
    outflow = 0
    inflow = amount
  else:
    outflow = -1 * amount
    inflow = 0

  writer.writerow([date, payee, category, memo, outflow, inflow])

transactionsConverted.close()
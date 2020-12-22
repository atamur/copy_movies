import json
import csv, time

fname = 'viseca_ilya.json'
fd = open(fname, encoding ="ISO-8859-1")
data = json.load(fd)
transactions = [x for x in data['list'] if x['stateType'] == 'booked' and x['type'] != 'fee']
# print(transactions[0])
transactionsConverted = open(fname + '.csv', 'w')
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

for row in transactions:
  print(row)
  date = time.strftime('%d/%m/%Y', time.strptime(row['date'], '%Y-%m-%dT%H:%M:%S')) # DD/MM/YYYY
  payee = row['merchantName']
  category = ''
  memo = row['details']
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
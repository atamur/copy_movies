import json
import csv, time
import pandas as pd

pd.set_option('display.max_columns', None)

fname = 'transactions.xls'
df = pd.read_excel(fname)
df = df[df['Status'] == 'Settled transaction']

transactionsConverted = open(fname + '.csv', 'w', encoding ="ISO-8859-1")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

for index, row in df.iterrows():
  print(row)
  date = row['Date']
  payee = row['Description']
  category = ''
  memo = ''
  amount = row['Amount']

  # Check if the transaction is Debit (outflow) or Credit (inflow)
  if amount >= 0:
    outflow = amount
    inflow = '0'
  else:
    outflow = '0'
    inflow = -1*amount

  writer.writerow([date, payee, category, memo, outflow, inflow])

transactionsConverted.close()
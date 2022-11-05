import csv, time
import pandas as pd

pd.set_option('display.max_columns', None)

def escape(str):
  return ''.join([x if ord(x) < 255 else '?' for x in str])

fname = 'account-statement_2022-07-01_2022-09-10_en_b66ded.csv'
df = pd.read_csv(fname)
df = df[df['State'] == 'COMPLETED']

transactionsConverted = open(fname + '.csv', 'w', encoding ="ISO-8859-1")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

for index, row in df.iterrows():
  print(row)
  date = time.strftime('%d/%m/%Y', time.strptime(row['Started Date'], '%Y-%m-%d %H:%M:%S')) # DD/MM/YYYY
  payee = row['Description']
  category = ''
  memo = ''
  amount = row['Amount'] - row['Fee']

  amount = round(amount, 2)

  if amount == 0:
    continue # skip empty

  if payee == 'To CHF':
    continue # skip transactions between current and savings

  # Check if the transaction is Debit (outflow) or Credit (inflow)
  if amount >= 0:
    outflow = 0
    inflow = amount
  else:
    outflow = -1 * amount
    inflow = 0

  writer.writerow([date, escape(payee), category, memo, outflow, inflow])

transactionsConverted.close()

import argparse
import json
import csv, time
from pathlib import Path
import pandas as pd

pd.set_option('display.max_columns', None)

parser = argparse.ArgumentParser(description='Convert Corner XLS export to YNAB CSV.')
parser.add_argument('input', help='Path to Corner XLS export')
args = parser.parse_args()

input_path = Path(args.input)
fname = input_path.name
df = pd.read_excel(input_path)
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

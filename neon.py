import argparse
import csv, time
from pathlib import Path

parser = argparse.ArgumentParser(description='Convert Neon export to YNAB CSV.')
parser.add_argument('input', help='Path to Neon CSV export')
args = parser.parse_args()

input_path = Path(args.input)
if input_path.suffix.lower() != '.csv':
  input_path = input_path.with_suffix('.csv')

fname = input_path.with_suffix('').name
fd = open(input_path, encoding ="windows-1252")
transactions = csv.DictReader(fd, delimiter=';' )

transactionsConverted = open(fname + ' conv.csv', 'w', encoding ="UTF-8")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

for row in transactions:
  print(row)

  date = time.strftime('%d/%m/%Y', time.strptime(row['Date'], '%Y-%m-%d')) # DD/MM/YYYY
  payee = row['Description'].split('  ')[0]
  if payee == "Google":
    payee = "Play Store"
  category = ''
  memo = row['Subject']

  amount = float(row['Amount'])
  if amount >= 0:
    outflow = 0
    inflow = amount
  else:
    outflow = -1 * amount
    inflow = 0

  writer.writerow([date, payee, category, memo, outflow, inflow])

transactionsConverted.close()

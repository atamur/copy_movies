import json
import csv, time

fname = 'ubs credit card 2'
fd = open(fname + ".csv", encoding ="windows-1252")
next(fd) # skip sep line
transactions = csv.DictReader(fd, delimiter=';' )

transactionsConverted = open(fname + ' conv.csv', 'w', encoding ="UTF-8")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

def parse(str):
  str = str.replace('\'','')
  if str == '':
    return 0.0
  return float(str)

for row in transactions:
  print(row)

  if not row['Account number']:
    continue

  date = time.strftime('%d/%m/%Y', time.strptime(row['Booked'], '%d.%m.%Y')) # DD/MM/YYYY
  payee = row['Booking text'].split('  ')[0]
  category = ''
  memo = row['Booking text']

  outflow = parse(row['Debit'])
  inflow = parse(row['Credit'])

  if outflow == 0 and inflow == 0:
    continue

  writer.writerow([date, payee, category, memo, outflow, inflow])

transactionsConverted.close()
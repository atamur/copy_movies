import csv, time

fname = '2022_10_account_statements'
fd = open(fname + ".csv", encoding ="windows-1252")
transactions = csv.DictReader(fd, delimiter=';' )

transactionsConverted = open(fname + ' conv.csv', 'w', encoding ="UTF-8")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])

for row in transactions:
  print(row)

  date = time.strftime('%d/%m/%Y', time.strptime(row['Date'], '%Y-%m-%d')) # DD/MM/YYYY
  payee = row['Description'].split('  ')[0]
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
import csv, time
import sys
sys.stdout.reconfigure(encoding='utf-8')  # Python 3.7+

fname = 'export'
fd = open(fname + ".csv", encoding ="UTF-8-sig")
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
  if row['Individual amount']:
    print(row['Description 1'])
    continue

  print(row)

  if not row['Trade date']:
    continue

  date = time.strftime('%d/%m/%Y', time.strptime(row['Trade date'], '%Y-%m-%d')) # DD/MM/YYYY
  if row['Description1'] in ['Payment', 'Salary Payment', 'Credit UBS TWINT', 'e-banking Order']:
    payee = row['Description2']
  elif row['Description1'] in []:
    payee = row['Description3']
  elif row['Description1'] in ['Debit card payment']:
    payee = row['Description3'].split(',')[0]
  else:
    payee = row['Description1']
  category = ''
  memo = row['Description1'] + '; ' + row['Description2'] + '; ' + row['Description3']

  outflow = parse(row['Debit'])
  if outflow < 0:
    outflow = -outflow
  inflow = parse(row['Credit'])

  if outflow == 0 and inflow == 0:
    continue

  writer.writerow([date, payee, category, memo, outflow, inflow])

transactionsConverted.close()
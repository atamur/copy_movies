import csv, time
import re

fname = 'export_transactions_20221105'
fd = open(fname + ".csv", encoding ="UTF-8-sig")
transactions = csv.DictReader(fd, delimiter=';' )

transactionsConverted = open(fname + ' conv.csv', 'w', encoding ="UTF-8")
writer = csv.writer(transactionsConverted)

# Write header row
writer.writerow(['Date','Payee','Category','Memo','Outflow','Inflow'])


def parse(str):
  if not str:
    return 0.0
  return float(str.replace("'", ""))

for row in transactions:
  print(row)

  pf_date = row['Date']
  if not pf_date:
    continue

  outflow = -parse(row['Debit in CHF'])
  inflow = parse(row['Credit in CHF'])

  if outflow == 0 and inflow == 0:
    continue

  date = time.strftime('%d/%m/%Y', time.strptime(pf_date, '%d.%m.%Y')) # DD/MM/YYYY
  memo = row['Notification text']

  if memo.startswith('CASH WITHDRAWAL'):
    if 'XXXX6722' in memo:
      payee = 'Ilya Cash'
    else:
      payee = 'Asya Cash'
  elif memo.startswith('PRICE FOR CASH WITHDRAWAL') or memo.startswith('PRICE FOR BANKING'):
    payee = 'Postfinance'
  elif memo.startswith('DEBIT'):
    result = re.search(r"^DEBIT.*?CH[^ ]{19}(.*?)(SENDER'S REFERENCE: (.*?)(\d+|$)|$)", memo)
    payee = result.group(1)
    ref = result.group(3)
    if ref:
      payee = ref
    if payee.strip().upper() == "ILYA PYATIGORSKIY":
      more_result = re.search(r"^DEBIT(.*?)CH[^ ]{19}", memo)
      bank = more_result.group(1)
      if bank:
        payee = payee + " / " + bank
  elif memo.startswith('ISR'):
    result = re.search(r"ISR.*\d+-\d+-\d+(.*?)(SENDER'S REFERENCE: (.*?)(\d+|$)|$)", memo)
    payee = result.group(1)
    ref = result.group(3)
    if ref:
      payee = ref
  elif memo.startswith('CREDIT MAILER'):
    if 'Pyatigorskiy I. et/ou Pyatigorskaya'.upper() in memo.upper():
      payee = 'BCGE'
    else:
      payee = re.search(r"CREDIT MAILER: (.*) COMMENTS:", memo).group(1)
  elif memo.startswith('CREDIT'):
    payee = re.search(r"CREDIT CH[^ ]{19} MAILER: (.*) COMMENTS:", memo).group(1)
  elif memo.startswith('TWINT PURCHASE/SERVICE'):
    result = re.search(r"FROM TELEPHONE NO. \+\d+ (.*)$", memo)
    if result:
      payee = result.group(1)
    else:
      payee = re.search(r"TWINT PURCHASE/SERVICE FROM [\d.]*(.*) ", memo).group(1)
  elif memo.startswith('TWINT SEND MONEY'):
    payee = re.search(r"TO MOBILE NO\. \+\d+(.*)( NOTICES: (.*)|$)", memo).group(1)
  else:
    payee = row['Notification text']
  payee = payee.strip()

  if payee == 'Cornèr Banca SA 6901 Lugano':
    payee = 'Corner'
  if payee.startswith('SWICA'):
    if outflow < 1400:
      payee = 'Swica Reimbursment'
    elif outflow > 1400:
      payee = 'Swica'

  category = ''
  print('---' + payee)

  writer.writerow([date, payee, category, memo, outflow, inflow])

transactionsConverted.close()
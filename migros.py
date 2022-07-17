# 2021: 13925479 13854000 13759514 13692207 13670724 13621575 13569007 13501582 13457406 13413689 13381156 13335864 13287107 13253231
# before: 13222058 13174096 13112763 13025263 12966078 12925110 12899768 12886568 12827135 12791370 12748969 12737140 12691751 12673904 12653386 12578684 12552246 12396137 12360725 12312943 12287884 12238305 12213928 12213906 12188266 12167804 12137881 12118728 12109323
# before apr 2020: 12037309 11961795 11961791 11880693 11695297 11681123 11566285 11513273 11376980 11267016 11154349 11077193 11034848 11017670 10919707 10919693 10818141 10728208 10548141 10533722 10426155 10367361
import os
import json
import pandas as pd
import urllib3
from sqlite_cache.sqlite_cache import SqliteCache
import dateutil.parser

sql_cache = SqliteCache('./cache')
http = urllib3.PoolManager()

def fetch_categories(product):
    product = str(product)
    info = sql_cache.get(product)
    if info is None:
        print('requesting product ' + product)
        r = http.request('GET',
                         "https://shop.migros.ch/supermarket/public/v1/api/breadcrumb/language/en/products/{}".format(
                             product),
                         headers={
                             "accept": "application/json, text/plain, */*",
                             "accept-language": "en",
                             "leshopch": "eyJsdmwiOiJVIiwiZW5jIjoiQTI1NkdDTSIsImFsZyI6ImRpciIsImtpZCI6ImU3NGQ5ZDI1LTBkYTUtNDVkZi04NmEzLTE1MWRhNGVkN2M1ZiJ9..zqlSDT4W3XH8dvi1.Ef3mQApGsn6yArQHFtDMssCV2H_42EOYAGpbq9_vPcBfATW6H1pQjS5Zpj6z0jx2LoF2AE-4OfiIJvFVVx6yzKtndz1R6IuK4XGTPEhXMIIIjx-VTJs4ytmBE-pfiNjAAxUIZgTA6GoHUx-VHWEzr4GgcNuywS9rLUVGPmROZcXh8GOX7niQyu4M_kTAArd8ES7Lf342DHsvbCLPZ1zcX1myhPLC_KgKCwcpqa7c2Vlc2CzqCz1z7wWe6f8h5FhRXyNCmi8uIoVY923MTRHULjtYR71w.VNnp7I4WYvyEEru-nkxvFA"
                         }
                         )
        print(r.data.decode('utf-8'))
        try:
            cats = json.loads(r.data.decode('utf-8'))[product]['categories']
            info = [x['slug'] for x in cats]
        except:
            info = ['unknown', 'unknown','unknown']
        sql_cache.set(product, info)
    return info


def add_cat_columns(product):
    cats = fetch_categories(product)
    return pd.Series({'cat1': cats[0], 'cat2': cats[1], 'cat3': cats[2]})

def file_to_df(file):
    fd = open(file, encoding="utf8")
    data = json.load(fd)
    df = pd.json_normalize(data[0]['details']['positions'])
    del df['promotions']

    date = dateutil.parser.parse(data[0]['creationDate'])
    df['creationMonth'] = date.strftime('%Y-%m')
    df['creationDate'] = date.strftime('%Y-%m-%d')
    df['orderNumber'] = data[0]['orderNumber']
    return df.merge(df['productId'].apply(add_cat_columns), left_index=True, right_index=True)


df = None
for root, dirs, files in os.walk('./'):
    for file in files:
        if file.startswith('m_'):
            new_df = file_to_df(file)
            if df is None:
                df = new_df
            else:
                df = df.append(new_df, ignore_index=True)

cols = df.columns.tolist()
# cols = cols[-6:] + cols[:-6]
# creationMonth,creationDate,orderNumber,cat1,cat2,cat3,itemNumber,state,productId,productName,brand,brandLine,requestedQuantity,deliveredQuantity,adjustedPrice,quotedPrice,weightedQuotedPrice,adjustedWeight,modificationNumber,deviceName,cumulus,taxRate,volume,temperature,sizeUnit,minimumSize,maximumSize,weight,basePrice
cols = cols[-7:] + ['productName','deliveredQuantity','adjustedPrice']
df = df[cols]
df.to_csv('migros.csv', index=False, encoding='utf8')





#
#
# fetch("https://shop.migros.ch/supermarket/public/v1/api/breadcrumb/language/en/products/229869", {
#   "headers": {
#     "accept": "application/json, text/plain, */*",
#     "accept-language": "en",
#     "leshopch": "eyJsdmwiOiJVIiwiZW5jIjoiQTI1NkdDTSIsImFsZyI6ImRpciIsImtpZCI6ImU3NGQ5ZDI1LTBkYTUtNDVkZi04NmEzLTE1MWRhNGVkN2M1ZiJ9..zqlSDT4W3XH8dvi1.Ef3mQApGsn6yArQHFtDMssCV2H_42EOYAGpbq9_vPcBfATW6H1pQjS5Zpj6z0jx2LoF2AE-4OfiIJvFVVx6yzKtndz1R6IuK4XGTPEhXMIIIjx-VTJs4ytmBE-pfiNjAAxUIZgTA6GoHUx-VHWEzr4GgcNuywS9rLUVGPmROZcXh8GOX7niQyu4M_kTAArd8ES7Lf342DHsvbCLPZ1zcX1myhPLC_KgKCwcpqa7c2Vlc2CzqCz1z7wWe6f8h5FhRXyNCmi8uIoVY923MTRHULjtYR71w.VNnp7I4WYvyEEru-nkxvFA",
#     "peer-id": "website-js-53.3.2",
#     "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google Chrome\";v=\"90\"",
#     "sec-ch-ua-mobile": "?0",
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "x-correlation-id": "bb0636ec-b3f3-4f05-9210-0564c12b799f"
#   },
#   "referrer": "https://shop.migros.ch/en/supermarket/home",
#   "referrerPolicy": "strict-origin-when-cross-origin",
#   "body": null,
#   "method": "GET",
#   "mode": "cors",
#   "credentials": "include"
# });
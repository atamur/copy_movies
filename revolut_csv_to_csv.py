import csv
from datetime import datetime
import pandas as pd
import requests

# --- Installation ---
# You need to install the pandas and requests libraries first.
# Open your terminal or command prompt and run:
# pip install pandas requests

# --- Configuration ---
# Place your Revolut CSV file in the same directory as this script.
# Update the FNAME variable to match your file's name.
FNAME = 'account-statement_2025-01-01_2025-08-24_en-us_873a73.csv'
TARGET_CURRENCY = 'CHF'

# --- Caching ---
# A dictionary to store exchange rates we've already fetched to speed up
# the script and reduce the number of API calls.
rate_cache = {}


# --- Functions ---

def get_converted_amount(date_obj, from_currency, to_currency, amount):
    """
    Converts an amount using historical exchange rates from the Frankfurter.app API.
    Includes caching to avoid redundant API calls.
    """
    # Don't convert if it's already the target currency
    if from_currency == to_currency:
        return amount

    date_str = date_obj.strftime('%Y-%m-%d')

    # Check the cache first
    if (date_str, from_currency) in rate_cache:
        rate = rate_cache[(date_str, from_currency)]
        return amount * rate

    # If not in cache, fetch from the API
    try:
        print(f"Fetching rate for {from_currency} to {to_currency} on {date_str}...")
        url = f"https://api.frankfurter.app/{date_str}?from={from_currency}&to={to_currency}"
        # Set a timeout to prevent the script from hanging indefinitely
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an error for bad responses (4xx or 5xx)

        data = response.json()
        rate = data['rates'][to_currency]

        # Save the rate to the cache
        rate_cache[(date_str, from_currency)] = rate

        return amount * rate
    except requests.exceptions.Timeout:
        print(f"  [Error] The request timed out for {from_currency} on {date_str}.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [Error] Could not fetch exchange rate for {from_currency} on {date_str}: {e}")
        return None
    except KeyError:
        print(f"  [Error] Rate for '{to_currency}' not found in API response for {date_str}.")
        return None


def escape(text_string):
    """Removes characters that can cause issues with CSV encoding."""
    return ''.join([char if ord(char) < 255 else '?' for char in str(text_string)])


# --- Main Script ---

try:
    df = pd.read_csv(FNAME)
except FileNotFoundError:
    print(f"Error: The file '{FNAME}' was not found. Please check the file name and location.")
    exit()

# Filter for only completed transactions and create a copy to avoid pandas warnings
df = df[df['State'] == 'COMPLETED'].copy()

# Prepare the new CSV file for YNAB 4 format
output_filename = FNAME.replace('.csv', '_ynab.csv')
with open(output_filename, 'w', encoding="ISO-8859-1", newline='') as transactions_converted:
    writer = csv.writer(transactions_converted)

    # Write the header row required by YNAB
    writer.writerow(['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow'])

    print(f"Processing {len(df)} completed transactions...")

    # Iterate over each transaction row in the DataFrame
    for index, row in df.iterrows():
        # --- 1. Data Extraction ---
        try:
            started_date_str = row['Started Date']
            date_obj = datetime.strptime(started_date_str, '%Y-%m-%d %H:%M:%S')
            ynab_date = date_obj.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            print(f"Warning: Skipping row {index + 2} due to invalid date: {row.get('Started Date', 'N/A')}")
            continue

        payee = row['Description']
        original_amount = row['Amount']
        fee = row['Fee']
        original_currency = row['Currency']
        memo = '' if original_currency == TARGET_CURRENCY else f"Original: {original_amount:.2f} {original_currency}"

        net_amount = original_amount - fee

        # --- 2. Skip Unnecessary Transactions ---
        if net_amount == 0:
            continue
        if payee == f'To {TARGET_CURRENCY}':
            continue

        # --- 3. Currency Conversion ---
        final_amount = get_converted_amount(date_obj, original_currency, TARGET_CURRENCY, net_amount)

        if final_amount is None:
            print(f"Warning: Skipping transaction for '{payee}' on {date_obj.date()} due to conversion failure.")
            continue  # Skip this transaction if conversion fails

        if original_currency != TARGET_CURRENCY:
            memo += f" | Converted: {final_amount:.2f} {TARGET_CURRENCY}"

        final_amount = round(final_amount, 2)

        # --- 4. Determine Outflow/Inflow for YNAB ---
        if final_amount >= 0:
            outflow = 0
            inflow = final_amount
        else:
            outflow = -1 * final_amount
            inflow = 0

        # --- 5. Write to YNAB CSV ---
        writer.writerow([ynab_date, escape(payee), '', escape(memo), outflow, inflow])

print(f"\nConversion complete! Your YNAB-ready file is saved as '{output_filename}'")

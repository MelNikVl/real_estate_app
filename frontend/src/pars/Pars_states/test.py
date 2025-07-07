import requests
import csv
import io

url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/state/totals/nst-est2024-hu.csv"
resp = requests.get(url)
resp.raise_for_status()
csv_text = resp.text

reader = csv.DictReader(io.StringIO(csv_text))
for row in reader:
    if row["NAME"] in ("Texas", "California"):
        print(f"{row['NAME']}:")
        print(f"  Housing Units 2024: {row['HU2024']}")
        print(f"  Housing Units 2023: {row['HU2023']}")
        




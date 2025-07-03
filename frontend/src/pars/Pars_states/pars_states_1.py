import sqlite3
import requests

# Функция скачивания через API US Census
def fetch_housing_data(state_fips):
    base = "https://api.census.gov/data/2022/pep/housing"
    params = {
        "get": "HU,HUH",
        "for": f"state:{state_fips}"
    }
    resp = requests.get(base, params=params)
    resp.raise_for_status()
    headers, values = resp.json()
    return dict(zip(headers, values))

# FIPS-коды: TX=48, CA=06
states = {"TX": "48", "CA": "06"}

conn = sqlite3.connect("real_estate.db")
cur = conn.cursor()

# Таблица контекстных данных должна уже существовать
for state_code, fips in states.items():
    data = fetch_housing_data(fips)
    # Пример: {'HU': 'X', 'HUH': 'Y', 'state': '48'}
    cur.execute("""
        INSERT INTO property_context_data (property_id, source, data_key, data_value)
        VALUES (?, ?, ?, ?)
    """, (None, "census_housing", f"{state_code}_HU", data["HU"]))
    cur.execute("""
        INSERT INTO property_context_data (property_id, source, data_key, data_value)
        VALUES (?, ?, ?, ?)
    """, (None, "census_housing", f"{state_code}_HUH", data["HUH"]))

conn.commit()
conn.close()
print("Скачаны данные по жилью для TX и CA")

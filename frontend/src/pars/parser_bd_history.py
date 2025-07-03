import sqlite3
from bs4 import BeautifulSoup

with open("redfin_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

def get_meta(name):
    tag = soup.find("meta", {"name": name})
    return tag["content"] if tag and "content" in tag.attrs else None

def clean_number(value):
    if not value:
        return None
    return int(value.replace("$", "").replace(",", "").strip())

# Предположим, ты потом добавишь реальные извлечения:
year_built = None
property_type = None

# Данные
data = {
    "url": get_meta("twitter:url:landing_url"),
    "address": get_meta("twitter:text:street_address"),
    "city": get_meta("twitter:text:city"),
    "state": get_meta("twitter:text:state_code"),
    "zip": get_meta("twitter:text:zip"),
    "price": clean_number(get_meta("twitter:text:price")),
    "beds": clean_number(get_meta("twitter:text:beds")),
    "baths": clean_number(get_meta("twitter:text:baths")),
    "sqft": clean_number(get_meta("twitter:text:sqft")),
    "year_built": year_built,
    "property_type": property_type,
    "description": get_meta("description")
}

# --- БД ---
conn = sqlite3.connect("real_estate.db")
cur = conn.cursor()

# Создание таблиц
cur.execute("""
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    beds INTEGER,
    baths INTEGER,
    sqft INTEGER,
    year_built INTEGER,
    property_type TEXT,
    description TEXT
)""")

cur.execute("""
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    price INTEGER,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id)
)""")

cur.execute("""
CREATE TABLE IF NOT EXISTS property_context_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    source TEXT,
    data_key TEXT,
    data_value TEXT,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id)
)""")

# --- Сохранение ---
cur.execute("SELECT id FROM properties WHERE url = ?", (data["url"],))
row = cur.fetchone()

if row:
    property_id = row[0]
else:
    cur.execute("""
    INSERT INTO properties (url, address, city, state, zip, beds, baths, sqft, year_built, property_type, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["url"], data["address"], data["city"], data["state"], data["zip"],
        data["beds"], data["baths"], data["sqft"], data["year_built"], data["property_type"],
        data["description"]
    ))
    property_id = cur.lastrowid

# История цен
cur.execute("""
SELECT price FROM price_history WHERE property_id = ? ORDER BY scraped_at DESC LIMIT 1
""", (property_id,))
last_price = cur.fetchone()

if not last_price or last_price[0] != data["price"]:
    cur.execute("INSERT INTO price_history (property_id, price) VALUES (?, ?)",
                (property_id, data["price"]))
    print(f"Цена обновлена: {data['price']}")
else:
    print("Цена не изменилась")

conn.commit()
conn.close()

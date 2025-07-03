
import sqlite3
import requests
from bs4 import BeautifulSoup

def get_meta(soup, name):
    tag = soup.find("meta", {"name": name})
    return tag["content"] if tag and "content" in tag.attrs else None

def clean_number(value):
    if not value:
        return None
    return int(value.replace("$", "").replace(",", "").strip())

def extract_extra_data(soup):
    year_built = None
    property_type = None

    all_text = soup.find_all(text=True)
    for i, text in enumerate(all_text):
        if not text or not isinstance(text, str):
            continue
        clean_text = text.strip().lower()

        if clean_text == "year built":
            try:
                year_built = int(all_text[i + 1].strip())
            except:
                pass

        if clean_text == "property type":
            try:
                property_type = all_text[i + 1].strip()
            except:
                pass

    return year_built, property_type

def add_context_data(cur, property_id, source, data_dict):
    for key, value in data_dict.items():
        cur.execute("""
        INSERT INTO property_context_data (property_id, source, data_key, data_value)
        VALUES (?, ?, ?, ?)
        """, (property_id, source, key, str(value)))

# Загружаем HTML с локального файла
with open("redfin_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

data = {
    "url": get_meta(soup, "twitter:url:landing_url"),
    "address": get_meta(soup, "twitter:text:street_address"),
    "city": get_meta(soup, "twitter:text:city"),
    "state": get_meta(soup, "twitter:text:state_code"),
    "zip": get_meta(soup, "twitter:text:zip"),
    "price": clean_number(get_meta(soup, "twitter:text:price")),
    "beds": clean_number(get_meta(soup, "twitter:text:beds")),
    "baths": clean_number(get_meta(soup, "twitter:text:baths")),
    "sqft": clean_number(get_meta(soup, "twitter:text:sqft")),
    "description": get_meta(soup, "description")
}

year_built, property_type = extract_extra_data(soup)
data["year_built"] = year_built
data["property_type"] = property_type

# Работа с базой
conn = sqlite3.connect("real_estate.db")
cur = conn.cursor()

# Таблицы
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

# Сохраняем property
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
cur.execute("SELECT price FROM price_history WHERE property_id = ? ORDER BY scraped_at DESC LIMIT 1", (property_id,))
last_price = cur.fetchone()

if not last_price or last_price[0] != data["price"]:
    cur.execute("INSERT INTO price_history (property_id, price) VALUES (?, ?)",
                (property_id, data["price"]))
    print(f"Цена обновлена: {data['price']}")
else:
    print("Цена не изменилась")

# Загрузка демографических данных (пример с фейковыми данными)
# TODO: заменить на реальный API или CSV
context_data = {
    "population_density": 3200,
    "crime_index": "moderate",
    "median_income": 58000
}
add_context_data(cur, property_id, "demo_source", context_data)

conn.commit()
conn.close()
print("Все данные сохранены.")

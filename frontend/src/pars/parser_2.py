from bs4 import BeautifulSoup

with open("redfin_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

def get_meta(name):
    tag = soup.find("meta", {"name": name})
    return tag["content"] if tag and "content" in tag.attrs else None

# Парсим данные
price = get_meta("twitter:text:price")
address = get_meta("twitter:text:street_address")
city = get_meta("twitter:text:city")
state = get_meta("twitter:text:state_code")
zip_code = get_meta("twitter:text:zip")
beds = get_meta("twitter:text:beds")
baths = get_meta("twitter:text:baths")
sqft = get_meta("twitter:text:sqft")
description = get_meta("description")

# Вывод результата
print("Цена:", price)
print("Адрес:", f"{address}, {city}, {state} {zip_code}")
print("Кровати:", beds)
print("Ванные:", baths)
print("Площадь:", sqft, "sqft")
print("Описание:", description)

import requests

url = "https://www.redfin.com/TX/Graham/1441-Brazos-St-76450/home/73776111"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

with open("redfin_test.html", "w", encoding="utf-8") as file:
    file.write(response.text)

print("HTML сохранён в redfin_test.html")

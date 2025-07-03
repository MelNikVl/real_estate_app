import requests

def fetch_housing_data(state_fips):
    base = "https://api.census.gov/data/2022/pep/charage"
    params = {
        "get": "NAME,POP,DATE_CODE",
        "for": f"state:{state_fips}"
    }
    resp = requests.get(base, params=params)
    resp.raise_for_status()
    headers, values = resp.json()
    return dict(zip(headers, values))

# Примеры: TX = 48, CA = 06
states = {"TX": "48", "CA": "06"}

for state_code, fips in states.items():
    data = fetch_housing_data(fips)
    print(f"{state_code}:")
    print(f"  Name: {data['NAME']}")
    print(f"  Population Estimate: {data['POP']}")
    print(f"  Year code: {data['DATE_CODE']}")
    print()

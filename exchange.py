import json
import random

DATA_FILE = "data.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_exchange_rates():
    data = load_data()
    for currency in data["exchange_rates"]:
        rate = data["exchange_rates"][currency]
        degisim = rate * random.uniform(-1.0, 0.25)  # %100 düşüş ile %25 artış arası
        yeni_fiyat = max(1, int(rate + degisim))
        data["exchange_rates"][currency] = yeni_fiyat
    save_data(data)

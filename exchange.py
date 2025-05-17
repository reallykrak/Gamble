import random
import json

DATA_FILE = "data.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_exchange_rates():
    data = load_data()
    rates = data.get("exchange_rates", {})

    for key in rates:
        change = random.randint(-45, 100)
        rates[key] = max(1, rates[key] + change)

    data["exchange_rates"] = rates
    save_data(data)
    return rates

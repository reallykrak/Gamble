import json
import random

DATA_FILE = "data.json"

def update_exchange_rates():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for currency in data["exchange_rates"]:
        rate = data["exchange_rates"][currency]
        change = rate * random.uniform(-0.25, 1.0)
        new_rate = max(1, int(rate + change))
        data["exchange_rates"][currency] = new_rate

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

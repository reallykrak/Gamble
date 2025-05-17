import json
import random

def update_exchange_rates():
    with open("data.json", "r") as f:
        data = json.load(f)

    rates = data["exchange_rates"]
    for key in rates:
        change_percent = random.randint(-25, 100)  # %25 düşüp %100 artar
        rates[key] = max(1, int(rates[key] * (1 + change_percent / 100)))

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

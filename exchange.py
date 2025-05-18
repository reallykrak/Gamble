import json
import random
import time

DATA_FILE = "data.json"

def update_exchange_rates():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for currency in data["exchange_rates"]:
        rate = data["exchange_rates"][currency]
        # %50 düşüp %50 artabilir
        change = rate * random.uniform(-0.5, 0.5)
        new_rate = max(1, int(rate + change))
        data["exchange_rates"][currency] = new_rate

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print("✅ Döviz kurları güncellendi!")

if __name__ == "__main__":
    while True:
        update_exchange_rates()
        time.sleep(120)  # Her 2 dakikada bir güncelle

import json, random, time

DATA_FILE = "data.json"

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_rates():
    data = load_data()
    rates = data.get("exchange_rates", {})
    for tur in rates:
        oran = rates[tur]
        degisim = random.uniform(-0.5, 1.0)  # %50 düşüş, %100 artış
        yeni = max(1, round(oran * (1 + degisim), 2))
        rates[tur] = yeni
    data["exchange_rates"] = rates
    save_data(data)
    print("💱 Döviz kurları güncellendi:", rates)

if __name__ == "__main__":
    while True:
        update_rates()
        time.sleep(120)

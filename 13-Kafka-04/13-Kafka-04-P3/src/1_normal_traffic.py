import json
import random
import time
import uuid
from datetime import datetime

from kafka import KafkaProducer


BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "enriched_features"
TRANSACTIONS_PER_SECOND = 2


MERCHANT_CATEGORIES = ["grocery", "electronics", "travel", "restaurant", "fuel", "online_retail"]
CARD_IDS = [f"card_{i:04d}" for i in range(1, 51)]
MERCHANT_IDS = [f"merchant_{i:03d}" for i in range(1, 21)]

# normal amount range per category
AMOUNT_RANGES = {
    "grocery": (5, 150),
    "electronics": (20, 1200),
    "travel": (50, 2500),
    "restaurant": (8, 120),
    "fuel": (20, 100),
    "online_retail": (5, 300),
}


def make_clean_transaction():
    category = random.choice(MERCHANT_CATEGORIES)
    lo, hi = AMOUNT_RANGES[category]
    return {
        "txn_id": str(uuid.uuid4()),
        "card_id": random.choice(CARD_IDS),
        "merchant_id": random.choice(MERCHANT_IDS),
        "amount": round(random.uniform(lo, hi), 2),
        "merchant_category": category,
        "txn_ts": int(time.time() * 1000),
        "velocity_score": round(random.uniform(0.0, 3.0), 2),
        "geo_distance_km": round(random.uniform(0.1, 50.0), 2),
    }


def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        key_serializer=lambda k: k.encode("utf-8"), # type: ignore
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print("Sending normal traffic. Press Ctrl+C to stop.\n")
    try:
        while True:
            txn = make_clean_transaction()
            producer.send(TOPIC, key=txn["txn_id"], value=txn)
            print(f"{datetime.now().strftime('%H:%M:%S')} -> "
                  f"card={txn['card_id']} amount={txn['amount']}")
            time.sleep(1.0 / TRANSACTIONS_PER_SECOND)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()

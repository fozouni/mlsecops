import json
import random
import time
import uuid
from datetime import datetime

from kafka import KafkaProducer

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "enriched_features"
NUMBER_OF_ATTACK_TRANSACTIONS = 15
SECONDS_BETWEEN_TRANSACTIONS = 0.3


MERCHANT_CATEGORIES = ["grocery", "electronics", "travel", "restaurant", "fuel", "online_retail"]
CARD_IDS = [f"card_{i:04d}" for i in range(1, 51)]
MERCHANT_IDS = [f"merchant_{i:03d}" for i in range(1, 21)]


def make_bad_transaction():
    """Pick one way to break the transaction's feature values."""
    variant = random.choice(["negative_amount", "huge_amount", "negative_velocity", "negative_geo"])

    txn = {
        "txn_id": str(uuid.uuid4()),
        "card_id": random.choice(CARD_IDS),
        "merchant_id": random.choice(MERCHANT_IDS),
        "amount": round(random.uniform(20, 300), 2),
        "merchant_category": random.choice(MERCHANT_CATEGORIES),
        "txn_ts": int(time.time() * 1000),
        "velocity_score": round(random.uniform(0.0, 3.0), 2),
        "geo_distance_km": round(random.uniform(0.1, 50.0), 2),
    }

    if variant == "negative_amount":
        txn["amount"] = round(-random.uniform(10, 500), 2)
    elif variant == "huge_amount":
        txn["amount"] = round(random.uniform(60000, 250000), 2)
    elif variant == "negative_velocity":
        txn["velocity_score"] = round(-random.uniform(0.5, 5.0), 2)
    elif variant == "negative_geo":
        txn["geo_distance_km"] = round(-random.uniform(1, 100), 2)

    return txn, variant


def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        key_serializer=lambda k: k.encode("utf-8"), # type: ignore
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Sending {NUMBER_OF_ATTACK_TRANSACTIONS} bad transactions...\n")
    for _ in range(NUMBER_OF_ATTACK_TRANSACTIONS):
        txn, variant = make_bad_transaction()
        producer.send(TOPIC, key=txn["txn_id"], value=txn)
        print(f"{datetime.now().strftime('%H:%M:%S')} [ATTACK:{variant}] -> "
              f"card={txn['card_id']} amount={txn['amount']} "
              f"velocity={txn['velocity_score']} geo={txn['geo_distance_km']}")
        time.sleep(SECONDS_BETWEEN_TRANSACTIONS)

    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()

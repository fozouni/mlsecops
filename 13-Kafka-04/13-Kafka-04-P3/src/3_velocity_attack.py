import json
import random
import time
import uuid
from datetime import datetime

from kafka import KafkaProducer


BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "enriched_features"
TARGET_CARD_ID = "card_0007"      # which card gets "attacked"
NUMBER_OF_ATTACK_TRANSACTIONS = 25
SECONDS_BETWEEN_TRANSACTIONS = 0.05  # rapid-fire, all within ~1 minute window
# ----------------------------------------------

MERCHANT_CATEGORIES = ["grocery", "electronics", "travel", "restaurant", "fuel", "online_retail"]
MERCHANT_IDS = [f"merchant_{i:03d}" for i in range(1, 21)]


def make_burst_transaction(card_id, base_amount):
    jitter = round(random.uniform(-3, 3), 2)
    return {
        "txn_id": str(uuid.uuid4()),
        "card_id": card_id,
        "merchant_id": random.choice(MERCHANT_IDS),
        "amount": max(1.0, base_amount + jitter),
        "merchant_category": random.choice(MERCHANT_CATEGORIES),
        "txn_ts": int(time.time() * 1000),
        "velocity_score": round(random.uniform(5.0, 9.0), 2),  # elevated but still "valid"
        "geo_distance_km": round(random.uniform(0.1, 5.0), 2),
    }


def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        key_serializer=lambda k: k.encode("utf-8"), # type: ignore
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    base_amount = round(random.uniform(50, 200), 2)
    print(f"Sending {NUMBER_OF_ATTACK_TRANSACTIONS} rapid-fire transactions "
          f"on {TARGET_CARD_ID}...\n")

    for _ in range(NUMBER_OF_ATTACK_TRANSACTIONS):
        txn = make_burst_transaction(TARGET_CARD_ID, base_amount)
        producer.send(TOPIC, key=txn["txn_id"], value=txn)
        print(f"{datetime.now().strftime('%H:%M:%S')} [ATTACK:velocity] -> "
              f"card={txn['card_id']} amount={txn['amount']}")
        time.sleep(SECONDS_BETWEEN_TRANSACTIONS)

    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()

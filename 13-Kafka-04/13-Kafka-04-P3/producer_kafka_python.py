#!/usr/bin/env python3
"""
MLSecOps Lab — Transaction Event Producer (kafka-python version)

Simulates a stream of card transactions flowing into Kafka topic
'enriched_features'. Supports a "clean" baseline mode and two attack
modes that the ksqlDB guardrail layer (see mlsecops_ksqldb_scenario.md)
is designed to catch:

  - range     : injects statistically/structurally invalid feature
                values (negative amount, negative velocity/geo, etc.)
                -> should trigger `invalid_feature_alerts`
  - velocity  : injects a burst of rapid-fire transactions on the same
                card_id (adversarial threshold-probing pattern)
                -> should trigger `velocity_alerts`
  - demo      : runs clean traffic, then automatically switches to
                range attack, back to clean, then velocity attack.
                This is the mode to run live in class.

Usage:
    pip install kafka-python --break-system-packages
    python3 producer.py --mode demo
    python3 producer.py --mode normal --rate 5
    python3 producer.py --mode range --count 20
    python3 producer.py --mode velocity --card-id card_0001 --count 30
"""

import argparse
import json
import random
import time
import uuid
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import KafkaError

TOPIC = "enriched_features"

MERCHANT_CATEGORIES = [
    "grocery", "electronics", "travel", "restaurant", "fuel", "online_retail"
]

CARD_IDS = [f"card_{i:04d}" for i in range(1, 51)]
MERCHANT_IDS = [f"merchant_{i:03d}" for i in range(1, 21)]


def make_producer(bootstrap_servers):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=10,
    )


def on_send_error(excp):
    print(f"  [DELIVERY FAILED] {excp}")


def make_clean_transaction():
    """A statistically normal transaction."""
    category = random.choice(MERCHANT_CATEGORIES)
    ranges = {
        "grocery": (5, 150),
        "electronics": (20, 1200),
        "travel": (50, 2500),
        "restaurant": (8, 120),
        "fuel": (20, 100),
        "online_retail": (5, 300),
    }
    lo, hi = ranges[category]
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


def make_range_attack_transaction():
    """
    Structurally/statistically invalid feature values — simulates a
    corrupted upstream enrichment service or a poisoning attempt.
    Should trip the `invalid_feature_alerts` stream (amount < 0,
    amount > 50000, velocity_score < 0, geo_distance_km < 0).
    """
    category = random.choice(MERCHANT_CATEGORIES)
    variant = random.choice(["negative_amount", "huge_amount", "negative_velocity", "negative_geo"])

    txn = {
        "txn_id": str(uuid.uuid4()),
        "card_id": random.choice(CARD_IDS),
        "merchant_id": random.choice(MERCHANT_IDS),
        "amount": round(random.uniform(20, 300), 2),
        "merchant_category": category,
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

    return txn


def make_velocity_attack_transactions(card_id, n):
    """
    A burst of near-identical, slightly-varied transactions on one
    card — simulates an attacker probing a fraud model's decision
    threshold. Should trip `velocity_alerts` (>10 txns/minute/card).
    """
    base_amount = round(random.uniform(50, 200), 2)
    txns = []
    for _ in range(n):
        jitter = round(random.uniform(-3, 3), 2)
        txns.append({
            "txn_id": str(uuid.uuid4()),
            "card_id": card_id,
            "merchant_id": random.choice(MERCHANT_IDS),
            "amount": max(1.0, base_amount + jitter),
            "merchant_category": random.choice(MERCHANT_CATEGORIES),
            "txn_ts": int(time.time() * 1000),
            "velocity_score": round(random.uniform(5.0, 9.0), 2),  # elevated but still "in range"
            "geo_distance_km": round(random.uniform(0.1, 5.0), 2),
        })
    return txns


def send(producer, txn, label=None):
    future = producer.send(TOPIC, key=txn["txn_id"], value=txn)
    future.add_errback(on_send_error)
    tag = f" [{label}]" if label else ""
    print(f"{datetime.now().strftime('%H:%M:%S')}{tag} -> "
          f"card={txn['card_id']} amount={txn['amount']} "
          f"velocity={txn['velocity_score']} geo={txn['geo_distance_km']}")


def run_normal(producer, count, rate):
    for _ in range(count):
        send(producer, make_clean_transaction())
        time.sleep(1.0 / rate)


def run_range_attack(producer, count):
    print("\n--- INJECTING RANGE/POISONING ATTACK ---\n")
    for _ in range(count):
        send(producer, make_range_attack_transaction(), label="ATTACK-RANGE")
        time.sleep(0.3)


def run_velocity_attack(producer, card_id, count):
    print(f"\n--- INJECTING VELOCITY ATTACK on {card_id} ---\n")
    for txn in make_velocity_attack_transactions(card_id, count):
        send(producer, txn, label="ATTACK-VELOCITY")
        time.sleep(0.05)  # rapid-fire, well within a 1-minute window


def run_demo(producer):
    print("\n=== PHASE 1: Baseline clean traffic (30s) ===")
    run_normal(producer, count=30, rate=2)

    print("\n=== PHASE 2: Range/poisoning attack burst ===")
    run_range_attack(producer, count=15)

    print("\n=== PHASE 3: Back to clean traffic (15s) ===")
    run_normal(producer, count=15, rate=2)

    print("\n=== PHASE 4: Velocity/adversarial probing attack ===")
    run_velocity_attack(producer, card_id=random.choice(CARD_IDS), count=25)

    print("\n=== PHASE 5: Cooldown, clean traffic (15s) ===")
    run_normal(producer, count=15, rate=2)

    print("\nDemo sequence complete. Check the `security_alerts` stream in ksqlDB CLI.")


def main():
    parser = argparse.ArgumentParser(description="MLSecOps ksqlDB lab traffic generator (kafka-python)")
    parser.add_argument("--mode", choices=["normal", "range", "velocity", "demo"], default="demo")
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--rate", type=float, default=3.0, help="transactions/sec for normal mode")
    parser.add_argument("--count", type=int, default=20, help="number of transactions for normal/range modes")
    parser.add_argument("--card-id", default=None, help="target card_id for velocity attack")
    args = parser.parse_args()

    producer = make_producer(args.bootstrap_servers)

    try:
        if args.mode == "normal":
            run_normal(producer, args.count, args.rate)
        elif args.mode == "range":
            run_range_attack(producer, args.count)
        elif args.mode == "velocity":
            card_id = args.card_id or random.choice(CARD_IDS)
            run_velocity_attack(producer, card_id, args.count)
        elif args.mode == "demo":
            run_demo(producer)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except KafkaError as e:
        print(f"Kafka error: {e}")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()

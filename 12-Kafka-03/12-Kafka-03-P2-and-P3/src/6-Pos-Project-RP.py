import random
import time
from faker import Faker # pip install faker
from kafka import KafkaProducer # pip install kafka-python
import json

fake = Faker()
producer = KafkaProducer(
    bootstrap_servers='localhost:9092,localhost:9094,localhost:9096',  # Update with your Kafka server address
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize to JSON
)


def generate_random_invoice():
    invoice = {
        "InvoiceNumber": fake.random_int(min=1, max=99999999),
        "CreatedTime": time.ctime(),
        "CustomerCardNo": fake.credit_card_number(),
        "TotalAmount": round(random.uniform(10.0, 1000.0), 2),
        "NumberOfItems": random.randint(1, 10),
        "PaymentMethod": random.choice(["Cash", "Credit Card", "Debit Card", "UPI"]),
        "TaxableAmount": round(random.uniform(0.0, 800.0), 2),
        "CGST": round(random.uniform(0.0, 100.0), 2),
        "SGST": round(random.uniform(0.0, 100.0), 2),
        "CESS": round(random.uniform(0.0, 50.0), 2),
        "StoreID": fake.uuid4(),
        "PosID": fake.uuid4(),
        "CashierID": fake.uuid4(),
        "CustomerType": random.choice(["Regular", "VIP", "Prime"]),
        "DeliveryType": random.choice(["Home Delivery", "Pickup"]),
        "DeliveryAddress": {
            "AddressLine": fake.address(),
            "City": fake.city(),
            "State": fake.state(),
            "PinCode": fake.zipcode(),
            "ContactNumber": fake.phone_number()
        },
        "InvoiceLineItems": [
            {
                "ItemCode": fake.uuid4(),
                "ItemDescription": fake.word() + " " + fake.word(),
                "ItemPrice": round(random.uniform(1.0, 100.0), 2),
                "ItemQty": random.randint(1, 5),
                "TotalValue": round(random.uniform(1.0, 500.0), 2),
            } for _ in range(random.randint(1, 5))
        ]
    }
    return invoice


if __name__ == "__main__":
    while True:
        invoice = generate_random_invoice()
        producer.send(topic='pos', value=invoice)
        print("This record has been sent:", invoice)
        time.sleep(5)
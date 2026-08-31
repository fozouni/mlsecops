from time import sleep
from json import dumps
from kafka import KafkaProducer #pip install kafka-python

producer = KafkaProducer(
    bootstrap_servers=[
        "localhost:9092",
        "localhost:9094",
        "localhost:9096",
    ],
    # value_serializer=lambda x: x.encode("utf-8"),  # ✅ STRING serializer # pyright: ignore[reportAttributeAccessIssue]
    value_serializer=lambda x: dumps(x).encode("utf-8"), # ✅ JSON serializer
)

TOPIC = "numbers2"

for e in range(500000):
    data = {"message": f"I Love You-{e}"}
    producer.send(TOPIC, value=data)
    print(f"Sending data : {data}")
    sleep(0.5)

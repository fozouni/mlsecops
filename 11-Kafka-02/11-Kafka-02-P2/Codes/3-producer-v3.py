# from time import sleep
from json import dumps
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=[
        "localhost:9092",
        "localhost:9094",
        "localhost:9096",
    ],
    value_serializer=lambda x: dumps(x).encode("utf-8"),
)

TOPIC = "invoice"

for e in range(500000):
    data = {"Simple Message- ": e}
    producer.send(TOPIC, value=data)
    print(f"Sending data : {data}")
# sleep(1)

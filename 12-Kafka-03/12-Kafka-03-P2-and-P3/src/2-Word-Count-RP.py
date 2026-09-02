import time
from random import choice
from quixstreams import Application

_app = Application(broker_address="localhost:9092,localhost:9094,localhost:9096")
topic = _app.topic(name="product_reviews")

review_list = [
    "This is the best thing since sliced bread. The best I say.",
    "This is terrible. Could not get it working.",
    "I was paid to write this. Seems good.",
    "Great product. Would recommend.",
    "Not sure who this is for. Seems like it will break after 5 minutes.",
    "I bought their competitors product and it is way worse. Use this one instead.",
    "I would buy it again. In fact I would buy several of them.",
    "Great great GREAT",
]

product_list = ["product_a", "product_b", "product_c", "product_d"]

if __name__ == "__main__":
    with _app.get_producer() as producer:
        while True:
            review = choice(review_list)  # Randomly select a review
            product = choice(product_list)  # Randomly select a product
            event = topic.serialize(key=product, value=review)
            print(f"Producing review for {event.key}: {event.value}")
            producer.produce(key=event.key, value=event.value, topic=topic.name)
            time.sleep(5)
import json
from kafka import KafkaConsumer
from json import loads

TOPIC_NAME = 'numbers2' 
consumer = KafkaConsumer(
    TOPIC_NAME,
    auto_offset_reset='earliest', 
    group_id='I am a CONSUMER',
    bootstrap_servers=['localhost:9092','localhost:9094','localhost:9096'],
    # value_deserializer=lambda m: m.decode('utf-8'), # STRING deserializer # pyright: ignore[reportOptionalMemberAccess]
    value_deserializer=lambda m: loads(m.decode('utf-8')),  # JSON deserializer  # pyright: ignore[reportOptionalMemberAccess]
)

def consume_events():
    for message in consumer:
        print(f"Partition:{message.partition}\tOffset:{message.offset}\tKey:{message.key}\tValue:{message.value}")

if __name__ == '__main__':
    print("Consumer Started ...")
    consume_events()
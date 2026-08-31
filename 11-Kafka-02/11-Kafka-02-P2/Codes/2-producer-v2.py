from time import sleep
from json import dumps
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

# Create admin client
admin_client = KafkaAdminClient(
    bootstrap_servers=[
        "localhost:9092",
        "localhost:9094",
        "localhost:9096",
    ]
)

# Define topic
topic_name = "love-v2"
topic = NewTopic(
    name=topic_name,
    num_partitions=3,
    replication_factor=3
)

# Try to create the topic
try:
    admin_client.create_topics([topic])
    print(f"Topic '{topic_name}' Created Successfully!")
except TopicAlreadyExistsError:
    print(f"Topic '{topic_name}' Already Exists, Continuing...")

# Create producer
producer = KafkaProducer(
    bootstrap_servers=[
        "localhost:9092",
        "localhost:9094",
        "localhost:9096",
    ],
    key_serializer=lambda x: x.encode("utf-8"),     # pyright: ignore[reportAttributeAccessIssue]
    value_serializer=lambda x: x.encode("utf-8"),   # pyright: ignore[reportAttributeAccessIssue]
)

# Send messages
for e in range(500000):
    key = f"key-{e % 3}"  
    data = f"I Love You- {e}"
    producer.send(topic_name, key=key, value=data) 
    print(f"Sending data : {data} with key: {key}")
    sleep(1)
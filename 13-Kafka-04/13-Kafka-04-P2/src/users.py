import random
import time
import json
from kafka import KafkaProducer
# pip install kafka-python

KAFKA_BROKER = 'localhost:9092'  
TOPIC = 'users'

# Create Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_user_data():
    student_id = random.randint(301, 500)
    gre = random.choice([312, 332, 400, 405, 234, 123, 433, 230, 212])
    toefl = random.choice([112, 110, 90, 87, 109, 70, 118, 112])
    cpga = random.choice([344, 450.9, 675, 432.4, 323])
    admit_chance = random.choice([0.9, 0.87, 0.67, 0.98, 0.678, 0.99])
    
    user_data = {
        'student_id': student_id,
        'gre': gre,
        'toefl': toefl,
        'cpga': cpga,
        'admit_chance': admit_chance
    }
    
    return user_data

def send_to_kafka(data):
    # Send message to Kafka
    future = producer.send(TOPIC, value=data)
    # Wait for the send to complete (optional)
    result = future.get(timeout=10)
    return result

if __name__ == '__main__':
    try:
        while True:
            user_data = generate_user_data()
            send_to_kafka(user_data)
            print(f"Sent: {user_data}")
            time.sleep(1) 
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        # Make sure to close the producer
        producer.close()
import json
from kafka import KafkaConsumer
from jsonschema import validate, ValidationError

schema = {
    "type": "object",
    "properties": {
        "student_id": {
            "type": "integer"
        },
        "gre": {
            "type": "integer",
            "minimum": 0
        },
        "toefl": {
            "type": "integer",
            "minimum": 0
        },
        "cpga": {
            "type": "integer",
            "minimum": 0
        },
        "admit_chance": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        }
    },
    "required": ["student_id", "gre", "toefl", "cpga", "admit_chance"],
    "additionalProperties": False
}
consumer = KafkaConsumer(
    'admission-json',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='my-group',
    value_deserializer=lambda x: x.decode('utf-8')
)

def validate_json(data, schema):
    try:
        validate(instance=data, schema=schema)
        return True, "Validation successful!"
    except ValidationError as e:
        return False, f"Validation error: {e.message}"

for message in consumer:
    json_data = message.value
    print(f"Received message: {json_data}")
    
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        continue
    
    is_valid, validation_message = validate_json(data, schema)
    print(validation_message)
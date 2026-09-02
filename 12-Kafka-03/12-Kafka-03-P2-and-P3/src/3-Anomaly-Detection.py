from quixstreams import Application
from quixstreams.models import TopicConfig

app = Application(
    broker_address="localhost:9092,localhost:9094,localhost:9096",
    consumer_group="temperature_alerter",
    auto_offset_reset="earliest",
)

temperature_readings_topic = app.topic(name="temperature_readings", config=TopicConfig(
        num_partitions=3,
        replication_factor=3,
    ))
alerts_topic = app.topic(
    name="alerts",
    config=TopicConfig(
        num_partitions=3,
        replication_factor=3,
    )
)

# {kafka_key: '0', kafka_value: {"Temperature_C": 65, "Timestamp": 1710856626905833677}}


def should_alert(window_value: int, key, timestamp, headers):
    if window_value >= 90:
        print(f"Alerting for MID {key}: Average Temperature {window_value}")
        return True

sdf = app.dataframe(topic=temperature_readings_topic)

sdf = sdf.apply(lambda data: data["Temperature_C"])

# >>> {"Temperature_C": 65, "Timestamp": 1710856626905833677}

# >>> 65

sdf = sdf.hopping_window(duration_ms=5000, step_ms=1000).mean().current()

# >>> {"value": 67.49478585, "start": 1234567890, "end": 1234567895}

# To understand current 👇👇👇

# >>> window1 = (1, 6),
#       window2 = (2, 7),
#          window3 = (3, 8),
#           window4 = (4, data is still coming 🤨)

############################
sdf = sdf.apply(lambda result: round(result["value"], 2)).filter(
    should_alert, metadata=True
)

sdf = sdf.to_topic(alerts_topic)

if __name__ == "__main__":
    app.run()

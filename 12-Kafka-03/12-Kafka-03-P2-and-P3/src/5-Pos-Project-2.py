from quixstreams import Application
from quixstreams.models import TopicConfig

app = Application(
    broker_address="localhost:9092,localhost:9094,localhost:9096",
    consumer_group="pos-project-consumer-2",
    auto_offset_reset="earliest",
)

pos_topic = app.topic(name="pos", config=TopicConfig(
        num_partitions=3,
        replication_factor=3,
    ))
loyalty_topic = app.topic(name="loyalty", config=TopicConfig(
        num_partitions=3,
        replication_factor=3,
    ))


sdf = app.dataframe(topic=pos_topic)

sdf = sdf[sdf["CustomerType"] == 'Prime']

sdf = sdf[["InvoiceNumber", "CustomerCardNo", "TotalAmount"]]

sdf["EarnedLoyaltyPoints"] = sdf["TotalAmount"] * 0.2

sdf = sdf.to_topic(loyalty_topic)

sdf.print()

if __name__ == "__main__":
    app.run()

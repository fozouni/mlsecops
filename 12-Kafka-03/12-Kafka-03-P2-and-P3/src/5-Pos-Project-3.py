from quixstreams import Application
from quixstreams.models import TopicConfig

app = Application(
    broker_address="localhost:9092,localhost:9094,localhost:9096",
    consumer_group="pos-project-consumer-3",
    auto_offset_reset="earliest",
)

pos_topic = app.topic(name="pos", config=TopicConfig(
        num_partitions=3,
        replication_factor=3,
    ))
hadoopsink_topic = app.topic(name="hadoop-sink", config=TopicConfig(
        num_partitions=3,
        replication_factor=3,
    ))


def expand_invoicelineitems(value: dict) -> list[dict]:
    items = [
        {
            'InvoiceNumber': value['InvoiceNumber'],
            "TotalAmount": value["TotalAmount"],
            "NumberOfItems": value["NumberOfItems"],
            "TaxableAmount": value["TaxableAmount"],
            "StoreID": value["StoreID"],
            "CustomerType": value["CustomerType"],
            "DeliveryType": value["DeliveryType"],
            **item
        } for item in value['InvoiceLineItems']
    ]
    return items


sdf = app.dataframe(topic=pos_topic)

sdf = sdf.apply(expand_invoicelineitems, expand=True)

sdf.print()

sdf.to_topic(hadoopsink_topic)

if __name__ == "__main__":
    app.run()

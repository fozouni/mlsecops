# Clustering Kafka with KRaft and some considerations

[toc]

## Copy KRaft server.properties

```bash
cp server.properties server-1.properties
cp server.properties server-2.properties
cp server.properties server-3.properties
```



## Setup the id of each server

```yaml
node.id=1
# in server-1.properties file

node.id=2
# in server-2.properties

node.id=3
# in server-3.properties
```

## Configure listeners

This defines the network addresses the Kafka server uses for communication. For server 1, you’ll set it to listen on ports 9092 for Kafka broker and 9093 for the controller.

A listener is a combination of a **protocol**, a **host**, and a **port**, such as

 `listeners = PLAINTEXT://your.host.name:9092` 

The protocol defines the security mechanism for the connection, such as PLAINTEXT, SSL, SASL, etc. When the host address is omitted (represented by `:`), it signifies that the Kafka broker will listen on all network interfaces available on the machine.

```YAML
# For server-1.properties
listeners=PLAINTEXT://0.0.0.0:9092,CONTROLLER://:9093

# For server-2.properties
listeners=PLAINTEXT://0.0.0.0:9094,CONTROLLER://:9095

# For server-3.properties
listeners=PLAINTEXT://0.0.0.0:9096,CONTROLLER://:9097
```

## Configure advertised.listeners

```yaml
# For server-1.properties
advertised.listeners=PLAINTEXT://localhost:9092

# For server-2.properties
advertised.listeners=PLAINTEXT://localhost:9094

# For server-3.properties
advertised.listeners=PLAINTEXT://localhost:9096
```

![](.\Pics\Proxy-Server.png)

------

### You are still confused?

1. **Kafka Broker**: You have a Kafka broker running on a server with an internal IP address (e.g., `192.168.1.1`). **(Listeners)**
2. **Proxy/Load Balancer**: You have a server in front of the Kafka broker with an external IP address (e.g., `192.45.32.1`). This could be a load balancer, reverse proxy, or another server that routes requests. **(Advertised Listeners)**
3. **Clients**: Producers and consumers interact only with the external server (i.e., `192.45.32.1`).

------

## Log Directories

```yaml
# For server-1.properties
log.dirs=/home/amin/tools/kafka_2.13-4.3.1/tmp/kraft-logs-1

# For server-2.properties
log.dirs=/home/amin/tools/kafka_2.13-4.3.1/tmp/kraft-logs-2

# For server-3.properties
log.dirs=/home/amin/tools/kafka_2.13-4.3.1/tmp/kraft-logs-3
```

## Controller Quorum Voters

Set this line in all three files server-1.properties till server-3.properties.

```bash
controller.quorum.voters=1@localhost:9093,2@localhost:9095,3@localhost:9097
```

## Create a UUID for our Cluster

```bash
KAFKA_CLUSTER_ID="$(kafka-storage.sh random-uuid)"

echo $KAFKA_CLUSTER_ID
```

## Bind UUID to Storage

cd into the root directory of kafka

```bash
kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c ./config/server-1.properties
kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c ./config/server-2.properties
kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c ./config/server-3.properties
```

## Start Servers

```bash
kafka-server-start.sh ./config/server-1.properties
kafka-server-start.sh ./config/server-2.properties
kafka-server-start.sh ./config/server-3.properties

#Check the quorum
bin/kafka-metadata-quorum.sh --bootstrap-controller localhost:9093 describe --status
```

## Create a topic

```bash
kafka-topics.sh --bootstrap-server localhost:9092 --create  --topic numbers  --partitions 4 --replication-factor 3

kafka-topics.sh --bootstrap-server localhost:9092 --list
```

```bash
amin@ubuntu24:~/tools/kafka_2.13-4.3.1$ bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic numbers

Topic: numbers  TopicId: xRh7a--VSmaD2nDqKWTL9w PartitionCount: 4       ReplicationFactor: 3    Configs: min.insync.replicas=1,segment.bytes=1073741824
        Topic: numbers  Partition: 0    Leader: 1       Replicas: 1,2,3 Isr: 1,2,3      Elr:    LastKnownElr:
        Topic: numbers  Partition: 1    Leader: 2       Replicas: 2,3,1 Isr: 2,3,1      Elr:    LastKnownElr:
        Topic: numbers  Partition: 2    Leader: 3       Replicas: 3,1,2 Isr: 3,1,2      Elr:    LastKnownElr:
        Topic: numbers  Partition: 3    Leader: 3       Replicas: 3,1,2 Isr: 3,1,2      Elr:    LastKnownElr:
```



> ELR comes from `Eligible Leader Replicas`. You can read more about this in
> https://kafka.apache.org/41/operations/eligible-leader-replicas/.



## Now see the different segments of log file and enjoy

```bash
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic invoice --partitions 5 --replication-factor 3 --config segment.bytes=1048576

python3 producer-v3.py
```



## Offsetexplorer, a good tool to see inside the Kafka

https://www.kafkatool.com/download4/offsetexplorer_64bit.exe


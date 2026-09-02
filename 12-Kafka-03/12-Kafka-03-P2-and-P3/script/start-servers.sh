#!/bin/bash
set -e

KAFKA_CLUSTER_ID="$(/home/$(whoami)/tools/kafka_2.13-4.3.1/bin/kafka-storage.sh random-uuid)"

/home/$(whoami)/tools/kafka_2.13-4.3.1/bin/kafka-storage.sh  format -t $KAFKA_CLUSTER_ID -c /home/$(whoami)/tools/kafka_2.13-4.3.1/config/server-1.properties

/home/$(whoami)/tools/kafka_2.13-4.3.1/bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c /home/$(whoami)/tools/kafka_2.13-4.3.1/config/server-2.properties

/home/$(whoami)/tools/kafka_2.13-4.3.1/bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c /home/$(whoami)/tools/kafka_2.13-4.3.1/config/server-3.properties



/home/$(whoami)/tools/kafka_2.13-4.3.1/bin/kafka-server-start.sh /home/$(whoami)/tools/kafka_2.13-4.3.1/config/server-1.properties >> /home/$(whoami)/tools/kafka_2.13-4.3.1/logs/broker-1.log 2>&1 &

# 2>&1: Redirects stderr (file descriptor 2) to wherever stdout (file descriptor 1) is currently pointing

# &: Runs the command in the background

sleep 10

echo "================================"
echo "🔴 The second broker is coming up 😎"
echo "================================"

/home/$(whoami)/tools/kafka_2.13-4.3.1/bin/kafka-server-start.sh /home/$(whoami)/tools/kafka_2.13-4.3.1/config/server-2.properties >> /home/$(whoami)/tools/kafka_2.13-4.3.1/logs/broker-2.log 2>&1 &

sleep 10

echo "================================"
echo "🔴 The third broker is coming up 🚀"
echo "================================"

/home/$(whoami)/tools/kafka_2.13-4.3.1/bin/kafka-server-start.sh /home/$(whoami)/tools/kafka_2.13-4.3.1/config/server-3.properties >> /home/$(whoami)/tools/kafka_2.13-4.3.1/logs/broker-3.log 2>&1 &



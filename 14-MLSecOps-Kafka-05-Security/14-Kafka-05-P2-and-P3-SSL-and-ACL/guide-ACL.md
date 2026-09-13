# Apache Kafka SSL and ACL Setup

[toc]

## 📝 Main Reference

Read the docs of Kafka only from this URL, not from LLMs (at the first step)
https://kafka.apache.org/42/getting-started/ 

## 📝 Another Option for Deploying

https://www.freestyle.sh/
(Only has **IPV6**)

---

## ==========

## 1️⃣ PART 1: SERVER SETUP

### Step 1: Make Our Server Ready (install Kafka & Java)

```bash
./make-server-ready.sh
```

---

### Step 2: Generate SSL Certificates

> In the following codes, instead of building a bash script, we use this style:
>
> ```bash
> cat > /root/generate-ssl.sh << 'SCRIPT_EOF'
> ...content here...
> SCRIPT_EOF
> ```
>
> 🚩 In that shell command, **`SCRIPT_EOF`** is a **heredoc delimiter** (also called a "here-document" marker). It's not a command or a variable. It's just an arbitrary label you choose to mark where the input starts and ends.

```bash
cat > /root/generate-ssl.sh << 'EOF'
#!/bin/bash
set -e

echo "=========================================="
echo "🔐 Generating SSL Certificates"
echo "=========================================="

DAYS=365
KEYSTORE_DIR="/etc/kafka/secrets"
IP="95.38.167.67"
DNS="server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir"
#🚩 The term DNS stands for Domain Name System.

#🚩 Generate a strong random password instead of a shared default
PASS=$(openssl rand -base64 24)

rm -rf "$KEYSTORE_DIR"
mkdir -p "$KEYSTORE_DIR"
cd "$KEYSTORE_DIR"

echo "Step 1: Creating Certificate Authority..."
openssl req -new -x509 -keyout ca-key -out ca-cert -days $DAYS \
  -passout pass:$PASS -subj "/CN=KafkaCA" 2>/dev/null

echo "Step 2: Creating server keystore with SAN..."
keytool -keystore kafka.server.keystore.jks -alias localhost -genkey \
  -keyalg RSA -keysize 2048 -storepass $PASS -keypass $PASS \
  -dname "CN=$DNS" \
  -ext "SAN=DNS:$DNS,IP:$IP" -validity $DAYS 2>/dev/null

#echo "Step 2: Creating server keystore with SAN..."
#keytool -keystore kafka.server.keystore.jks -alias localhost -genkey \
#  -keyalg RSA -keysize 2048 -storepass $PASS -keypass $PASS \
#  -dname "CN=$IP" \
#  -ext "SAN=IP:$IP" -validity $DAYS 2>/dev/null

echo "Step 3: Generating certificate signing request..."
keytool -keystore kafka.server.keystore.jks -alias localhost -certreq \
  -file server.csr -storepass $PASS -keypass $PASS 2>/dev/null

echo "Step 4: Signing certificate with CA..."
openssl x509 -req -CA ca-cert -CAkey ca-key -in server.csr -out server.crt \
  -days $DAYS -CAcreateserial -passin pass:$PASS \
  -extfile <(echo "subjectAltName=DNS:$DNS,IP:$IP") 2>/dev/null

#echo "Step 4: Signing certificate with CA..."
#openssl x509 -req -CA ca-cert -CAkey ca-key -in server.csr -out server.crt \
#  -days $DAYS -CAcreateserial -passin pass:$PASS \
#  -extfile <(echo "subjectAltName=IP:$IP") 2>/dev/null

echo "Step 5: Creating server truststore..."
keytool -keystore kafka.server.truststore.jks -alias CARoot -import \
  -file ca-cert -storepass $PASS -noprompt 2>/dev/null

echo "Step 6: Importing CA into server keystore..."
keytool -keystore kafka.server.keystore.jks -alias CARoot -import \
  -file ca-cert -storepass $PASS -noprompt 2>/dev/null

echo "Step 7: Importing signed certificate into server keystore..."
keytool -keystore kafka.server.keystore.jks -alias localhost -import \
  -file server.crt -storepass $PASS -noprompt 2>/dev/null

echo "Step 8: Creating admin client certificate (for mTLS)..."
keytool -keystore admin.client.keystore.jks -alias admin -genkey \
  -keyalg RSA -keysize 2048 -storepass $PASS -keypass $PASS \
  -dname "CN=admin" -validity $DAYS 2>/dev/null

keytool -keystore admin.client.keystore.jks -alias admin -certreq \
  -file admin.csr -storepass $PASS -keypass $PASS 2>/dev/null

openssl x509 -req -CA ca-cert -CAkey ca-key -in admin.csr -out admin.crt \
  -days $DAYS -CAcreateserial -passin pass:$PASS 2>/dev/null

keytool -keystore admin.client.truststore.jks -alias CARoot -import \
  -file ca-cert -storepass $PASS -noprompt 2>/dev/null

keytool -keystore admin.client.keystore.jks -alias CARoot -import \
  -file ca-cert -storepass $PASS -noprompt 2>/dev/null

keytool -keystore admin.client.keystore.jks -alias admin -import \
  -file admin.crt -storepass $PASS -noprompt 2>/dev/null

#🚩 Clean up intermediates, but keep ca-key
rm -f server.csr server.crt admin.csr admin.crt ca-cert.srl

#🚩 Lock down permissions: jks/cert files readable by kafka user, CA key root-only
chmod 640 *.jks ca-cert
chmod 600 ca-key

#🚩 Save the generated password to a root-only file — do NOT hardcode it in configs
echo "$PASS" > "$KEYSTORE_DIR/.ssl-password"
chmod 600 "$KEYSTORE_DIR/.ssl-password"

echo ""
echo "=========================================="
echo "✅ SSL CERTIFICATES GENERATED SUCCESSFULLY!"
echo "=========================================="
ls -lh *.jks
echo ""
echo "Generated keystore/truststore password (also saved to $KEYSTORE_DIR/.ssl-password):"
echo "$PASS"
#🚩 Comment the abbove line in important envs (for example production)
echo "=========================================="
EOF

chmod +x /root/generate-ssl.sh

/root/generate-ssl.sh
```

> 1- **Copy the printed password somewhere safe**. You'll substitute it for `<YOUR_SSL_PASSWORD>` in the configs below. You can also retrieve it later with:
>
> ```
> cat /etc/kafka/secrets/.ssl-password
> ```
>
> 2- `keytool` and `jps` comes bundled with the JDK, so it only exists after apt install openjdk-21-jdk (installed by a script on Step1).
>
> 3- `2>/dev/null` redirects stderr (error/warning output) to `/dev/null`, a special file that discards everything written to it. For production we redirect to a concrete log file:
>
> ```bash
> # ✅ Production: keep errors, just move them out of the terminal into a log
> keytool -keystore kafka.server.keystore.jks -alias localhost -genkey \
>   -keyalg RSA -keysize 2048 -storepass $PASS -keypass $PASS \
>   -dname "CN=$DNS" \
>   -ext "SAN=DNS:$DNS,IP:$IP" -validity $DAYS 2>> /etc/kafka/secrets/cert-gen.log
> 
> # ⚠️ OK for a demo run: discard noisy-but-harmless warnings entirely
> keytool -keystore kafka.server.keystore.jks -alias localhost -genkey \
>   -keyalg RSA -keysize 2048 -storepass $PASS -keypass $PASS \
>   -dname "CN=$DNS" \
>   -ext "SAN=DNS:$DNS,IP:$IP" -validity $DAYS 2>/dev/null
> ```



### Step 3: Create Admin Client Config

```bash
PASS=$(cat /etc/kafka/secrets/.ssl-password)

cat > /etc/kafka/secrets/admin-client.properties << EOF

security.protocol=SSL
ssl.truststore.location=/etc/kafka/secrets/admin.client.truststore.jks
ssl.truststore.password=$PASS
ssl.keystore.location=/etc/kafka/secrets/admin.client.keystore.jks
ssl.keystore.password=$PASS
ssl.key.password=$PASS
bootstrap.servers=server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093
EOF

chmod 600 /etc/kafka/secrets/admin-client.properties
```



### Step 4: Configure server.properties

```bash
PASS=$(cat /etc/kafka/secrets/.ssl-password)

cat > /root/kafka_2.13-4.3.1/config/server.properties << EOF
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@localhost:9094

listeners=PLAINTEXT://127.0.0.1:9092,SSL://0.0.0.0:9093,CONTROLLER://0.0.0.0:9094

advertised.listeners=PLAINTEXT://127.0.0.1:9092,SSL://server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093

inter.broker.listener.name=PLAINTEXT
controller.listener.names=CONTROLLER
listener.security.protocol.map=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,SSL:SSL

ssl.keystore.location=/etc/kafka/secrets/kafka.server.keystore.jks
ssl.keystore.password=$PASS
ssl.key.password=$PASS
ssl.truststore.location=/etc/kafka/secrets/kafka.server.truststore.jks
ssl.truststore.password=$PASS

# Require client certs signed by your CA (mutual TLS), not just encryption
ssl.client.auth=required
ssl.enabled.protocols=TLSv1.2,TLSv1.3

log.dirs=/var/lib/kafka/data
metadata.log.dir=/var/lib/kafka/metadata
num.partitions=3

offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1

log.retention.hours=168
log.segment.bytes=1073741824
EOF
```

> 🚩 `ssl.client.auth=required` enforces mutual TLS so only clients holding a cert signed by your CA can connect.



### Step 5: Create Data Directories

```bash
mkdir -p /var/lib/kafka/data /var/lib/kafka/metadata
```



### Step 6: Start Kafka

```bash
CLUSTER_ID=$(/root/kafka_2.13-4.3.1/bin/kafka-storage.sh random-uuid)
/root/kafka_2.13-4.3.1/bin/kafka-storage.sh format -t $CLUSTER_ID \
  -c /root/kafka_2.13-4.3.1/config/server.properties

/root/kafka_2.13-4.3.1/bin/kafka-server-start.sh -daemon \
  /root/kafka_2.13-4.3.1/config/server.properties

sleep 5
```

Since the PLAINTEXT listener is now localhost-only, admin commands **on the server itself** can still use it directly if you don't want to bother with certs for local testing. But the examples below use the SSL listener throughout, matching what remote clients must use.



### Step 7: Test on Server

First add the record to `etc/host` file as follows:

```
echo "95.38.167.67 server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir" | sudo tee -a /etc/hosts
```

Now run this:

```bash
KAFKA_BIN=/root/kafka_2.13-4.3.1/bin
CFG=/etc/kafka/secrets/admin-client.properties

#🚩 Create topic
$KAFKA_BIN/kafka-topics.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --create --topic test --partitions 3 --replication-factor 1 \
  --command-config $CFG

#🚩 List topics
$KAFKA_BIN/kafka-topics.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --list --command-config $CFG

#🚩 Produce message
echo "Hello SSL!" | $KAFKA_BIN/kafka-console-producer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --topic test \
  --command-config $CFG

#🚩 Consume message
$KAFKA_BIN/kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --topic test \
  --from-beginning \
  --max-messages 1 \
  --command-config $CFG
```

---



## ==========

## 2️⃣ PART 2: LOCAL MACHINE SETUP

To avoid path mismatches, use **one consistent directory** on your local machine for everything in this section. For example `~/kafka-certs` or even `~/Desktop`. 

### Step 8: Copy Certificates to Local

```bash
#🚩 On your LOCAL machine
mkdir -p ~/kafka-certs
cd ~/kafka-certs
# or just go to Desktop

scp root@95.38.167.67:/etc/kafka/secrets/admin.client.keystore.jks .
scp root@95.38.167.67:/etc/kafka/secrets/admin.client.truststore.jks .
scp root@95.38.167.67:/etc/kafka/secrets/.ssl-password ./ssl-password.txt

chmod 600 *.jks ssl-password.txt
```



### Step 9: Create Local Client Config

Created in the same directory (`~/kafka-certs`) as the copied keystores, so relative paths resolve correctly.

```bash
cd ~/kafka-certs
PASS=$(cat ssl-password.txt)

cat > client.properties << EOF
security.protocol=SSL
ssl.truststore.location=./admin.client.truststore.jks
ssl.truststore.password=$PASS
ssl.keystore.location=./admin.client.keystore.jks
ssl.keystore.password=$PASS
ssl.key.password=$PASS
bootstrap.servers=server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093
EOF

chmod 600 client.properties
```



### Step 10: Test from Local

Run these from the same directory where you created `client.properties` .

```bash
#🚩 List topics
kafka-topics.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --list --command-config client.properties

#🚩 Produce message
echo "Hello from LOCAL!" | kafka-console-producer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --topic test \
  --producer.config client.properties

#🚩 Consume message
kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --topic test \
  --from-beginning \
  --max-messages 1 \
  --command-config client.properties
```



## ==========

## 3️⃣ PART 3: OFFSET EXPLORER CONFIGURATION

### Step 11: Offset Explorer Settings

```
General Tab:

- Cluster name: SSL-Kafka-Test
- Bootstrap servers: DNS:9093  

Broker Security Tab:

- Type: SSL
- Truststore Location: <path to admin.client.truststore.jks>
- Truststore Password: <the generated password from Step 2>
- Keystore Location: <path to admin.client.keystore.jks>
- Keystore Password: <the generated password from Step 2>
- Keystore Private Key Password: <the generated password from Step 2>
- ☑ Validate SSL Endpoint Hostname
```



## ==========

## 4️⃣ PART 4: ACL CLASSROOM DEMO

Since `ssl.client.auth=required`, every client already presents a certificate. Kafka can turn that certificate's CN into an authorization **principal**. This demo adds a second identity ("student") with restricted permissions, so **you can see an allow vs. deny** in real time.

### Step 12: Enable the Authorizer

Add these lines to `/root/kafka_2.13-4.3.1/config/server.properties` (KRaft mode uses `StandardAuthorizer`):

```bash
cat >> /root/kafka_2.13-4.3.1/config/server.properties << 'EOF'

# --- ACL demo additions ---
authorizer.class.name=org.apache.kafka.metadata.authorizer.StandardAuthorizer
ssl.principal.mapping.rules=RULE:^CN=(.*?)$/$1/,DEFAULT
super.users=User:admin;User:ANONYMOUS
EOF

#🚩 Restart Kafka to pick up the change
/root/kafka_2.13-4.3.1/bin/kafka-server-stop.sh

sleep 3

/root/kafka_2.13-4.3.1/bin/kafka-server-start.sh -daemon \
  /root/kafka_2.13-4.3.1/config/server.properties
  
sleep 5
```

With `authorizer.class.name` set, Kafka now denies everything **by default** unless an ACL (or `super.users`) grants it. 

> 1- A **principal** is the identity string Kafka uses internally to represent "who is making this request".
>
> 2- **`super.users`**: a list of principals that bypass ACL checks entirely (always allowed).
>
> 3- `User:ANONYMOUS`: the identity used for unauthenticated internal traffic on the PLAINTEXT controller listener. Without it, the broker can't register itself with the controller and authorization blocks its own startup.
>
> 4- `ssl.principal.mapping.rules`=RULE:^CN=(.*?)$/$1/,DEFAULT:
> converts a client cert's Distinguished Name into a Kafka principal string. The regex `^CN=(.*?)$` matches the whole DN if it's just `CN=<something>`, and `/$1/` replaces it with just that `<something>`. So `CN=admin`  turns into principal `admin` (i.e. `User:admin`), instead of the ugly full DN.
>
> Here `DEFAULT` is the fallback rule if the regex doesn't match.



### Step 13: Create a "`student`" Certificate

Reuses the same CA you already generated, so no new trust chain is needed on the client side.

```bash
cd /etc/kafka/secrets
PASS=$(cat .ssl-password)

keytool -keystore student.client.keystore.jks -alias student -genkey \
  -keyalg RSA -keysize 2048 -storepass $PASS -keypass $PASS \
  -dname "CN=student" -validity 365 2>/dev/null

keytool -keystore student.client.keystore.jks -alias student -certreq \
  -file student.csr -storepass $PASS -keypass $PASS 2>/dev/null

openssl x509 -req -CA ca-cert -CAkey ca-key -in student.csr -out student.crt \
  -days 365 -CAcreateserial -passin pass:$PASS 2>/dev/null

keytool -keystore student.client.keystore.jks -alias CARoot -import \
  -file ca-cert -storepass $PASS -noprompt 2>/dev/null

keytool -keystore student.client.keystore.jks -alias student -import \
  -file student.crt -storepass $PASS -noprompt 2>/dev/null

rm -f student.csr student.crt
chmod 640 student.client.keystore.jks

#🚩 The student can reuse the existing truststore since it trusts the same CA
cp admin.client.truststore.jks student.client.truststore.jks
chmod 640 student.client.truststore.jks

cat > student-client.properties << EOF
security.protocol=SSL
ssl.truststore.location=/etc/kafka/secrets/student.client.truststore.jks
ssl.truststore.password=$PASS
ssl.keystore.location=/etc/kafka/secrets/student.client.keystore.jks
ssl.keystore.password=$PASS
ssl.key.password=$PASS
bootstrap.servers=server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093
EOF

chmod 600 student-client.properties
```



### Step 14: Create Two Demo Topics as Admin

```bash
KAFKA_BIN=/root/kafka_2.13-4.3.1/bin
ADMIN_CFG=/etc/kafka/secrets/admin-client.properties

$KAFKA_BIN/kafka-topics.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --create --topic public-topic --partitions 1 --replication-factor 1 \
  --command-config $ADMIN_CFG

$KAFKA_BIN/kafka-topics.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --create --topic secret-topic --partitions 1 --replication-factor 1 \
  --command-config $ADMIN_CFG
```



### Step 15: Grant the Student Read Access to Only One Topic

```bash
$KAFKA_BIN/kafka-acls.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --command-config $ADMIN_CFG \
  --add --allow-principal User:student \
  --operation Read --operation Describe \
  --topic public-topic --group '*'

#🚩 List every ACL currently in effect
$KAFKA_BIN/kafka-acls.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --command-config $ADMIN_CFG --list
```

Notice **no ACL is added for `secret-topic`**  under `StandardAuthorizer`, that alone is enough to deny access. You don't need an explicit `--deny` rule.



### Step 16: Demonstrate Allow vs. Deny

```bash
STUDENT_CFG=/etc/kafka/secrets/student-client.properties

# ✅ Should succeed. the `student` entity has Read+Describe on public-topic.
echo "Hello students!" | $KAFKA_BIN/kafka-console-producer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic public-topic \
  --producer.config $ADMIN_CFG   # produced as admin so the topic has data

$KAFKA_BIN/kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic public-topic \
  --from-beginning --max-messages 1 \
  --consumer.config $STUDENT_CFG

# ❌ Should fail, `student` has no ACL on secret-topic.
$KAFKA_BIN/kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic secret-topic \
  --from-beginning --max-messages 1 \
  -command-config $STUDENT_CFG

echo "Hello students!" | $KAFKA_BIN/kafka-console-producer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic secret-topic \
  --producer.config $ADMIN_CFG
  
# ✅ Should work
$KAFKA_BIN/kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic secret-topic \
  --from-beginning --max-messages 1 \
  --consumer.config $ADMIN_CFG  
```



### Step 17: Get the certs of students and try from local machine

```bash
# On your LOCAL machine
mkdir -p ~/kafka-certs 
cd ~/kafka-certs

scp root@<YOUR_SERVER_IP>:/etc/kafka/secrets/student.client.keystore.jks .
scp root@<YOUR_SERVER_IP>:/etc/kafka/secrets/student.client.truststore.jks .

chmod 640 student.client.*.jks
```

```bash
cd ~/kafka-certs
PASS=$(cat ssl-password.txt)

cat > student-client.properties << EOF
security.protocol=SSL
ssl.truststore.location=./student.client.truststore.jks
ssl.truststore.password=$PASS
ssl.keystore.location=./student.client.keystore.jks
ssl.keystore.password=$PASS
ssl.key.password=$PASS
bootstrap.servers=<YOUR_DNS_NAME>:9093
EOF

chmod 600 student-client.properties
```

```bash
#🚩 Should succeed
kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic public-topic \
  --from-beginning --max-messages 1 \
  --command-config student-client.properties

#🚩 Should fail with TopicAuthorizationException
kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic secret-topic \
  --from-beginning --max-messages 1 \
  --command-config student-client.properties
```



### Step 18 (optional): Explicit Deny Overrides Allow

To show that deny rules always win, even over a broader allow:

```bash
#🚩 Grant broad read access to all topics
$KAFKA_BIN/kafka-acls.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --command-config $ADMIN_CFG \
  --add --allow-principal User:student \
  --operation Read --topic '*'

#🚩 Then explicitly deny secret-topic
$KAFKA_BIN/kafka-acls.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --command-config $ADMIN_CFG \
  --add --deny-principal User:student \
  --operation Read --topic secret-topic

#🚩 public-topic: still works. secret-topic: still denied, despite the wildcard allow.
```



### Step 19 (optional): Clean Up ACLs (allow `student` to read)

```bash
#🚩 Run from Server
$KAFKA_BIN/kafka-acls.sh --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 \
  --command-config $ADMIN_CFG \
  --add --allow-principal User:student \
  --operation Read --operation Describe \
  --topic secret-topic
  
#✅ Now this work from local
kafka-console-consumer.sh \
  --bootstrap-server server-b5ef5727-e7d6-4f32-a886-910694008533.ir-thr-si1.arvancompute.ir:9093 --topic secret-topic \
  --from-beginning --max-messages 1 \
  --command-config student-client.properties
```



## ==========

## 5️⃣ Appendix: all used commands in this tutorial



### System and package tools

| Command                          | Used for                                       |
| :------------------------------- | ---------------------------------------------- |
| `apt update / upgrade / install` | Installing Java + downloading/extracting Kafka |
| `wget`, `tar`                    | Downloading and unpacking the Kafka release    |



### `openssl`: creating and signing certificates

| Command                                                     | Used for                                                     |
| ----------------------------------------------------------- | ------------------------------------------------------------ |
| `openssl req -new -x509 ...`                                | Creates the CA itself: a self-signed certificate (`ca-cert`) + its private key (`ca-key`) |
| `openssl rand -base64 24`                                   | Generates a strong random password instead of hardcoding one |
| `openssl x509 -req -CA ... -CAkey ... -in *.csr -out *.crt` | Signs a CSR with the CA's private key, producing a certificate |



### `keytool`: managing Java keystores/truststores

| Command                         | Used for                                                     |
| ------------------------------- | ------------------------------------------------------------ |
| `keytool -genkey`               | Generates a new private key + self-signed placeholder cert inside a keystore |
| `keytool -certreq`              | Exports a CSR from an existing keystore entry, to be signed by the CA |
| `keytool -import -alias CARoot` | Imports the CA's public cert into a keystore/truststore, so it trusts anything that CA signed |
| `keytool -import -alias <name>` | Imports the CA-signed certificate back into the keystore, replacing the self-signed placeholder |



### Filesystem and permissions

| Command                       | Used for                                                     |
| ----------------------------- | ------------------------------------------------------------ |
| `mkdir -p`, `rm -rf`, `rm -f` | Creating/cleaning the `/etc/kafka/secrets` directory and deleting spent CSR/cert intermediates |
| `chmod 600 & 640`             | Locking down private keys, keystores, and password/config files to restrictive permissions |
| `cat > file-name << EOF`      | Writing multi-line config files (`server.properties`, `*-client.properties`) without an editor |



### DNS and networking

| Command                                  | Used for                                                     |
| ---------------------------------------- | ------------------------------------------------------------ |
| `echo "IP DNS" | sudo tee -a /etc/hosts` | Manually resolving your server's DNS name when real DNS resolution was unreliable |
| `scp`                                    | Copying keystore/truststore/password files from server to local machine |



### Kafka's own CLI tools

| Command                                          | Used for                                                     |
| ------------------------------------------------ | ------------------------------------------------------------ |
| `kafka-storage.sh random-uuid`                   | Generates a cluster ID                                       |
| `kafka-storage.sh format`                        | Initializes the KRaft metadata log on disk before first start |
| `kafka-server-start.sh` & `kafka-server-stop.sh` | Starts & stops the broker process                            |
| `kafka-topics.sh --create & --list`              | Creates topics (`test`, `public-topic`, `secret-topic`) and lists them |
| `kafka-console-producer.sh`                      | Sends messages into a topic (as `admin`)                     |
| `kafka-console-consumer.sh`                      | Reads messages from a topic (as `admin` or `student`)        |
| `kafka-acls.sh --add & --list`                   | Grants (`--allow-principal`) or denies (`--deny-principal`) ACL permissions, and lists current ACLs |



### Process and diagnostics

| Command                | Used for                                                     |
| ---------------------- | ------------------------------------------------------------ |
| `jps`                  | Confirming whether the Kafka JVM process is alive            |
| `pkill -f kafka.Kafka` | Force-killing a stuck/lingering Kafka process before restarting |
| `sleep N`              | Giving Kafka time to start/stop before the next command runs |

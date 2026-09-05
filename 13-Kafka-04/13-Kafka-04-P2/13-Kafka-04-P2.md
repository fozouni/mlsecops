# Streaming with ksqlDB

[toc]

## Get Confluent Kafka

```bash
curl -O https://packages.confluent.io/archive/8.3/confluent-community-8.3.1.tar.gz

tar -xvf confluent-community-8.3.1.tar.gz
```



## Add the Binary of Confluent to the PATH

```bash
echo 'export PATH=$PATH:/home/amin/tools/confluent-8.3.1/bin' >> ~/.bashrc
```



## Start our Kafka Stack

```bash
./script/start_servers.sh
```



## Start the ksqlDB-cli and set some configs on KSQL:

```bash
/home/amin/tools/confluent-8.3.1/bin/ksql http://localhost:8088

# or if you added the bin directory to your PATH just run

ksql http://localhost:8088
```

To see your updates, a few settings need to be configured by first running:

```bash
set 'commit.interval.ms'='2000'; #offsets will be committed every 2 seconds.

set 'cache.max.bytes.buffering'='10000000';
# This setting specifies the maximum size of the buffer for caching messages. A larger buffer (10000000 bytes, or approximately 10 MB) can improve speed by allowing more messages to be processed in memory before being sent to Kafka, reducing the number of network calls.

set 'auto.offset.reset'='earliest';
```



## Work with some data structures in ksqlDB:

### i- Work with csv files;

```bash
SHOW TOPICS; or list topics;

kafka-topics --create --topic admission-csv --bootstrap-server localhost:9092

kafka-topics --list --topic admission-csv --bootstrap-server localhost:9092

🚩🚩🚩 Press "Alt + Shift + -" to see two pane horizontally 

CREATE STREAM admission_csv (student_id INTEGER, gre INTEGER, toefl INTEGER, cpga DOUBLE, admit_chance DOUBLE) WITH (KAFKA_TOPIC='admission-csv', VALUE_FORMAT='DELIMITED');

select * from admission_csv emit changes;

🚩🚩🚩 'emit changes' denotes the push query.

cat admit.csv | kafka-console-producer --bootstrap-server localhost:9092 --topic admission-csv

🚩🚩🚩 Insert some data manually

###🔴300, 321, 100, 8.0, 0.98
###🟢300,321,100,8.0,0.98
###🔴300,"Amin and Reza",100,12,0.98

kafka-console-consumer --bootstrap-server localhost:9092 --topic admission-csv --from-beginning

CREATE STREAM admission_csv_v2 (student_id INTEGER, name STRING, toefl INTEGER, cpga DOUBLE, admit_chance DOUBLE) WITH (KAFKA_TOPIC='admission-csv',VALUE_FORMAT='DELIMITED');

🚩🚩🚩 STRING type accepts any value --- numbers, text, or mixed characters
```





### ii- Work with JSON files;

```bash
kafka-topics --create --topic admission-json --bootstrap-server localhost:9092

CREATE STREAM admission_json (student_id INTEGER, gre INTEGER, toefl INTEGER, cpga DOUBLE, admit_chance DOUBLE) WITH (KAFKA_TOPIC='admission-json', VALUE_FORMAT='JSON');

select * from admission_json emit changes;

kafka-console-producer --bootstrap-server localhost:9092 --topic admission-json

#🟢{"student_id":1, "gre":34, "toefl":432, "cpga":321, "admit_chance":0.9}
#🟢{"student_id":2, "gre":34, "toefl":432, "cpga":321, "admit_chance":0.29}
#🟢{"student_id":3, "gre":34, "toefl":432, "cpga":321, "admit_chance":0.269}
#🟢{"student_id":33, "gre":34, "toefl":432, "cpga":321, "admit_chance":2.269}
#🔴{"student_id":14, "gre":-2, "toefl":432, "cpga":321, "admit_chance":2.269}
#🔴{"student_id":101, "gre":34, "toefl":432, "cpga":321, "admit_chance":Sara}

kafka-console-consumer --bootstrap-server localhost:9092 --topic admission-json --from-beginning

#Something BAD has happend 🤯🤔

python3 ./src/schema-checker.py

#🚀 This checker works amazing 
```



### iii- Working with nested JSON

```bash
kafka-topics --create --topic weather-nested --bootstrap-server localhost:9092

CREATE STREAM weather_nested (
    city STRUCT <name VARCHAR, country VARCHAR, latitude DOUBLE, longitude DOUBLE>,
    description VARCHAR,
    clouds BIGINT,
    deg BIGINT,
    humidity BIGINT,
    pressure DOUBLE,
    rain DOUBLE
) WITH (
    kafka_topic='weather-nested',
    value_format='JSON'
);

select * from weather_nested emit changes;

cat weather.json | kafka-console-producer --bootstrap-server localhost:9092 --topic weather-nested

select city->name AS city_name, description from weather_nested emit changes;

kafka-console-producer  --bootstrap-server localhost:9092 --topic weather-nested

{  "city": {    "name": "France",    "country": "FR", "latitude":-33.8688, "longitude":151.2093 },  "description": "light rain",  "clouds": 92,  "deg": 26,  "humidity": 94,  "pressure": 1025.12,  "rain": 1.25  }

{  "city": {    "name": "Oman",    "country": "OM", "latitude":-33.8688, "longitude":151.2093 },  "description": "light rain",  "clouds": 92,  "deg": 26,  "humidity": 94,  "pressure": 1025.12,  "rain": 1.25  }
```



## Create one stream and one table to see the difference

```bash
kafka-topics --create --topic country-csv --bootstrap-server localhost:9092

kafka-console-producer --bootstrap-server localhost:9092 --topic country-csv --property "parse.key=true" --property "key.separator=:"
>
IR:Iran
IN:India
US:United States
IR:Persia

CREATE TABLE country_table (
    countrycode VARCHAR PRIMARY KEY,
    countryname VARCHAR
) WITH (
    KAFKA_TOPIC='country-csv',
    VALUE_FORMAT='DELIMITED');

list tables;

kafka-topics --create --topic country-csv-v2 --bootstrap-server localhost:9092

kafka-console-producer --bootstrap-server localhost:9092 --topic country-csv-v2 --property "parse.key=true" --property "key.separator=:"
>
IR:IR,Iran
IN:IN,India
US:US,United States
IR:IR,Persia    

CREATE STREAM country_stream (
	countrycode VARCHAR,
    countryname VARCHAR
) WITH (
    KAFKA_TOPIC='country-csv-v2',
    VALUE_FORMAT='DELIMITED'
);

select * from country_table where countrycode='IR';
# You will get an error. But pay attention to cli that will be leading you.

select * from country_stream where countrycode='IR';
```



## Run one python script and see what ksqlDB can Do

```sql
python3 src/users.py #this will create the topic "users" automatically

CREATE STREAM users (student_id INTEGER, gre INTEGER, toefl INTEGER, cpga DOUBLE, admit_chance DOUBLE) WITH (KAFKA_TOPIC='users', VALUE_FORMAT='JSON');

select * from users where toefl >= 100 emit changes;
```

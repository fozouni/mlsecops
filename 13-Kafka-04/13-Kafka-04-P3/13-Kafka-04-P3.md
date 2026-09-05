# One MLSecOps Scenario handled by Kafka and ksqlDB

```bash
/home/amin/tools/confluent-8.3.1/bin/ksql http://localhost:8088

/home/amin/tools/confluent-8.3.1/bin/ksql http://localhost:8088 -f setup_statements.sql
```



## What should we do?

```bash
# In terminal #1
python3 src/1_normal_traffic.py

# In terminal #2
SELECT * FROM security_alerts EMIT CHANGES;

# In terminal #3
python3 src/2_range_attack.py 

# In terminal #1
python3 src/3_velocity_attack.py

# In terminal #2 interupt the process and run this
SELECT * FROM velocity_alerts EMIT CHANGES;
```

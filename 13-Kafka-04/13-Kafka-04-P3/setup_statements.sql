-- 1. Raw enriched feature stream

CREATE STREAM enriched_features (
    txn_id VARCHAR KEY,  -- comed form trancation_id
    card_id VARCHAR,
    merchant_id VARCHAR,
    amount DOUBLE,
    merchant_category VARCHAR,
    txn_ts BIGINT,
    velocity_score DOUBLE,
    geo_distance_km DOUBLE -- The distance between where this transaction is happening. A transaction 3,000 km from someone's usual spending area is a classic fraud signal.
) WITH (
    KAFKA_TOPIC = 'enriched_features',
    VALUE_FORMAT = 'JSON',
    TIMESTAMP = 'txn_ts',
    PARTITIONS = 1
);


-- 2. Range / schema validation
-- When the process of building done, you will se something like
--✅ Created query with ID CSAS_INVALID_FEATURE_ALERTS_17✅.
-- Here CSAS comes from; Create Stream As Select pattern.

CREATE STREAM invalid_feature_alerts AS
SELECT
    txn_id,
    card_id,
    amount,
    velocity_score,
    geo_distance_km,
    '🔴INVALID_RANGE' AS alert_type
FROM enriched_features
WHERE amount < 0
   OR amount > 50000
   OR velocity_score < 0
   OR geo_distance_km < 0
EMIT CHANGES;


-- 3. Rolling baseline statistics

CREATE TABLE amount_stats_5min AS -- CTAS pattern
SELECT
    merchant_category, 
    AVG(amount) AS avg_amount,
    STDDEV_SAMP(amount) AS stddev_amount, -- STDDEV is a standard deviation function. How spread out those amounts are around that average.
    COUNT(*) AS txn_count -- How many transactions happened.
FROM enriched_features
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY merchant_category
EMIT CHANGES;


-- 4. Transaction burst / velocity detection

CREATE TABLE velocity_alerts AS
SELECT
    card_id,
    COUNT(*) AS txn_count_1min,
    'VELOCITY_ANOMALY' AS alert_type
FROM enriched_features
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY card_id
HAVING COUNT(*) > 10
EMIT CHANGES;


-- 5. Stream-based security alerts

CREATE STREAM security_alerts AS
SELECT
    txn_id,
    card_id,
    alert_type
FROM invalid_feature_alerts
EMIT CHANGES;
---
title: Latest state from change data capture
date: 2024-06-08
draft: true
---

`![hero image](./assets/hero.webp)`

The next steps in making my Change Data Capture data useful for solving my usecase are handling multiple transactions and handling changes across multiple tables. The solutions I'll outline here evolved quickly from initial solutions based on traditional methods like Slowly Changing Dimensions, and worked well from multiple perspectives, in particular performance and controlling complexity.

--8<-- "ee.md"

<!-- more -->

## Previous example

In the last post, I had successfully disambiguated the operations in transactions, but ended up with two records in my promotions view - the result of two separate transaction. Having worked through an example of a simplified real-world usecase, I'll generalise problem statements now.

> Given the change data capture feed, I want to determine the state of an entity in the source database at any given point in time.

I've used the word "entity" there to cover the idea of something that the source database might represent. I'll look at single-table case first, where the state we're interested in is fully contained within one table. Then I'll cover the more general case where the interesting state is spread across multiple tables.

## Single-table history

When I ended the last post, we had two transactions appearing in the promotions output for order `20002`.

|order_id|order_date|required_date|shipped_date|notice_period_days|qualifies_for_promotion|
|--------|----------|-------------|------------|------------------|-----------------------|
|20002|1996-07-04|1996-08-25|1996-08-01|52|true|
|20002|1996-07-04|1996-07-10|1996-08-01|6|false|

We can't tell from this output the order in which the transactions committed, and we certainly can't tell which represented the current state at any given point in time. We'll need to go back to the underlying data and use the metadata added by the DMS process to figure that out. `transaction_commit_timestamp` gives me what I need. The `transaction_sequence_number` field could also be an option, but in this data it appears that `transaction_commit_timestamp` has higher precision, the 6 decimal places implied microsecond precision.

??? note "Timestamps and Clock Skew"
    It's worth remembering that timestamps produced by different computers are subject to "[clock skew](https://en.wikipedia.org/wiki/Clock_skew)", so it's possible that this precision is something of an illusion. The kinds of databases acting as CDC source systems will typically run a transaction or connection in a single thread on a single machine for reasons of integrity, so I've seen no evidence of clock skew impact in my CDC work to date, but I've usually found evidence of a problem in data feeds from genuinely distributed systems. I don't have a solution for those cases, other than quantifying and monitoring the problem for consumer awareness.


```sql title="Getting the transactions in the right order"
SELECT
    transaction_commit_timestamp,
    order_id,
    order_date,
    required_date
FROM orders_disambiguated
WHERE order_id = '20002'
ORDER BY transaction_commit_timestamp
```

|transaction_commit_timestamp|order_id|order_date|required_date|
|----------------------------|--------|----------|-------------|
|2024-06-12 10:30:30.041474|20002|1996-07-04|1996-08-25|
|2024-06-12 10:30:30.412977|20002|1996-07-04|1996-07-10|

Those timestamps are less than a second apart because I ran these transactions through quickly. I can simulate looking at the history at different points in time by adding `transaction_commit_timestamp` to the `WHERE` clause.

```sql title="State immediately before the first transaction"
WHERE order_id = '20002'
    AND transaction_commit_timestamp < '2024-06-12 10:30:30.041474'
```

As you might guess, this query returns no records. We don't know anything about this order before that time.

```sql title="State immediately before the second transaction"
WHERE order_id = '20002'
    AND transaction_commit_timestamp < '2024-06-12 10:30:30.041474'
```

One row for the disambiguated transaction with the previous timestamp - and we already know that we get two rows if we query for any later timestamp. We can use a variation of the previous disambiguation approach, lifting the window to operate over transactions instead of statements within a transaction to get the latest state of a row in the source database.

```sql title="orders_latest view yields the latest state of a row"
CREATE OR REPLACE VIEW orders_latest AS
WITH
  identify_last_transaction AS (
   SELECT
     *
   , ROW_NUMBER() OVER (transactions_reverse_chronological_order) position_in_chronology
   FROM
     orders_disambiguated
   WINDOW transactions_reverse_chronological_order AS (
    PARTITION BY order_id
    ORDER BY transaction_commit_timestamp DESC)
)

SELECT *
FROM
  identify_last_transaction
WHERE (position_in_chronology = 1)
```

Querying this view for the `order_id`s I created last time, I have one row per `order_id`:

```sql title="Latest state of orders added in the last post"
SELECT
    transaction_commit_timestamp,
    cdc_operation,
    order_id,
    order_date,
    required_date
FROM orders_latest
WHERE order_id IN ('19998', '19999', '20000', '20002')
ORDER BY transaction_commit_timestamp
```

|transaction_commit_timestamp|cdc_operation|order_id|order_date|required_date|
|----------------------------|-------------|--------|----------|-------------|
|2024-06-12 10:30:25.854359|D|19998|||||
|2024-06-12 10:30:26.480361|D|19999|||||
|2024-06-12 10:30:28.764078|D|20000||||
|2024-06-12 10:30:30.412977|U|20002|1996-07-04|1996-07-10|

Looking back at the source database operations, these are all correct. `19998`, `19999` abd `20000` ended with delete operations and the last operation on `20002` set the `required_date=1996-07-10` as reflected in the results. My promotions view gives me the single correct row when updated to use this view, instead of going direct to the `orders_disambiguated` view, which is that the latest version of this row does not qualify for the promotion:

|order_id|order_date|required_date|shipped_date|notice_period_days|qualifies_for_promotion|
|--------|----------|-------------|------------|------------------|-----------------------|
|20002|1996-07-04|1996-07-10|1996-08-01|6|false|

I can't use this view to look back in time for the latest state of a row before the last one, as the window functions look over the whole dataset. Adding a condition based on `transaction_commit_timestamp` will return no rows for which there has been a subsequent transaction.

## Slowly changing dimensions



## Different kinds of time

This seems like a a good time to mention the fact that we're dealing with multiple kinds of "time" here. 

- the time when the event actually occurred - we don't have an explicit record of that. Some typically newer systems record a timestamp to capture say the time at which a button was clicked, but may don't, like this case.
- the time when the event was recorded by the source system - our `transaction_commit_timestamp`, which is also our best guess for when the event actually occurred.
- the time when the CDC record was processed and made available.

The timestamp at which the CSV file was stored in S3 gives us that last one. The Trino technology that Athena uses exposes [metadata about the underlying files in "pseudocolumns"](https://trino.io/docs/current/connector/hive.html#metadata-columns). If I add the `$file_modified_time` pseudocolumn to a query on the base `orders` table, I can get visibility into the latency of that last step:

```sql title="Exploring latency with Trino's pseudocolumns"
SELECT
    transaction_commit_timestamp,
    "$file_modified_time",
    order_id,
    order_date,
    required_date
FROM orders
WHERE order_id = '20002'
ORDER BY transaction_commit_timestamp
```

I've snipped a few uninteresting rows out. You can see we're looking at about a minute of latency in that last step.

|transaction_commit_timestamp|$file_modified_time|order_id|order_date|required_date|
|----------------------------|-------------------|--------|----------|-------------|
|2024-06-12 10:30:30.041474|2024-06-12 10:31:26.000 UTC|20002|1996-07-04|1996-07-05|
|2024-06-12 10:30:30.412977|2024-06-12 10:31:26.000 UTC|20002|1996-07-04|1996-07-10|


## Chonology over multiple tables

```sql
-- 29999 single-table

BEGIN;
INSERT INTO orders VALUES(29999,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, CURRENT_DATE - INTERVAL '12' day, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
UPDATE orders SET ship_address = '59 rue de l''Abbaye' WHERE order_id = '29999';
COMMIT;

BEGIN;
UPDATE orders SET required_date = CURRENT_DATE - INTERVAL '2' day WHERE order_id = '29999';
COMMIT;

BEGIN;
UPDATE orders SET ship_address = '60 rue de l''Abbaye' WHERE order_id = '29999';
COMMIT;

BEGIN;
UPDATE orders SET required_date = CURRENT_DATE - INTERVAL '1' day WHERE order_id = '29999';
COMMIT;
```

```sql
SELECT
    cdc_operation,
    transaction_commit_timestamp,
    order_id,
    order_date,
    required_date
FROM orders_disambiguated
WHERE order_id = '29999'
ORDER BY transaction_commit_timestamp
```

|cdc_operation|transaction_commit_timestamp|order_id|order_date|required_date|
|-------------|----------------------------|--------|----------|-------------|
|I|2024-06-12 10:34:12.047482|29999|2024-05-03|2024-06-09|
|U|2024-06-12 10:34:17.272844|29999|2024-05-03|2024-06-09|
|U|2024-06-12 10:34:21.197492|29999|2024-05-03|2024-06-10|
|U|2024-06-12 10:34:25.518704|29999|2024-05-03|2024-06-10|
|U|2024-06-12 10:34:29.748046|29999|2024-05-03|2024-06-11|

can see the history, can see the latest state correctly. what about this?

```sql
BEGIN;
INSERT INTO orders VALUES(30000,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, CURRENT_DATE - INTERVAL '12' day, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
INSERT INTO order_details VALUES(30000,1,11,12,0);
UPDATE order_details SET quantity = 1 WHERE order_id = 30000;
UPDATE order_details SET product_id = 77 WHERE order_id = 30000;
COMMIT;
```

only row; but there were changes in the order_details table,

```sql
CREATE EXTERNAL TABLE northwind_cdc.order_details (
  cdc_operation string,
  transaction_commit_timestamp string,
  order_id string, 
  product_id string, 
  unit_price string, 
  quantity string, 
  discount string,
  transaction_sequence_number string)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' 
LOCATION 's3://843328850426-cdc/cdc/public/order_details'
```

```sql
SELECT
    cdc_operation,
    transaction_commit_timestamp,
    order_id,
    quantity,
    transaction_sequence_number
FROM order_details
WHERE order_id = '30005'
```

|cdc_operation|transaction_commit_timestamp|order_id|quantity|transaction_sequence_number|
|-------------|----------------------------|--------|--------|---------------------------|
|I|2024-06-12 10:34:40.296951|30000|12|20240612103440290000000000000000289|
|U|2024-06-12 10:34:40.296951|30000|1|20240612103440290000000000000000293|
|U|2024-06-12 10:34:40.296951|30000|1|20240612103440290000000000000000297|

Same metadata, same disambiguation problem to solve

```sql
CREATE OR REPLACE VIEW northwind_cdc.order_details_disambiguated AS
WITH
  identify_last_transaction AS (
   SELECT
     *
   , ROW_NUMBER() OVER (transactions_reverse_chronological_order) position_in_chronology
   FROM
     order_details
   WINDOW transactions_reverse_chronological_order AS (
    PARTITION BY order_id, product_id
    ORDER BY transaction_commit_timestamp DESC
  )
)

SELECT *
FROM
  identify_last_transaction
WHERE (position_in_chronology = 1)
```



```
<figure markdown="span">
 ![template figure](./assets/image.webp)
 <figcaption>template figure</figcaption>
</figure>
```

--8<-- "blog-feedback.md"


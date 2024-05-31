---
title: Disambiguating Transactions in Change Data Capture
date: 2024-05-31
---


intro snippet

--8<-- "ee.md"

<!-- more -->

## Recap

Last time, I looked at [how transactions in the source system manifest in change data capture output](../2024-05-28-exploring-transactions-in-cdc/index.md). I also set Athena up so that I could interact with the CDC output with SQL.
We've covered enough to illustrate a problem I had to deal with for a usecase I was recently working with.

## Example Usecase - Promotions

I think a concrete usecase will help steer away from being too hypothetical. Be aware that I am making this usecase up though, so please be prepared to suspend your disbelief accordingly. There will be cases I don't consider because they don't really tell us anything new or interesting about handling the CDC data.

Marketing had another great idea and the new product we're building is a promotions system. We need to identify orders that qualify for a promotion so that we can send those customers a voucher for a discount off their next order.

> If the customer gave more than 28 days' notice between the order date and the required date at the time it was shipped, then we send one of our vouchers.

We've already got a CDC feed set up, and we'd rather not monkey around with the actual sales system, so can we do it using the CDC feed? Probably - let's have a go. Our Northwind database represents the backed of a sales system, and we'll focus on one table for this post - `orders`. As we saw last time, each row in the `orders` table represents an order. There's about 14 columns, and it seems likely that there's a subset that are interesting for this usecase:

- `order_id` - a unique identifier for an order
- `order_date` - the date the order was placed
- `required_date` - the date the order is required by

I'm going to assert that a non-`NULL` value in `shipped_date` is sufficient to tell us that the order was shipped - we'll ignore the possibility of errors and corrections in that field. A quick query to see if we have any likely qualifying orders in the current dataset.

```sql
WITH order_urgency AS (
    SELECT
        order_id,
        order_date,
        required_date,
        DATE_DIFF('day', DATE(order_date), DATE(required_date)) notice_period_days
    FROM orders
)

SELECT * FROM order_urgency
WHERE notice_period_days > 28
    AND shipped_date IS NOT NULL
```
We get 61 results back, all with 42 `days_between_order_and_required`. Let's come up with some test cases.

## Simple Case - Shipped by First Load

First, orders that were already shipped when we did our CDC full load, one qualifying, one not. We can pick those out of the existing historical data and build the basic query we need.

|order_id|order_date|required_date|shipped_date|notice_period_days|qualifies|
|--------|----------|-------------|------------|------------------|---------|
|10249|1996-07-05|1996-08-16|1996-07-10|42|TRUE|
|10253|1996-07-10|1996-07-24|1996-07-16|14|FALSE|

A new query based on the original one gives the correct results.

```sql
WITH order_urgency AS (
    SELECT
        order_id,
        order_date,
        required_date,
        shipped_date,
        DATE_DIFF('day', DATE(order_date), DATE(required_date)) notice_period_days
    FROM orders
)

SELECT
    order_id,
    notice_period_days > 28 qualifies_for_promotion
FROM order_urgency
WHERE order_id IN (10249, 10253)
    AND shipped_date IS NOT NULL
```

|order_id|qualifies_for_promotion|
|--------|-----------------------|
|10249|true|
|10253|false|

### Making a Test Case

It's going to be a pain for both of us if I have to keep copy-pasting this query as it evolves, not to mention checking that the results are correct. I'll show how I can turn it into a test case and going forward I'll skip the boilerplate.

```sql
-- specify the expected results
WITH test_set AS (
    SELECT 10249 AS order_id, TRUE AS expected
    UNION ALL SELECT 10253, FALSE
),

-- base data for the promotions
order_urgency AS (
    SELECT
        order_id,
        order_date,
        required_date,
        shipped_date,
        DATE_DIFF('day', DATE(order_date), DATE(required_date)) notice_period_days
    FROM orders
),

-- order promotion qualification information
promotions AS (
    SELECT
        *,
        notice_period_days > 28 qualifies_for_promotion
    FROM order_urgency
    WHERE shipped_date IS NOT NULL
)

-- test that each expected row matches the corresponding promotions row
SELECT
    *
FROM test_set
    LEFT JOIN promotions USING (order_id)
WHERE test_set.expected IS DISTINCT FROM promotions.qualifies_for_promotion
-- "IS DISTINCT FROM" handles NULL cases correctly with a no match if either side null
```

This query returns no rows at the moment. As we add cases I'll be adding them to the test set and improving the query.

## Handling a Multi-Statement Transaction

I'll take the [multi-statement transaction from the last post](../2024-05-28-exploring-transactions-in-cdc/index.md#multi-statement-transactions-in-cdc) and run it to see how that looks with our logic.

Adding `order_id 19998` to the test cases with NULL as expected to make it appear in the results, we get `INVALID_CAST_ARGUMENT: Value cannot be cast to date:`. Our transaction ended with a `DELETE` operation, and as everything else is from the CDC full load, this is the first `DELETE` we've seen.

What does the CDC data look like?

|cdc_operation|transaction_commit_timestamp|order_id|order_date|required_date|transaction_sequence_number|
|-------------|----------------------------|--------|----------|-------------|---------------------------|
|I|2024-05-31 20:09:45.208234|19998|1996-07-01|1996-08-01|20240531200945200000000000000000061|
|U|2024-05-31 20:09:45.208234|19998|1996-07-01|1996-08-01|20240531200945200000000000000000065|
|D|2024-05-31 20:09:45.208234|19998|||20240531200945200000000000000000069|

Ah - when `cdc_operation=D` for delete, we get NULL back in the data fields other than the `order_id`. `NULL` can't be parsed to a date so I'll have to handle that. I'll modify the `notice_period_days` calculation to handle the delete case:

```sql hl_lines="7-10 17"
order_urgency AS (
    SELECT
        order_id,
        order_date,
        required_date,
        shipped_date,
        CASE
            WHEN cdc_operation = 'D' THEN NULL
            ELSE DATE_DIFF('day', DATE(order_date), DATE(required_date))
        END notice_period_days
    FROM orders
),

promotions AS (
    SELECT
        *,
        COALESCE(notice_period_days > 28, FALSE) qualifies_for_promotion
    FROM order_urgency
    WHERE shipped_date IS NOT NULL
)
```

I get two rows out of my test case, when there should be none. That's because I have three rows of history for this `order_id` - the original insert, an update and then the delete. What I need is a single row representing the state of the database for this order at the end of the transaction.

## Simple Disambiguation

It's possible to use `GROUP BY` to do this but it's not pretty. The technique I reach for here uses a simple window function. I think [BigQuery's Window Function docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/window-function-calls) are the most accessible I've seen. I think this logic is all about the order and CDC process so I'll add a view over the orders table to do this work and keep the complexity away from my promotions logic.


```sql title="Disambiguated order transactions view"
CREATE OR REPLACE VIEW orders_disambiguated AS
WITH identify_last_order_statement_in_transactions AS (
    SELECT
        *,
        -- last statement in transaction gets TRUE
        ROW_NUMBER() OVER(
            statements_in_transaction_reverse_chronological_order
        ) = 1 is_last_statement_in_transaction
    FROM orders
    -- could be inlined, this way I can give it a meaningful name
    WINDOW statements_in_transaction_reverse_chronological_order AS (
        -- rows with same order_id and commit timestamp
        -- are in the same transaction
        PARTITION BY order_id, transaction_commit_timestamp
        ORDER BY transaction_sequence_number DESC
    )
)

SELECT
    *
FROM identify_last_statement_in_transactions
-- filter in only the last statements in each transaction
WHERE is_last_statement_in_transaction
```

I can inspect the contents of this view and write test cases independencly for it, too - for example, to ensure that this transaction does resolve to a single row, and it's the delete. The modifications to my promotions logic are now minimal, just swapping `FROM orders_disambiguated` in place of `FROM orders`... and my test passes again.

## More Complex Disambiguation

Based on my experience, a common design pattern that's used in user interfaces is to queue up a series of `ALTER` statements as a user navigates an interface making multiple changes. That makes the transactions larger and more complex, so I'll simulate that to check the disambiguation logic still works.

```sql title="Simulating an interactive session queuing statements and commiting on save"
-- simulates queuing of statements in a transaction as user makes edits
BEGIN;
-- create record
INSERT INTO orders VALUES(20002,'VINET', 5, '1996-07-04', '1996-07-05', '1996-08-02', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
-- user selects required_date field and changes it
UPDATE orders SET required_date = '1996-09-01' WHERE order_id = 20002;
-- user selects required_date field and changes it again
UPDATE orders SET required_date = '1996-08-25' WHERE order_id = 20002;
-- user selects ship_address field and changes it
UPDATE orders SET ship_address = '60 rue de l''Abbaye' WHERE order_id = 20002;
-- user sets the shipped_date
UPDATE orders SET shipped_date = '1996-08-01' WHERE order_id = 20002;
-- user hits save
COMMIT;
```

### Before/After Disambiguation

Switching my promotions logic back to the source orders table and querying the CDC records for this more complex transaction:

|order_id|order_date|required_date|shipped_date|notice_period_days|qualifies_for_promotion|
|--------|----------|-------------|------------|------------------|-----------------------|
|20002|1996-07-04|1996-07-05|1996-08-02|1|false|
|20002|1996-07-04|1996-09-01|1996-08-02|59|true|
|20002|1996-07-04|1996-08-25|1996-08-01|52|true|
|20002|1996-07-04|1996-08-25|1996-08-02|52|true|
|20002|1996-07-04|1996-08-25|1996-08-02|52|true|

As we'd expect, we're seeing a row per transaction. Row number three in the table above has the updated shipping date - that's the row that represents the final state of the transaction. Flipping to `FROM orders_disambiguated`...

|order_id|order_date|required_date|shipped_date|notice_period_days|qualifies_for_promotion|
|--------|----------|-------------|------------|------------------|-----------------------|
|20002|1996-07-04|1996-08-25|1996-08-01|52|true|

That's the right row!

### Next Time

Are we done? Let's try this transaction and check out the promotions view...

```sql title="A subsequent edit saved on the order"
BEGIN;
-- user goes back into the record and makes another update
UPDATE orders SET required_date = '1996-07-10' WHERE order_id = 20002;
-- then saves
COMMIT;
```

|order_id|order_date|required_date|shipped_date|notice_period_days|qualifies_for_promotion|
|--------|----------|-------------|------------|------------------|-----------------------|
|20002|1996-07-04|1996-08-25|1996-08-01|52|true|
|20002|1996-07-04|1996-07-10|1996-08-01|6|false|

You guessed it. There's a second row, because we have a separate transaction now. Next time, I'll show how we can assemble a chronology across transactions, tables and systems to solve the usecase.

[northwind_cdc.tar.gz](../2024-05-21-cdc-with-aws-dms/assets/northwind_cdc.tar.gz){:download="northwind_cdc.tar.gz"}

--8<-- "blog-feedback.md"


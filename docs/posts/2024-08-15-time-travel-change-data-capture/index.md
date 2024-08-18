---
title: Time travelling with change data capture
date: 2024-08-15
---


--8<-- "ee.md"

<!-- more -->

## The historical query problem

The last post showed that it's quite easy to see the latest state of any order in our orders table, but I ran into problems trying to see the latest state at a specific prior point in time. I'll pick a transaction with several updates to explore a solution and come back to `order_20002` at the end to demonstrate the solution.

```sql title="Recap transactions for order_30101"
SELECT
    transaction_commit_timestamp,
    order_date,
    required_date,
    shipped_date
FROM orders_disambiguated
WHERE order_id = '30101'
ORDER BY transaction_commit_timestamp
```

|transaction_commit_timestamp|order_date|required_date|shipped_date|
|----------------------------|----------|-------------|------------|
|2024-06-28 07:18:49.975747|1996-07-04|1996-07-05||
|2024-06-28 07:19:01.482931|1996-07-04|1996-08-25||
|2024-06-28 07:19:14.859907|1996-07-04|1996-07-20||
|2024-06-28 07:19:32.597790|1996-07-04|1996-07-20|1996-08-01|
|2024-06-28 07:19:43.913391|1996-07-04|1996-07-20|1996-08-02|

This order was updated four times after the original insert. These example updates are each a few seconds apart. In a real system they could have been seconds, hours, days or years apart. The general question I want to answer is:

> what was the state of this order at a specific time?

I'll take an example of `2024-06-28 07:19:15.000000`. It's obvious to a human that the correct answer is row three in the table above. The timestamp of that row, ending `07:19:14.859907`, is before the timestamp we're interested in, and the next row has a timestamp several seconds later, which is afterwards.

A simple `WHERE` clause won't help. `WHERE transaction_commit_timestamp = '2024-06-28 07:19:15.000000'` gives no results, because no transaction took place at that exact time. I can easily get all the transactions before or after the timestamp, but I can't get the one transaction giving the state of this order at that moment in time.

### Visualising the problem

Each transaction related to a given primary key gets its own row in the database. That row indicates when the transaction took place - the point in time when the change took effect. The row does not tell us when the change was superceded by the next change. I visualise what's going on like this:

```console title="CDC records provide only start timestamps"
                      
      t1    t2    t3  ?  t4  future
Insert|-----|-----|---?--|----->
      Update|-----|---?--|----->
            Update|---?--|----->
                   Update|----->
```

Starting with the insert, each transaction is a new arrow, occurring at times t1, t2, t3 and so on. Querying for a timestamp between t3 and t4, indicated by a line of `?` characters, crosses all three transactions that have already occurred, so can't tell which one was "current" at that time without extra work.

### A messy solution

If I create a CTE including only the rows after the timestamp of interest, I can then use a subquery to select only the updates up to the timestamp of interest. The row I want is the the one with the largest timestamp.

```sql title="Messy solution involving subqueries"
WITH candidate_rows AS (
    SELECT
        *
    FROM orders_disambiguated
    WHERE transaction_commit_timestamp <= '2024-06-28 07:19:15.000000'
)

SELECT
    transaction_commit_timestamp,
    order_date,
    required_date,
    shipped_date
FROM candidate_rows
WHERE transaction_commit_timestamp = (SELECT MAX(transaction_commit_timestamp) FROM candidate_rows)
    AND order_id = '30101'
```

|transaction_commit_timestamp|order_date|required_date|shipped_date|
|---|---|---|---|
|2024-06-28 07:19:14.859907|1996-07-04|1996-07-20||

I don't like this solution. It's not obvious what's going on and the timestamp has leaked into the CTE. That means I can't easily capture this logic by turning it into a view. This logic will have to be codified in documentation and embedded in every query.

What else might I do?

### Window functions for end timestamps

Within each row, I can only see the timestamp at which the change takes effect. I can't see when it was superceded. I would need to order the rows by timestamp and then look in the next row for that, which suggests a window function might be a simple and efficient solution.

```console title="End timestamps represent reality better"
      t1    t2    t3  ?  t4  future
Insert|---->|     |   ?  |
      Update|---->|   ?  |
            Update|---?->|
                   Update|----->
```

Again, starting with the insert, each transaction is a new arrow occurring at times t1, t2, t3 and so on. This time, the arrow for t1 ends at t2, instead of continuing indefinitely. That means a query for a timestamp between t3 and t4, indicated by a line of `?` characters, only crosses the transaction that most recently occurred, with no further filtering needed.

If I have "end" timestamps, then I can write a simple, intuitive query for the single transaction that was valid at the time.

```sql title="Example end timestamps for order_30101"
SELECT
    transaction_commit_timestamp,
    LEAD(transaction_commit_timestamp) OVER (
        PARTITION BY order_id
        ORDER BY transaction_commit_timestamp
    ) end_timestamp
FROM orders_disambiguated
WHERE order_id = '30101'
ORDER BY transaction_commit_timestamp
```

|transaction_commit_timestamp|end_timestamp|
|----------------------------|-------------|
|2024-06-28 07:18:49.975747|2024-06-28 07:19:01.482931|
|2024-06-28 07:19:01.482931|2024-06-28 07:19:14.859907|
|2024-06-28 07:19:14.859907|2024-06-28 07:19:32.597790|
|2024-06-28 07:19:32.597790|2024-06-28 07:19:43.913391|
|2024-06-28 07:19:43.913391||

I can see each row now has an `end_timestamp` that contains the `transaction_commit_timestamp` from the **next row**. The last row has `NULL` in this column, because there is no next row. I'll wrap that in a CTE to try it out.

```sql title="Ad-hoc trial of end timestamps in a query"
WITH orders_with_ends AS (
    SELECT
        *,
        LEAD(transaction_commit_timestamp) OVER (
            PARTITION BY order_id
            ORDER BY transaction_commit_timestamp
        ) end_timestamp
    FROM orders_disambiguated
)

SELECT
    transaction_commit_timestamp,
    order_date,
    required_date,
    shipped_date
FROM orders_with_ends
WHERE (
        transaction_commit_timestamp <= '2024-06-28 07:19:15.000000'
        AND end_timestamp > '2024-06-28 07:19:15.000000'
    )
    AND order_id = '30101'
```

|transaction_commit_timestamp|order_date|required_date|shipped_date|
|---|---|---|---|
|2024-06-28 07:19:14.859907|1996-07-04|1996-07-20||

The exclusive bound on the `end_timestamp` is important. An inclusive bound returns the row you want **and the row before** when the timestamp exactly matches a `transaction_commit_timestamp`.

## Using end timestamps

I'll create a new view with my end timestamps and check it works well with real queries.

```sql title="Promoting end timestamps into a standalone view"
CREATE OR REPLACE VIEW orders_windowed AS
SELECT
    *,
    LEAD(transaction_commit_timestamp) OVER (
        PARTITION BY order_id
        ORDER BY transaction_commit_timestamp
    ) end_timestamp
FROM orders_disambiguated
```

Querying for the timestamp we looked for earlier returns exactly the same results as I saw earlier, so I won't waste space repeating that here. More interesting is what happens when we look at a point in time after the last recorded transaction.

```sql title="Example query incorporating end timestamps"
SELECT
    transaction_commit_timestamp,
    order_date,
    required_date,
    shipped_date
FROM orders_windowed
WHERE (
        transaction_commit_timestamp <= '2024-08-01 00:00:00.000000'
        AND end_timestamp > '2024-08-01 00:00:00.000000'
    )
    AND order_id = '30101'
```

No results. That's not right - the last transaction was a delete, and is still the current state of `order_30101` at this point in time. The problem is that null value for the final transaction end timestamp. When `end_timestamp` is null, the comparison becomes `NULL > 'some-timestamp'`, and the result of that is actually null. Here's a query to prove it.

```sql title="Operations involving null may be counterintuitive"
SELECT
    (NULL > 'a') IS NOT DISTINCT FROM NULL comparison_with_null_is_null,
    (true AND NULL) IS NOT DISTINCT FROM NULL and_null_is_null
```

|comparison_with_null_is_null|and_null_is_null|
|---|---|
|true|true|

This behaviour feels unintuitive to me, but I think I'm reading meaning into null values that's not really there in the SQL. It makes more sense if I [translate "null" to "unknown" as explained at modern-sql.com](https://modern-sql.com/concept/three-valued-logic). Essentially, most operations involving "unknown" result in "unknown", which makes more sense to me.

It's easy enough to deal with the null in the query. Something like this solves the problem and returns the correct final transaction row.

```sql title="Handling the null/unknown/current end timestamps"
AND (
    end_timestamp > '2024-08-01 00:00:00.000000'
    OR end_timestamp IS NULL
)
```

In principle it's a nice, clear solution when you read "null" as "unknown". In practice, I've found it complicates real-world use of the view. Anyone using this view will need to remember to handle the null case, or they will get queries that work but produce incorrect results for transactions that are current. In other words, a breeding ground for bugs.

### Handling null end timestamps

To provide more intuitive handlng of end timestamps for this kind of common point-in-time query, I can update my view to provide appropriate values. Null in this situation means that there is no known subsequent transaction. I can use `COALESCE` to provide an appropriate value in place of null.

There are several options to make the kind of query I outlined above work intuitively.

- `CURRENT_TIMESTAMP` inserts the timestamp when the query ran. I need to be careful to get the timestamp format correct as I'm depending on string sorting. Precision hasn't caused any issues for me, but timezones could present problems.
- As the values are strings, and non-null values will start with a number, I could use a string like `unknown` to represent those values with correct ordering. This approach could cause problems if users need to parse and compute with the timestamp values.
- I could choose a fixed, valid timestamp value in the far future.

I'm not sure which is "best", but I think I would try the "unknown" value next time. It seems least likely to cause confusion and will break if anyone tried to inappropriately parse it as a meaningful timestamp. Let's give it a try.

```sql title="A less error-prone view of end timestamps"
CREATE OR REPLACE VIEW orders_windowed AS
SELECT
    *,
    COALESCE(
        LEAD(transaction_commit_timestamp) OVER (
            PARTITION BY order_id
            ORDER BY transaction_commit_timestamp
        ), 'unknown'
    ) end_timestamp
FROM orders_disambiguated
```

This view now works as expected with the naive, non-null handling version of the earlier query, returing the single last row at `07:19:43.913391`. Here are the start and end timestamp values for the final two transactions in that order, the last row including the synthetic end timestamp.

|transaction_commit_timestamp|end_timestamp|
|---|---|
|2024-06-28 07:19:32.597790|2024-06-28 07:19:43.913391|
|2024-06-28 07:19:43.913391|unknown|

## Indicating the current state

It's straightforward to add a column that indicates whether the row is the current state of the order at the time the query is executed. I'll pull the window function logic out into a CTE and reuse it to create an `end_timestamp` and an `is_current` boolean-valued column.

```sql title="Intuitive identification of which row is current"
CREATE OR REPLACE VIEW orders_windowed AS
WITH end_timestamps AS (
    SELECT
        *,
        LEAD(transaction_commit_timestamp) OVER (
            PARTITION BY order_id
            ORDER BY transaction_commit_timestamp
        ) maybe_end_timestamp
    FROM orders_disambiguated
)

SELECT
    *,
    COALESCE(maybe_end_timestamp, 'unknown') end_timestamp,
    maybe_end_timestamp IS NULL is_current
FROM end_timestamps
```

A query including `WHERE is_current` now selects only the current state of orders at the time of the query.

This view is compatible with the previous queries I've run. It also shows how to retain the null current timestamp in a `maybe_end_timestamp` column. That could ease those cases where it makes sense to explicitly handle the null value, in addition to `is_current` and `end_timestamp`.

Here are the values of all the new columns for the last couple of transactions in `order_30101`.

|transaction_commit_timestamp|maybe_end_timestamp|end_timestamp|is_current|
|---|---|---|---|
|2024-06-28 07:19:32.597790|2024-06-28 07:19:43.913391|2024-06-28 07:19:43.913391|false|
|2024-06-28 07:19:43.913391||unknown|true|

## Solving the promotions usecase

In the last article, I ran into [problems finding the correct transactions to use in promotions processing](../2024-06-30-cdc-latest-and-historical/index.md#why-i-cant-time-travel). The need to collect transactions into arbitrary time windows for processing in window functions caused problems and complexity.

In contrast, this approach only needs to determine the timestamp of the next transaction for a given order, if it exists, to populate the `end_timestamp` field. The window of rows processed by the window function does not need to align in the same way with the time window of interest to the query.

To recap the problem I needed to solve: identify the orders that had a `shipped_date` falling within a specific month based on the transaction states that were "current" at the end of the month.

```sql title="Example query conditions to pick qualifying transactions"
WHERE ('1996-08-01' <= shipped_date AND shipped_date < '1996-09-01')
  AND transaction_commit_timestamp <= '2024-06-12 10:30:30.412977'
  AND order_id = '20002'
```

This query did not work correctly in the cases I looked at.

### Updating the promotions view

First, I'll update the promotions view to use the new `orders_windowed` view.

```sql title="Updating the promotions view to use orders_windowed" hl_lines="8"
CREATE OR REPLACE VIEW "promotions" AS 
WITH
  order_urgency AS (
   SELECT
     *
   , (CASE WHEN (cdc_operation = 'D') THEN null ELSE DATE_DIFF('day', DATE(order_date), DATE(required_date)) END) notice_period_days
   FROM
     orders_windowed
) 
SELECT
  *
, COALESCE((notice_period_days > 28), false) qualifies_for_promotion
FROM
  order_urgency
```

The only change is the highlighted line, where I swap the `FROM` to point to the new view. The use of `*` in my `SELECT`s means no other changes are needed. If I were listing specific columns, I'd need to explicitly pass `end_timestamp` through.

### Checking correct behaviour

Now I can adjust my query for qualifying orders and check the test cases that tripped up the previous solution. `order_20002` was the test case. It has two updates with `shipped_date` in the range, but the earlier one qualified, and the update that was active at the end of month did not.

```sql title="Checking correct behaviour for order_20002"
SELECT
    transaction_commit_timestamp,
    end_timestamp,
    shipped_date,
    qualifies_for_promotion
FROM promotions
WHERE order_id = '20002'
    -- and shipped_date is in the qualifying period
    AND (
        '1996-08-01' <= shipped_date
        AND shipped_date < '1996-09-01'
    )
    -- measured by the state where the timestamp we're interested in falls between the commit and end timestamps
    AND (
        transaction_commit_timestamp <= '2024-06-12 10:30:30.412977'
        AND end_timestamp > '2024-06-12 10:30:30.412977'
    )
```

|transaction_commit_timestamp|end_timestamp|shipped_date|qualifies_for_promotion|
|---|---|---|---|
|2024-06-12 10:30:30.412977|unknown|1996-08-01|false|

This query returns the single, correct result as before. If we set the timestamp we're interested in to exclude the last transaction, we should get the previous transaction back.

We can move the the equality conditions in the last `AND` block to look just before the timestamp. We could also subtract one of the smallest time unit to get the same effect.

```sql title="Checking correct behaviour for order_20002"
    AND (
        transaction_commit_timestamp < '2024-06-12 10:30:30.412977'
        AND end_timestamp >= '2024-06-12 10:30:30.412977'
    )
```

|transaction_commit_timestamp|end_timestamp|shipped_date|qualifies_for_promotion|
|---|---|---|---|
|2024-06-12 10:30:30.041474|2024-06-12 10:30:30.412977|1996-08-01|true|

Where the previous solution returned no results, the `end_timestamp` approach brings back the correct row representing the state of the previous transaction.

## Solving the promotions usecase

We can now solve the promotions usecase as it stands. Which orders qualified for the promotion in the month of August 1996, based on the latest change data capture data at end August 2024?

```sql title="Identifying qualifying orders"
SELECT
    order_id,
    transaction_commit_timestamp,
    end_timestamp,
    shipped_date
FROM promotions
WHERE
    qualifies_for_promotion
    -- shipped_date is in the qualifying period
    AND (
        '1996-08-01' <= shipped_date
        AND shipped_date < '1996-09-01'
    )
    -- measured by the state where the timestamp we're interested in falls between the commit and end timestamps
    AND (
        transaction_commit_timestamp < '2024-09-01 00:00:00.000000'
        AND end_timestamp >= '2024-09-01 00:00:00.000000'
    )
```

There are two!

|order_id|transaction_commit_timestamp|end_timestamp|shipped_date|
|---|---|---|---|
|30100|2024-06-28 07:17:32.254799|unknown|1996-08-01|
|30102|2024-06-28 07:28:41.227500|unknown|1996-08-01|

--8<-- "blog-feedback.md"


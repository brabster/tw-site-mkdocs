---
title: Time travelling with change data capture
date: 2024-07-14
---


--8<-- "ee.md"

<!-- more -->

## The historical query problem

The last post showed that it's quite easy to see the latest state of any order in our orders table, but I ran into problems trying to see the latest state at a specific prior point in time. I'll pick a transaction with several updates to explore a solution.

```sql
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

For exmaple, `2024-06-28 07:19:15.000000`. I can see the correct answer is row three in the table above - the row with timestamp ending `07:19:14.859907`.

A simple `WHERE` clause can't help. `WHERE transaction_commit_timestamp = '2024-06-28 07:19:15.000000'` gives no results, because no transaction took place at that exact time. I can't see a simple way to construct a cause based on inequalities that returns the correct row alone either - less than or equal to the timestamp gives us the correct row, plus the two previous rows.

### Visualising the problem

Each transaction related to a given primary key gets its own row in the database. That row indicates when the transaction took place - the point in time when the change took effect. The row does not tell us when the change was superceded by the next change. I visualse what's going on like this:

```console
                      
      t1    t2    t3  ?  t4  future
Insert|-----|-----|---|--|----->
      Update|-----|---|--|----->
            Update|---|--|----->
                   Update|----->
```

Starting with the insert, each transaction is a new arrow. Each arrow begins when the transaction committed and never ends.

### A messy solution

If I create a CTE including only the rows after the timestamp of interest, I can then use a subquery to select only the updates up to the timestamp of interest. The row I want is the the one with the largest timestamp.

```sql
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

Within each row, I can only see the timestamp at which the change takes effect. I can't see when it was superceded - I would need to order the rows by timestamp and then look in the next row for that, which suggests a window function might be a simple and efficient solution.

If I have "end" timestamps, then I can write a simple, intuitive query for the single transaction that was valid at the time.

```console
      t1    t2    t3  ?  t4  future
Insert|---->|     |   |  |
      Update|---->|   |  |
            Update|---|->|
                   Update|----->
```

The window function is straightforward.

```sql
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

```sql
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



--8<-- "blog-feedback.md"


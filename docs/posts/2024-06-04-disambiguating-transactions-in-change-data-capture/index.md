---
title: Disambiguating Transactions in Change Data Capture
date: 2024-06-04
---

![Example query against disambiguated view](./assets/disambiguated_sql.webp)

intro snippet

--8<-- "ee.md"

<!-- more -->

## Recap

Last time, I looked at [how transactions in the source system a represented in change data capture output](../2024-05-28-exploring-transactions-in-cdc/index.md). I also set Athena up so that I could interact with the CDC output with SQL.
We've covered enough to illustrate a problem I had to deal with for a usecase I was recently working with.

!!! note
    [northwind_cdc.tar.gz](../2024-05-21-cdc-with-aws-dms/assets/northwind_cdc.tar.gz){:download="northwind_cdc.tar.gz"} is a copy of the CDC output used in this series for your own exploration without having to spin up databases and DMS.

## Example Usecase - Promotions

Here's an example of the kind of problem we might be able to solve with a bit of SQL that might otherwise need significant changes to software. Be aware that I am making the usecase up, so please be prepared to suspend your disbelief accordingly. I'll only be focusing aspects of the problem that I think show interesting challenges in CDC data.

### Problem Statement

We want to encourage customers to allow us plenty of time to fulfil their orders. We'll incentivise that with a promotion. Each month, we'll enter qualifying orders into a raffle to win some swag. "Qualifying" orders give more than 28 days' notice between order and required dates when the order ships.

### Discussion

Can I find the qualifying orders using the CDC feed? I think so - we can run a query at the end of each month to find eligible orders, I could even pick a winner from those (`ORDER BY RANDOM() LIMIT 1`?). Our Northwind database represents the backed of a sales system, and we'll focus on the `orders` table for this post. As we saw last time, each row in the `orders` table represents an order. There's about 14 columns, and it seems likely that there's a subset that are interesting for this usecase:

- `order_id` - a unique identifier for an order
- `order_date` - the date the order was placed
- `required_date` - the date the order is required by
- `shipped_date` - the date the order shipped

### Exploring Qualification

A quick query to see if we have any possibly qualifying orders in the current dataset.

```sql
WITH order_urgency AS (
    SELECT
        order_id,
        order_date,
        required_date,
        DATE_DIFF('day', DATE(order_date), DATE(required_date)) notice_period_days
    FROM orders
)

SELECT
    *
FROM order_urgency
WHERE notice_period_days > 28
```

I get 61 results back, all with 42 `notice_period_days`. 

## Case: Initial Load

First, orders that were already shipped when we did our CDC full load, one that could qualify, one that could not.I pick those out of the existing historical data to help get a feel for the basic query I need.

```sql
WITH order_urgency AS (
    SELECT
        order_id,
        order_date,
        required_date,
        DATE_DIFF('day', DATE(order_date), DATE(required_date)) notice_period_days
    FROM orders
)

SELECT
    *,
    notice_period_days > 28 qualifies_for_promotion
FROM order_urgency
WHERE order_id IN ('10249', '10253')
```

|order_id|order_date|required_date|notice_period_days|qualifies_for_promotion|
|--------|----------|-------------|------------------|-----------------------|
|10249|1996-07-05|1996-08-16|42|true|
|10253|1996-07-10|1996-07-24|14|false

## From Query to View

Having this logic in a query is going to be a pain to work with. The case above is an example - my promotions logic and my test case details are mixed up in the same query. To separate them out, I'll put the logic in a view instead - then I can query that view to debug and test my logic.

!!! note
    This is the first step from a query to a data pipeline, and opens up lots of flexibility and power to build up complex, robust solutions from simpler, well-tested pieces. Plain SQL will quickly become problematic, in the same way that trying to build a Java application just using plain text files containing code would. Tooling like `dbt`, `DataForm` et al. help to deal with the emergent complexity and needs in much the same way that `Maven` or `Gradle` do for Java applications.

```sql title="Promotions logic in a view"
CREATE OR REPLACE VIEW promotions AS
WITH order_urgency AS (
    SELECT
        *,
        DATE_DIFF('day', DATE(order_date), DATE(required_date)) notice_period_days
    FROM orders
)

SELECT
    *,
    notice_period_days > 28 qualifies_for_promotion
FROM order_urgency
```

Now, my exploratory query is much simpler. The following query gives the same results as before.

```sql title="Exploratory query now just contains the interesting order_ids"
SELECT
    *
FROM promotions
WHERE order_id IN ('10249', '10253')
```

### Aside on `SELECT *`

`SELECT *` is often a bad idea in queries, usually referenced in the "best practice" advice from the data warehouse vendor, like number 10 in the [Athena top 10 performance tuning tips](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-tips-for-amazon-athena/). This is great general advice for queries, but there are a couple of important exceptions.

- if the dataset is small, or you can guarantee that you're only scanning a small amount of data with the `SELECT *`, then it can be really helpful for exploratory analysis.
- if you're working in a view, the backing data is columnar (native tables, Parquet et al. are) and the data warehouse supports predicate pushdown (modern data warehouses do) then `SELECT *` actually has no performance impact. The columns selected in a query against the view will dictate which columns actually get scanned. It's a really handy way of augmenting a table with new, computed columns without having to repeat lists of column names.

This case ticks the first criterion.

## Case: Multi-Statement Transaction

Let's get on with exploring the disambiguation problem.. I'll take the [multi-statement transaction from the last post](../2024-05-28-exploring-transactions-in-cdc/index.md#multi-statement-transactions-in-cdc) and run it to see how that looks with our logic.

```sql title="Find the three statements involved in the example transaction"
SELECT
    *
FROM promotions
WHERE order_id = '19999'
```

Ah. `INVALID_CAST_ARGUMENT: Value cannot be cast to date:`. Our transaction ended with a `DELETE` operation, and as everything else is from the CDC full load, this is the first `DELETE` we've seen.

What does the CDC data look like?

```sql title="Find the three statements involved in the example transaction"
SELECT
    *
FROM orders
WHERE order_id = '19999'
```

|cdc_operation|transaction_commit_timestamp|order_id|order_date|required_date|transaction_sequence_number|
|-------------|----------------------------|--------|----------|-------------|---------------------------|
|I|2024-05-31 20:09:45.208234|19998|1996-07-04|1996-08-01|20240531200945200000000000000000061|
|U|2024-05-31 20:09:45.208234|19998|1996-07-04|1996-08-01|20240531200945200000000000000000065|
|D|2024-05-31 20:09:45.208234|19998|||20240531200945200000000000000000069|

OK, when `cdc_operation=D` for delete, we get `NULL` or the empty string back in the data fields other than the `order_id`. I can't tell the difference in the Athena UI, but `DATE(NULL) = NULL` so it must be the empty string, as we get a parse error. Why the empty string? Probably because the source data is `.csv`, so there's no notion of `NULL`-ness distince from the empty string. Using the alternative Parquet format is a better choice, as it would provide a way of expressing `NULL`, as well as mote metadat like column type information.

!!! tip
    I use the SQL UI to whatever database I'm using to answer questions I have about how functions behave in these kinds of scenarios. `SELECT DATE(NULL)` is a valid SQL statement and returns `NULL`. `SELECT DATE('')` is also a valid statement but returns the parse error, confirming my suspicion. Learning that I don't actually need a `FROM` clause is a superpower, turning the SQL interface into a kind of REPL.

I'll modify the `notice_period_days` calculation to handle the delete case.

```sql hl_lines="5-8 14" title="Handling DELETE operations"
CREATE OR REPLACE VIEW promotions AS
WITH order_urgency AS (
    SELECT
        *,
        CASE
            WHEN cdc_operation = 'D' THEN NULL
            ELSE DATE_DIFF('day', DATE(order_date), DATE(required_date))
        END notice_period_days
    FROM orders
)

SELECT
    *,
    COALESCE(notice_period_days > 28, FALSE) qualifies_for_promotion
FROM order_urgency
```

As usual, there's other ways to express that logic. I think that's a fairly clear expression of what's going on. I won't just filter the delete operations out yet as I might need them before I'm done.

I get three rows out of the query, one for each statement in the original transaction. Two of those rows represent "work in progress" and aren't useful for this usecase (or any other interesting usecase I can think of, to be honest. If you know of one, please enlighten me via feedback, instructions at bottom of post). What I need is a single row representing the state of the database for this order at the end of the transaction.

## Simple Disambiguation

I'm sure it's possible to use `GROUP BY` to do this but it's not going to be clear or straightforward. `GROUP BY` summarises groups of rows, column by column. I want to filter out the rows before the last one in each transaction group. I can use a window function to label the last row in each transaction group and then use that label to filter out the other rows.

Building the window function: for each row, the "window" is the other rows in the same transaction: `PARTITION BY order_id, transaction_commit_timestamp`, in reverse chronological order: `ORDER BY transaction_sequence_number DESC`.

That ordering puts the most recent row first. I use the `ROW_NUMBER()` function with this window to label each row with its position in the transaction, so that the latest row getting the value `1`. It's now easy to filter out the rows that have values other than `1`.

!!! note
    I don't have a reliable `transaction_id` in the data. `transaction_commit_timestamp` is the nearest thing, but I can't rely on that alone. If transaction for two different orders happened to commit at the exact same time, I'd only get one row out, which means I'd get the correct update for one order but miss the update for the other. Partitioning by `order_id` as well mitigates that risk, now I'd need two transactions for the same order committing at the exact same time to have a problem. I don't see a simple way of getting a unique `transaction_id` out of DMS (`PreserveTransactions` alters the directory structure, so wouldn't be straightforward to use and would constrain other settings), so this seems like the best we can do.


I think this logic is all about the order and CDC process rather than the promotions thing I'm doing. I'll add a view over the orders table to do this work and keep the complexity away from my promotions logic.

```sql title="Disambiguated order transactions view"
CREATE OR REPLACE VIEW orders_disambiguated AS
WITH identify_last_order_statement_in_transactions AS (
    SELECT
        *,
        -- last statement in transaction gets TRUE
        ROW_NUMBER() OVER(
            transaction_statements_reverse_chronological_order
        ) AS position_in_transaction
    FROM orders
    -- could be inlined, this way I can give it a meaningful name
    WINDOW transaction_statements_reverse_chronological_order AS (
        -- rows with same order_id and commit timestamp
        -- are in the same transaction
        PARTITION BY order_id, transaction_commit_timestamp
        ORDER BY transaction_sequence_number DESC
    )
)

SELECT
    *
FROM identify_last_order_statement_in_transactions
-- filter in only the last statements in each transaction
WHERE position_in_transaction = 1
```

I ran this query earlier still selects the three rows related to this transaction from the `orders` table:

```sql title="Still three rows in orders table involved in the example transaction"
SELECT
    *
FROM orders
WHERE order_id = '19999'
```

The same query from the `orders_disambiguated` view returns only the DELETE row, as expected.

<figure markdown="span">
 ![Screenshot of Athena output of one row for disambiguated transaction](./assets/disambiguation_athena_output.webp)
 <figcaption>Screenshot of Athena output of one row for disambiguated transaction</figcaption>
</figure>

!!! note
    Many data warehouse systems, like [BigQuery, have a `QUALIFY` clause](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#qualify_clause). That allows you to add the clause `QUALIFY position_in_transaction = 1` to the CTE instead of needing a separate query to do that filtering. Athena/Trino does not support the `QUALIFY` clause.

## Case: Complex Multi-Statement Transaction

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

## Sense Check

Taking a step back, there's one simple check I can do to find any glaring issues. There should some examples in the `orders` table for the same transaction that have more than one row. There should be none in the `orders_disambiguated` table. Is that the case?

```sql title="Find multi-row transactions in the orders table"
SELECT
    order_id,
    transaction_commit_timestamp,
    COUNT(1) record_count
FROM orders
GROUP BY order_id, transaction_commit_timestamp
HAVING COUNT(1) > 1
```

Results: Two. `order_id 19999` has a transaction with three rows, `order_id 20002` has one with six.

Same query, but `FROM orders_disambiguated`?

`No results`.

## Importance of `transaction_sequence_number`

`transaction_sequence_number` is crucial to the solution above. There's a couple of other scenarios worth mentioning.

### CSV Line Number Order

[AWS documentation indicates that DMS writes lines to these `.csv` files in transaction order](https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.S3.html) - and it looks like the rows come out in the right order when we query, so why bother with `transaction_sequence_number`? We could talk about the drawbacks of depending implicitly on the line ordering in the source files, but in the same docs, AWS tell us that the row order is not meaninful in Parquet, which is the output type you'll almost certainly see in the real world applications.

### No `transaction_sequence_number`

That `transaction_sequence_number` is pretty important, and it wasn't there by default. I had to explictly [add that column to the defaults as part of the setup](../2024-05-21-cdc-with-aws-dms/index.md#dms-mapping-rules). Can you still disambiguate transactions reliably if you **don't** have that column available?

This in the tricky scenario my team faced in a recent engagement - and we were working with Parquet, so depending on source file line order wasn't an option even if we'd wanted to. After picking the problem apart with other experts in the team, we came up with a plan. We implemented some heuristics, based on how CDC worked and what we knew about the source application and database.

- if the ambiguous transaction contained an `INSERT`, then anything else should have happened afterwards and we can ignore the insert
- if the ambiguous transaction contained a `DELETE`, then that should have been the last thing that happened and we can ignore everything else
- for the remaining cases
    - for each column, collect the possible values and if there's more than one, subtract the previous transaction's value from the options
- after applying those heuristics, take the values that are left for each column, adding a new column that indicates whether there any columns that hadn't resolved down to a single value.

It's not satifying or pretty, but after a couple of days work, a lot of tests and a lot of automation and manual validation, we couldn't find any remaining ambiguous cases. If I get time, I'll recap the specifics of how we did it.

## Next Time

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


--8<-- "blog-feedback.md"


---
title: GROUP BY ALL solves a really annoying SQL problem
date: 2025-05-29
---

![hero image](./assets/modified_query.webp)

Does your SQL still copy most of your columns from `SELECT` after `GROUP BY`?

Behold: `GROUP BY ALL`.

--8<-- "ee.md"

<!-- more -->

## The problem

A simple example of the problem looks like this. I have a table of page views, one row per view. I want to know how many downloads I had each day, so I write some SQL like this:

```sql
SELECT
    view_date,
    COUNT(1) num_views
FROM the_raw_views_table
GROUP BY
    view_date
```

See how I have to repeat `view_date` in the `GROUP BY` clause? It's required, and it's pretty much the only appropriate simple value. I must add any columns that I'm not aggregating (I used the aggregate function `COUNT()` here) to the `GROUP BY` clause for the query to be valid.

Grouping is something we do all the time. It's a minor irritation when there are only a couple of columns to add, but I've seen queries where there are tens, maybe even hundreds of columns that have to be carefully kept synchronised.

A chunkier example from GitHub:

```sql
GROUP BY the_date, countryname, twitter_trend, google_trend, latcent, longcent
```

## The poor solution

I've seen a bad solution around, where you don't need to actually name the columns but can instead use the column's ordinal number. The previous query would look like:

```sql
GROUP BY
    1
```

This is a bad idea for readability, and now you have a list of sequential numbers to keep in sync instead. Here's an example I found on GitHub for how silly it can get:

```sql
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, i.indnatts
```

## The good solution

[On 23 May 2024, Google made `GROUP BY ALL` generally available](https://cloud.google.com/bigquery/docs/release-notes#May_13_2025), and I totally missed it. Now, I can just say what I mean :tada:.

```sql
SELECT
    view_date,
    COUNT(1) num_views
FROM the_raw_views_table
GROUP BY ALL
```

It doesn't matter if you have one plain select column or 100. `GROUP BY ALL` infers the list. [The full documentation explains the specifics and how the inference works](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#group_by_all).

## Supporting platforms

I actually found [`GROUP BY ALL` first on the Databricks platform](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-groupby#parameters).

- It's also [available on Snowflake](https://docs.snowflake.com/en/sql-reference/constructs/group-by#parameters).
- [Amazon Redshift has it](https://docs.aws.amazon.com/redshift/latest/dg/r_GROUP_BY_clause.html).
- [DuckDB has GROUP BY ALL too](https://duckdb.org/docs/stable/sql/query_syntax/groupby.html#group-by-all).

I don't think Trino (and by extension AWS Athena) have `GROUP BY ALL`.


--8<-- "blog-feedback.md"


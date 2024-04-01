---
title: The BigQuery Safety Net
date: 2024-02-16
categories:
  - python
  - security
  - insights
  - operations
---

[Last time](../2024-02-08-pypi-downloads-danger/index.md), I said:

> [BigQuery] doesn't offer a "don't bankrupt me without asking first" setting.

After further work, I find that's not true! This setting is available in the UI, just a bit tricky to find. More importantly, there's another set of controls elsewhere that you **need** to know about if you want to use BigQuery safely.

--8<-- "ee.md"

<!-- more -->

Since publishing the last post, I've heard a couple of anecdotes from other folks about nasty billing surprises after playing with BigQuery. I take that to mean it's not just me being an idiot - it's quite easy to spend accidental money with this service.

## The Problem

I describe the problem in detail in [$1,370 Gone In Sixty Seconds](../2024-02-08-pypi-downloads-danger/index.md). In summary:

### Billing Model

By default, BigQuery is billed based on how much data is scanned by your queries

### UI Challenges

The UI gives an indication of the scanned data volume, but this is easy to miss and isn't linked to cash spend in the UI. ~~There is no UI in BigQuery to limit how much data is scanned~~

Contrary to what I said last time, there **IS** a UI element to set the max bytes billed. I totally missed it in a ghosted text input field that I never noticed. To me, it looks like part of the Encryption settings. The fact that no-one has corrected me on the previous post suggests that it's not just me. It takes three-to-four clicks and a scroll to find it:

- More
  - Query Settings
      - Advanced Settings
        - Ghosted Text Input Field: "Maximum Bytes Billed"

<figure markdown="span">
  ![](./assets/max_bytes_billed.png)
  <figcaption>Screenshot of the max bytes billed setting in BigQuery UI</figcaption>
</figure>

Easy when you know how.

### Per-Query Settings

The `max-bytes-billed` setting is super-helpful both in the UI and programmatic calls, but there's a problem from a cost management perspective. It's per-query, not per-user or per-unit-time. Whilst I can prevent a single query from scanning from, say, 1TB and thus costing more than $5, I can't prevent a hundred executions of a query from costing $100*5 = $500.

If only there was a way to set limits on spend over time?

## The Missing Piece - Quotas

I was aware of limits and quotas as a soft or hard limit on resource utilisation imposed by the cloud provider from my initial contact with AWS about a decade ago (no, the web was not in black and white back then, whippersnapper!). Soft limits could be increased but I don't think there was any way of **reducing** them.

GCP provides a [general "Cloud Quotas" service](https://cloud.google.com/docs/quotas), which provides exactly that. There's a lot of granularity here, but I've found what I think is the critical setting you want as a safety net to limit query spend per day. Here's how you find and update it.

Note that it's a **project-level** setting - I've not seen a way to set a default quota over a whole account or org yet.

---

Open the project's quota panel.

<figure markdown="span">
  ![](./assets/find_quotas.png)
  <figcaption>Per-project quotas panel</figcaption>
</figure>

---

Search for the query usage quota setting.

<figure markdown="span">
  ![](./assets/quota_find_query_usage_bq.png)
  <figcaption>Searching for a specific quota</figcaption>
</figure>

---

You get some information about the current quota setting and actual usage - I've not run any queries in this project today, if I had you would see that in the usage metrics.

{{< figure
  src="./assets/quota_query_usage_per_day_bq.png"
  caption="Information about a quota, including current limit and real usage in the current period" >}}

---

To adjust the quota you have to select the checkbox next to the quota(s) you want to change and hit "edit" over in the top-right.

>  maybe Google could use some UX support... I know a [great consultancy](https://equalexperts.com) that would be happy to help ;)

You have the option of setting a limit on query bytes scanned for the project, or per-user. I'm setting a limit of 1TB per day for the whole project here. You have to uncheck "unlimited" to update the setting.


<figure markdown="span">
  ![](./assets/quota_update_bq.png)
  <figcaption>Update quota panel</figcaption>
</figure>

---

Hit submit request, and it'll update. But does it work? I've risked the spend so you don't have to...

<figure markdown="span">
  ![](./assets/query_usage_quota_effect.png)
  <figcaption>Effect of quota update</figcaption>
</figure>

Woohoo! I tried to run a 3.4TB query, and I was prevented from doing so. I can see that the query was stopped at the planning stage, before any execution took place - so I was billed nothing, instead of around $17.

## Operability of Quotas

This is a project-level setting - so if you're working as part of an organisation there's a good chance you won't have permissions to adjust it. In this case you can be the finops hero your organisation needs by flagging up the financial risk and simple mitigation to whomever looks after your GCP platform and pointing them at automation like the [GCP Terraform provider's `service_usage_consumer_quota_override`](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_usage_consumer_quota_override).

There's some useful info in the quotas view that helps you understand your utilisation over time.
Here's my quota use - you can see where I made the mistakes I talked about last time and scanned several TB in a day!

<figure markdown="span">
  ![](./assets/query_usage_quota_metrics.png)
  <figcaption>Quota console metrics for usage of a particular quota over recent history</figcaption>
</figure>

If you aren't able to access this information, I'd suggest to your GCP Overlords they try to make it available to you, so you can work out what you want that quota set to. There's no useful information provided in the BigQuery UI, even when you hit a quota limit.

I'd want to set things up to have fairly generous quotas by default - there might be a temptation to really restrict potential spend once someone with a budgetary responsibliity starts thinking about it.
A generous default is literally infinitely better than an unlimited default! I'd set up with a generous default and per-project overrides. There will be no way you can work around the quota if you do need to use more than the allotted quota per day, aside from waiting until the next day. That would be **really** frustrating.


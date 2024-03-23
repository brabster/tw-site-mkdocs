---
title: 'TBC'
date: 2023-10-25
draft: true
category: SQL
tags:
 - dbt
 - sql
 - contract-testing
 - data-mesh

---

TBC

<!--more-->


## The Snapshot Report

Alongside these dashboards, a scheduled point-in-time report needs to be produced, that tells a similar story alongside a narrative, and covering a different time period.

For this report we found subset of the expectations we saw of the dashboard, although the different, fixed time period creates some differences. Additionally, as this report is generated on a schedule, it can be challenging to maintain specific expertise in the report with the ability to spot subtle problems.

We considered contracts for this reporting process when we saw the current production process generate numerous questions about the correctness and completeness of the underlying data. Conversations framed around producing a data contract for the report seemed much more productive in helping capture expectations in an executable way that had never been written down before.


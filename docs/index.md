# Home

<div class="grid cards" markdown>
  - ![Profile photo for Paul Brabban](./assets/images/profile_small.gif) Paul Brabban, Lead Consultant at [Equal Experts](https://www.equalexperts.com/blog/author/paul-brabban/)

    ---

    With experience in software development, data engineering and machine learning, I specialise in data-intensive problems and decentralised data engineering at scale. My experience extends to leading teams, technical architecture and product development. Find out more about my experience and publications in my portfolio.

    ---

    Contact me to see how I can help at paul@tempered.works.
</div>

<!-- GENERATED_CONTENT -->

## Recent posts

### [How to get pwned with --extra-index-url](https://tempered.works/posts/2025-12-06-how-to-get-pwned-with---extra-index-url/)

  *Dec 6, 2025* &nbsp; `automation` `operations` `security`


<figure markdown="span">
 ![A diagram illustrating a dependency confusion attack using Python's pip. The layout compares a "private registry" hosting a safe package (version 0.0.1) against a "public registry" hosting a malicious package of the same name (version 1.0.0). An arrow from the private registry is labeled "nope, too old," while an arrow from the public registry is labeled "winner!" pointing to the user's computer. The computer is stamped "COMPROMISED" because pip prioritized the higher version number found on the public index.](posts/2025-12-06-how-to-get-pwned-with---extra-index-url/assets/scenario.webp)
</figure>

Python's built-in pip package manager is unsafe when used with the `--extra-index-url` flag (there are other dangerous variants too). An attacker can publish a malicious package with the same name and...

### [UDAFs, stored procedures and more in dbt](https://tempered.works/posts/2025-08-04-udafs-stored-procedures-and-more-in-dbt/)

  *Aug 4, 2025* &nbsp; `insights`


<figure markdown="span">
 ![A screenshot showing a stored procedure in the BigQuery console, with dbt compilation details in a comment block.](posts/2025-08-04-udafs-stored-procedures-and-more-in-dbt/assets/sp.webp)
</figure>

It's been over a year since I first wrote about managing UDFs using custom dbt materializations. The approach has held up well, but a recent project required me to go further and bring UDAFs (user-def...

### [BigQuery, safer by default from September 2025](https://tempered.works/posts/2025-07-17-bigquery-will-be-safer-by-default/)

  *Jul 17, 2025* &nbsp; `insights` `operations`


<figure markdown="span">
 ![A snippet of an email from Google, showing the change in BigQuery project quota defaults](posts/2025-07-17-bigquery-will-be-safer-by-default/assets/mail.webp)
</figure>

On September 1st 2025, Google will make BigQuery a lot safer by default, changing the default quotas for projects under the default on-demand pricing model. Instead of unlimited financial damage, the ...

### [GitHub Codespaces, one year later](https://tempered.works/posts/2025-06-07-my-year-with-github-codespaces/)

  *Jun 7, 2025* &nbsp; `operations` `security`


<figure markdown="span">
 ![A screenshot of the GitHub web UI option to create a new Codespace on main](posts/2025-06-07-my-year-with-github-codespaces/assets/codespaces_hero.webp)
</figure>

Back in early 2024 I tried GitHub Codespaces, and quickly ditched my local dev setup entirely. This post shares my experience going cloud-native for development: benefits for onboarding, agility, and ...

### [GROUP BY ALL solves a really annoying SQL problem](https://tempered.works/posts/2025-05-29-group-by-all-solves-a-really-annoying-sql-problem/)

  *May 29, 2025*


<figure markdown="span">
 ![A SQL query screenshot demonstrating GROUP BY ALL, which eliminates the need to list non-aggregated columns explicitly after GROUP BY](posts/2025-05-29-group-by-all-solves-a-really-annoying-sql-problem/assets/modified_query.webp)
</figure>

Does your SQL still copy most of your columns from `SELECT` after `GROUP BY`? Behold: `GROUP BY ALL`.

### [My path to consultancy](https://tempered.works/posts/2025-05-11-my-consulting-story/)

  *May 11, 2025* &nbsp; `operations`


<figure markdown="span">
 ![A country road stretches off into the sunny, leafy distance as my little boy cycles his favourite route home from school](posts/2025-05-11-my-consulting-story/assets/country_road.webp)
</figure>

I had big doubts about becoming a consultant or contractor. Could I do it? Would I find work? Could I run my own business? Would I need to change who I am, wear a suit, or buy a briefcase? Seven years...

### [Rethinking the guest network to improve my home network security](https://tempered.works/posts/2025-03-23-rethinking-the-guest-network-to-improve-my-home-network-security/)

  *Mar 23, 2025* &nbsp; `operations` `security`


<figure markdown="span">
 ![Network diagram showing the internet connected to a router, linked to four devices: tablet, mobile phone, laptop, and IoT device.](posts/2025-03-23-rethinking-the-guest-network-to-improve-my-home-network-security/assets/schematic_guest_network.webp)
</figure>

I believe that making my guest network my default network reduces the potential harm a compromised app or device can cause. What was my "trusted" network is now my "untrusted" network, with only a few...

### [Generating portable and user-friendly identifiers](https://tempered.works/posts/2025-03-08-generating-portable-and-user-friendly-identifiers/)

  *Mar 8, 2025* &nbsp; `insights` `operations` `performance`


<figure markdown="span">
 ![A screenshot of the BigQuery console, with example SQL for generating an identifier from a string value as I outline below](posts/2025-03-08-generating-portable-and-user-friendly-identifiers/assets/image.webp)
</figure>

I'll share how I generate unique identifiers from data in 2025, avoiding the pitfalls I've seen along the way. TL;DR: I'm using MD5 to produce a digest from a string or bytes value, then I'm using pla...

### [Using AWS billing to track down lost resources](https://tempered.works/posts/2025-02-09-using-aws-billing-to-track-down-lost-resources/)

  *Feb 9, 2025* &nbsp; `operations`


<figure markdown="span">
 ![Screenshot of the AWS billing console showing cost and usage data with an unexpectedly higher bill](posts/2025-02-09-using-aws-billing-to-track-down-lost-resources/assets/aws_billing_console.webp)
</figure>

My AWS bill was higher than I expected, and it wasn't immediately clear what was driving the cost. Here's how I tracked down the culprits.

### [Testing stored procedures](https://tempered.works/posts/2025-01-18-testing-stored-procedures/)

  *Jan 18, 2025* &nbsp; `insights`


<figure markdown="span">
 ![Screenshot of a stored procedure definition and test written in BigQuery SQL](posts/2025-01-18-testing-stored-procedures/assets/hero.webp)
</figure>

Update August 2025 Since writing this post, I've found a clean way to handle stored procedures and their outputs for dbt users by treating them as materializations. This makes testing them as straight...

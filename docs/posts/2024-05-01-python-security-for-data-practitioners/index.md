---
title: My Python Data Security Cheat Sheet
date: 2024-05-01
---

![hero image](./assets/hero.webp)

Where I see significant risks in the Python ecosystem for data practititioners and the steps I take to mitigate them across the projects I work on.

--8<-- "ee.md"

<!-- more -->

When I speak to fellow data practitioners like (but not exclusively) data scientists, data engineers and analysts/analytics engineers, I find there's common concern about the security risks they're exposed to, but a lack of clear, pragmatic guidance on how to mitigate them. A lot of the guidance out there, like [Snyk's Python security best practices](https://snyk.io/blog/python-security-best-practices-cheat-sheet/), focuses on traditional software engineering.

This cheat sheet is intended for the diversity of experience I've seen in the data-centric world.

## Paritioning My Work

I have at least three different, isolated working environments that I use locally. One laptop is for my personal stuff. At any given time it may have access to credentials for my AWS accounts, my GCP account, my password manager and GMail. If someone bad got into the first two they could run me up a painful bill, despite having billing alarms set up (I talk about that in [$1,370 Gone in Sixty Seconds](../2024-02-08-pypi-downloads-danger/index.md)). If they got into either of the last two they can steal my identity and do untold harm to me and my family. I really need to minimse the risk on that computer!

Then I have a laptop that Equal Experts gave me. This will have credentials for EE things that I have a responsibilty to protect. EE-related work on here.

Finally I have a laptop that I do client work on. Same deal, even greater responsibility to protect. This laptop is used for nothing but client work.

I have a separate long, strong password for all three, and their disks are all encrypted. That's the basic layer of pretection - if any one were ever compromised, it's bad enough. But it's better than all three being compromised. There's more about how I manage multiple laptops and additional security measures I use in my posts on [automating my laptop build](../2024-02-27-automated-laptop-build-intro/index.md) and [living with an automated laptop build](../2024-03-01-automated-laptop-build-conclusion/index.md).

### PIP_REQUIRE_VIRTUALENV

It's really easy to install into your system Python by mistake - you forget to activate the venv, or you think it's active when it's not. Ideally, your system permissions are set up so that you can't write to your system Python installation, but I find that's quite rare. It's certainly not the case on the current Ubuntu OS on the laptop I'm sitting in front of right now.

You can change the default behaviour of pip on your computer so that it won't install in the system python.
I set an environment variable `PIP_REQUIRE_VIRTUALENV` to `true` in scripts where I interact with pip. For example, [the init_and_update.sh script in this repository sets PIP_REQUIRE_VIRTUALENV](https://github.com/brabster/tw-site-mkdocs/blob/27b7a94d7dcaf0fd51c39395a205db1e5de1e9a2/.dev_scripts/init_and_update.sh#L5). I also set it one-off as a system-wide environment variable.

```console
$ export PIP_REQUIRE_VIRTUALENV=true
$ pip install safety
ERROR: Could not find an activated virtualenv (required).
```

There are [a number of other ways to tell pip not to install in the system python](https://docs.python-guide.org/dev/pip-virtualenv/#requiring-an-active-virtual-environment-for-pip) if environment variables don't work for you.


## Using pip

For the past 18 months, I've used plain old [pip, the Python Packaging Authority's recommended tooling](https://packaging.python.org/en/latest/guides/tool-recommendations/#installing-packages) and I'm actually very happy there and would recommend it to other Python practitioners. My workflow with pip and venv is:

```console
$ python -m venv venv # create a venv for the current project if needed
$ source venv/bin/activate # activate the venv (slightly different command on Windows)
$ which python # check that the venv is active; IDE usually indicates clearly when venv is active
$ pip install -U -r requirements.txt # install and update packages in this venv based on requirements.txt file
```

### Pipenv, Poetry et al.

I've used [pipenv](https://pipenv.pypa.io/en/latest/). I've used [Poetry](https://python-poetry.org/). There's several more. In my experience, they're far more trouble than they're worth. I have a bunch of stories about this that I'll share another day.


### Conda

I haven't used conda. One of the reasons for that is complexity around commercial use in the [terms of service](https://conda-forge.org/blog/2020/11/20/anaconda-tos/) to warrant a [clarifying blog post](https://legal.anaconda.com/policies/en/). I expect the advice here around managing dependencies applies equally to conda but I can't say for sure.


## Assessing Dependency Risk

Any software you bring onto your computer has the potential to hurt you. In the case of Python, just installing it a package can let bad actors loose on your computer. My working assumption is that any software running on the computer I'm using can do anything I can do, including accessing any passwords, access tokens, session tokens I have. Maybe even my password manager if it's unlocked.

To exacerbate the problem, I don't trust what I see on the internet. Anyone can publish anything they want and say anything they want. Identities can and have been stolen and used to inject malware into previously safe software. Maintainers can be bought out or get burnt out. I don't think there's anything I can do here that completely mitigates the risks, but I can reduce it. I'll take this opportunity to plug [a responsible, in-depth treatment of package handling over at python.land](https://python.land/virtual-environments/installing-packages-with-pip).

### Is the package popular?

A heavily-used package is a juicy target for bad actors. On the other hand... heavily-used packages have more eyeballs on them. They're more likely to be looked at by security researchers, and if there is a problem I'm in a larger crowd of potential victims, so a lower chance that I will exploited before I have a chance to respond or my credentials and so on expire or are changed. On balance, I prefer packages with evidence of large user communities.

- search for articles and blogs mentioning it
- check out GitHub stars, forks

Special mention to [libraries.io](https://libraries.io/search?q=colourama&sort=dependents_count), providing a search interface with metrics about how a package is used by others - `Sort: Dependents`.

!!! warning
    **Copy-paste the package name from somewhere you trust!** The bad actors love publishing malware-laden packages with similar names to popular legitimate packages. These packages are downloaded thousands of times before they are identified and removed!


### Minimising Dependency Use

There's so much software out there, a solution for every problem or suboptimal thing you could imagine. I save myself the time of more in-depth thinking by just trying to be honest with myself about whether I really need something or not.

- Do I really need to use `Poetry`? No, I can use boring old `pip`.
- Do I really need to use `murmurhash`? No, I can use Python's boring old built-in `hash`.
- Do I really need to use `colorama`? No, I can live with boring old monochrome terminal text.

Remember too that just because you're making boring choices in the name of safety does not mean the packages you do choose to depend on are make safety-over-coolness choices. Every time you avoid a dependency, you're actually cutting out that dependency, and its dependencies, and their dependencies and so on! That whole subtree of dependencies, and the choices their maintainers make, and their vulnerabilities? Not your problem anymore.

### Using Common Cross-Project Dependencies

I also try to use the same dependencies everywhere, instead of allowing variation without good reason. That helps me really get to know those dependencies and their maintainers whilst reducing the exposure I have to different supply chains generally.

Want more on this topic? [ZDD (Zero Dependency Development)](https://gist.github.com/sleepyfox/8415e64da732c7fea02f21f1c0314f62) is a well argued and more detailed case for minimising and elimiating dependencies.

### Well-Maintained Dependencies

I'm suspicious of packages that:

- have only one maintainer - bus factor, anyone?
- have more than five maintainers - (who are all these people? how do they decide what to approve or not?)
- don't have a history of being updated regularly
- don't have any obvious source of funding and don't ask for any
- don't have a security policy

I have more Opinions on this one, but they're less related directly to malicious software. I'll pop that on my backlog for a future post.

## Updating Dependencies Automatically

I think it's fair to say that keeping your dependencies up to date is not an industry standard practice [^1]. Tools like Pipenv, Poetry and the like default you to locking the exact version of every dependency, and their dependencies, and so on. They instruct you to commit these lockfiles to source control. Unless you go run special commands to update them and then commit those changes, all your app will be frozen in time, accumulating vulnerabilities that you won't even know about unless you're [scanning them for vulnerabilities](#scanning-for-vulnerabilities).

Another checkmark for `pip` which does not lock by default. If you look at any of my more recent Python repositories, you'll find minimum-bound version constraints, along with builds and IDE support for automatically updating versions.

### Example: dbt_bigquery_template

I have exactly one dependency in [dbt_bigquery_template](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/requirements.txt#L1), which is currently this:

`dbt-bigquery>=1.7.0`

This translates as "get me the latest **release** of `dbt-bigquery`". Unlike some other ecosystems I've had the misfortune of needing to work with, `pip` has a wonderful feature in [requiring an explicit flag `--pre` to include pre-release versions](https://pip.pypa.io/en/stable/cli/pip_install/#pre-release-versions), so you won't get the technically-latest-but-unstable `1.8.0b2` beta. The latest release is currently [dbt-bigquery 1.7.7](https://libraries.io/pypi/dbt-bigquery/1.7.7).

When I open `dbt_bigquery_template` in VSCode, [the init-and-update task](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.vscode/tasks.json#L7) automatically kicks off and runs a series of commands updating different kinds of dependencies including [pip install -U -r ${PROJECT_DIR}/requirements.txt](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.dev_scripts/init_and_update.sh#L23). [`-U` means `--upgrade`](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-U) and updates all dependencies to their latest versions.

The build for `dbt_bigquery_template` does the same thing. [This line in the workflow is basically the same as the line in the VSCode task script](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.github/actions/setup_dbt/action.yml#L18). Assuming you close and re-open VSCode at least once each day, that means your development environment and your build or workflow management system are both within a few hours of latest and one another at any given point in time. You don't need to freeze everything to 

There's a lot more to day about automatically updating dependencies, but I'll keep things minimal for this post. First - in my opinion, this is the least bad approach, not a perfect solution. The big risk - if something you're depending on **becomes** bad, you'll pick it up automatically. I think vulnerabilities that we do and do not know about in old software is a much bigger risk. Updating automatically you get all the security fixes straightaway, at no time cost to your team, before the manual-updaters have had chance to realise there's a problem, prioritise the work to update, decide whether it needs fixing, and get round to dealing with it.

I've used this approach for several months or so with multiple teams collaborating over multiple repositories and I can't recall any significant problems. The main inconvience that occurs are those rare occasions when a dependency lets a breaking change through, which you find out about the next day. I see this as a feature, not a bug. These kinds of breaks aren't subtle. Any sort of automated build process or your orchestration tooling is going to notice when version conflicts can't be resolved, an API change prevents your tests from running or the maintainers change something that your permissions don't let you do. Maybe don't pick the most mission-critical thing you can find to learning how auto-updating works in your context?

It's very useful to know when a breaking change just landed on you. You can deal with it while it's fresh, before the work has had any chance to pile up. You get to understand how reliable your dependencies **really** are - perhaps a dependency that keeps breaking you isn't so trustworthy after all? Most importantly - you don't find out you've got multiple breaking changes in the way when your scans alert you to a critical must-fix vulnerability in the two-year old version of that dependency you haven't updated.

Speaking of which...

## Scanning for Vulnerabilities

Tools like [safetycli](https://safetycli.com/product/safety-cli) and [Snyk](https://snyk.io/) will scan your installed dependencies and tell you whether there's any known vulnerabilities in there. You'll see my use of the safetycli python package to scan dependencies as part of my init-and-update process both [locally](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.dev_scripts/init_and_update.sh#L29) and in [build and workflow infrastructure](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.github/actions/setup_dbt/action.yml#L23).

They both offer free single-developer plans at time of writing for your personal and side-projects, and paid plans for teams and enterprises. There's other options too - [GitLab, for example, provides some vulnerability scanning tooling](https://docs.gitlab.com/ee/user/application_security/dependency_scanning/#python), so check what your organisation might already be using for a potentially easy option.

I wrote a little about how and when to check your dependencies back in [Checking your Depenedencies](../2020-12-03-dependency-checking/index.md).

### Safety Usage Example

```console
$ safety check
...snip...
  Using open-source vulnerability database
  Found and scanned 54 packages
  Timestamp 2024-05-02 21:13:23
  0 vulnerabilities reported
  0 vulnerabilities ignored
+============+

 No known security vulnerabilities reported. 

+============+

  Safety is using PyUp's free open-source vulnerability database. This data is 30 days old and limited. 
  For real-time enhanced vulnerability data, fix recommendations, severity reporting, cybersecurity support, team and project policy management and more sign up at
https://pyup.io or email sales@pyup.io
```

## Using Least-Privilege Credentials

## Cloud Controls

## Developing in the Cloud

## Templating



--8<-- "blog-feedback.md"

[^1]: This is the one that kickstarted my interest in this area 18 months or so ago. I shared my practice of automatically updating dependencies instead of updating only when I became aware of vulnerabilities in the Equal Experts network and I saw quite the spectrum of opinion! Cue me chewing on it, trying to get to the bottom of why I feel so strongly that it's the least-bad approach of the options available and gather my thoughts and evidence together to argue the case properly.

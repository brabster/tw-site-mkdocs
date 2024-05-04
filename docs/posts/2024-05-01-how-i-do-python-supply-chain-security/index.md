---
title: How I Do Python Data Supply Chain Security
date: 2024-05-01
---

![A photo taken whilst SCUBA diving of Thresher shark circling off a seamount in the Phillipines. Credit: me](./assets/hero.webp)

We data practitioners - data scientists, data engineers, analytics engineers, et al. - have a hard time when it comes to security. We're exposed to tools that demand we write code and deal with the messy world of programming languages and packages. We often have little choice but to drag insights out of real and sensitive data, exposing us to risks other developers can avoid, because insights don't hide in test data. Training, career paths and dev-experience efforts typically overlook data folks, depriving them of knowledge about the risks they're exposed to and how to mitigate them. Read on and I'll share what I do (and why) to protect myself, [Equal Experts](https://equalexperts.com) and my clients from the security risks lurking behind every piece of software.

--8<-- "ee.md"

<!-- more -->

When I speak to fellow data practitioners I find there's a common concern about the security risks they're exposed to, but a lack of clear, pragmatic guidance on how to mitigate them. A lot of the guidance out there, like [Snyk's Python security best practices](https://snyk.io/blog/python-security-best-practices-cheat-sheet/), focuses on traditional software engineering. "Data" work can be a little different.

This story covers the things I've learned to do in my day-to-day over the past decade or more, including:

- [Partitioning My Work](#partitioning-my-work)
- [Using pip](#using-pip)
- [Assessing Dependency Risk](#assessing-dependency-risk)
- [Keeping Dependencies Up To Date](#updating-dependencies-automatically)
- [Scanning for Vulnerabilities](#scanning-for-vulnerabilities)
- [Using Least-Privilege Credentials](#using-least-privilege-credentials)
- [Cloud Controls](#cloud-controls)
- [Templating](#templating)

## Partitioning My Work

I have at least three different, isolated working environments that I use locally. One laptop is for my personal stuff. At any given time it may have access to credentials for my AWS accounts, my GCP account, my password manager and GMail. If someone bad got into the first two they could run me up a painful bill, despite having billing alarms set up (I talk about that in [$1,370 Gone in Sixty Seconds](../2024-02-08-pypi-downloads-danger/index.md)). If they got into either of the last two they can steal my identity and do untold harm to me and my family. I really need to minimise the risk on that computer!

Then I have a laptop that Equal Experts gave me. This will have credentials for EE things that I have a responsibility to protect. EE-related work on here.

Finally, I have a laptop that I do client work on. Same deal, with even greater responsibility to protect. This laptop is used for nothing but client work.

I have a separate long, strong password for all three (I can reliably hold about four such passwords in my brain at once, if I'm using them regularly and don't have to change them all at once!), and their disks are all encrypted. That's the basic layer of protection - if any one were ever compromised, it's bad enough. But it's better than all three being compromised. There's more about how I manage multiple laptops and additional security measures I use in my posts on [automating my laptop build](../2024-02-27-automated-laptop-build-intro/index.md) and [living with an automated laptop build](../2024-03-01-automated-laptop-build-conclusion/index.md).

!!! warning
    Like many things I'll talk about in this post, password managers are awesome but ship with unsafe defaults - convenience over security :shrug:. I make an point of setting the delay before my password manager clears the clipboard to 30 seconds (default is never!) and setting the timeout before locking again to five minutes. Reduces the time window things have to steal passwords without significantly impacting my day to day, Don't forget the password manager app on your phone...

I've recently been having a great experience with even more protective partitioning - a dedicated, isolated, customisable development environment per **repository** with GitHub Codespaces. I think it's the future. If coding in the cloud is an option for you, I'd recommend giving it a try with an open mind. I've even got [a Codespaces walkthrough and video to help](../2024-04-23-codespaces/index.md)!

### Using Virtualenvs

It's really easy to install into your system Python by mistake - you forget to activate the venv, or you think it's active when it's not. Ideally, your system permissions are set up so that you can't write to your system Python installation, but I find that's quite rare. It's certainly not the case on the current Ubuntu OS on the laptop I'm sitting in front of right now.

You can change the default behaviour of pip on your computer so that it won't install in the system Python.
I set an environment variable `PIP_REQUIRE_VIRTUALENV` to `true` in scripts where I interact with pip. For example, [the init_and_update.sh script in this repository sets PIP_REQUIRE_VIRTUALENV](https://github.com/brabster/tw-site-mkdocs/blob/27b7a94d7dcaf0fd51c39395a205db1e5de1e9a2/.dev_scripts/init_and_update.sh#L5). I also set it one-off as a system-wide environment variable.

```console
$ export PIP_REQUIRE_VIRTUALENV=true
$ pip install safety
ERROR: Could not find an activated virtualenv (required).
```

There are [several other ways to tell pip not to install in the system Python](https://docs.python-guide.org/dev/pip-virtualenv/#requiring-an-active-virtual-environment-for-pip) if environment variables don't work for you.


## Using pip

For the past 18 months, I've used plain old [pip, the Python Packaging Authority's recommended tooling](https://packaging.python.org/en/latest/guides/tool-recommendations/#installing-packages). I'm very happy with it and would recommend it to other Python data practitioners. My workflow with pip and venv is:

```console
$ python -m venv venv # create a venv for the current project if needed
$ source venv/bin/activate # activate the venv (slightly different command on Windows)
$ which python # check that the venv is active; IDE usually indicates clearly when venv is active
$ pip install -U -r requirements.txt # install and update packages in this venv based on requirements.txt file
```

### Pipenv, Poetry et al.

I've used [pipenv](https://pipenv.pypa.io/en/latest/). I've used [Poetry](https://python-poetry.org/). There are several more. In my experience, they don't deliver significant benefits over pip and are more trouble than they're worth. I have a bunch of stories about this that I'll share another day.

### Conda

I haven't used conda. One of the reasons for that is the complexity around commercial use in the [terms of service](https://conda-forge.org/blog/2020/11/20/anaconda-tos/) to warrant a [clarifying blog post](https://legal.anaconda.com/policies/en/). I think the advice here applies equally to conda users but I can't speak from my own experience.


## Assessing Dependency Risk

Any software you bring onto your computer has the potential to hurt you. In the case of Python, just installing a package can let bad actors loose on your computer. My working assumption is that any software running on the computer I'm using can do anything I can do, including accessing any passwords, access tokens, and session tokens I have. Maybe even my password manager if it's unlocked.

I don't trust what I see on the internet. Anyone can make up an identity, publish anything they want and say anything they want. Identities can and have been stolen and used to inject malware into previously safe software. Maintainers can be bought out or get burnt out. I don't think there's anything I can do here that completely mitigates the risks, but I can reduce it. I'll take this opportunity to plug [a responsible, in-depth treatment of package handling over at python.land](https://python.land/virtual-environments/installing-packages-with-pip).

### Is the package popular?

A heavily-used package is a juicy target for bad actors. On the other hand... heavily-used packages have more eyeballs on them. They're more likely to be looked at by security researchers, and if there is a problem I'm in a larger crowd of potential victims, so a lower chance that I will be exploited before I have a chance to respond or my credentials and so on expire or are changed. On balance, I prefer packages with evidence of large user communities.

- search for articles and blogs mentioning it
- check out GitHub stars, forks

Special mention to [libraries.io](https://libraries.io/search?q=colourama&sort=dependents_count), providing a search interface with metrics about how a package is used by others - `Sort: Dependents`.

!!! warning
    **Copy-paste the package name into requirements.txt from somewhere you trust!** The bad actors love publishing malware-laden packages with similar names to popular legitimate packages. These packages are downloaded thousands of times before they are identified and removed!


### Minimising Dependency Use

There's so much software out there, a solution for every problem or suboptimal thing you could imagine. I save myself the time of more in-depth thinking by just trying to be honest with myself about whether I really need something or not.

> [Python is famous for its "batteries included" philosophy](https://docs.python.org/3/tutorial/stdlib.html#batteries-included), so I find it's worth checking whether you can use something built in for no additional risk rather than a package that does expose you to new risks.

- Do I really need to use `Poetry`? No, I can use boring old `pip`.
- Do I really need to use `murmurhash`? No, I can use Python's boring old built-in `hash`.
- Do I really need to use `colorama`? No, I can live with boring old monochrome terminal text.

Just because I'm making boring choices in the name of safety does not mean the packages I depend on are making similar choices. Every time I avoid a dependency, I'm cutting out that dependency, and its dependencies, and their dependencies and so on! That whole subtree of dependencies, and the choices their maintainers make, and their vulnerabilities? Not my problem.

### Using Common Cross-Project Dependencies

I also try to use the same dependencies everywhere, instead of allowing variation without good reason. That helps me really get to know those dependencies and their maintainers whilst reducing the exposure I have to different supply chains generally. Want more on this topic? [ZDD (Zero Dependency Development)](https://gist.github.com/sleepyfox/8415e64da732c7fea02f21f1c0314f62) is a well-argued and more detailed case for minimising and eliminating dependencies.

### Well-Maintained Dependencies

I'm suspicious of packages that:

- have only one maintainer - bus factor, high risk of burnout, where are checks, measures and accountability?
- have more than five maintainers - (who are all these people? How do they decide what to approve or not?)
- don't have a history of being updated regularly
- don't have any obvious source of funding and don't ask for any
- aren't backed by an organisation I trust
- don't have a security policy (eg. security tab in GitHub)


I have more *Opinions* on this one, but they go broader than the scope of this post. I'll pop that on my backlog for a future post.

## Updating Dependencies Automatically

I think it's fair to say that keeping your dependencies up to date is not an industry standard practice[^1]. Tools like Pipenv, Poetry and the like default you to locking the exact version of every dependency, and their dependencies, and so on. They instruct you to commit these lockfiles to source control without mentioning the drawbacks. Unless you go and run special commands to update them and then commit those changes, your app will be frozen in time, accumulating vulnerabilities that you won't even know about unless you're [scanning them for vulnerabilities](#scanning-for-vulnerabilities).

Another :+1: for `pip` which does not lock by default. If you look at any of my more recent Python repositories, you'll find minimum-bound version constraints, along with builds and IDE support for automatically updating versions.

> If you have to use a tool that creates lockfiles for now, you can [`git rm` them](https://www.git-tower.com/learn/git/commands/git-rm), then add them to your `.gitgnore` file to have Git ignore them going forward. That cuts out the need to commit updates back and so simplifies updating.

### Example: dbt_bigquery_template

I have exactly one dependency in [dbt_bigquery_template](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/requirements.txt#L1), which is currently this:

`dbt-bigquery>=1.7.0`

This translates as "get me the latest **release** of `dbt-bigquery` that's no older than `1.7.0`". The low bound ensures that I know things will blow up if somehow I get an older dependency than the last one I had reason to look at (`1.7.0` in this case). If there's a problem with the latest version, and I can't fix it right now, I can still pin to the previous working version temporarily - but I've found this is a rare exception rather than a fatiguing everyday occurrence.

 Unlike some other ecosystems I've had the misfortune of needing to work with, `pip` has a wonderful feature in [requiring an explicit flag `--pre` to include pre-release versions](https://pip.pypa.io/en/stable/cli/pip_install/#pre-release-versions), so you won't get the technically-latest-but-unstable `1.8.0b2` beta. Yay! The latest release is currently [dbt-bigquery 1.7.7](https://libraries.io/pypi/dbt-bigquery/1.7.7).

#### In the IDE

When I open `dbt_bigquery_template` in VSCode, [the init-and-update task](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.vscode/tasks.json#L7) automatically kicks off and runs a series of commands updating different kinds of dependencies including [`pip install -U -r ${PROJECT_DIR}/requirements.txt`](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.dev_scripts/init_and_update.sh#L23). [`-U` means `--upgrade`](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-U) and updates any dependencies you've already got to their latest versions if newer versions are available.

#### In the Build

The build for `dbt_bigquery_template` does the same thing. [This line in the workflow is basically the same as the line in the VSCode task script](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.github/actions/setup_dbt/action.yml#L18). Assuming you close and re-open VSCode at least once each day, that means your development environment and your build or workflow management system are both within a few hours of latest and one another at any given point in time. You don't need to freeze the world forever to avoid "works-on-my-machine" problems.

There's a lot more to say about automatically updating dependencies, but I'll keep things minimal for this post.

### The Least-Bad Solution

First - in my opinion, this is the least bad approach, not a perfect solution. The big risk - if something you're depending on **becomes** bad, you'll pick it up automatically. I think vulnerabilities that we do and do not know about in old software are a much bigger risk. Updating automatically you get all the security fixes straight away, at no time cost to your team, before the manual updaters have had a chance to realise there's a problem, prioritise the work to update, decide whether it needs fixing, and get around to dealing with it.

I take it as validating that regulators are increasingly calling for timely and automatic updates everywhere from IoT devices to phones, servers and so on - so staying up to date seems to be generally accepted as the better position to be in.

### Works In Practice

I've used this approach for several months or so with multiple teams collaborating over multiple repositories and I can't recall any significant problems. The main inconvenience that occurs is those rare occasions when a dependency lets a breaking change through, which you find out about the next day.

I see this as a feature, not a bug. These kinds of breaks aren't subtle. Any sort of automated build process or your orchestration tooling is going to notice when version conflicts can't be resolved, an API change prevents your tests from running or the maintainers change something that your permissions don't let you do. I maybe wouldn't pick the most mission-critical thing I could find to try auto-updating for the first time!

Oh - and yes, setting the constraint to allow semantic-versioning-major "breaking changes" through is by design, not accidental. I'd rather find out about a breaking change that actually affects me when it happens, not months later with a critical vulnerability to fix and no update path except through the breaking version. In my experience the ideals of [semver 2.0.0](https://semver.org/spec/v2.0.0.html) and reality don't really line up all that well - yet another post for another day.

### What about renovate and dependabot?

When I talk with someone about automatically updating, automated PR-raisers often come up. I haven't used either tool myself and I avoid them. If I'm keeping up to date and not committing every update back to source control, I don't need a tool raising PRs to help me manage the relentless torrent of vulnerability notices because I don't have that problem. Plus, [they're not immune from expoitation themselves](https://checkmarx.com/blog/surprise-when-dependabot-contributes-malicious-code/). Another supply chain bites the dust :wave:

### Increased Awareness

It's very useful to know when a breaking change just landed on you. You can deal with it while it's fresh before the work has had any chance to pile up. You get to understand how reliable your dependencies **really** are - perhaps a dependency that keeps breaking you isn't so trustworthy after all? Most importantly - you don't find out you've got multiple breaking changes in the way when your scans alert you to a critical must-fix vulnerability in the two-year-old version of that dependency you haven't updated.

Speaking of which...

## Scanning for Vulnerabilities

Tools like [safetycli](https://safetycli.com/product/safety-cli) and [Snyk](https://snyk.io/) will scan your installed dependencies and tell you whether there are any known vulnerabilities in there. You'll see my use of the safetycli Python package to scan dependencies as part of my init-and-update process both [locally](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.dev_scripts/init_and_update.sh#L29) and in [build and workflow infrastructure](https://github.com/brabster/dbt_bigquery_template/blob/2af5ffd769ec698757847e0366aa00aea984b94e/.github/actions/setup_dbt/action.yml#L23).

They both offer free single-developer plans at the time of writing for your personal and side-projects and paid plans for teams and enterprises. There are other options too - [GitLab, for example, provides some vulnerability scanning tooling](https://docs.gitlab.com/ee/user/application_security/dependency_scanning/#python), so check what your organisation might already be using for a potentially easy option.

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
### Scanning vs. Automatically Updating?

I scan my dependencies after installing the latest versions. As I mentioned before, auto-updating is not a perfect solution, and I could still have a vulnerability even after updating - for example, a known issue with no fix available. We seem to be getting pretty good at responsible disclosure of late. It seems much more rare that I get a vulnerability notice that's not already fixed - auto-updating means I'll already have the fix installed by the time the alert would have landed in my inbox.

If I do end up in that situation, my options are limited. Try to fix it myself? Not very safe nor likely to be feasible. Add an ignore? I haven't had to do this for a while but [safety, for example, looks to have better support now for expiring ignores](https://docs.safetycli.com/safety-docs/administration/safety-policy-files) than last time I had to do it. Lastly - shut the thing down until a fix is available. It's worth considering in a pinch, particularly if the software or pipeline isn't all that time- or mission-critical.

## Using Least-Privilege Credentials

It's been a long read to here, so I'll briefly mention a couple more points and wrap up.

Try to avoid having powerful credentials lying around, or using more powerful credentials than are needed for a job. [Partitioning your development environments](#partitioning-my-work) helps, by letting you reduce the variety of credentials you have in the same place. My experience with Codespaces shines here as I can restrict a repository to exactly the permissions it needs with nothing else lying around.

## Cloud Controls

There are powerful controls in Cloud infrastructures to limit cost exposure and where data can be copied. I've been looking around at Google Cloud and [quotas are cost controls far more proactive and effective than billing alarms](../2024-02-16-bigquery-quotas/index.md). [VPC Service Perimeters](https://cloud.google.com/vpc-service-controls/docs/service-perimeters) can prevent data from being transferred outside your organisation. Both are effectively disabled by default and not straightforward to use, but I'm building my understanding and will share some pragmatic advice when I have some.

## Templating

A lot is going on here, and you'll hit issues as you work with more repositories. I start small and build up. [dbt_bigquery_template](https://github.com/brabster/dbt_bigquery_template) is one way I'm speeding up and improving consistency in my dbt projects (and there's a [short walkthrough video](https://youtu.be/KQg6D0Mkyks?feature=shared) that touches on some of the content here) I've also had some interesting success using [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) to reuse scripts and so on across multiple repositories and teams in a fairly effortless manner, which I'll write about another day.

## Wrap

I'll wrap up by saying that whilst this post focuses on Python packages, the risks and ideas apply to most if not all of the **other** supply chains I'm exposed to. Off the top of my head - Operating system. Firmare. Application software. IDE plugins. Browser plugins. dbt packages. The list goes on and on. Any of these things might be able to get up to the kind of mischief we've been talking about, so stay vigilant and think before installing. I hope the content here helps with the thinking part!

If you got this far - wow, well done, and best of luck. I'd love any feedback - including anything I got wrong or didn't make sense, or I should have covered! There's some information about how to get in touch here.

--8<-- "blog-feedback.md"

[^1]: This is the one that kickstarted my interest in this area 18 months or so ago. I shared my practice of automatically updating dependencies instead of updating only when I became aware of vulnerabilities in the Equal Experts network and I saw quite the spectrum of opinion! Cue me chewing on it, trying to get to the bottom of why I feel so strongly that it's the least-bad approach of the options available and gather my thoughts and evidence together to argue the case properly.

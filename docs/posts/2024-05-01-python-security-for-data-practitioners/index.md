---
title: My Python Data Security Cheat Sheet
date: 2024-05-01
---

![hero image](./assets/hero.webp)

Where I see significant risks in the Python ecosystem for data practititioners and the steps I take to mitigate them across the projects I work on.

--8<-- "ee.md"

<!-- more -->

What I speak to fellow data practitioners like (but not exclusively) data scientists, data engineers and analysts/analytics engineers, I find there's common concern about the security risks they're exposed to, but a lack of clear, pragmatic guidance on how to mitigate them. A lot of the guidance out there, like [Snyk's Python security best practices](https://snyk.io/blog/python-security-best-practices-cheat-sheet/), focuses on traditional software engineering.

This cheat sheet is intended for the diversity of experience I've seen in the data-centric world.

## Using venv (Virtualenv)

### PIP_REQUIRE_VIRTUALENV

It's really easy to install into your system Python by mistake - you forget to activate the venv, or you think it's active when it's not. Ideally, your system permissions are set up so that you can't write to your system Python installation, but I find that's quite rare. It's certainly not the case on the current Ubuntu OS on the laptop I'm sitting in front of right now.

You can change the default behaviour of pip on your computer so that it won't install in the system python.
I set an environment variable `PIP_REQUIRE_VIRTUALENV` to `true` in scripts where I interact with pip. For example, [the init_and_update.sh script in this repository sets PIP_REQUIRE_VIRTUALENV](https://github.com/brabster/tw-site-mkdocs/blob/27b7a94d7dcaf0fd51c39395a205db1e5de1e9a2/.dev_scripts/init_and_update.sh#L5). I also set it one-off as a system-wide environment variable.

```console
paul@laptop:~$ export PIP_REQUIRE_VIRTUALENV=true
paul@laptop:~$ pip install safety
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

I've used [pipenv](https://pipenv.pypa.io/en/latest/). I've used [Poetry](https://python-poetry.org/). There's several more. In my experience, they're far more trouble than they're worth. I have a bunch of anecdotes about this that I'll share another day.


### Conda

I haven't used conda. One of the reasons for that is complexity around commercial use in the [terms of service](https://conda-forge.org/blog/2020/11/20/anaconda-tos/) to warrant a [clarifying blog post](https://legal.anaconda.com/policies/en/). I expect the advice here around managing dependencies applies equally to conda but I can't say for sure.


## Assessing Dependency Risk

Any software you bring onto your computer has the potential to hurt you. In the case of Python, just installing it a package can let bad actors loose on your computer. My working assumption is that any software running on the computer I'm using can do anything I can do.

> How can you tell whether a Python package is trustworthy?

Very good question. I don't think you really can. I'll share the strategies I use for determining whether I'm going to take the risk of using a dependency these days. I use other mitigations like [minimising dependency use](#minimising-dependency-use), [using least-privilege credentials](#using-least-privilege-credentials) and more recently [developing in the cloud](#developing-in-the-cloud) to mitigate the residual risk and give myself more breathing space.

The basic algorithm I think I use is:

### Do I need it, or do I want it?

There's so much software out there, a solution for every problem or suboptimal thing you could imagine. I save myself the time of more in-depth thinking by just trying to be honest with myself about whether I really need something or not.

- Do I need to use Poetry? No, I can use pip, and avoid a dependency.
- Do I really need to use murmurhash? No, I can use Python's built-in `hash`.



## Minimising Dependency Use



## Updating Dependencies Automatically

## Scanning for Vulnerabilities

## Using Least-Privilege Credentials

## Cloud Controls

## Developing in the Cloud

## Templating



--8<-- "blog-feedback.md"
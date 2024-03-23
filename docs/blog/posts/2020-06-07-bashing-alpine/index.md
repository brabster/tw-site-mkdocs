---
title: Bashing Alpine
date: 2020-06-07
category: DevOps
tags:
 - alpine
 - docker
 - scripting
 - bash
 - ash
 - gotcha
description: For those times when a script is both missing and exactly where it should be.
---

So this annoying and trivial little problem catches me out every so often. I am always misled by the error message! You'll see what I mean shortly. For context, it usually happens when I'm working in Docker containers on a build.

<!--more-->

{{< res-figure figcaption="Photo by https://unsplash.com/@bradleyhowington" >}}
  {{< img src="bradley-howington-P6rYiIgGT6k-unsplash.jpg" alt="A bear, lying on its side facepalming" >}}
{{< /res-figure >}}

Let's say we have a script like this, saved as `bash-script.sh`:

```sh
#!/bin/bash

echo "Hello, Bash"
```

Nice and simple. Let's build a Docker image with it that runs it. Here's the Dockerfile.


```dockerfile
FROM alpine

COPY bash-script.sh .

RUN ./bash-script.sh
```

Let's build and see what happens:

```bashsession
$ podman build -f bash.Dockerfile .
STEP 1: FROM alpine
STEP 2: COPY bash-script.sh .
--> 01a74a697df
STEP 3: RUN ./bash-script.sh
/bin/sh: ./bash-script.sh: not found
Error: error building at STEP "RUN ./bash-script.sh": error while running runtime: exit status 127
```

Aww, snap! The script has to be there, we *just* copied it into place. So why do we get an error saying that `./bash-script.sh` is not found?

The answer is... because we're trying to run a Bash script on an Alpine image. Alpine doesn't ship with a Bash shell, so the error is really saying that the interpreter `/bin/bash` isn't found, not that the script itself isn't found. Catches me out every time!

The fix? `#!/bin/sh` instead. Might need to avoid any Bash-specific syntax. Given this script saved as `sh-script.sh`:

```sh
#!/bin/sh

echo "Hello, Shell"
```
Add in an adjusted Dockerfile to pick up the new script instead:
```Dockerfile
FROM alpine

COPY sh-script.sh .

RUN ./sh-script.sh
```
Building, we get:
```bashsession
$ podman build -f sh.Dockerfile .
STEP 1: FROM alpine
STEP 2: COPY sh-script.sh .
--> d82ae1d0b10
STEP 3: RUN ./sh-script.sh
Hello, Shell
STEP 4: COMMIT
--> 8fa27f213ed
```
We're all good. The `#!/bin/sh` directive [should attempt to use a compatible shell](https://en.wikipedia.org/wiki/Shebang_(Unix)) rather than requiring Bash specifically.
---
title: Checking your Dependencies
date: 2020-12-03
category: DevOps
tags:
 - gotcha
 - dependency-check
 - security
description: Should you check dependencies on every push?
---

Following high-profile incidents like the [2017 Equifax Breach](https://www.wired.com/story/equifax-breach-no-excuse/), checking your dependencies for vulnerabilities is a common practice today.
We can use great tools like [OWASP Dependency Check](https://jeremylong.github.io/DependencyCheck/), [Trivy](https://github.com/aquasecurity/trivy) and [Snyk](https://snyk.io) in our builds to raise the alarm when vulnerabilities are found.

The question that I find comes up isn't **whether** we should check dependencies - but **when**?

<!--more-->

My thinking, argued in the rest of the post, is that:

- **check on push** alone is inadequate
- **scheduling** your dependency check is probably the best solution
- check on every push **in addition** to checking on a schedule adds little to no real value
- check on push **when changing dependencies** is a valuable addition to check on schedule
- services with a publish-subscribe model for dependency checking are an alternative worth consideration

## 💩 Check on Push
    

I'd bet the first time you put a dependency check into your build, you did what I did. You run the check when you push. When the check fails, you break the build.

<!-- {{< img src="push.jpg"
    alt="A push sign on a door"
    >}} -->

On its own, it's a terrible solution. A vulnerability can be released at any time, regardless of when you happen to push changes. How will you find out that a service you're not actively working on has a known and fixable vulnerability? One that might end up being how the criminals who stole your customer data got in. Ouch.

There's a nasty tradeoff with this approach, too. I've pushed a change to a repository in a capable, fast-moving, remote-first team and had the build fail because a vulnerability happened to just have been released. I stop, scrambling to see why my build failed. People around me are pushing and having their builds fail too. Half the team screeches to a halt and has to co-ordinate looking at the vulnerability, deciding what to do and getting that change made, pushed and the build made green again. In a less well co-ordinated team (or the same team on a bad day) he whole thing can quickly resemble a motorway pile-up.

Is it a worthwhile tradeoff to jump on that vulnerability as quickly as possible? The safe answer is "yes, of course, because security"  - but I'm going with no - it's not a robust solution.

What if the same vulnerability had been announced a few hours later, after the last push of the day? Would anyone have looked at it before the following morning, twelve-or-more hours later? If it was the Thursday before the UK's Easter four-day holiday, we're talking around 100 hours before anyone's due to push again!

The time between a vulnerability that affects you becoming public knowledge and you becoming aware of it varies unpredictably between seconds and never, in the case of the project no one is working on anymore. That's not good.

## ⏰ Check on Schedule

To address those issues you'll set up a scheduled build. It runs the dependency check and alerts the team to issues rather than breaking the build. Now you've got a specific worst-case time to discovery. A nightly build sets that time to 24 hours, but you could schedule more frequently - an hourly build means you'll know within the hour.

Scheduling your dependency check works regardless of how frequently you push. You don't get the broken build knocking unrelated work off track and you can plan your vulnerability management activities into your team's roles and other activities.

Now that you know, worst case, how long it will take you to discover a vulnerability, you can start thinking about your vulnerability management as part of how you run your service. It forces you to accept the inescapable, nauseating reality that there's a delay between a vulnerability being made public knowledge and you becoming aware that you're affected. A window of opportunity has been open in your service for criminals for some period of time and you just found out about it. If you're anything like me, you'll start worrying more about how to respond effectively. You'll start asking questions like:

- How do I know that I wasn't already compromised?
- How do I respond efficiently when multiple repositories are affected by a vulnerability in a common library?
- How can I be sure I'm actually running scheduled checks across multiple repositories?

Should you check on every push as well? I'd argue there's no real value and some cost of unplanned disruption in doing so, once you have your scheduled builds and response times. If you need to know faster, schedule more frequently. I'd advocate for focusing more on an effective response to the vulnerability alerts you get from your scheduled checks.

## 🛑 Breaking Check on Dependency Change 

Everything we've talked about so far is about finding out you have a vulnerability in production. A build-breaking check **when you push a change to your dependencies** will stop you introducing a dependency with a known vulnerability. Your scheduled check would catch the problem later, but never introducing an avoidable window of opportunity for criminals is worth breaking the build. It's also likely to rarely break compared to the other cases we've talked about.

## ✉️ Register and Notify

I've had a little informal experience with Snyk lately, and it seems to offer a third option which might point us toward a brighter future. Instead of constantly checking your dependencies in each build, you push your dependency lists to them, and they notify you when a vulnerability is announced that affects you.

In my opinion, that's a really appealing model. It's really neat to get the emails saying that a new vulnerability is out there that affects my projects. Not only does it seem to minimise the time to find out about a vulnerability that affects you, but it cuts out the complexity of per-build scheduling. It's free for open source projects (yay) but you'll pay for commercial use.

## 🔬 Details, Details

Dependency checking is a great technique for managing your security risks. **In theory**. In reality, regardless of when you do your checks, there are some real challenges in ensuring that checks are being done where they should be, when they should be. The most diligent teams will struggle with the alert fatigue that comes from lots of repositories and lots of checks. That's a topic for another day...

---
title: Why Try Codespaces?
date: 2024-04-23
---

![A toddler running into an open field under a blue sky with goalposts in the distance. Credit: me](./assets/child_running.webp)



<!-- more -->

## The Problem

To date, I've worked with software projects by cloning a repository onto my local machine to work with it. I've felt increasingly uncomfortable over the past few years with what this implies - running other people's software on my computer. My recent posts on [irresponsible expertise](../2024-03-23-irresponsible-expertise-install-python-package/index.md) and [Python's setup.py problem](../2024-03-31-exploring-setup-py/index.md) have really made me think hard about how to mitigate those risks.

## Just Enough and No More

Let's say want to do some work on a repository. I want the software and all its dependencies, plugins, IDE extensions and whatever other weird and wonderful gubbins is needed to have access to just what's needed to develop that specific piece of software and no more. Running locally as I have been, this is certainly not the case. Any one of those things being compromised could get access to any and all credentials laying around on my disk, my browser's stored passwords, credentials for any sites I'm currently logged into, probably even my password manager if it's unlocked.

## Examples

A couple of weeks ago, I wanted to fix my website's RSS plugin. It was incorrectly rendering images, and that was messing up my content on [Equal Experts' Network Blogs page](https://www.equalexperts.com/network-blogs/). The plugin is [mkdocs-rss-plugin](https://github.com/Guts/mkdocs-rss-plugin), so I cloned the repo, and followed the instructions to get set to write code and run tests.

Immediately after running `python -m pip install -U -r requirements/development.txt`, I realised that anything nasty in that code, or its sprawling network dependencies could have compromised me. By the time I'd thought about it, it would have been too late. (To be clear - I was working on my own laptop rather than the one my employer or my client gave me, so the blast radius was relatively restricted)

Another one - after reading [this LinkedIn post on how the recruitment "tech test" process can be an attack vector](https://www.linkedin.com/feed/update/urn:li:activity:7178644736809836544/), it occurred to me that a "candidate" could pull the same trick **returning** a tech test for review. I've reviewed tech tests in the past and it got me thinking. Even with some defenses, like running stuff in containers, I still felt pretty uneasy about the risk.

## Local Defenses?

After spending far too many hours over the years listening to [Steve Gibson's awesome Security Now podcast](https://twit.tv/shows/security-now) (five stars, would recommend), I think my level of paranoia has increased to where it probably should have been all along. There's been some astonishingly inventive and dangerous attacks, often subsequently commoditized and delivered "as-a-service" covered there.

How to stay secure? It's a laughably unfair fight. I have to defend against every possible attack, whereas the attacker only needs to find one chink in the armour. [Qubes](https://www.qubes-os.org/)? Containers? [devcontainers](https://code.visualstudio.com/docs/devcontainers/containers)? VMs? [AppArmor](https://apparmor.net/)? None of these options are straightforward, and we all know that [complexity is the enemy of security](https://www.goodreads.com/quotes/7441842-complexity-is-the-worst-enemy-of-security-and-our-systems).

For example, my first attempts a couple of weeks ago to use devcontainers to keep projects away from my local filesystem and services in VSCode met with failure because the extension seems [incompatible with a rootless docker (or rootless anything) install](https://github.com/microsoft/vscode-remote-release/issues/7354).

My day job isn't defending - it's to solve business problems and deliver value. I've come to the conclusion that attackers, who have spent their professional lives attacking computer systems, are going to be way better at attacking than I could possibly be at defending. Any of these things I could try, making my own life more difficult, and still miss something that leaves me exposed.

## Operating System Architecture at Fault?

Consider my up-to-date Android phone. It has a fairly fine-grained permission system. Some app you install wants to read files? Use the camera? Get your location information? It has to ask, and I have consistent options beyond "yes" and "no" like "ask me each time". Even with this, I'm limited to what the permissions system supports - for example, I've not seen any evidence that I can grant an app access to only one file - or make it ask me every time it wants to talk over the network. So I'm still running with more risk than I would like.

Why is it so hard to partition up a single-user machine like my personal laptop? I think the problem lies with the roots and architecture of operating systems. My Linux OS is essentially a multi-user server operating system thats been tweaked to make it more usable as an end user device. The basic security model is about separating admins from users, and users from one another. Partitioning one application from another and from the surrounding user environment isn't something it was designed to do.

## Admin Rights to the Rescue?

I've certainly come across folks who seem to be of the opinion that the risk with software comes from "admin rights". If you don't install it with admin rights it's fine, right? I work from the assumption that **any software that's on my laptop can do anything I can do** on that laptop. Again - certainly would be true in a multi-user environment, but on this laptop in front of me? I don't think there's much more harm you can do with admin rights than you can do as me.

Oh, and no I don't run as admin, and I have neutered sudo to be in compliance with Cyber Essentials. I talked about the hows and whys in my post about [automating my laptop build](https://tempered.works/posts/2024/03/02/living-with-an-automated-laptop-build/#cyber-essentials).

## Virtual Machines

With that in mind, the most robust local partitioning strategy I can think of locally is Virtual Machines. Ignoring [VM escapes](https://en.wikipedia.org/wiki/Virtual_machine_escape) that seems to completely partition off the VM from my user-level resources. I've used VMs before and they are not very convenient to work with. There's some UX challenges and they're pretty resource-heavy.

I can solve the resource heaviness by putting the VM in the cloud. I spent a fair bit of time setting up AWS Workspaces - commoditised virtual desktops in the AWS cloud a couple of years ago - here's a [video series on the workspaces setup](https://youtu.be/rf8moSkS0U4?feature=shared). There was a lot of work to do to get set up and the end resolve was deeply underwhelming.

So...

## GitHub Codespaces

My experience over the past couple of weeks with [GitHub Codespaces](https://docs.github.com/en/codespaces/overview) suggests they pretty much solve all these problems.

<figure markdown="span">
  ![Screenshot of this blog post being written in a Codespaces browser window](./assets/codespace_example.webp)
  <figcaption>Screenshot of this blog post being written in a Codespaces browser window</figcaption>
</figure>

They are VMs in the cloud, but they're purpose-built to work from a repository and run an IDE. They use the devcontainers spec with extensions to reproducibly provision an appropriately setup environment for the particular project I'm working on. They have access to nothing on my local machine. I have to rely on browser security to interact with pretty much anything anyway. Watch out for the clipboard though, especially if you use a password manager. They have documented facilities for managing permissions and secrets. Running in the cloud, they put no load on my machine. The day-to-day of working with software is all well-catered for - for example, port-forwarding is seamless, as is uploading a specific file from my local machine. Everything just worked, unlike pretty much everything else I've tried.S

Best of all - security folks at GitHub who **do** spend a good chunk-to-all their professional time defending computer systems have been involved with designing this capability, and here's some documentation explaining how the [security stuff works](https://docs.github.com/en/codespaces/reference/security-in-github-codespaces). There's a [generous free tier](https://docs.github.com/en/codespaces/overview#billing-for-codespaces), but I've signed up for the first paid tier at $4/month (!) because I **want** to pay for this. I want it to exist, I want it to be secure and I want it to be pleasant to use!

I've used codespaces with a couple of projects now, including writing this post, and had no problems that weren't covered by documentation. I'll be putting out a bit of how-to content, but for now I've recorded a [5-minute video to give you a taste of the real-world Codespaces experience](https://youtu.be/88sPBtJp6gA?feature=shared).
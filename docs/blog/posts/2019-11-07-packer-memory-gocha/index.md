---
title: Packer & Fedora Gotchas
date: 2019-11-07
category: Development
tags:
 - packer
 - fedora
 - dracut
summary: |
    Lately, I've been working in virtual machines to strengthen my security posture for clients.
    There's more to come on that, but for now I wanted to share a fix for a confusing problem I had.
    I was trying to install Fedora 31 as a [Packer](https://www.packer.io/) build.
---

It's been a while!
I've got lots on my blog-backlog but here's a tidbit in case it helps anyone else out there.

Lately, I've been working in virtual machines to strengthen my security posture for clients.
There's more to come on that, but for now I wanted to share a fix for a confusing problem I had.
I was trying to install Fedora 31 as a [Packer](https://www.packer.io/) build.

`packr build fedora.json` boots the VM just fine. The automated installer then fails to start, with:

```
[timestamp] initramfs upacking failed: write error
[timestamp] dracut: FATAL: iscsiroot requested but kernel/initrd does not support iscsi
```

After a bit of judicious Googling and poking, I found the problem.
I'd not specified a memory allocation for the embryonic VM and the default appears to be too low.

Adding `"memory": "4096"` to my `fedora.json` spec fixed the problem.

Now my Packer VM is booting and mostly running my kickstart install.
When it's fully working and my [Ansible](https://www.ansible.com/) post install tasks are running,
I should be able to build my perfect, minimal, hardened developer workstation with no clicking or typing in minutes.
I'll look forward to telling you about it!

Note: No, `packr` is not a typo! I've renamed my Packer binary to [because `packer` collides with a package `sudo` uses on Fedora.](https://github.com/cracklib/cracklib/issues/7)

---
title: Rebuild with mkdocs-material
date: 2024-03-29
---

![A photo from a hotel in Manchester, of a new tower construction nearby in the foreground with skyline in the background](./assets/hero.jpg)

I started with a [custom Gatsby site](../2018-08-19-setting-up-a-gatsby-site/index.md), then switched to Hugo (which I didn't write about). Last weekend, I switched again to mkdocs. Am I addicted to fiddling and changing stuff? Well, maybe... but each of those changes happened because of problems or concerns I was had. I hope that mkdocs and mkdocs-material will be my home for while. Pull up a seat and let's take a look at how and why I ended up here.

<!-- more -->

# Starting with Gatsby

<figure markdown="span">
  ![](./assets/gatsby-wayback.png)
  <figcaption>tempered.works in 2020, thanks to the Internet Archive Wayback machine</figcaption>
</figure>

The first original post on this blog covered my original [Gatsby site](../2018-08-19-setting-up-a-gatsby-site/index.md).
The repo for that site is [here](https://github.com/brabster/tw-site).
It was an interesting place to start but was quite complex and needed up-to-date front end skills to set up.
It also gave me the flexibility to do whatever I wanted.
That might sound like a good thing, but after a while I realised I was spending more time fiddling with the technology than writing content.

I'm not a professional frontend person - my skills are weak at best, good enough to put together basic internal web-based user interfaces at a push.
I decided that it wasn't a good use of my time to fiddle with front-end tech, and wanted to use something more purpose-built for what I wanted.

What did I want? The Gatsby exercise helped me figure that out.

- somewhere to put my portfolio and company details
- somewhere to host my LaTeX-based CV as PDF
- a blog, supporting things like syntax highlighting
- a markdown and git-based workflow
- a clean and accessible look and feel, that provided a good experience to a visitor
- no tracking, just server-side traffic metrics to see what was being used and any problems related to URLs

I'd been using Hugo-based static sites with clients for documentation sites supporting automatic docs generation and publishing workflows.
The experience looked like it'd tick more of the things I wanted than my Gatsby experience so I thought I'd give it a go.

## Sorting the CV

It became clear that my CV didn't work as part of the site build process.
I've had the same basic setup for a long time now - it's a LaTeX document that uses a `moderncv` template.
There's a bunch of dependencies needed to build it and they're nothing to do with my site tech.

<figure markdown="span">
  ![](./assets/cv.png)
  <figcaption>My out-of-date CV, built from its own repo and a Travis CI pipeline to handle the weird and wonderful LaTeX dependencies</figcaption>
</figure>

Eventually, I realised that the obvious thing to do was to put my CV in [its own repository](brabster/tw-site-md).
A side-effect of this approach that I appreciate more these days is that I don't have to install the weird and wonderful dependcies on this laptop
to build it. I'll work in an PR and let the hardened environment on the build running handle my trust issues, thank you.

The update/build process for my CV is independent of my website but that's not turned out to be an issue so far.
It's a bit out of date but easy enough to update as the need arises. As I'm a permie for [Equal Experts](https://equalexperts.com) these days it's not a priority right now!

## Next Stop - Hugo and beautifulhugo

...








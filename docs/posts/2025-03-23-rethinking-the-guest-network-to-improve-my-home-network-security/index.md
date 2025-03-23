---
title: Rethinking the guest network to improve my home network security
date: 2025-03-23
---

![Network diagram showing the internet connected to a router, linked to four devices: tablet, mobile phone, laptop, and IoT device.](./assets/schematic_guest_network.webp)

I believe that making my guest network my default network reduces the potential harm a compromised app or device can cause. What was my "trusted" network is now my "untrusted" network, with only a few low-risk devices that **really** need local network connectivity connected to it, isolated from other devices that matter.

It's a simple change in how you use your home network, rather than requiring in-depth knowledge and experience. Having operated this way at home for a few months now, I've found little impact on day-to-day usability, but it's really helped me sleep better at night. I'll explain what I changed, why, and how I've adjusted my wider thinking on my home network security to take better advantage of this approach.

--8<-- "ee.md"

<!-- more -->

## What's a "guest" network?

Modern routers generally support a "guest" network, alongside the "trusted" network. The purpose of this guest network is to allow untrusted devices to use your fast and cheap internet connectivity without giving them any access to devices on your home network. ["What’s a guest Wi-Fi network, and why do you need one?"](https://www.kaspersky.co.uk/blog/guest-wifi/14446/) via Kaspersky describes the risk that this setup mitigates.

> Many pieces of malware are able to spread themselves over a local network, and if an infected device is connected to your Wi-Fi, it will try to contaminate everything in its range.

I visualise the guest network as devices that are connected to the internet via my router but are not aware of one another. They can call out to the internet but can't see one another.

<figure markdown="span">
 ![Network diagram showing the internet connected to a router, linked to four devices: tablet, mobile phone, laptop, and IoT device.](./assets/schematic_guest_network.webp)
 <figcaption>The devices on the guest network can call out to the internet, but cannot see one another.</figcaption>
</figure>

The trusted network looks quite different. These devices can also call out to the internet, but can also see and try to interact with other devices that are on the same network.

<figure markdown="span">
 ![Network diagram showing the internet connected to a router, linked to a network that contains four devices.](./assets/schematic_trusted_network.webp)
 <figcaption>The devices on the trusted network can call out to the internet, but can also see one another.</figcaption>
</figure>

Every description of a guest network, including [the guest network description provided by the Eero devices I use](https://support.eero.com/hc/en-us/articles/207895123-How-do-I-share-my-eero-network-with-guests), is very specific about the kinds of devices you should use the guest network for: "sharing your home WiFi with others".

I now believe it makes sense to use the guest network for **everything** that does not need local network connectivity, and that nearly every device I use on this network falls into that category.

## What is zero trust?

The guest network allows "untrusted" devices to use my home internet connectivity - but why trust any device? Are those I own more resilient to attack than those belonging to people who visit my house? What about my partner and child's devices? Modern network security principles advocate for a zero-trust approach, and I'll let [Cloudflare sum up the reasons for zero-trust](https://www.cloudflare.com/learning/security/glossary/what-is-zero-trust/) better than I could.

> everyone inside the network is trusted by default. The problem with this approach is that once an attacker gains access to the network, they have free rein over everything inside.

Good point, right? Particularly if you work from home as I do, where your home network security could provide attackers a way into your employer or client!

So, applying a more zero-trust approach, the meanings of these two networks flip.

- guest network: the **strong security** network, making it harder for an attacker to move between devices and compromise the things that matter
- untrusted network: the **weak security** network where a compromised device can more easily affect all the devices on that network

## Which devices need local network connectivity?

I've found local network connectivity is rarely needed - the only devices I have that I believe need it are:

- Google chromecast
- Sonos soundbar
- IKEA dirigera hub and connected IoT devices

Although I've struggled to find a definitive statement from the vendors, my experience is that these devices need to be on the same WiFi network as the device that is controlling them. The good news is that these devices don't **need** any access to anything that matters. I have these devices connected to my "untrusted" network.

### Adding an isolated home hub

To control them, I registered a new Google account specifically for our home, and bought a tablet to function as a portable hub (I presume the same approach would work with other ecosystems like Apple?). If I'd had an old tablet or phone that was still getting updates, I'd have used that. After installing the relevant apps on this hub, I removed them from my phone.

[Malicious apps with millions of downloads are generating lots of coverage today](https://www.google.com/search?q=android+app+malicious+millions+of+downloads+recent), so that felt pretty good. Not only have I reduced the impact of one of these devices being compromised, but I've also eliminated the risk these apps posed on my phone. 

I felt it important to register a new Google account as part of the process. Had I used my own personal Google account, a compromised device could have given access to my Gmail, which then could have been used to start logging into things and resetting passwords and more broadly compromising things that matter. A separate Google account can be shared with my family, and we can still explicitly share things with that hub account identity - in fact, it's part of [our Google family](https://families.google/families/) so it has access to books, apps and other things that we've bought. Super convenient, but reduced risk!

## What's on my guest network?

So what's on my "guest" network? My phone, tablet, personal laptop, work laptop, my partner's personal and work devices, my child's Yoto player (another app I deleted from my phone, my partner and I use the hub to manage his story player now!), our games console, our smart TV, Switchbot temperature and humidity sensor, Ring doorbell, kindle - and so on. The point is almost all of the devices we have and use don't need local network access. They need to talk to the internet and that's it. My VPN (I use ExpressVPN) also works just fine on my guest network as you'd expect.

I don't do anything cool or impressive on my home network - back in the day I had my WiFi printer, NAS, Raspberry Pi and so on, and those might have made the switch more difficult. I don't have anything like that these days. For me, they represent a lot of risk for minor cool and convenience and I can't justify or afford the time required to apply appropriate levels of security diligence. My advice to anyone who's being forced onto their "untrusted" network by unnecessary technology would be to think carefully about whether you can justify it.

--8<-- "blog-feedback.md"


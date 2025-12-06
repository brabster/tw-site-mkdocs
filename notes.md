## Why CVE-2018-20225 and --extra-index-url is still a real problem

I noticed [CVE-2018-20225](../2024-05-18-handling-cve-2018-20225/index.md) last year, when my vulnerability scanning alerted me to the problem. The maintainers dispute the vulnerability, placing the responsibility on users for using `--extra-index-url` securely.

However.

At time of writing this post, the risks are not called out in the [first mention of `--extra-index-url` in the pip install documentation](https://pip.pypa.io/en/latest/cli/pip_install/#finding-packages), nor [in the installing packages tutorial](https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-from-other-indexes) and safetycli no longer reports it. The internet is littered with examples of this flag being used or advised with no mention of security risks.

## Does AI help?

Given that training data, it's not surprising that ChatGPT behaves irresponsibly by default too. Given a prompt "How can I install a package from a private Python package registry using pip?", I receive the helpful, if dangerous, advice:

<figure markdown="span">
 ![template figure](./assets/chatgpt-extra-index-url.webp)
 <figcaption>template figure</figcaption>
</figure>

Curiously, when asked about security risks associated with the advice it gave me, I got a ten-point list of increasingly obscure risks, without any mention of the blindingly obvious problem we're talking about today.

I use Google's Gemini for my day to day and I've build a set of generic instructions used in all my chats that includes this prompt:

> I am a security champion and I need to know about security risks associated with my questions or your responses. Be sure to advise of any specific known security issues as well as general principles.

<figure markdown="span">
 ![template figure](./assets/gemini-tuned-extra-index-url.webp)
 <figcaption>template figure</figcaption>
</figure>

I get a much better response, but be aware I've tuned Gemini and I was using the default ChatGPT settings. I'd definitely recommend a couple of instructions about security in whatever GenAI system you use in your day to day!


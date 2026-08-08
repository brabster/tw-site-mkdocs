This is a blog and should follow a consistent style over time. Posts are in `docs/posts`. It is an mkdocs site, using the mkdocs-material theme. The configuration is in `mkdocs.yml`.

The goal is to make informative, engaging content, based on real-life experience, accessible and easy to understand for a general audience.

- The blog is written in British English and follows AP style.
- The blog uses sentence case for titles and does not use em-dashes or smart quotes.
- The blog is written in a conversational tone and should maintain that tone throughout.
- The blog should avoid technical jargon or complex language that may confuse the reader where such language is not required for clear communication.
- The blog should be informative and engaging, providing value to the reader without being overly verbose or complicated.
- The blog must be concise and to the point, avoiding unnecessary repetition or filler content.
- The blog should be structured logically, with clear headings and subheadings to guide the reader through the content.
- The blog should include relevant examples and anecdotes to illustrate key points and make the content relatable.
- The blog must be factually accurate and well-researched, providing reliable information to the reader.
- The blog must be free of spelling and grammatical errors, ensuring a polished and professional final product.
- The blog must be formatted correctly, with appropriate use of bullet points, lists, and other formatting elements to enhance readability.
- The blog should be optimised for search engines, using relevant keywords and phrases to improve visibility and reach.
- The blog must include appropriate links to sources and references, providing additional context and information for the reader.
- Images must have useful alt-text for audience with sight challenges including colour blindness. Alt text describes what the picture looks like and is read by screen readers; it is not a caption and must not appear as visible text on the page.
- Captions must also be provided to be useful for the whole audience. Captions explain why the picture matters or what it means in context, and are distinct from alt text in both purpose and wording.
- Any links in the blog must be checked for accuracy and functionality, ensuring they lead to the correct and relevant content.
- The blog should be written in a way that encourages reader engagement and interaction, inviting comments and feedback.

Images in the blog content must be declared in figure and caption markup, like this:

```markdown
<figure markdown="span">
 ![alt-text](./assets/image.webp)
 <figcaption>a caption</figcaption>
</figure>
```

## AI behaviour

AI assumes the role of editor and proofreader.

When asked to proof content, the AI should:

- suggest improvements to achieve the goals outlined above.
- review historical content and suggest cross-references relevant to the current post.
- suggest edits for historical posts indicating where there is newer, relevant content, for example in `docs/posts/2024-02-08-pypi-downloads-danger/index.md`, the following references were added:

```markdown
---

## Update February 2024

There actually **is** a "don't bankrupt me" setting, although it's a pain to find. More importantly, there is a quota system lurking in there you can use for much more observable and effective control on a per-project or per-user over-time basis. Read more in [the next post in the series](../2024-02-16-bigquery-quotas/index.md).

---

## Update July 2025

Google is making BigQuery safer by default from September 2025, introducing daily usage limits for new projects. If you’re concerned about runaway costs, see my latest post: [BigQuery, safer by default from September 2025](../2025-07-17-bigquery-will-be-safer-by-default/index.md) for details on the new quota system.
```

- AI is a native UK English speaker and has expertise in UK English spelling and grammar.
- Do not correct the use of hyphens, single quotes, or double quotes unless explicitly instructed.
- Avoid suggesting changes that contradict my original style preferences.


## Categories

Blog posts should have one or more categories, chosen from the `categories_allowed` list in `mkdocs.yml`.

- Descriptions for each categories can be found under `docs/categories`.
- If no suitable categories are found, a new category should be suggested.

## Build system

The site is built with [Zensical](https://zensical.org), reading `mkdocs.yml` natively. Zensical replaced mkdocs-material in 2026.

The full local build sequence (mirroring Netlify) is:

```
python -m unittest test_generate_blog_meta -v
python generate_blog_meta.py --step pre
zensical build --strict
python generate_blog_meta.py --step post
```

`generate_blog_meta.py` is the build helper script. It has two responsibilities:

- **`--step pre`** — regenerates the "recent posts" section of `docs/index.md` before the build, so the homepage content reaches `site/index.html`.
- **`--step post`** — writes a valid RSS 2.0 feed to `site/feed_rss_created.xml` after the build.

Always run the pre step before `zensical build` and the post step after, or the homepage and RSS feed will be stale.

### docs/index.md

`docs/index.md` is partially generated. The static header (profile card, contact line) sits above the `<!-- GENERATED_CONTENT -->` marker. Only edit content above that marker by hand; everything below it is overwritten by `generate_blog_meta.py --step pre`.

### Post URLs

Post URLs follow the pattern `https://tempered.works/posts/{YYYY}/{MM}/{DD}/{slug}/`. The slug comes from the `slug` front matter field if present, or is derived from the post title by lower-casing, removing non-word characters, and replacing whitespace with hyphens.

### Draft posts

Posts with `draft: true` in their front matter are excluded from the homepage recent-posts list and the RSS feed. Zensical also suppresses their pages from the built site.

### RSS feed

A custom RSS 2.0 feed is generated at `site/feed_rss_created.xml`. Items include title, link, publication date, categories, and excerpt text (up to the `<!-- more -->` marker). Full post content and feed image metadata are not included.

### Generated and ignored files

The following paths are in `.gitignore` and must not be committed:

- `site/` — full build output
- `__pycache__/` — Python bytecode cache
- `.cache/` — Zensical build cache


## Build system

The site is built with [Zensical](https://zensical.org), reading `mkdocs.yml` natively. Zensical replaced mkdocs-material in 2026.

The full local build sequence (mirroring Netlify) is:

```
python -m unittest test_generate_blog_meta -v
python generate_blog_meta.py --step pre
zensical build --strict
python generate_blog_meta.py --step post
```

`generate_blog_meta.py` is the build helper script. It has two responsibilities:

- **`--step pre`** — regenerates the "recent posts" section of `docs/index.md` before the build, so the homepage content reaches `site/index.html`.
- **`--step post`** — writes a valid RSS 2.0 feed to `site/feed_rss_created.xml` after the build.

Always run the pre step before `zensical build` and the post step after, or the homepage and RSS feed will be stale.

### docs/index.md

`docs/index.md` is partially generated. The static header (profile card, contact line) sits above the `<!-- GENERATED_CONTENT -->` marker. Only edit content above that marker by hand; everything below it is overwritten by `generate_blog_meta.py --step pre`.

### Post URLs

Post URLs follow the pattern `https://tempered.works/posts/{YYYY}/{MM}/{DD}/{slug}/`. The slug comes from the `slug` front matter field if present, or is derived from the post title by lower-casing, removing non-word characters, and replacing whitespace with hyphens.

### Draft posts

Posts with `draft: true` in their front matter are excluded from the homepage recent-posts list and the RSS feed. Zensical also suppresses their pages from the built site.

### RSS feed

A custom RSS 2.0 feed is generated at `site/feed_rss_created.xml`. Items include title, link, publication date, categories, and excerpt text (up to the `<!-- more -->` marker). Full post content and feed image metadata are not included.

### Generated and ignored files

The following paths are in `.gitignore` and must not be committed:

- `site/` — full build output
- `__pycache__/` — Python bytecode cache
- `.cache/` — Zensical build cache

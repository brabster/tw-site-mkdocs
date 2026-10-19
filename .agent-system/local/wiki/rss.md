# RSS feeds

Zensical generates the feeds, then `.dev_scripts/postprocess_rss.py` adapts them for this site's content and feed-reader compatibility. Netlify runs the same sequence:

```sh
zensical build --strict
python3 .dev_scripts/postprocess_rss.py
```

Install the build dependency with `python3 -m pip install -r requirements.txt`. Run the focused regression tests with:

```sh
python3 -m unittest discover -s tests -v
```

## Feed requirements

- Keep the feeds at `/feed_rss_created.xml` and `/feed_rss_updated.xml`, with autodiscovery links in the homepage.
- Descriptions use rendered article HTML, not the Markdown in Zensical's feed. The `<!-- more -->` marker ends the excerpt; without a marker, the article content is not truncated. New posts should use the marker after their intended feed introduction.
- Resolve relative `href` and `src` values against the post URL. The post-processor also converts the site's legacy `img` and `figure` shortcodes.
- Omit `data-type` attributes from description HTML.
- Each Atom self link must identify its own feed. Zensical's canonical URL is retained by default; when Netlify sets `DEPLOY_PRIME_URL`, use that deploy URL so preview feeds refer to themselves.
- Use name-only `dc:creator` attribution and omit RSS `author` and channel `managingEditor` fields to avoid exposing email addresses.

The regression tests in `tests/test_postprocess_rss.py` cover these requirements, excerpt handling, idempotence and invalid feed paths. Update them when feed behavior changes.

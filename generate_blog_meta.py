"""Build script for the Tempered Works blog.

Reads all posts in docs/posts/ and:
  - Regenerates the "recent posts" section of docs/index.md
  - Writes site/feed_rss_created.xml (RSS 2.0)

Run in two steps around the site build:

    python generate_blog_meta.py --step pre   # updates docs/index.md before build
    zensical build --strict
    python generate_blog_meta.py --step post  # writes site/feed_rss_created.xml after build

The netlify.toml runs these steps automatically; local builds should follow the same order
so that docs/index.md is up-to-date when the site is built and the RSS feed is generated
from the final site output.
"""

import argparse
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent
DOCS_DIR = REPO_ROOT / "docs"
POSTS_DIR = DOCS_DIR / "posts"
INDEX_MD = DOCS_DIR / "index.md"
SITE_DIR = REPO_ROOT / "site"
FEED_XML = SITE_DIR / "feed_rss_created.xml"

GENERATED_MARKER = "<!-- GENERATED_CONTENT -->"
SITE_URL = os.environ.get("SITE_URL", os.environ.get("DEPLOY_PRIME_URL", "https://tempered.works"))
SITE_NAME = "Tempered Works Ltd."
SITE_DESCRIPTION = "Software and Data Consulting Services"
AUTHOR_NAME = "Paul Brabban"
AUTHOR_EMAIL = "paul@tempered.works"
RECENT_POSTS_COUNT = 10
FEED_POSTS_COUNT = 20

DISALLOWED_INLINE_SCRIPT_MARKERS = [
    (re.compile(r"\bgtag\s*\(", re.IGNORECASE), "Google Analytics gtag"),
    (re.compile(r"\bdataLayer\b", re.IGNORECASE), "Google Tag Manager dataLayer"),
    (re.compile(r"\b(?:window\.)?plausible\s*\(", re.IGNORECASE), "Plausible analytics"),
    (re.compile(r"\bumami\.track\s*\(", re.IGNORECASE), "Umami analytics"),
    (re.compile(r"\bclarity\s*\(", re.IGNORECASE), "Microsoft Clarity"),
    (re.compile(r"\bhj\s*\(", re.IGNORECASE), "Hotjar"),
    (re.compile(r"\bfbq\s*\(", re.IGNORECASE), "Facebook Pixel"),
    (re.compile(r"\bdocument\.cookie\s*=", re.IGNORECASE), "browser cookie writes"),
    (re.compile(r"\bnavigator\.sendBeacon\s*\(", re.IGNORECASE), "beacon-style tracking calls"),
]

RESOURCE_TAG_ATTRIBUTES = {
    "audio": "src",
    "iframe": "src",
    "img": "src",
    "link": "href",
    "script": "src",
    "source": "src",
    "video": "src",
}


class _CookieBannerRiskParser(HTMLParser):
    """Collect browser-loaded resources and inline script bodies from HTML."""

    def __init__(self, allowed_hosts: set[str]):
        super().__init__()
        self.allowed_hosts = allowed_hosts
        self.external_resources: list[tuple[str, str]] = []
        self.inline_scripts: list[str] = []
        self._script_chunks: list[str] | None = None
        self._script_has_src = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {name.lower(): value for name, value in attrs if value is not None}

        resource_attr = RESOURCE_TAG_ATTRIBUTES.get(tag)
        if resource_attr:
            url = attr_map.get(resource_attr)
            if url:
                parsed = urlparse(url)
                if (
                    (parsed.scheme in ("http", "https") or (not parsed.scheme and parsed.netloc))
                    and parsed.hostname
                    and parsed.hostname not in self.allowed_hosts
                ):
                    self.external_resources.append((tag, url))

        if tag == "script":
            self._script_has_src = "src" in attr_map
            self._script_chunks = []

    def handle_data(self, data: str) -> None:
        if self._script_chunks is not None and not self._script_has_src:
            self._script_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._script_chunks is not None:
            if not self._script_has_src:
                self.inline_scripts.append("".join(self._script_chunks))
            self._script_chunks = None
            self._script_has_src = False


# ---------------------------------------------------------------------------
# Post parsing
# ---------------------------------------------------------------------------

def _slugify(title: str) -> str:
    """Convert a post title to a URL slug, matching the mkdocs blog plugin."""
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


def _extract_cover_image(raw: str, slug: str) -> tuple[str, str, str] | None:
    """Return (alt_text, src_relative_to_docs_root, caption) for the first image
    found in raw, or None if no image is present. caption is the figcaption text
    if the image is inside a <figure> block, otherwise an empty string. src paths
    relative to the post directory are rebased so they work when referenced from
    docs/index.md."""
    m = re.search(r'!\[([^\]]*)\]\(([^)\s]+)\)', raw)
    if not m:
        return None
    alt = m.group(1)
    src = m.group(2).strip()
    # Rebase relative paths from post directory to docs root.
    # Use removeprefix to handle only the leading "./" safely.
    if not src.startswith("http") and not src.startswith("/"):
        src = f"posts/{slug}/{src.removeprefix('./')}"

    # Look for a <figcaption> in the same <figure> block that contains the matched image.
    caption = ""
    # Find the figure block that contains the matched image by anchoring on the image position.
    img_pos = m.start()
    fig_m = re.search(r'<figure[^>]*>(.*?)</figure>', raw, re.DOTALL)
    if fig_m and fig_m.start() <= img_pos <= fig_m.end():
        cap_m = re.search(r'<figcaption>(.*?)</figcaption>', fig_m.group(1), re.DOTALL)
        if cap_m:
            caption = cap_m.group(1).strip()

    return (alt, src, caption)


def parse_post(path: Path) -> dict | None:
    """Parse a post's front matter and extract a plain-text excerpt."""
    content = path.read_text(encoding="utf-8")

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not m:
        return None

    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None

    if (
        not isinstance(fm, dict)
        or fm.get("draft", False)
        or not fm.get("title")
        or not fm.get("date")
    ):
        return None

    body = content[m.end():]

    # Text before <!-- more --> is the excerpt; fall back to first 500 chars.
    if "<!-- more -->" in body:
        excerpt_raw = body.split("<!-- more -->")[0]
    else:
        excerpt_raw = body[:500]

    excerpt = _clean_excerpt(excerpt_raw)

    # slug for asset path rebasing uses the directory name
    slug = path.parent.name

    date_val = fm["date"]
    if isinstance(date_val, str):
        post_date = datetime.strptime(date_val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        # yaml may parse it as a date object
        post_date = datetime(date_val.year, date_val.month, date_val.day, tzinfo=timezone.utc)

    # Derive URL using the configured post_url_format: posts/{date}/{slug}
    # {date} is YYYY/MM/DD, {slug} is the explicit slug from front matter or
    # the title slugified to match how the mkdocs blog plugin generates permalinks.
    url_slug = fm.get("slug") or _slugify(fm["title"])
    date_path = post_date.strftime("%Y/%m/%d")
    url = f"{SITE_URL.rstrip('/')}/posts/{date_path}/{url_slug}/"

    return {
        "title": fm["title"],
        "date": post_date,
        "date_str": post_date.strftime("%b %-d, %Y"),
        "categories": fm.get("categories", []) or [],
        "excerpt": excerpt,
        "cover_image": _extract_cover_image(excerpt_raw, slug),
        "url": url,
        "slug": slug,
    }


def _clean_excerpt(raw: str) -> str:
    """Strip Markdown/HTML noise from excerpt text."""
    # Remove pymdownx snippet directives
    text = re.sub(r"--8<--[^\n]*", "", raw)
    # Remove block elements that include text we don't want in excerpts (e.g. figcaption)
    text = re.sub(r"<figcaption>.*?</figcaption>", "", text, flags=re.DOTALL)
    # Remove remaining HTML tags (keeping their inner text where appropriate)
    text = re.sub(r"<[^>]+>", "", text, flags=re.DOTALL)
    # Remove Markdown images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Convert Markdown links to plain text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove Markdown headings
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_posts() -> list[dict]:
    """Load all posts sorted newest first."""
    posts = []
    for path in POSTS_DIR.glob("*/index.md"):
        post = parse_post(path)
        if post:
            posts.append(post)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def _allowed_resource_hosts(site_url: str = SITE_URL) -> set[str]:
    """Return hosts that are allowed in browser-loaded resource URLs."""
    parsed = urlparse(site_url)
    hosts: set[str] = set()
    if parsed.hostname:
        hosts.add(parsed.hostname)
    return hosts


def validate_no_cookie_banner_risks(
    site_dir: Path | None = None,
    site_url: str = SITE_URL,
) -> None:
    """Fail if built pages include likely cookie-banner-triggering features.

    Assumes site_dir contains the current HTML output from the build that just ran.
    """
    built_site = site_dir or SITE_DIR
    allowed_hosts = _allowed_resource_hosts(site_url)
    html_files = list(built_site.rglob("*.html"))

    if not html_files:
        raise ValueError(f"{built_site} does not contain any built HTML files to validate.")

    for path in html_files:
        raw = path.read_text(encoding="utf-8")
        parser = _CookieBannerRiskParser(allowed_hosts)
        parser.feed(raw)
        inline_script_text = "\n".join(parser.inline_scripts)
        for pattern, description in DISALLOWED_INLINE_SCRIPT_MARKERS:
            if pattern.search(inline_script_text):
                raise ValueError(f"{path} includes {description}, which is not allowed.")

        if parser.external_resources:
            tag, url = parser.external_resources[0]
            raise ValueError(
                f"{path} loads an off-site <{tag}> resource ({url}), which is not allowed."
            )


# ---------------------------------------------------------------------------
# Homepage generation
# ---------------------------------------------------------------------------

def generate_homepage(posts: list[dict], index_path: Path | None = None) -> None:
    """Rewrite docs/index.md: keep everything up to GENERATED_MARKER, append
    a 'Recent posts' section for the N most recent posts."""

    idx = index_path or INDEX_MD
    base_content = idx.read_text(encoding="utf-8")

    if GENERATED_MARKER in base_content:
        base_content = base_content[: base_content.index(GENERATED_MARKER) + len(GENERATED_MARKER)]
    else:
        base_content = base_content.rstrip() + "\n\n" + GENERATED_MARKER

    lines = [base_content, "\n\n## Recent posts\n"]

    for post in posts[:RECENT_POSTS_COUNT]:
        category_badges = " ".join(
            f"`{cat}`" for cat in sorted(post["categories"])
        )
        badge_line = f"  *{post['date_str']}*" + (f" &nbsp; {category_badges}" if category_badges else "")

        cover = post.get("cover_image")
        if cover and cover[2]:
            cover_md = (
                f'\n<figure markdown="span">\n'
                f' ![{cover[0]}]({cover[1]})\n'
                f' <figcaption>{cover[2]}</figcaption>\n'
                f'</figure>\n\n'
            )
        elif cover:
            cover_md = (
                f'\n<figure markdown="span">\n'
                f' ![{cover[0]}]({cover[1]})\n'
                f'</figure>\n\n'
            )
        else:
            cover_md = ""

        lines.append(
            f"\n### [{post['title']}]({post['url']})\n\n"
            f"{badge_line}\n\n"
            f"{cover_md}"
            f"{post['excerpt'][:200]}{'...' if len(post['excerpt']) > 200 else ''}\n"
        )

    idx.write_text("".join(lines), encoding="utf-8")
    print(f"Updated {idx} with {min(len(posts), RECENT_POSTS_COUNT)} recent posts.")


# ---------------------------------------------------------------------------
# RSS feed generation
# ---------------------------------------------------------------------------

def generate_rss(posts: list[dict], output: Path | None = None) -> None:
    """Write a valid RSS 2.0 feed to site/feed_rss_created.xml."""

    out = output or FEED_XML

    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = SITE_NAME
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = SITE_DESCRIPTION
    ET.SubElement(channel, "language").text = "en-gb"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now(tz=timezone.utc)
    )
    ET.SubElement(channel, "generator").text = "generate_blog_meta.py"

    # Atom self-link (good practice)
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", f"{SITE_URL.rstrip('/')}/feed_rss_created.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for post in posts[:FEED_POSTS_COUNT]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post["title"]
        ET.SubElement(item, "link").text = post["url"]
        ET.SubElement(item, "guid", isPermaLink="true").text = post["url"]
        ET.SubElement(item, "pubDate").text = format_datetime(post["date"])
        if post["excerpt"]:
            ET.SubElement(item, "description").text = post["excerpt"]
        for cat in post["categories"]:
            ET.SubElement(item, "category").text = cat

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")

    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(fh, encoding="unicode", xml_declaration=False)

    print(f"Written {out} with {min(len(posts), FEED_POSTS_COUNT)} items.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        choices=["pre", "post", "all"],
        default="all",
        help="pre: homepage only; post: RSS + built-site validation; all: both (use only when site/ is already built)",
    )
    args = parser.parse_args()

    posts = load_posts()
    print(f"Found {len(posts)} posts.")
    if args.step in ("pre", "all"):
        generate_homepage(posts)
    if args.step in ("post", "all"):
        generate_rss(posts)
        validate_no_cookie_banner_risks()

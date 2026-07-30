"""Build script for the Tempered Works blog.

Reads all posts in docs/posts/ and:
  - Regenerates the "recent posts" section of docs/index.md
  - Writes site/feed_rss_created.xml (RSS 2.0)

Run this after `zensical build`. The netlify.toml does this automatically.
"""

import argparse
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Post parsing
# ---------------------------------------------------------------------------

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

    if not fm or not fm.get("title") or not fm.get("date"):
        return None

    body = content[m.end():]

    # Text before <!-- more --> is the excerpt; fall back to first 500 chars.
    if "<!-- more -->" in body:
        excerpt_raw = body.split("<!-- more -->")[0]
    else:
        excerpt_raw = body[:500]

    excerpt = _clean_excerpt(excerpt_raw)

    # Derive post URL from directory name: posts/<dir-name>/
    slug = path.parent.name
    url = f"{SITE_URL.rstrip('/')}/posts/{slug}/"

    date_val = fm["date"]
    if isinstance(date_val, str):
        post_date = datetime.strptime(date_val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        # yaml may parse it as a date object
        post_date = datetime(date_val.year, date_val.month, date_val.day, tzinfo=timezone.utc)

    return {
        "title": fm["title"],
        "date": post_date,
        "date_str": post_date.strftime("%b %-d, %Y"),
        "categories": fm.get("categories", []) or [],
        "excerpt": excerpt,
        "url": url,
        "slug": slug,
    }


def _clean_excerpt(raw: str) -> str:
    """Strip Markdown/HTML noise from excerpt text."""
    # Remove pymdownx snippet directives
    text = re.sub(r"--8<--[^\n]*", "", raw)
    # Remove HTML block elements (figures, divs, etc.)
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

        lines.append(
            f"\n### [{post['title']}]({post['url']})\n\n"
            f"{badge_line}\n\n"
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
        help="pre: homepage only; post: RSS only; all: both (default)",
    )
    args = parser.parse_args()

    posts = load_posts()
    print(f"Found {len(posts)} posts.")
    if args.step in ("pre", "all"):
        generate_homepage(posts)
    if args.step in ("post", "all"):
        generate_rss(posts)

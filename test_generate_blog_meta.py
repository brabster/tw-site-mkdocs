"""Tests for generate_blog_meta.py.

Covers:
  - _clean_excerpt: Markdown/HTML stripping
  - parse_post: front-matter parsing, URL derivation, excerpt selection
  - generate_homepage: marker insertion and replacement, post count limit
  - generate_rss: RSS 2.0 structural compliance, date formats, item fields
  - load_posts: integration smoke test against the real docs/posts/ tree
"""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import generate_blog_meta as gbm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_post(
    title: str = "Test Post",
    date_str: str = "2024-06-15",
    categories: list[str] | None = None,
    excerpt: str = "A short excerpt.",
    url: str = "https://example.com/posts/test-post/",
    slug: str = "test-post",
) -> dict:
    date = datetime(2024, 6, 15, tzinfo=timezone.utc)
    return {
        "title": title,
        "date": date,
        "date_str": date.strftime("%b %-d, %Y"),
        "categories": categories or [],
        "excerpt": excerpt,
        "url": url,
        "slug": slug,
    }


def _parse_rss(path: Path) -> ET.Element:
    """Return the root element of an RSS file."""
    return ET.parse(path).getroot()


# ---------------------------------------------------------------------------
# _clean_excerpt
# ---------------------------------------------------------------------------

class TestCleanExcerpt(unittest.TestCase):

    def test_removes_snippet_directives(self):
        result = gbm._clean_excerpt("Before\n--8<-- some/file.md\nAfter")
        self.assertNotIn("--8<--", result)
        self.assertIn("Before", result)
        self.assertIn("After", result)

    def test_removes_html_tags(self):
        result = gbm._clean_excerpt("<figure><img src='x.png'></figure>Plain text.")
        self.assertNotIn("<", result)
        self.assertIn("Plain text.", result)

    def test_removes_markdown_images(self):
        result = gbm._clean_excerpt("Text ![alt](./image.png) more text.")
        self.assertNotIn("![", result)
        self.assertIn("Text", result)
        self.assertIn("more text.", result)

    def test_converts_markdown_links_to_plain_text(self):
        result = gbm._clean_excerpt("See [the docs](https://example.com) for details.")
        self.assertNotIn("[", result)
        self.assertNotIn("(https://", result)
        self.assertIn("the docs", result)

    def test_removes_heading_markers(self):
        result = gbm._clean_excerpt("## Section heading\n\nParagraph text.")
        self.assertNotIn("##", result)
        self.assertIn("Section heading", result)

    def test_collapses_whitespace(self):
        result = gbm._clean_excerpt("Word1   \n\n   Word2")
        self.assertNotIn("  ", result)
        self.assertIn("Word1", result)
        self.assertIn("Word2", result)

    def test_empty_string(self):
        self.assertEqual(gbm._clean_excerpt(""), "")


# ---------------------------------------------------------------------------
# parse_post
# ---------------------------------------------------------------------------

class TestParsePost(unittest.TestCase):

    def _write_post(self, tmp_dir: Path, front_matter: str, body: str) -> Path:
        post_dir = tmp_dir / "2024-06-15-my-post"
        post_dir.mkdir()
        path = post_dir / "index.md"
        path.write_text(f"---\n{front_matter}\n---\n{body}", encoding="utf-8")
        return path

    def test_parses_valid_post_with_more_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_post(
                Path(tmp),
                "title: My Post\ndate: 2024-06-15\ncategories:\n  - python\n",
                "Intro text.\n<!-- more -->\nFull body.",
            )
            post = gbm.parse_post(path)
        self.assertIsNotNone(post)
        self.assertEqual(post["title"], "My Post")
        self.assertEqual(post["slug"], "2024-06-15-my-post")
        self.assertIn("Intro text.", post["excerpt"])
        self.assertNotIn("Full body.", post["excerpt"])
        self.assertEqual(post["categories"], ["python"])

    def test_parses_valid_post_without_more_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_post(
                Path(tmp),
                "title: Simple Post\ndate: 2024-01-01\n",
                "A" * 600,
            )
            post = gbm.parse_post(path)
        self.assertIsNotNone(post)
        self.assertLessEqual(len(post["excerpt"]), 500)

    def test_returns_none_for_missing_front_matter(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "no-fm"
            d.mkdir()
            path = d / "index.md"
            path.write_text("No front matter here.", encoding="utf-8")
            self.assertIsNone(gbm.parse_post(path))

    def test_returns_none_for_missing_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_post(Path(tmp), "date: 2024-06-15\n", "Body.")
            self.assertIsNone(gbm.parse_post(path))

    def test_returns_none_for_missing_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_post(Path(tmp), "title: No Date\n", "Body.")
            self.assertIsNone(gbm.parse_post(path))

    def test_date_as_yaml_date_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            # PyYAML parses bare dates like 2024-06-15 as date objects
            path = self._write_post(
                Path(tmp),
                "title: Date Object Post\ndate: 2024-06-15\n",
                "Body.",
            )
            post = gbm.parse_post(path)
        self.assertIsNotNone(post)
        self.assertEqual(post["date"].year, 2024)
        self.assertEqual(post["date"].month, 6)
        self.assertEqual(post["date"].day, 15)
        self.assertIsNotNone(post["date"].tzinfo)

    def test_url_derived_from_directory_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "2024-06-15-slug-test"
            d.mkdir()
            path = d / "index.md"
            path.write_text(
                "---\ntitle: Slug Test\ndate: 2024-06-15\n---\nBody.",
                encoding="utf-8",
            )
            post = gbm.parse_post(path)
        self.assertIsNotNone(post)
        self.assertIn("2024-06-15-slug-test", post["url"])
        self.assertTrue(post["url"].endswith("/"))

    def test_empty_categories_defaults_to_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_post(
                Path(tmp),
                "title: No Categories\ndate: 2024-06-15\n",
                "Body.",
            )
            post = gbm.parse_post(path)
        self.assertIsNotNone(post)
        self.assertEqual(post["categories"], [])


# ---------------------------------------------------------------------------
# generate_homepage
# ---------------------------------------------------------------------------

class TestGenerateHomepage(unittest.TestCase):

    def _write_index(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def test_appends_generated_section_when_no_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = Path(tmp) / "index.md"
            self._write_index(idx, "# Home\n\nWelcome.")
            post = _make_post()
            gbm.generate_homepage([post], index_path=idx)
            result = idx.read_text(encoding="utf-8")
        self.assertIn(gbm.GENERATED_MARKER, result)
        self.assertIn("## Recent posts", result)
        self.assertIn(post["title"], result)

    def test_replaces_existing_generated_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = Path(tmp) / "index.md"
            self._write_index(
                idx,
                f"# Home\n\n{gbm.GENERATED_MARKER}\n\n## Recent posts\n\n### Old Post\n",
            )
            new_post = _make_post(title="New Post")
            gbm.generate_homepage([new_post], index_path=idx)
            result = idx.read_text(encoding="utf-8")
        self.assertIn("New Post", result)
        self.assertNotIn("Old Post", result)
        self.assertEqual(result.count(gbm.GENERATED_MARKER), 1)

    def test_respects_recent_posts_count_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = Path(tmp) / "index.md"
            self._write_index(idx, "# Home\n")
            posts = [_make_post(title=f"Post {i}", slug=f"post-{i}") for i in range(gbm.RECENT_POSTS_COUNT + 5)]
            gbm.generate_homepage(posts, index_path=idx)
            result = idx.read_text(encoding="utf-8")
        for i in range(gbm.RECENT_POSTS_COUNT):
            self.assertIn(f"Post {i}", result)
        for i in range(gbm.RECENT_POSTS_COUNT, gbm.RECENT_POSTS_COUNT + 5):
            self.assertNotIn(f"Post {i}", result)

    def test_empty_post_list_produces_empty_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = Path(tmp) / "index.md"
            self._write_index(idx, "# Home\n")
            gbm.generate_homepage([], index_path=idx)
            result = idx.read_text(encoding="utf-8")
        self.assertIn("## Recent posts", result)

    def test_category_badges_appear_in_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = Path(tmp) / "index.md"
            self._write_index(idx, "# Home\n")
            post = _make_post(categories=["python", "data"])
            gbm.generate_homepage([post], index_path=idx)
            result = idx.read_text(encoding="utf-8")
        self.assertIn("`python`", result)
        self.assertIn("`data`", result)

    def test_long_excerpt_is_truncated_to_200_chars(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = Path(tmp) / "index.md"
            self._write_index(idx, "# Home\n")
            post = _make_post(excerpt="X" * 300)
            gbm.generate_homepage([post], index_path=idx)
            result = idx.read_text(encoding="utf-8")
        self.assertIn("...", result)
        # The displayed excerpt portion should not exceed 200 Xs followed by ...
        self.assertNotIn("X" * 201, result)


# ---------------------------------------------------------------------------
# generate_rss  (RSS 2.0 compliance)
# ---------------------------------------------------------------------------

def _is_rfc2822(date_str: str) -> bool:
    """Return True if date_str is a parseable RFC 2822 date."""
    try:
        parsedate_to_datetime(date_str)
        return True
    except Exception:
        return False


class TestGenerateRss(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name) / "feed.xml"
        self.posts = [
            _make_post(
                title="First Post",
                excerpt="First excerpt.",
                categories=["python"],
                url="https://example.com/posts/first/",
                slug="first",
            ),
            _make_post(
                title="Second Post",
                excerpt="Second excerpt.",
                categories=["data", "cloud"],
                url="https://example.com/posts/second/",
                slug="second",
            ),
        ]

    def tearDown(self):
        self._tmp.cleanup()

    def _root(self) -> ET.Element:
        return _parse_rss(self.out)

    def test_writes_file_to_specified_path(self):
        gbm.generate_rss(self.posts, output=self.out)
        self.assertTrue(self.out.exists())

    def test_root_element_is_rss(self):
        gbm.generate_rss(self.posts, output=self.out)
        root = self._root()
        self.assertEqual(root.tag, "rss")

    def test_rss_version_is_2_0(self):
        gbm.generate_rss(self.posts, output=self.out)
        self.assertEqual(self._root().get("version"), "2.0")

    def test_channel_has_required_elements(self):
        gbm.generate_rss(self.posts, output=self.out)
        channel = self._root().find("channel")
        self.assertIsNotNone(channel)
        self.assertIsNotNone(channel.find("title"))
        self.assertIsNotNone(channel.find("link"))
        self.assertIsNotNone(channel.find("description"))

    def test_channel_title_is_site_name(self):
        gbm.generate_rss(self.posts, output=self.out)
        title = self._root().find("channel/title").text
        self.assertEqual(title, gbm.SITE_NAME)

    def test_channel_link_is_site_url(self):
        gbm.generate_rss(self.posts, output=self.out)
        link = self._root().find("channel/link").text
        self.assertEqual(link, gbm.SITE_URL)

    def test_channel_description_is_set(self):
        gbm.generate_rss(self.posts, output=self.out)
        desc = self._root().find("channel/description").text
        self.assertEqual(desc, gbm.SITE_DESCRIPTION)

    def test_last_build_date_is_rfc2822(self):
        gbm.generate_rss(self.posts, output=self.out)
        lbd = self._root().find("channel/lastBuildDate").text
        self.assertTrue(_is_rfc2822(lbd), f"lastBuildDate not RFC 2822: {lbd!r}")

    def test_atom_self_link_present_with_correct_attributes(self):
        gbm.generate_rss(self.posts, output=self.out)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        atom_link = self._root().find("channel/atom:link", ns)
        self.assertIsNotNone(atom_link, "atom:link element missing")
        self.assertEqual(atom_link.get("rel"), "self")
        self.assertEqual(atom_link.get("type"), "application/rss+xml")
        href = atom_link.get("href")
        self.assertTrue(href.startswith("http"), f"atom:link href not a URL: {href!r}")

    def test_items_have_required_elements(self):
        gbm.generate_rss(self.posts, output=self.out)
        channel = self._root().find("channel")
        items = channel.findall("item")
        self.assertEqual(len(items), len(self.posts))
        for item in items:
            self.assertIsNotNone(item.find("title"), "item missing <title>")
            self.assertIsNotNone(item.find("link"), "item missing <link>")
            self.assertIsNotNone(item.find("guid"), "item missing <guid>")

    def test_item_guid_is_permalink(self):
        gbm.generate_rss(self.posts, output=self.out)
        items = self._root().findall("channel/item")
        for item in items:
            guid = item.find("guid")
            self.assertEqual(guid.get("isPermaLink"), "true")

    def test_item_pub_date_is_rfc2822(self):
        gbm.generate_rss(self.posts, output=self.out)
        items = self._root().findall("channel/item")
        for item in items:
            pub_date = item.find("pubDate")
            self.assertIsNotNone(pub_date, "item missing <pubDate>")
            self.assertTrue(
                _is_rfc2822(pub_date.text),
                f"pubDate not RFC 2822: {pub_date.text!r}",
            )

    def test_item_description_included_when_excerpt_present(self):
        gbm.generate_rss(self.posts, output=self.out)
        first_item = self._root().find("channel/item")
        self.assertIsNotNone(first_item.find("description"))
        self.assertEqual(first_item.find("description").text, "First excerpt.")

    def test_item_categories_included(self):
        gbm.generate_rss(self.posts, output=self.out)
        items = self._root().findall("channel/item")
        second_item = items[1]
        categories = [c.text for c in second_item.findall("category")]
        self.assertIn("data", categories)
        self.assertIn("cloud", categories)

    def test_item_description_absent_when_no_excerpt(self):
        post = _make_post(excerpt="")
        gbm.generate_rss([post], output=self.out)
        item = self._root().find("channel/item")
        self.assertIsNone(item.find("description"))

    def test_respects_feed_posts_count_limit(self):
        many = [_make_post(title=f"Post {i}", slug=f"post-{i}") for i in range(gbm.FEED_POSTS_COUNT + 5)]
        gbm.generate_rss(many, output=self.out)
        items = self._root().findall("channel/item")
        self.assertEqual(len(items), gbm.FEED_POSTS_COUNT)

    def test_output_is_valid_xml(self):
        gbm.generate_rss(self.posts, output=self.out)
        content = self.out.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("<?xml"))
        # Re-parsing must not raise
        ET.fromstring(content)

    def test_empty_post_list_produces_channel_with_no_items(self):
        gbm.generate_rss([], output=self.out)
        items = self._root().findall("channel/item")
        self.assertEqual(len(items), 0)


# ---------------------------------------------------------------------------
# load_posts  (integration smoke test against the real docs/posts/ tree)
# ---------------------------------------------------------------------------

class TestLoadPosts(unittest.TestCase):

    def setUp(self):
        self.posts = gbm.load_posts()

    def test_returns_non_empty_list(self):
        self.assertGreater(len(self.posts), 0)

    def test_posts_have_required_keys(self):
        required = {"title", "date", "date_str", "categories", "excerpt", "url", "slug"}
        for post in self.posts:
            self.assertTrue(required.issubset(post.keys()), f"Post missing keys: {post}")

    def test_posts_are_sorted_newest_first(self):
        dates = [p["date"] for p in self.posts]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_all_dates_are_timezone_aware(self):
        for post in self.posts:
            self.assertIsNotNone(post["date"].tzinfo, f"Naive date in post: {post['slug']}")

    def test_all_urls_are_absolute(self):
        for post in self.posts:
            self.assertTrue(post["url"].startswith("http"), f"Relative URL in post: {post['slug']}")


if __name__ == "__main__":
    unittest.main()

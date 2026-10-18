import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".dev_scripts"))
from postprocess_rss import postprocess, postprocess_feed


class PostprocessRSSTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.site_dir = Path(self.temp_dir.name)
        self.post_path = self.site_dir / "posts/example/index.html"
        self.post_path.parent.mkdir(parents=True)
        self.post_path.write_text(
            '<article class="md-content__inner md-typeset">'
            "<h1>Post title</h1>"
            '<p>Rendered <a href="../../other/index.html">link</a>.</p>'
            '<img src="../../images/example.webp" alt="Example">'
            '<p>{{&lt; figure\n src="./assets/photo.webp"\n caption="A caption" &gt;}}</p>'
            '<p>{{&lt; img src="./assets/photo.webp" alt="Photo" &gt;}}</p>'
            "</article>",
            encoding="utf-8",
        )
        self.feed_xml = (
            '<?xml version="1.0"?>'
            '<rss version="2.0"><channel><title>Test</title>'
            '<link>https://example.test/</link>'
            '<managingEditor>brabster</managingEditor>'
            '<item><title>Example</title>'
            '<author>Paul Brabban</author>'
            '<link>https://example.test/posts/example/</link>'
            '<description>Raw markdown ![image](./image.webp)</description>'
            '</item></channel></rss>'
        )
        for filename in ("feed_rss_created.xml", "feed_rss_updated.xml"):
            (self.site_dir / filename).write_text(self.feed_xml, encoding="utf-8")
        self.index_path = self.site_dir / "index.html"
        self.index_path.write_text("<html><head></head><body></body></html>", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_renders_feed_descriptions_and_adds_autodiscovery_links(self):
        postprocess(self.site_dir)
        for filename in ("feed_rss_created.xml", "feed_rss_updated.xml"):
            root = ET.parse(self.site_dir / filename).getroot()
            self.assertEqual(
                root.findtext("./channel/managingEditor"),
                "paul@tempered.works (Paul Brabban)",
            )
            self.assertEqual(
                root.findtext("./channel/item/author"),
                "paul@tempered.works (Paul Brabban)",
            )
            description = root.findtext("./channel/item/description")
            self.assertIn("Rendered", description)
            self.assertNotIn("Raw markdown", description)
            self.assertNotIn("<h1>", description)
            self.assertIn(
                'href="https://example.test/other/index.html"',
                description,
            )
            self.assertIn(
                'src="https://example.test/images/example.webp"',
                description,
            )
            self.assertIn(
                'src="https://example.test/posts/example/assets/photo.webp"',
                description,
            )
            self.assertIn("<br />A caption", description)
            self.assertIn(
                'src="https://example.test/posts/example/assets/photo.webp" alt="Photo"',
                description,
            )
            self.assertEqual(
                root.findtext("./channel/item/link"),
                "https://example.test/posts/example/",
            )

        homepage = self.index_path.read_text(encoding="utf-8")
        self.assertIn('href="feed_rss_created.xml"', homepage)
        self.assertIn('href="feed_rss_updated.xml"', homepage)

    def test_is_idempotent(self):
        postprocess(self.site_dir)
        first_feed = (self.site_dir / "feed_rss_created.xml").read_text(encoding="utf-8")
        first_homepage = self.index_path.read_text(encoding="utf-8")
        postprocess(self.site_dir)
        self.assertEqual(
            (self.site_dir / "feed_rss_created.xml").read_text(encoding="utf-8"),
            first_feed,
        )
        self.assertEqual(self.index_path.read_text(encoding="utf-8"), first_homepage)

    def test_rejects_feed_urls_outside_site_directory(self):
        feed_path = self.site_dir / "feed_rss_created.xml"
        xml = self.feed_xml.replace(
            "https://example.test/posts/example/",
            "https://example.test/../../outside/",
        )
        feed_path.write_text(xml, encoding="utf-8")
        with self.assertRaises(ValueError):
            postprocess_feed(feed_path, self.site_dir)


if __name__ == "__main__":
    unittest.main()

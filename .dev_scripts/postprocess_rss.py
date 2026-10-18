#!/usr/bin/env python3

import argparse
import html
from html.parser import HTMLParser
from pathlib import Path
import re
import shlex
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET


FEEDS = ("feed_rss_created.xml", "feed_rss_updated.xml")
MANAGING_EDITOR = "paul@tempered.works"
SHORTCODE_PATTERN = re.compile(r"\{\{<\s*(img|figure)\s+(.*?)\s*>\}\}", re.DOTALL)
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class ArticleHTMLParser(HTMLParser):
    def __init__(self, page_url):
        super().__init__()
        self.page_url = page_url
        self.parts = []
        self.depth = 0
        self.heading_depth = 0
        self.in_article = False

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if not self.in_article:
            if tag == "article" and "md-content__inner" in classes:
                self.in_article = True
                self.depth = 1
            return

        if self.heading_depth:
            if tag not in VOID_ELEMENTS:
                self.heading_depth += 1
            return

        if tag == "h1" and self.depth == 1:
            self.heading_depth = 1
            return

        self.parts.append(self._start_tag(tag, attrs))
        if tag not in VOID_ELEMENTS:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        if self.in_article and not self.heading_depth:
            self.parts.append(self._start_tag(tag, attrs, closed=True))

    def handle_endtag(self, tag):
        if not self.in_article:
            return
        if self.heading_depth:
            self.heading_depth -= 1
            return
        if tag == "article" and self.depth == 1:
            self.in_article = False
            return
        self.depth -= 1
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if self.in_article and not self.heading_depth:
            cursor = 0
            for match in SHORTCODE_PATTERN.finditer(data):
                self.parts.append(html.escape(data[cursor:match.start()], quote=False))
                self.parts.append(self._render_shortcode(match))
                cursor = match.end()
            self.parts.append(html.escape(data[cursor:], quote=False))

    def handle_entityref(self, name):
        if self.in_article and not self.heading_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if self.in_article and not self.heading_depth:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        if self.in_article and not self.heading_depth:
            self.parts.append(f"<!--{data}-->")

    def _start_tag(self, tag, attrs, closed=False):
        rendered_attrs = []
        for name, value in attrs:
            if value is None:
                rendered_attrs.append(name)
                continue
            if name in ("href", "src") and value:
                value = urljoin(self.page_url, value)
            rendered_attrs.append(f'{name}="{html.escape(value, quote=True)}"')
        ending = " />" if closed or tag in VOID_ELEMENTS else ">"
        return f"<{tag}{(' ' + ' '.join(rendered_attrs)) if rendered_attrs else ''}{ending}"

    def _render_shortcode(self, match):
        try:
            attrs = dict(argument.split("=", 1) for argument in shlex.split(match.group(2)))
        except ValueError:
            return html.escape(match.group(0), quote=False)
        src = attrs.get("src")
        if not src:
            return html.escape(match.group(0), quote=False)
        src = html.escape(urljoin(self.page_url, src), quote=True)
        if match.group(1) == "img":
            alt = html.escape(attrs.get("alt", ""), quote=True)
            return f'<img src="{src}" alt="{alt}" />'
        caption = attrs.get("caption", "")
        alt = html.escape(caption, quote=True)
        caption = html.escape(caption, quote=False)
        return f'<img src="{src}" alt="{alt}" /><br />{caption}'


def rendered_article(page_path, page_url):
    parser = ArticleHTMLParser(page_url)
    parser.feed(page_path.read_text(encoding="utf-8"))
    parser.close()
    if not parser.parts:
        raise ValueError(f"No rendered article found in {page_path}")
    return "".join(parser.parts)


def page_path_for_url(site_dir, page_url):
    path = unquote(urlsplit(page_url).path).lstrip("/")
    candidate = site_dir / path
    if path.endswith("/") or not candidate.suffix:
        candidate /= "index.html"
    candidate = candidate.resolve()
    if not candidate.is_relative_to(site_dir.resolve()):
        raise ValueError(f"Feed item URL escapes the site directory: {page_url}")
    return candidate


def postprocess_feed(feed_path, site_dir):
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_pis=True))
    tree = ET.parse(feed_path, parser=parser)
    for _, (prefix, namespace) in ET.iterparse(feed_path, events=("start-ns",)):
        ET.register_namespace(prefix, namespace)

    channel = tree.find("channel")
    if channel is None:
        raise ValueError(f"Missing RSS channel in {feed_path}")
    managing_editor = channel.find("managingEditor")
    if managing_editor is not None:
        managing_editor.text = MANAGING_EDITOR
    for item in channel.findall("item"):
        link = item.findtext("link")
        description = item.find("description")
        if not link or description is None:
            raise ValueError(f"RSS item missing link or description in {feed_path}")
        page_path = page_path_for_url(site_dir, link)
        if not page_path.is_file():
            raise ValueError(f"Rendered post not found for RSS item: {page_path}")
        description.text = rendered_article(page_path, link)

    tree.write(feed_path, encoding="utf-8", xml_declaration=True)


def add_feed_discovery(site_dir):
    index_path = site_dir / "index.html"
    content = index_path.read_text(encoding="utf-8")
    for feed in FEEDS:
        pattern = re.compile(
            rf'<link\b(?=[^>]*\btype=["\']application/rss\+xml["\'])'
            rf'(?=[^>]*\bhref=["\']{re.escape(feed)}["\'])[^>]*>',
            re.IGNORECASE,
        )
        if not pattern.search(content):
            tag = (
                f'<link rel="alternate" type="application/rss+xml" '
                f'href="{feed}" />'
            )
            content, count = re.subn(
                r"</head\s*>", f"    {tag}\n  </head>", content, count=1,
                flags=re.IGNORECASE,
            )
            if count != 1:
                raise ValueError(f"Missing </head> in {index_path}")
    index_path.write_text(content, encoding="utf-8")


def postprocess(site_dir):
    for filename in FEEDS:
        feed_path = site_dir / filename
        if not feed_path.is_file():
            raise FileNotFoundError(f"RSS feed not found: {feed_path}")
        postprocess_feed(feed_path, site_dir)
    add_feed_discovery(site_dir)


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("site_dir", nargs="?", type=Path, default=Path("site"))
    site_dir = argument_parser.parse_args().site_dir.resolve()
    postprocess(site_dir)


if __name__ == "__main__":
    main()

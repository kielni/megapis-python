from datetime import datetime, timedelta
import re
import time
from typing import Dict, Set, List

from bs4 import BeautifulSoup

import feedparser
from dateutil import parser, tz
import requests

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    "sources": None,  # URL to JSON doc containing sources: {url: {name: 'x', stories: 3}}
    "max_age": 3,  # max age in days
    "max_items": 3,  # default max items per source (if not specified in sources)
    "max_sources": 0,
}


class RssTask(TaskBase):
    """get items from RSS feeds in sources"""

    def __str__(self):
        return "RssTask"

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(RssTask, self).__init__(config)
        self.date_re = re.compile(r"\d\d\d\d.\d\d.\d\d")
        self.tz = tz.gettz("America/Los_Angeles")
        now = datetime.now().astimezone(self.tz)
        self.min_dt = now - timedelta(days=self.config["max_age"])

    def run(self, data):
        items = []
        empty = []
        limit = self.config["max_sources"]
        # load urls from json
        print(f"sources={self.config['sources']}")
        sources = requests.get(self.config["sources"]).json()
        for idx, url in enumerate(sources.keys()):
            if limit and idx >= int(limit):
                break
            data = feedparser.parse(url)  # pylint: disable=no-member
            saved = 0
            print(f"\n{url}\t{data.get('feed', {}).get('title')}")
            print(f"\t{len(data['entries'])} entries")
            if not data["entries"]:
                empty.append(url)
            output = True
            for entry in data["entries"]:
                entry = self._parse_entry(entry, output=output)
                if not entry:
                    output = False
                    continue
                entry.update(
                    {
                        "source": sources[url]["name"],
                        "sourceLink": data.feed.link,
                        "imagePosition": sources[url].get("imagePosition", "right"),
                    }
                )
                items.append(entry)
                saved += 1
                if saved == sources[url].get("stories", self.config["max_items"]):
                    break
        print(f"\n{len(items)} total items")
        keep: List[Dict] = []
        titles: Set[str] = set()
        for item in items:
            if item["title"] in titles:
                print(f"dropping duplicate {item['title']}")
                continue
            keep.append(item)
            titles.add(item["title"])
        items = sorted(keep, key=lambda x: x["date"], reverse=True)
        for item in items:
            print(f"{item['date']}\t{item['title']}")
        print(f"{len(items)} de-duped items")
        for url in empty:
            print(f"\nWARNING: no entries for {url}")
        return {
            "items": items,
            "updated": datetime.now().astimezone(self.tz).isoformat(),
        }

    def _published_date(self, entry):
        """look for date in published_parsed, dc:date, updated_parsed, url"""
        # <dc:date>2018-11-01T12:45:00+00:00</dc:date>
        dt = None
        if "published_parsed" in entry:
            try:
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            except:
                print(f"error parsing {str(entry.published_parsed)}")
        if "dc:date" in entry:
            try:
                dt = parser.parse(entry["dc:date"])
            except:
                print(f"error parsing {str(entry['dc:date'])}")
        if "updated_parsed" in entry:
            try:
                dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            except:
                print(f"error parsing {str(entry.updated_parsed)}")
        if not dt:
            # look for date in URL
            match = self.date_re.search(entry.link)
            if match:
                dt = parser.parse(match.group(0))
        if not dt:
            print(f"warning: no timestamp for entry {entry.keys()}")
            dt = datetime.fromtimestamp(int(self.min_dt.timestamp()))
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            dt = dt.astimezone(self.tz)
        return dt

    def _parse_entry(self, entry, output):
        print(entry.title)
        dt = self._published_date(entry)
        print(f"\tpublished={dt}")
        """
        if output:
            prefix = "- " if dt < self.min_dt else "✓ "
            # print('\t%s%s\t%s' % (prefix, dt.strftime('%-m/%-d'), entry.title[:80]))
        """
        if dt < self.min_dt:
            print("\ttoo old")
            return None
        summary = None
        # get image from html
        img_url = None
        for key in ["description", "content", "content:encoded"]:
            html = entry.get(key)
            if isinstance(html, list):
                html = html[0]
            if isinstance(html, dict):
                html = html.get("value")
            # print('html=|%s|' % html)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            summary = soup.get_text()
            img = soup.find("img")
            if img:
                # print('found %s' % img)
                img_url = img.get("src")
        # media:thumbnail url=""
        if entry.get("media_thumbnail"):
            img_url = entry["media_thumbnail"][0]["url"]
        if not summary:
            try:
                summary = BeautifulSoup(entry.summary, "html.parser").get_text()
            except:
                print(f"error getting summary for {entry}")
                summary = ""
        return {
            "title": entry.title,
            "summary": summary,
            "date": dt.isoformat(),
            "image": img_url,
            "url": entry.link,
        }

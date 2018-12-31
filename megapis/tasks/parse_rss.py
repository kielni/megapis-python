from datetime import datetime, timedelta
import re
import time

from bs4 import BeautifulSoup

import feedparser
from dateutil import parser, tz
import requests

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'sources': None,  # URL to JSON doc containing sources: {url: {name: 'x', stories: 3}}
    'max_age': 3, # max age in days
    'max_items': 3,  # default max items per source (if not specified in sources)
}

class RssTask(TaskBase):
    '''get items from RSS feeds in sources'''
    def __str__(self):
        return 'RssTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(RssTask, self).__init__(config)
        self.date_re = re.compile(r'\d\d\d\d.\d\d.\d\d')
        self.tz = tz.gettz('America/Los_Angeles')
        now = datetime.now().astimezone(self.tz)
        self.min_dt = now - timedelta(days=self.config['max_age'])

    def run(self, data):
        items = []
        empty = []
        # load urls from json
        print('sources=%s' % self.config['sources'])
        sources = requests.get(self.config['sources']).json()
        for url in sources.keys():
            data = feedparser.parse(url) # pylint: disable=no-member
            saved = 0
            print('\n%s\t%s' % (url, data.get('feed', {}).get('title')))
            print('\t%s entries' % (len(data['entries'])))
            if not data['entries']:
                empty.append(url)
            output = True
            for entry in data['entries']:
                entry = self._parse_entry(entry, output=output)
                if not entry:
                    output = False
                    continue
                entry.update({
                    'source': sources[url]['name'],
                    'sourceLink': data.feed.link,
                    'imagePosition': sources[url].get('imagePosition', 'right'),
                })
                items.append(entry)
                saved += 1
                if saved == sources[url].get('stories', self.config['max_items']):
                    break
        print('%s items' % (len(items)))
        for url in empty:
            print('\nWARNING: no entries for %s' % url)
        return {'items': items, 'updated': datetime.now().astimezone(self.tz).isoformat()}

    def _published_date(self, entry):
        '''look for date in published_parsed, dc:date, updated_parsed, url'''
        # <dc:date>2018-11-01T12:45:00+00:00</dc:date>
        dt = None
        if 'published_parsed' in entry:
            try:
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            except:
                print('error parsing %s' % str(entry.published_parsed))
        if 'dc:date' in entry:
            try:
                dt = parser.parse(entry['dc:date'])
            except:
                print('error parsing %s' % str(entry['dc:date']))
        if 'updated_parsed' in entry:
            try:
                dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            except:
                print('error parsing %s' % str(entry.updated_parsed))
        if not dt:
            # look for date in URL
            match = self.date_re.search(entry.link)
            if match:
                dt = parser.parse(match.group(0))
        if not dt:
            print('warning: no timestamp for entry %s' % entry.keys())
            dt = datetime.fromtimestamp(int(self.min_dt.timestamp()))
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            dt = dt.astimezone(self.tz)
        return dt

    def _parse_entry(self, entry, output):
        print(entry.title)
        dt = self._published_date(entry)
        if output:
            prefix = '- ' if dt < self.min_dt else '✓ '
            #print('\t%s%s\t%s' % (prefix, dt.strftime('%-m/%-d'), entry.title[:80]))
        if dt < self.min_dt:
            return None
        summary = None
        # get image from html
        img_url = None
        for key in ['description', 'content', 'content:encoded']:
            html = entry.get(key)
            if isinstance(html, list):
                html = html[0]
            if isinstance(html, dict):
                html = html.get('value')
            #print('html=|%s|' % html)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            summary = soup.get_text()
            img = soup.find('img')
            if img:
                #print('found %s' % img)
                img_url = img.get('src')
        # media:thumbnail url=""
        if entry.get('media_thumbnail'):
            img_url = entry['media_thumbnail'][0]['url']
        if not summary:
            try:
                summary = BeautifulSoup(entry.summary, 'html.parser').get_text()
            except:
                print('error getting summary for %s' % entry)
                summary = ''
        return {
            'title': entry.title,
            'summary': summary,
            'date': dt.isoformat(),
            'image': img_url,
            'url': entry.link,
        }

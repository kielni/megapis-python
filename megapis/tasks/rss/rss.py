import json
import logging
import re
import sys
import time

from bs4 import BeautifulSoup
from datetime import datetime, timedelta

import boto3
import feedparser
from dateutil import parser, tz
import requests

'''
    config
        sources: sourceURL
        max_age = in days
        bucket
        key
        profile
'''
date_re = re.compile(r'\d\d\d\d.\d\d.\d\d')
this_tz = tz.gettz('America/Los_Angeles')

def rss_to_json(config):
    now = datetime.now().astimezone(this_tz)
    min_dt = now - timedelta(days=config['max_age'])
    items = []
    # load urls from json
    sources = requests.get(config['sources']).json()
    for url in sources.keys():
        data = feedparser.parse(url)
        saved = 0
        print('\n%s\t%s' % (url, data.get('feed', {}).get('title')))
        print('%s entries' % (len(data['entries'])))
        for entry in data['entries']:
            entry = parse_entry(entry, min_dt)
            if not entry:
                continue
            entry.update({
                'source': sources[url]['name'],
                'sourceLink': data.feed.link,
            })
            items.append(entry)
            saved += 1
            if saved == sources[url].get('stories', 2):
                break
    # write to S3
    print('%s items to %s/%s' % (len(items), config['bucket'], config['key']))
    boto3.setup_default_session(profile_name=config['profile'])
    print(boto3.client('s3').put_object(
        ACL='public-read',
        Body=json.dumps({'items': items, 'updated': now.isoformat()}).encode('utf-8'),
        Bucket=config['bucket'],
        ContentType='application/json',
        Key=config['key']
    ))


def parse_entry(entry, min_dt):
    #print(entry)
    dt = datetime(2000, 1, 1)
    if 'published_parsed' in entry:
        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
    else:
        # look for date in URL
        match = date_re.search(entry.link)
        if match:
            dt = parser.parse(match.group(0))
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.astimezone(this_tz)
    print('\t%s\t%s' % (entry.title, dt.isoformat()))
    if dt < min_dt:
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
    if not summary:
        summary = BeautifulSoup(entry.summary, 'html.parser').get_text()
    return {
        'title': entry.title,
        'summary': summary,
        'date': dt.isoformat(),
        'image': img_url,
        'url': entry.link,
    }

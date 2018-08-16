import json
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
    empty = []
    # load urls from json
    sources = requests.get(config['sources']).json()
    for url in sources.keys():
        data = feedparser.parse(url)
        saved = 0
        print('\n%s\t%s' % (url, data.get('feed', {}).get('title')))
        print('%s entries' % (len(data['entries'])))
        if not data['entries']:
            empty.append(url)
        output = True
        for entry in data['entries']:
            entry = parse_entry(entry, min_dt, output=output)
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
            if saved == sources[url].get('stories', 3):
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
    for url in empty:
        print('\nWARNING: no entries for %s' % url)


def parse_entry(entry, min_dt, output):
    #print(entry)
    dt = min_dt
    if 'published_parsed' in entry:
        try:
            dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        except:
            print('error parsing %s' % str(entry.published_parsed))
    else:
        # look for date in URL
        match = date_re.search(entry.link)
        if match:
            dt = parser.parse(match.group(0))
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.astimezone(this_tz)
    if output:
        prefix = '- ' if dt < min_dt else '✓ '
        print('\t%s%s\t%s' % (prefix, dt.strftime('%-m/%-d'), entry.title[:80]))
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

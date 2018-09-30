'''
    get Prime eligible Kindle books; exclude from list of ASINs from URL
'''
import random
import re
import sys
import time

from bs4 import BeautifulSoup
import requests

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'urls': [],
    'excludeUrl': None,
    'descriptionLength': 1000
}

class PrimeBooksTask(TaskBase):
    def __str__(self):
        return 'PrimeBooksTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(PrimeBooksTask, self).__init__(config)

    def run(self, data):
        config = self.config
        exclude = requests.get(url=config['excludeUrl']).json() if config['excludeUrl'] else []
        print('found %s books to exclude' % len(exclude))
        books = []
        fetched = []
        next_urls = []
        print('loading %s config urls' % len(config['urls']))
        for list_url in config['urls']:
            rval = _load_url(list_url, fetched, exclude, config['descriptionLength'])
            if not rval:
                continue
            books = books + rval['books']
            next_urls = next_urls + rval['next_urls']
        print('loading %s more urls' % len(next_urls))
        for list_url in next_urls:
            rval = _load_url(list_url, fetched, exclude, config['descriptionLength'])
            if not rval:
                continue
            books = books + rval['books']
        print('found %s books' % len(books))
        return books


def _load_url(list_url, fetched, exclude, max_len):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    }
    print('url=%s' % list_url)
    try:
        resp_text = requests.get(url=list_url, headers=headers).text
        #print('-----\n%s\n-----' % resp_text)
        with open('out.html', 'w') as outf:
            outf.write(resp_text)
        soup = BeautifulSoup(resp_text, 'html5lib')
    except:
        print('error loading %s: %s' % (list_url, sys.exc_info()[0]))
        return None
    # next page url
    next_urls = []
    next_link = soup.select('#pagnNextLink')
    if next_link:
        next_page = soup.select('#pagnNextLink')[0].get('href')
        if 'http' not in next_page:
            match = re.match('(http.?//.+?)/', list_url)
            if match:
                next_page = '%s%s' % (match.group(1), next_page)
        next_urls.append(next_page)
    # page meta
    page = soup.title.string
    for tag in ['Amazon.com: ', 'Prime Eligible ', 'Kindle Edition ', 'Books', '-', ':']:
        page = page.replace(tag, '')
    books = []
    print('%s result items' % len(soup.select('.s-result-item')))
    for book in soup.select('.s-result-item'):
        # list page: asin, title, author, url, image
        asin = book.get('data-asin')
        details = book.select_one('.s-access-detail-page')
        if not asin or not details:
            # s-result-list-layout-placeholder
            continue
        title = details.get('title')
        #print('%s\t%s' % (asin, title))
        if asin in fetched or asin in exclude:
            continue
        # series
        match = re.match(r'.*?Book (\d+)', title)
        if match and match.group(1) != '1':
            print('skipping series book %s' % title)
            continue
        fetched.append(asin)
        url = details.get('href')
        author = None
        for row in book.select_one('.a-col-right').select('.a-row'):
            text = row.get_text()
            if not 'by ' in text:
                continue
            match = re.match('.*?by (.*)', text)
            if match:
                author = match.group(1)
        # detail page
        time.sleep(random.randint(500, 2000)/1000)
        detail_soup = BeautifulSoup(requests.get(url=url, headers=headers).text, 'html5lib')
        desc = detail_soup.\
            select('#bookDescription_feature_div noscript')[0].\
            get_text().\
            strip().\
            replace('.', '. ')
        if len(desc) > max_len:
            short = max_len
            if ' ' in desc[max_len:]:
                short = max_len + desc[max_len:].index(' ')
            desc = desc[:short]+' ...'
        tags = []
        for tag in detail_soup.select('.zg_hrsr_item'):
            tags.append(re.sub('Kindle Store > Kindle eBooks > ',
                               '', tag.get_text(),
                               flags=re.DOTALL).\
                        strip().\
                        replace('\n', ' ').\
                        replace('\xa0', ' '))
        book = {
            'asin': asin,
            'title': title,
            'description': desc,
            'author': author,
            'url': detail_soup.select('link[rel="canonical"]')[0].get('href'),
            'img': book.select('.a-col-left img')[0].get('src'),
            'tag': '\n'.join(tags),
            'page': page
        }
        print('%s by %s' % (book['title'], book['author']))
        books.append(book)
    return {
        'next_urls': next_urls,
        'books': books
    }

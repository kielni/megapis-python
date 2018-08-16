import logging
import random
import re
import sys
import time

from bs4 import BeautifulSoup
from celery.utils.log import get_task_logger
import requests

from megapis.celeryapp import app
from megapis import celeryconfig
from megapis.task import MegapisTask

logging.basicConfig(level=logging.INFO)
log = get_task_logger(__name__)

class PrimeBooksTask(MegapisTask):
    default_config = {
        'output': 'something',
        'urls': [],
        'exclude_url': None,
        'description_length': 1000
    }

    def run(self):
        config = self.config
        exclude = requests.get(url=config['exclude_url']).json() if config['exclude_url'] else []
        log.info('found %s books to exclude %s', len(exclude), exclude)
        books = []
        fetched = []
        next_urls = []
        log.info('loading %s config urls', len(config['urls']))
        for list_url in config['urls']:
            rval = load_url(list_url, fetched, exclude, config['description_length'])
            if not rval:
                continue
            books = books + rval['books']
            next_urls = next_urls + rval['next_urls']
        log.info('loading %s more urls', len(next_urls))
        for list_url in next_urls:
            rval = load_url(list_url, fetched, exclude, config['description_length'])
            if not rval:
                continue
            books = books + rval['books']
        log.info('found %s books', len(books))
        self.replace(config['output'], books)


def load_url(list_url, fetched, exclude, max_len):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    }
    log.info('url=%s', list_url)
    try:
        resp_text = requests.get(url=list_url, headers=headers).text
        soup = BeautifulSoup(resp_text, 'html.parser')
    except:
        log.error('error loading %s: %s', list_url, sys.exc_info()[0])
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
    for s in ['Amazon.com: ', 'Prime Eligible ', 'Kindle Edition ', 'Books', '-', ':']:
        page = page.replace(s, '')
    books = []
    for book in soup.select('.s-result-item'):
        # list page: asin, title, author, url, image
        asin = book.get('data-asin')
        if not book.select('.s-access-detail-page'):
            continue
        details = book.select('.s-access-detail-page')[0]
        title = details.get('title')
        if asin in fetched:
            log.info('already fetched %s', title)
            continue
        if asin in exclude:
            log.info('exclude %s', title)
            continue
        series_match = re.match(r'.*?Book (\d+)', title)
        if series_match and series_match.group(1) != '1':
            log.info('skipping series book %s', title)
            continue
        fetched.append(asin)
        url = details.get('href')
        author = None
        for row in book.select('.a-col-right')[0].select('.a-row'):
            text = row.get_text()
            if not 'by ' in text:
                continue
            match = re.match('.*?by (.*)', text)
            if match:
                author = match.group(1)
        # detail page
        time.sleep(random.randint(500, 2000)/1000)
        resp_text = requests.get(url=url, headers=headers).text
        detail_soup = BeautifulSoup(resp_text, 'html.parser')
        desc = detail_soup.\
            select('#bookDescription_feature_div noscript')[0].\
            get_text().\
            strip()
        desc = desc.replace('.', '. ')
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
        b = {
            'asin': asin,
            'title': title,
            'description': desc,
            'author': author,
            'url': detail_soup.select('link[rel="canonical"]')[0].get('href'),
            'img': book.select('.a-col-left img')[0].get('src'),
            'tag': '\n'.join(tags),
            'page': page
        }
        log.info('%s by %s', b['title'], b['author'])
        log.debug(b)
        books.append(b)
    return {
        'next_urls': next_urls,
        'books': books
    }


@app.task(name='package.task')
def run_task(config):
    PrimeBooksTask(config).run()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'primebooks-fetch'
    PrimeBooksTask(celeryconfig.config[name]).run()

import logging
import sys
import time

from celery.utils.log import get_task_logger
import requests
import xmltodict

from megapis.celeryapp import app
from megapis import celeryconfig
from megapis.task import MegapisTask

logging.basicConfig(level=logging.INFO)
log = get_task_logger(__name__)

class GoodreadsTask(MegapisTask):
    default_config = {
        'user_id': 1,
        'api_key': 'abc',
        'output': 'something',
        'books': 20,
        'exclude_url': None # json list of ids to exclude: {"123": true, "456": true}
    }

    def run(self):
        config = self.config
        # get list of books for user
        resp = requests.get(
            url='https://www.goodreads.com/review/list/%s.xml' % config['user_id'],
            params={'v': 2, 'per_page': config['books'], 'key': config['api_key']})
        read = set()
        authors = set()
        for book in xmltodict.parse(resp.content)['GoodreadsResponse']['reviews']['review']:
            read.add(book['book']['id']['#text'])
            if not book['rating']:
                continue
            if int(book['rating']) < 4:
                continue
            authors.add(book['book']['authors']['author']['id'])
        log.info('read=%s authors=%s', len(read), len(authors))

        exclude = requests.get(url=config['exclude_url']).json() if config['exclude_url'] else []
        log.info('found %s books to exclude %s', len(exclude), exclude)
        # get list of books for each author
        books = []
        for author_id in authors:
            resp = requests.get(
                url='https://www.goodreads.com/author/list/%s' % author_id,
                params={'format': 'xml', 'per_page': 100, 'key': config['api_key']})
            author_books = xmltodict.parse(resp.content)\
                ['GoodreadsResponse']['author']['books']['book']
            # one book is an object, not list
            if not isinstance(author_books, list):
                author_books = [author_books]
            for book in author_books:
                book_id = str(book['id']['#text'])
                if book_id in read or book_id in exclude or not book['description']:
                    log.info('skipping %s\t%s', book_id, book['title'])
                    continue
                log.info('%s\t%s', book_id, book['title'])
                book_obj = {
                    'id': book_id,
                    'author': book['authors']['author']['name'],
                    'title': book['title'],
                    'description': book['description'],
                    'published': book['published'],
                    'image_url': book['image_url'],
                    'link': book['link']
                }
                if isinstance(book['isbn'], str):
                    book_obj['isbn'] = book['isbn']
                books.append(book_obj)
            # rate limit 1 per second
            time.sleep(1)
        log.info('saving %s books to %s', len(books), config['output'])
        self.replace(config['output'], books)


@app.task(name='goodreads.read-next')
def get_books(config):
    GoodreadsTask(config).run()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'goodreads-read-next'
    GoodreadsTask(celeryconfig.config[name]).run()

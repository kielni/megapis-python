import time

import requests
import xmltodict

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'user_id': 1,
    'api_key': 'abc',
    'output': 'something',
    'books': 20,
    'exclude_url': None # json list of ids to exclude: {"123": true, "456": true}
}

class GoodreadsTask(TaskBase):
    def __str__(self):
        return 'GoodreadsTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(GoodreadsTask, self).__init__(config)

    def run(self, data):
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
        print('read=%s authors=%s' % (len(read), len(authors)))

        exclude = requests.get(url=config['exclude_url']).json() if config['exclude_url'] else []
        print('found %s books to exclude %s' % (len(exclude), exclude))
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
                    print('skipping %s\t%s' % (book_id, book['title']))
                    continue
                print('%s\t%s' % (book_id, book['title']))
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
        print('saving %s books to %s' % (len(books), config['output']))
        self.replace(config['output'], books)

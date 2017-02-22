import logging
import re
import sys

from bs4 import BeautifulSoup
from celery.utils.log import get_task_logger
import requests

from megapis.celeryapp import app
from megapis import celeryconfig
from megapis.task import MegapisTask

logging.basicConfig(level=logging.DEBUG)
log = get_task_logger(__name__)

class AmazonPriceCheckTask(MegapisTask):
    default_config = {
        'items': {},
        'notify_body': '{item} now {current} (was {previous})',
    }

    def run(self):
        config = self.config
        prices_key = self.read(config['name'])
        prices = prices_key[0] if len(prices_key) else {}
        for item in config['items']:
            url = config['items'][item]
            price = get_current(url)
            prev = prices.get(item, 999999)
            log.info('%s: was %s, now %s', item, prev, price)
            if not price:
                continue
            if config.get('notify') and price < prev:
                if item not in prices:
                    prev = 'unknown'
                prices[item] = price
                body = config['notify_body'].format(item=item, previous=prev,
                                                    current=price)
                headers = {}
                if config.get('notify_content_type'):
                    headers['Content-Type'] = config['notify_content_type']
                resp = requests.post(url=config['notify'], data=body, headers=headers)
                log.info('sent %s to %s:\n%s', body, config['notify'], resp.text)
        self.replace(config['name'], [prices])


def get_current(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) '+\
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    }
    resp_text = requests.get(url=url, headers=headers).text
    soup = BeautifulSoup(resp_text, 'html.parser')
    price = soup.select('#priceblock_ourprice')
    log.info('price=%s', price)
    if price:
        log.info('price block=%s', price)
        return float(re.sub(r'[^\d\.]', '', price[0].get_text()))
    log.warning('price block not found: page=%s', resp_text)
    return None


@app.task(name='amazon-price-check.check')
def run_task(config):
    AmazonPriceCheckTask(config).run()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'amazon-price-check'
    task_config = celeryconfig.config[name]
    task_config['name'] = name
    AmazonPriceCheckTask(task_config).run()

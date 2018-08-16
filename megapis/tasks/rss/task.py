import json
import logging
import re
import sys
import time

from bs4 import BeautifulSoup
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta

from megapis.celeryapp import app
from megapis import celeryconfig
from megapis.task import MegapisTask
import rss

logging.basicConfig(level=logging.INFO)
log = get_task_logger(__name__)

class RssTask(MegapisTask):
    default_config = {
        'sources': '',
        'max_age': 2,  # in days
        'per_feed': 5,
        'profile': '',
        'bucket': '',
        'key': '',
    }

    def run(self):
        rss.rss_to_json(**self.config)


@app.task(name='rss.fetch')
def run_task(config):
    RssTask(config).run()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'rss'
    RssTask(celeryconfig.config[name]).run()

from datetime import datetime, timedelta
import re
import sys

from bs4 import BeautifulSoup
import dateutil.parser as date_parser
import requests

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'url': 'http://store.steampowered.com/search/results?sort_by=Released_DESC&category2=9',
    'min_age': 0,  # in days
    'max_age': 365,  # in days
    'exclude': None, # regex; skip games which match tags or title
}

class SteamNewReleasesTask(TaskBase):
    '''scrape new releases from Steam for a date range

    exclude by regex matching tags or title
    '''
    def __str__(self):
        return 'SteamNewReleasesTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(SteamNewReleasesTask, self).__init__(config)
        now = datetime.now()
        self.min_dt = now - timedelta(days=self.config['max_age'])
        self.max_dt = now - timedelta(days=self.config['min_age'])
        self.exclude = None
        if self.config['exclude']:
            self.exclude = re.compile(self.config['exclude'])

    def run(self, data):
        url = self.config['url']
        # scrape
        page = 1
        rval = self._get_list_page(url)
        games = rval['games']
        while rval['dt'] > self.min_dt:
            page += 1
            rval = self._get_list_page('%s&page=%s' % (url, page))
            games += rval['games']
        print('found %s games' % len(games))
        return games


    def _get_list_page(self, url):
        games = []
        try:
            resp_text = requests.get(url=url).text
            soup = BeautifulSoup(resp_text, 'html.parser')
        except:
            print('error loading %s: %s' % (url, sys.exc_info()[0]))
            return None
        dt = None
        for row in soup.select('a.search_result_row'):
            title = row.select_one('.title').string
            if 'Fantasy Grounds' in title:
                continue  # too many to output
            match = self.exclude.match(title.strip()) if self.exclude else None
            if match:
                print('skipping %s: title matches exclude %s' % (title, match.group(0)))
                continue
            dt_str = row.select_one('.search_released').string
            dt = date_parser.parse(dt_str)
            if dt > self.max_dt or dt < self.min_dt:
                continue
            reviews_el = row.select_one('.search_review_summary')
            if reviews_el:
                reviews = reviews_el.get('data-store-tooltip', '').replace('<br>', ' ')
            else:
                reviews = None
            game_url = row.get('href')
            game = {
                'url': game_url,
                'title': title,
                'date': dt.strftime('%B %d'),
                'reviews': reviews
            }
            details = self._get_details(title, game_url)
            if not details:
                continue
            game.update(details)
            print('*** %s (%s)\ttags=%s players=%s' % (
                game['title'], game['date'], game['tags'], game['players']))
            games.append(game)
        return {
            'games': games,
            'dt': dt
        }


    def _get_details(self, title, url):
        try:
            soup = BeautifulSoup(requests.get(url=url).text, 'html.parser')
        except:
            print('error loading %s: %s' % (url, sys.exc_info()[0]))
            return None
        if soup.select_one('#agegate_box'):
            print('skipping %s: age-restricted' % (title))
            return None
        game = {}
        # tags
        game['tags'] = []
        skip = None
        for user_tag in soup.select('.app_tag')[:10]:
            tag = user_tag.text.strip()
            if tag == '+':
                continue
            if self.exclude and self.exclude.match(tag):
                skip = tag
            game['tags'].append(tag)
        if skip:
            print('skipping %s: tag matches exclude %s' % (title, skip))
            return None
        # players
        game['players'] = []
        for desc in soup.select('.game_area_details_specs'):
            text = desc.text
            if 'Player' in text or 'Co-op' in text:
                game['players'].append(text)
        # description
        desc = soup.select_one('#game_area_description')
        if desc:
            desc = re.sub('<h2>About.*?</h2>', '', str(desc)).strip()
            desc = re.sub('</?br>', '', desc)
            game['description'] = desc
        img = soup.select_one('.game_header_image_full')
        if img:
            game['img'] = img.get('src')
        return game

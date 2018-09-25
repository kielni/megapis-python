import re
import sys

from bs4 import BeautifulSoup
import requests

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'apiKey': '',
    'steamId': '',
    'libraryUrl': '',
    'excludeTags': [
        '+', 'Valve', 'Valve Anti-Cheat enabled', 'Steam Trading Cards',
        'Captions available', 'Steam Workshop', 'Steam Cloud', 'Steam Achievements',
        'Commentary available'
    ],
}

class SteamLibraryTask(TaskBase):
    def __str__(self):
        return 'SteamLibraryTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(SteamLibraryTask, self).__init__(config)

    def run(self, data):
        owned = self._get_owned()
        '''
        {
            "appid": 42910,
            "name": "Magicka",
            "playtime_2weeks": 609,
            "playtime_forever": 3268,
            "img_icon_url": "0eb97d0cd644ee08b1339d2160c7a6adf2ea0a65",
            "img_logo_url": "8c59c674ef40f59c3bafde8ff0d59b7994c66477",
            "has_community_visible_stats": true
        },

        '''
        added = 0
        # get library as dict
        library = self._get_library()
        for game in owned:
            appid = game['appid']
            if appid in library:
                # update playtime and icons
                library[appid].update(game)
                continue
            # fetch and update metadata
            game.update(self._get_meta(appid))
            library[appid] = game
            added += 1
        # back to list
        print('updated %s games' % added)
        return {'data': [library[appid] for appid in library]}

    def _get_meta(self, appid):
        url = 'http://store.steampowered.com/app/%s' % appid
        try:
            soup = BeautifulSoup(requests.get(url=url).text, 'html.parser')
        except:
            print('error loading %s: %s' % (url, sys.exc_info()[0]))
            return {}
        if soup.select('#app_agegate'):
            return {
                'ageRestricted': True
            }
        # see if it redirected somewhere else
        redirect = True
        for meta in soup.select('meta[property="og:url"]'):
            if '/app/%s' % appid in meta.get('content', ''):
                redirect = False
        if redirect:
            return {
                'missingSteamPage': True
            }
        # meta property="og:url" content
        print('get %s' % appid)
        meta = {}
        meta['title'] = soup.select_one('.apphub_AppName').string
        text = str(soup.select_one('#game_area_description'))
        text = re.sub(r'id=".*?"', '', text).replace('<h2>About This Game</h2', '')
        meta['description'] = text
        meta['players'] = []
        meta['tags'] = []
        for detail in [s.string for s in soup.select('.game_area_details_specs a.name')]:
            key = 'players' if 'player' in detail.lower() else 'tags'
            if detail in meta[key] or detail in self.config['excludeTags']:
                continue
            meta[key].append(detail)
        for tag in [s.string.strip() for s in soup.select('.glance_tags .app_tag')]:
            if tag in meta['tags'] or tag in self.config['excludeTags']:
                continue
            meta['tags'].append(tag)
        text = soup.select('.details_block .linkbar')
        meta['genres'] = [g.string for g in text if '/genre/' in g['href']]
        print('new game %s\t%s\t%s' % (appid, meta['title'], ', '.join(meta['tags'])))
        return meta

    def _get_owned(self):
        # https://developer.valvesoftware.com/wiki/Steam_Web_API#GetOwnedGames_.28v0001.29
        url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?'
        url += 'key=%s&steamid=%s&format=json&include_appinfo=1' % (
            self.config['apiKey'], self.config['steamId'])
        print('url=%s' % url)
        return requests.get(url).json()['response']['games']

    def _get_library(self):
        # load library.json
        resp = requests.get(self.config['libraryUrl'])
        # list to dict
        library = {}
        for game in resp.json()['data']:
            library[game['appid']] = game
        return library

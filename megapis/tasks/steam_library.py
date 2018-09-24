import sys

from bs4 import BeautifulSoup
import requests

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'api_key': '',
    'steam_id': '',
    'library_url': '',
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
        print('owned=%s' % len(owned))
        # get library
        library = self._get_library()
        for game in owned:
            appid = game['appid']
            if appid in library:
                # update playtime and icons
                library[appid].update(game)
                continue
            game.update(self._get_meta(appid))
            library[appid] = game
        # back to list
        return {'data': [library[appid] for appid in library]}

    def _get_meta(self, appid):
        # TODO:
        meta = {}
        url = 'http://store.steampowered.com/app/%s/' % appid
        try:
            soup = BeautifulSoup(requests.get(url=url).text, 'html.parser')
        except:
            print('error loading %s: %s' % (url, sys.exc_info()[0]))
            return meta
        '''
            game.url = 'http://store.steampowered.com/app/'+game.appid+'/';
            x(game.url, {
                title: '.apphub_AppName',
                players: '.game_area_details_specs',
                genres: ['.details_block a'],
                linkbar: ['.details_block .linkbar'],
                description: '#game_area_description@html',
                positive: '#ReviewsTab_positive',
                negative: '#ReviewsTab_negative',
                tags: ['.glance_tags .app_tag'],
                features: ['.game_area_details_specs'],
                birthdate: '#agegate_box'
            })(function(err, meta) {
                if (err || (meta && meta.birthdate)) {
                    game.ageRestricted = true;
                    library.push(game);
                    forEachCallback();
                    return;
                }
                if (meta) {
                    _.extend(game, meta);
                }
                ['positive', 'negative', 'reviews', 'description'].forEach(function(field) {
                    if (game[field]) {
                        game[field] = game[field].trim().replace(/\s+/g, ' ');
                    }
                });
                if (game.description) {
                    game.description = game.description.replace('<h2>About This Game</h2>', '');
                }
                // genre a tags in first .details_block have no additional class;
                // link a tags in second .details_block have .linkbar
                game.linkbar.forEach(function(link) {
                    game.genres = _.without(game.genres, link);
                });
                delete game.linkbar;
                // + button is styled like a tag
                game.tags = _.without(game.tags, '+');
                ['genres', 'tags', 'features'].forEach(function(field) {
                    if (!game[field]) {
                        return;
                    }
                    game[field] = _.uniq(game[field].map(function(val) {
                        return val.trim();
                    }));
                    if (exclude.length) {
                        _.pullAll(game[field], exclude);
                    }
                });

        '''
        return {}

    def _get_owned(self):
        # https://developer.valvesoftware.com/wiki/Steam_Web_API#GetOwnedGames_.28v0001.29
        url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?'
        url += 'key=%s&steamid=%s&format=json&include_appinfo=1' % (
            self.config['api_key'], self.config['steam_id'])
        print('url=%s' % url)
        return requests.get(url).json()['response']['games']

    def _get_library(self):
        # load library.json
        resp = requests.get(self.config['library_url'])
        # list to dict
        library = {}
        for game in resp.json()['data']:
            library[game['appid']] = game
        return library


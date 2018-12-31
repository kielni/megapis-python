import requests

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'base_url': None,  #  S3 bucket URL
    'key': None,  # S3 key; add to base_url for sources
    'source': None, # source URL
    'name': None, # source name
    'hide': False,
}

class RssSourcesTask(TaskBase):
    '''get sources json and patch with data'''
    def __str__(self):
        return 'RssSourcesTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(RssSourcesTask, self).__init__(config)

    def run(self, data):
        config = self.config
        url = '%s/%s' % (config['base_url'], config['key'])
        all_sources = requests.get(url).json()
        source = config['source']
        if not source:
            print('source not found')
            return all_sources
        params = {
            'name': config.get('name', source),
            'hide': config.get('hide', 'false') == 'true'
        }
        print('set %s to %s' % (source, params))
        all_sources[source].update(params)
        return all_sources

import json

import boto3

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'path': 'output.txt',
    'transform': 'string',
}

TRANSFORMS = {
    'string': str,
    'json': json.dumps
}

class LocalFileTask(TaskBase):
    '''transform data and save as a local file'''
    def __str__(self):
        return 'LocalFileTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(LocalFileTask, self).__init__(config)

    def run(self, data):
        '''transform data and write to path'''
        print('save to %s' % (self.config['path']))
        with open(self.config['path'], 'w') as outfile:
            outfile.write(TRANSFORMS[self.config['transform']](data))

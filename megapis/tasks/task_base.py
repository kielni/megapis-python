import copy

class TaskBase:
    def __init__(self, config):
        instance_config = copy.deepcopy(getattr(self, 'default_config') or {})
        instance_config.update(config)
        self.config = instance_config
        self.name = __name__

    def run(self, data):
        print('run %s' % self.name)
        return data

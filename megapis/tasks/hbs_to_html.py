from pybars import Compiler

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'template': 'test.hbs',  # path to template
}

class HbsToHtmlTask(TaskBase):
    '''load template, merge with array of data, and return html'''
    def __str__(self):
        return 'HbsToHtmlTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(HbsToHtmlTask, self).__init__(config)

    def run(self, data):
        compiler = Compiler()
        with open(self.config['template'], 'r') as tmpl:
            template = compiler.compile(tmpl.read())
        return template({'data': data, 'count': len(data)})

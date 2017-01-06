import logging
import sys

from celery.utils.log import get_task_logger

from megapis.celeryapp import app
from megapis import celeryconfig
from megapis.task import MegapisTask

logging.basicConfig(level=logging.INFO)
log = get_task_logger(__name__)

class ATask(MegapisTask):
    default_config = {
    }

    def run(self):
        config = self.config


@app.task(name='package.task')
def run_task(config):
    ATask(config).run()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'a-task'
    ATask(celeryconfig.config[name]).run()

import json
import logging
import sys

import boto3
from celery.utils.log import get_task_logger

from megapis.celeryapp import app
from megapis import celeryconfig
from megapis.task import MegapisTask

logging.basicConfig(level=logging.INFO)
log = get_task_logger(__name__)

class S3UploadTask(MegapisTask):
    default_config = {
        'bucket': 'bucket',
        'key': 'filename',
        'acl': 'public-read',
        'transform': 'string',
        'profile': 'megapis'
    }

    transforms = {
        'string': str,
        'json': json.dumps
    }

    def run(self, consume=True):
        config = self.config
        log.info('S3Upload.run: upload %s to %s/%s',
                 config['name'], config['bucket'], config['key'])
        if consume:
            values = self.consume(config['name'])
        else:
            values = self.read(config['name'])
        log.info('get %s', config['name'])
        values = self.read(config['name'])

        boto3.setup_default_session(profile_name=config['profile'])
        s3 = boto3.client('s3')
        if values:
            data = self.transforms[config['transform']](values)
            content_type = 'application/json' if config['transform'] == 'json' else 'text/plain'
            log.info('put %s/%s', config['bucket'], config['key'])
            log.info(s3.put_object(
                ACL=config['acl'],
                Body=data.encode('utf-8'),
                Bucket=config['bucket'],
                ContentType=content_type,
                    Key=config['key']))
        else:
            log.info('delete %s/%s', config['bucket'], config['key'])
            log.info(s3.delete_object(
                Bucket=config['bucket'],
                Key=config['key']))


@app.task(name='aws.s3-upload')
def run_task(config):
    S3UploadTask(config).run()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'aws-s3-upload'
    S3UploadTask(celeryconfig.config[name]).run(consume=False)

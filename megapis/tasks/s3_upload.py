import json

import boto3

from megapis.tasks.task_base import TaskBase

DEFAULT_CONFIG = {
    'bucket': 'bucket',
    'key': 'filename',
    'acl': 'public-read',
    'transform': 'string',
    'profile': 'megapis',
    'content_type': 'text/plain'
}

TRANSFORMS = {
    'string': str,
    'json': json.dumps
}

class S3UploadTask(TaskBase):
    '''transform data and upload to S3; delete if empty'''
    def __str__(self):
        return 'S3UploadTask'

    def __init__(self, config):
        self.default_config = DEFAULT_CONFIG
        super(S3UploadTask, self).__init__(config)

    def run(self, data):
        '''transform array and upload to S3; delete if empty'''
        print('upload to %s/%s' % (self.config['bucket'], self.config['key']))
        boto3.setup_default_session(profile_name=self.config['profile'])
        s3 = boto3.client('s3')
        if data:
            output = TRANSFORMS[self.config['transform']](data)
            content_type = self.config['content_type']
            print('put %s/%s as %s' % (
                self.config['bucket'], self.config['key'], content_type))
            print(s3.put_object(
                ACL=self.config['acl'],
                Body=output.encode('utf-8'),
                Bucket=self.config['bucket'],
                ContentType=content_type,
                Key=self.config['key']))
            print('https://%s.s3.amazonaws.com/%s' % (self.config['bucket'], self.config['key']))
        else:
            print('delete %s/%s' % (self.config['bucket'], self.config['key']))
            print(s3.delete_object(
                Bucket=self.config['bucket'],
                Key=self.config['key']))

'''
    run task sequences

    sequence.run_sequence('steam-library')
'''
import argparse
import os
import sys
import time

from megapis.tasks.goodreads import GoodreadsTask
from megapis.tasks.hbs_to_html import HbsToHtmlTask
#from megapis.tasks.local_file import LocalFileTask
from megapis.tasks.prime_books import PrimeBooksTask
from megapis.tasks.parse_rss import RssTask
from megapis.tasks.s3_upload import S3UploadTask
from megapis.tasks.steam_library import SteamLibraryTask
from megapis.tasks.steam_new_releases import SteamNewReleasesTask

SEQUENCES = {
    'goodreads': [GoodreadsTask, S3UploadTask],
    'prime-books': [PrimeBooksTask, S3UploadTask],
    'rss': [RssTask, S3UploadTask],
    'rss-e': [RssTask, S3UploadTask],
    'steam-library': [SteamLibraryTask, S3UploadTask],
    'steam-new-releases': [SteamNewReleasesTask, HbsToHtmlTask, S3UploadTask],
}

def run(tasks, config):
    '''run a list of tasks'''
    ts = time.time()
    data = None
    for task in tasks:
        task_obj = task(config)
        print('\nrun %s\n' % task_obj)
        data = task_obj.run(data)
    print('\ndone %s tasks in %ss' % (len(tasks), time.time() - ts))

'''
    command line
    get config from localconfig
'''
def run_sequence(name):
    if name not in SEQUENCES:
        print('ERROR: %s not found' % name)
        sys.exit(1)

    # load config from file
    try:
        from megapis.localconfig import TASKS_CONFIG # pylint: disable=wrong-import-position
    except ImportError:
        print('error importing localconfig')
        sys.exit(1)
    # run
    print('sequence=%s\nconfig=%s' % (
        [str(seq) for seq in SEQUENCES[name]],
        TASKS_CONFIG.get(name, {})))
    run(SEQUENCES[name], TASKS_CONFIG.get(name, {}))

if __name__ == '__main__':
    # get task to run
    parser = argparse.ArgumentParser(description='Run task')
    parser.add_argument('task', help='task name')
    args = parser.parse_args()
    run_sequence(args.task)

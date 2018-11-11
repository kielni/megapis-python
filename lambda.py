import os

from megapis import sequence as seq

'''
    AWS lambda entry functions

    get config from environment
'''

def _assemble_config(name):
    '''fix up environment variables

    AWS Lambda environment variables must be < 256 characters and
    must satisfy regular expression pattern:  ^([\p{L}\p{Z}\p{N}_.:/=+\-@]*)$]
    - combine name[0-9] environment variables into name
    - convert :: to | as used by tasks
    '''
    val = ''
    for i in range(10):
        key = '%s%i' % (name, i)
        if key in os.environ:
            print('adding %s to %s' % (key, name))
            val += os.environ[key]
    val = val.replace('::', '|')
    os.environ[name] = val
    print('environment: %s' % (os.environ))


def steam_new_releases(event=None, context=None): #pylint: disable=unused-argument
    '''Handler: lambda.steam_new_releases'''
    _assemble_config('exclude')
    seq.run(seq.SEQUENCES['steam-new-releases'], os.environ)

def steam_library(event=None, context=None): #pylint: disable=unused-argument
    '''Handler: lambda.steam_library'''
    _assemble_config('excludeTags')
    seq.run(seq.SEQUENCES['steam-library'], os.environ)

def rss(event=None, context=None): #pylint: disable=unused-argument
    seq.run(seq.SEQUENCES['rss'], os.environ)

def rss_evan(event=None, context=None): #pylint: disable=unused-argument
    seq.run(seq.SEQUENCES['rss-evan'], os.environ)

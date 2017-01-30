from copy import copy

from .config import config

broker_url = 'redis://'

task_serializer = 'json'
accept_content = ['json']
timezone = config.get('timezone', 'America/Los_Angeles')
enable_utc = True
imports = config.get('imports', ())

global_config = config.get('global', {'redis': {'host': 'localhost', 'port': 6379}})

'''
    'task-key': {
        'task': 'task-name',  # must match @app.task(name=...)
        'schedule': crontab(hour=7, minute=0, day_of_week=1),
        'config': {  # task-specific config
            'user_id': '123',
            'api_key': 'abcdef',
            ...
        }
    },

'''
tasks = config.get('tasks', {})

beat_schedule = {}
for task_key in tasks:
    task = tasks[task_key]
    # skip config-only tasks
    if not task.get('schedule'):
        continue
    config = copy(global_config)
    config.update(task.get('config', {}))
    config['name'] = task_key
    beat_schedule[task_key] = {
        'task': task['task'],
        'schedule': task['schedule'],
        'args': [config]
    }

config = {}
for task_key in beat_schedule:
    config[task_key] = beat_schedule[task_key]['args'][0]

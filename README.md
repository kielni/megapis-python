# Megapis python

Run tasks with [http://www.celeryproject.org](celery)

## Setup

`source venv/bin/activate`

in [megapis](megapis):

    pip install -e .

configure tasks in `config.py`

example:

```
from celery.schedules import crontab


MEGAPIS = {
    'timezone': 'America/Los_Angeles',
    'imports': (
        'megapis.tasks.goodreads.readnext',
        'megapis.tasks.aws.s3upload',
    ),
    'tasks': {
        'goodreads-read-next': {
            'task': 'goodreads.read-next',
            'schedule': crontab(hour=7, minute=0, day_of_week=1),
            'config': {
                'user_id': '123',
                'api_key': 'abc456',
                'output': 'goodreads-upload',
                'books': 200,
                'exclude_url': 'https://my-db.firebaseio.com/goodreads/exclude.json'
            }
        },
```

## Run

with celery:

    ./start.sh

command line:

    $ cd tasks/goodreads
    $ python3 readnext.py

## Create a task

- copy [megapis/tasks/template.py](template.py) to a new directory under [megapis/tasks](megapis/tasks)
- fill in the `run` method
- add config to `config.py`

[megapis/task.py](MegapisTask) base class provides methods to read and write data from a Redis store.

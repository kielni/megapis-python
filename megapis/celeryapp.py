from celery import Celery

app = Celery('megapis')
app.config_from_object('megapis.celeryconfig')
if __name__ == '__main__':
    app.start()

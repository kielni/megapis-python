import logging
import sys

from celery.utils.log import get_task_logger
import requests

from megapis.celeryapp import app
from megapis import celeryconfig
from megapis.task import MegapisTask

logging.basicConfig(level=logging.DEBUG)
log = get_task_logger(__name__)

class NationalPriceCheckTask(MegapisTask):
    default_config = {
        'notify_body': '{item} now {current} (was {previous})',
        'car_type': 'Midsize'
    }

    def run(self):
        config = self.config
        prices_key = self.read(config['name'])
        prices = prices_key[0] if len(prices_key) else {}
        current = get_current(config)
        car_type = config['car_type']
        if not current:
            log.warning('%s car not found', car_type)
            return
        prev = prices.get(car_type, 999999)
        log.info('%s: was %s, now %s', car_type, prev, current)
        if config.get('notify') and current < prev:
            if car_type not in prices:
                prev = 'unknown'
            prices[car_type] = current
            tag = 'National %s car' % car_type
            body = config['notify_body'].format(item=tag, previous=prev,
                                                current=current)
            headers = {}
            if config.get('notify_content_type'):
                headers['Content-Type'] = config['notify_content_type']
            resp = requests.post(url=config['notify'], data=body, headers=headers)
            log.info('sent %s to %s:\n%s', body, config['notify'], resp.text)
        self.replace(config['name'], [prices])


def get_current(details):
    s = requests.Session()
    # start session
    s.get('https://www.nationalcar.com/en_US/car-rental/home.html')
    # get token
    r = s.get('https://www.nationalcar.com/content/data/apis/live/loyalty/common/getLoginMessages.sfx.json/channelName%3Dnationalcar_com/locale%3Den_US.json?state=anon')
    dropoff_key = 'dropoff_location' if 'dropoff_location' in details else 'pickup_location'
    data = {
        'pickUpLocation.searchCriteria': details['pickup_location'],
        'returnToSameLocation': 'on',
        'dropOffLocation.searchCriteria': details[dropoff_key],
        'pickUpDateTime.date': details['pickup_date'],
        'pickUpDateTime.time': details['pickup_time'],
        'pickUpDateTime.blackOut': '',
        'dropOffDateTime.date': details['dropoff_date'],
        'dropOffDateTime.time': details['dropoff_time'],
        'dropOffDateTime.blackOut': '',
        'renterAge': '25',
        'customerNumberDeeplinked': False,
        'customerNumber': '',
        'enableReservationReset': True,
        'homepage': True,
        'secureToken': r.json()['secureToken']
    }
    # submit step 1
    s.post('https://www.nationalcar.com/content/data/apis/live/reservation/start/submit.sfx.json/channelName%3Dnationalcar_com/locale%3Den_US.json',
        data=data)
    # get results
    r = s.get('https://www.nationalcar.com/content/data/apis/live/reservation/vehicleList.sfx.json/channelName%3Dnationalcar_com/locale%3Den_US.json')
    for car in r.json()['vehicleSummary']['vehicleDetail']:
        log.debug('%s = %s', car['name'], car['vehicleRate']['totalPrice'])
        if car['name'] == details['car_type']:
            return float(car['vehicleRate']['totalPrice'])
    return None


@app.task(name='national-price-check.check')
def run_task(config):
    NationalPriceCheckTask(config).run()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'national-price-check'
    task_config = celeryconfig.config[name]
    task_config['name'] = name
    NationalPriceCheckTask(task_config).run()

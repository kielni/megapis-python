# National price check

Check price on National car rental and notify if price is lower than last check.

## config

- `pickup_location` - location name
- `pickup_date` - mm/dd/yyyy
- `pickup_time` - hhmm, in 24 hour time
- `dropoff_date` - mm/dd/yyyy
- `dropoff_time` - hhmm, in 24 hour time
- `car_type` - car category; default Midsize
- `notify` - where to POST `notify_body` content on lower price
- `notify_body` - string to send with notification; can include `{item}`, `{previous}`, and `{current}` replacements
- `notify_content_type` - value for Content-Type header on POST

# Amazon price check

Check Amazon prices on a list of products and notify if price is lower than last time.

## config

- `items` - dict of {'key': 'url'}
- `notify` - where to POST `notify_body` content on lower price
- `notify_body` - string to send with notification; can include `{item}`, `{previous}`, and `{current}` replacements
- `notify_content_type` - value for Content-Type header on POST

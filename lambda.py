import json
import os

from megapis import sequence as seq

"""
    AWS lambda entry functions

    get config from environment
"""


def _assemble_config(name):
    """fix up environment variables

    AWS Lambda environment variables must be < 256 characters and
    must satisfy regular expression pattern:  ^([\\p{L}\\p{Z}\\p{N}_.:/=+\-@]*)$]
    - combine name[0-9] environment variables into name
    - convert :: to | as used by tasks
    """
    val = ""
    for i in range(10):
        key = "%s%i" % (name, i)
        if key in os.environ:
            print("adding %s to %s" % (key, name))
            val += os.environ[key]
    val = val.replace("::", "|")
    os.environ[name] = val
    print("environment: %s" % (os.environ))


def steam_new_releases(event=None, context=None):  # pylint: disable=unused-argument
    """Handler: lambda.steam_new_releases"""
    _assemble_config("exclude")
    seq.run(seq.SEQUENCES["steam-new-releases"], os.environ)


def steam_library(event=None, context=None):  # pylint: disable=unused-argument
    """Handler: lambda.steam_library"""
    _assemble_config("excludeTags")
    seq.run(seq.SEQUENCES["steam-library"], os.environ)


def rss(event=None, context=None):  # pylint: disable=unused-argument
    seq.run(seq.SEQUENCES["rss"], os.environ)


def rss_evan(event=None, context=None):  # pylint: disable=unused-argument
    seq.run(seq.SEQUENCES["rss-evan"], os.environ)


def rss_refresh(event=None, context=None):
    keys = os.environ["keys"].split(",")
    for key in keys:
        # set source URL
        os.environ["sources"] = "%s/rss/sources-%s.json" % (os.environ["base_url"], key)
        os.environ["key"] = "rss/rss-%s.json" % key
        print("refresh %s from %s" % (os.environ["key"], os.environ["sources"]))
        seq.run(seq.SEQUENCES["rss"], os.environ)


def rss_api(event=None, context=None):
    """run RSS method via AWS API gateway

    POST /feed
        action={refresh,update}
        key=whitelisted_key
    for update:
        source=url
        name=name
        hide=true|false
    """
    print("lambda.rss_api: body=%s" % event.get("body", "{}"))
    # 'body': '{"key":"evan","action":"refresh"}'
    if not event or not event.get("body"):
        print("invalid event")
        return
    body = json.loads(event["body"])
    os.environ.update(body)

    # get and validate key
    key = body.get("key", "")
    keys = os.environ["keys"].split(",")
    if key not in keys:
        print("invalid key %s" % key)
        return

    # run sequence
    sequence = None
    action = body.get("action", "")
    if action == "refresh":
        # set source URL
        os.environ["sources"] = "%s/rss/sources-%s.json" % (os.environ["base_url"], key)
        os.environ["key"] = "rss/rss-%s.json" % key
        sequence = "rss"
    if action == "update":
        os.environ["key"] = "rss/sources-%s.json" % key
        sequence = "rss-sources"
    print("action=%s sequence=%s environ=%s" % (action, sequence, os.environ))
    if not sequence:
        print("invalid action %s" % action)
        return
    result = seq.run(seq.SEQUENCES[sequence], os.environ)
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": result,
    }

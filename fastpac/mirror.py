from requests import get as get_response
from fastpac.util import aslist
import json

def get(url):
    return get_response(url).content

def is_mirror_https(mirror):
    # Explicit param
    if "protocol" in mirror:
        return mirror["protocol"] == "https"

    # Based of url
    return mirror["url"].startswith("https")


def get_mirrorlist_online(url, https=True, sort=None):
    mirrors = json.loads(get(url))["urls"]

    if sort:
        mirrors = sorted(mirrors, key=lambda x: x[sort])

    for mirror in mirrors:
        if not mirror["url"].startswith("http"):
            continue

        if https:
            if is_mirror_https(mirror):
                yield mirror["url"]
        else:
            yield mirror["url"]


@aslist
def parse_mirrorlist(raw_text):
    for line in raw_text.split("\n"):
        if not line.startswith("Server"):
            continue

        # "Server = http://a/sub/$repo/os/$arch"
        # 1. Get the string behind the equal sign
        # " http://a/sub/$repo/os/$arch"
        # 2. Remove any whitespace
        # "http://a/sub/$repo/os/$arch"
        # 3. Remove $repo/o...
        # "http://a/sub/"
        #
        #         |      1.      |    2.    |             3.             |
        yield line.split("=")[-1].strip(" ").replace("$repo/os/$arch", "")


def get_mirrorlist_offline(path="/etc/pacman.d/mirrorlist"):
    with open(path) as f:
        return [e for e in parse_mirrorlist(f.read()) if is_mirror_https({"url": e})]

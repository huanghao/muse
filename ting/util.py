import os
import sys
import time
import urllib2
from urlparse import urlparse

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno != 17: # OSError: [Errno 17] File exists:
            raise

def get_key(url):
    com = urlparse(url)
    path = os.path.join(CACHE_DIR, com.netloc, com.path.strip('/'))
    if com.query:
        path = os.path.join(path, com.query)
    return path

def is_cached(key):
    return os.path.exists(key)

def write_cache(key, content):
    path = os.path.dirname(key)
    makedirs(path)
    with open(key, 'w') as f:
        f.write(content)

def read_cache(key):
    with open(key) as f:
        return f.read()

def clean_cache(key):
    if is_cached(key):
        os.unlink(key)

def wget(url, force=False):
    key = get_key(url)
    if is_cached(key):
        if not force:
            return read_cache(key)
        clean_cache(key)

    time.sleep(.5)
    print >> sys.stderr, 'getting', url
    page = urllib2.urlopen(url).read()
    write_cache(key, page)
    return page



if __name__ == '__main__':
    key = get_key('http://music.baidu.com/data/user/getalbums?start=30&ting_uid=4596')
    #ParseResult(scheme='http', netloc='music.baidu.com', path='/data/user/getalbums', params='', query='start=30&ting_uid=4596', fragment='')
    key = get_key('http://music.baidu.com/album/10486848')
    print key
    if is_cached(key):
        print read_cache(key)
    else:
        write_cache(key, 'a')

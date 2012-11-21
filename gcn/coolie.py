#coding: utf8
import os
os.environ['DJANGO_SETTINGS_MODULE'] = "orpheus.settings"

import time, datetime, sys, urllib, traceback, urllib2
from Queue import Empty
from multiprocessing import Queue, Process

from orpheus.gcn.models import URLQueue


DOWNLOAD_DIR = '/home/huanghao/workspace/orpheus/cache/download'

COOLIES = 2
QUEUE_SIZE = 200
RETRY_TIMES = 3
CHECK_INTERVAL = 10
BULK_SIZE = 20
COOLIE_REST = 10



def trim_name(url):
    return urllib.unquote(str(url.split('/')[-1])).decode('utf8')


def trim_path(url):
    dirname = os.path.join(DOWNLOAD_DIR,
                           url.url_hash[:-4],
                           url.url_hash[-4:-2],
                           url.url_hash[-2:])
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError:
            pass
    basename = trim_name(url.url)
    fname = os.path.join(dirname, basename)
    return fname


def download(url):
    url.start = datetime.datetime.now()
    path = trim_path(url)

    with open(path, 'w') as f:
        f.write(urllib2.urlopen(url.url).read())

    url.duration = (datetime.datetime.now() - url.start).seconds
    url.path = path
    url.status = 0
    


def coolie(pending, done):
    def get_from_pending():
        retried = 0
        url = None
        while True:
            if retried >= RETRY_TIMES:
                print 'coolie no work to do'
                break
            try:
                url = pending.get(timeout=CHECK_INTERVAL)
            except Empty:
                retried += 1
            else:
                break
        return url
    
    def put_2_done(url):
        try:
            download(url)
            url.status = 2
        except Exception, e:
            url.status = 3
            url.age += 1
            print >> sys.stderr, url.id, e
            traceback.print_exc()
        done.put(url)
            
    while True:
        url = get_from_pending()
        if url:
            put_2_done(url)
        time.sleep(COOLIE_REST)

    print 'coolie exit', os.getpid()


def foreman(pending, done):
    def write_done_2_db():
        while True:
            try:
                u = done.get(timeout=CHECK_INTERVAL)
            except Empty:
                break
            u.save()
    
    def get_from_db():
        retried = 0
        urls = []
        
        while True:
            if retried >= RETRY_TIMES:
                print 'foreman no work to do'
                break
            write_done_2_db()
            
            urls = URLQueue.objects.filter(status=0).order_by('age')[:BULK_SIZE]
            if urls:
                break
            
            retried += 1
            time.sleep(CHECK_INTERVAL)
        return urls
    
    def put_2_pending(urls):
        for u in urls:
            u.status = 1
            u.age += 1
            u.save()
            pending.put(u)
    
    while True:
        write_done_2_db()
        urls = get_from_db()
        put_2_pending(urls)
    
    print 'foreman exit', os.getpid()


def main():
    pending = Queue(QUEUE_SIZE)
    done = Queue(BULK_SIZE)
    ps = [ Process(target=foreman, args=(pending,done)) ] + \
        [ Process(target=coolie, args=(pending,done)) for _ in range(COOLIES)]

    for p in ps:
        p.start()
    for p in ps:
        p.join()



if __name__ == '__main__':
    main()
import os
import time
from pprint import pprint as pp
import sqlite3

from load2db import DBNAME, fetch_download_url
from utils import makedirs


COLS = ('id', 'done', 'priority', 'fname', 'singer', 'album', 'path', 'url', 'songid')

def main():
    conn = sqlite3.connect(DBNAME, isolation_level=None)
    c = conn.cursor()
    while 1:
        c.execute('select * from jobs where done==0 or done==-1 order by priority desc limit 1')
        row = c.fetchone()
        if not row:
            print 'work done'
            break
        item = dict(zip(COLS, row))
        pp(item)

        for i in range(2):
            ret = download(item)
            if ret == 0:
                c.execute('update jobs set done=1 where id=?', (item['id'],))
                time.sleep(5)
                break
            elif ret == 1536:
                url = fetch_download_url(item['songid'], True)
                c.execute('update jobs set done=-1,url=? where id=?', (url, item['id'],))
                print 'update url from %s to %s' % (item['url'], url)
                break
            time.sleep(5)
            print 'try again'

        if i==2 and ret !=0:
            c.execute('update jobs set done=-2 where id=?', (item['id'],))
            print 'tried 3 times but still failed, exit ...'
            break


COOKIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookie.txt')
def download(item):
    path = item['path']
    if not os.path.exists(path):
        makedirs(path)

    cmd = 'cd "%s"; wget --no-cookies --header "Cookie: $(cat %s)" "%s" ' % (item['path'], COOKIE, item['url'])
    if item['fname']:
        cmd += '-O "%s"' % item['fname']
    print cmd
    print
    ret = os.system(cmd)
    print 'EXIT CODE:', ret
    return ret



if __name__ == '__main__':
    main()

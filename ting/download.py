import os
import time
from pprint import pprint as pp
import sqlite3

from load2db import DBNAME, fetch_download_url
from utils import makedirs


COLS = ('id', 'done', 'priority', 'fname', 'singer', 'album', 'path', 'url', 'songid')
NAP = 1
MAX_TRY = 2

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

        if not item['url'] and not item['songid']:
            print 'insane'
            c.execute('update jobs set done=-2 where id=?', (item['id'],))
            continue

        elif not item['url']:
            item['url'] = fetch_download_url(item['songid'])
            c.execute('update jobs set url=? where id=?', (item['url'], item['id'],))

        for i in range(MAX_TRY):
            ret = download(item)
            if ret == 0:
                c.execute('update jobs set done=1 where id=?', (item['id'],))
                time.sleep(NAP)
                break
            elif ret == 1536:
                url = fetch_download_url(item['songid'], True)
                c.execute('update jobs set done=-1,url=? where id=?', (url, item['id'],))
                print 'update url from %s to %s' % (item['url'], url)
                break
            time.sleep(5)
            print 'try again'

        if i==MAX_TRY-1 and ret !=0:
            c.execute('update jobs set done=-3 where id=?', (item['id'],))
            print 'tried 3 times but still failed, exit ...'


COOKIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookie.txt')
def download(item):
    path = item['path']
    if not os.path.exists(path):
        makedirs(path)

    #cmd = 'cd "%s"; wget --no-cookies --header "Cookie: $(cat %s)" "%s" ' % (item['path'], COOKIE, item['url'])
    cmd = 'cd "%s"; wget "%s" ' % (item['path'], item['url'])
    if item['fname']:
        cmd += '-O "%s"' % item['fname']
    print cmd
    print
    ret = os.system(cmd.encode('utf8'))
    print 'EXIT CODE:', ret
    return ret

#TODO:
#save exit code into db
#save time info, start time, cost, speed
#shell esc
#status check, todo, done, error, avg time
#album cover url


if __name__ == '__main__':
    main()

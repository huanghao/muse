import os
import time
from pprint import pprint as pp
import sqlite3

from load2db import DBNAME
from utils import makedirs


COLS = ('id', 'done', 'priority', 'fname', 'singer', 'album', 'path', 'url',)

def main():
    conn = sqlite3.connect(DBNAME, isolation_level=None)
    c = conn.cursor()
    while 1:
        c.execute('select * from jobs where done=0 order by priority desc limit 1')
        row = c.fetchone()
        if not row:
            print 'work done'
            break
        item = dict(zip(COLS, row))
        pp(item)

        failed = True
        for i in range(2):
            if download(item):
                c.execute('update jobs set done=1 where id=?', (item['id'],))
                failed = False
                time.sleep(5)
                break
            time.sleep(5)
            print 'try again'

        if failed:
            c.execute('update jobs set done=-1 where id=?', (item['id'],))
            print 'tried 3 times but still failed, exit ...'
            break


def download(item):
    path = item['path']
    if not os.path.exists(path):
        makedirs(path)

    cmd = 'cd "%s"; wget "%s" ' % (item['path'], item['url'])
    if item['fname']:
        cmd += '-O "%s"' % item['fname']
    print cmd
    print
    return os.system(cmd) == 0



if __name__ == '__main__':
    main()

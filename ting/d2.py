import os
import time
import sqlite3
import argparse

from util import makedirs, wget

from BeautifulSoup import BeautifulSoup as BS


BASE = 'http://music.baidu.com'

def parse_download(html):
    soup = BS(html)
    return soup.find('a', 'btn-download')['href'].strip()

def fetch_download_url(songid, force=False):
    dlink = '%s%s/download' % (BASE, songid)
    page = wget(dlink, force)
    return BASE + parse_download(page)

def getopt():
    parser = argparse.ArgumentParser(description='ting mp3 downloader')
    parser.add_argument('db', nargs='?', default='songs.db', type=os.path.abspath, help='db file')
    return parser.parse_args()

def download(item):
    path = item['path']
    if not os.path.exists(path):
        makedirs(path)

    cmd = 'cd "%s"; wget "%s" ' % (item['path'], item['url'])
    if item['fname']:
        cmd += '-O "%s"' % item['fname']
    print cmd
    return os.system(cmd.encode('utf8'))

def get_file_size(item):
    path, fname = item['path'], item['fname']
    if not fname:
        return -1
    path = os.path.join(path, fname)
    return os.stat(path).st_size

def main():
    args = getopt()

    conn = sqlite3.connect(args.db, isolation_level=None)
    c = conn.cursor()
#TODO:
#status check, todo, done, error, avg time
#load into a named db
#duplicate detect

    def update(id, **kw):
        sql = ['update jobs set']
        vals = []
        for k,v in kw.iteritems():
            sql.append('%s=?' % k)
            vals.append(v)
        sql.append('where id=?')
        vals.append(id)
        sql = ' '.join(sql)
        return c.execute(sql, vals)

    COLS = ('id', 'done', 'priority', 'fname', 'singer', 'album', 'path', 'url', 'songid')

    while 1:
        c.execute('select * from jobs where done==0 or done==2 order by priority desc limit 1')
        row = c.fetchone()
        if not row:
            break
        item = dict(zip(COLS, row))

        for k,v in item.iteritems():
            print '%s: %s' % (k, v.encode('utf8') if isinstance(v, unicode) else str(v))

        id, url, songid = item['id'], item['url'], item['songid']

        if not url and not songid:
            update(id, done=-1)
            continue

        if not url:
            url = fetch_download_url(songid)
            update(id, url=url)

        at = time.time()
        ret = download(item)
        cost = time.time() - at

        changes = {'at': at, 'cost': cost}
        if ret == 0:
            update(id, done=1, size=get_file_size(item), **changes)
            time.sleep(1)
        elif ret == 1536:
            url = fetch_download_url(songid, True)
            update(id, url=url, done=2, **changes)
            print 'update url from %s to %s' % (item['url'], url)
        else:
            update(id, done=-2, code=ret, **changes)
            print '!!!! error:EXIT CODE:', ret
            time.sleep(5)


if __name__ == '__main__':
    main()
    print 'ALL DONE'

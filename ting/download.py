#!/usr/bin/env python
import os
import time
import pprint
import sqlite3
import argparse
from BeautifulSoup import BeautifulSoup as BS
from util import makedirs, wget, fetch


BASE = 'http://music.baidu.com'
NAP = 1
MAX_TRY = 2

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

def main():
    args = getopt()

    cols = ('id', 'done', 'priority', 'fname', 'singer', 'album', 'path', 'url', 'songid')
    conn = sqlite3.connect(args.db, isolation_level=None)
    c = conn.cursor()
    while 1:
        c.execute('select * from jobs where done==0 or done==-1 order by priority desc limit 1')
        row = c.fetchone()
        if not row:
            print 'work done'
            break
        item = dict(zip(cols, row))
        pprint.pprint(item)

        if not item['url'] and not item['songid']:
            print 'insane'
            c.execute('update jobs set done=-2 where id=?', (item['id'],))
            continue

        elif not item['url']:
            item['url'] = fetch_download_url(item['songid'])
            c.execute('update jobs set url=? where id=?', (item['url'], item['id'],))

        for i in range(MAX_TRY):
            ret = fetch(item['url'], item['path'], item['fname'])
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


#TODO:
#save exit code into db
#save time info, start time, cost, speed
#status check, todo, done, error, avg time
#load into a named db
#duplicate detect


if __name__ == '__main__':
    main()

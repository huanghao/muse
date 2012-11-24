#!/usr/bin/env python
import os
import re
import sys
import json
import string
import sqlite3
import argparse
import itertools
from util import wget, makedirs
from urlparse import urlparse
from pprint import pprint as pp
from BeautifulSoup import BeautifulSoup as BS


BASE = 'http://music.baidu.com'

def esc(txt):
    for ch in '`~$%&@\\*?|<>/="#;':
        txt = txt.replace(ch, '')
    return txt.strip()

def text(node):
    html = str(node)
    html = re.sub(r'<[^>]*>', '', html)
    return html

def parse_album(html):
    soup = BS(html)
    album_name = soup.find('h2', 'album-name').string.strip()
    cover_link = soup.find('span', 'cover').find('img')['src']
    span = soup.find('span', 'author_list')
    try:
        singer = span['title'].strip()
    except KeyError:
        singer = span.find('a')['title'].strip()
    node = soup.find('span', 'description-all')
    if node:
        desc = text(node).strip()
    else:
        desc = None

    alb = {
        'name': album_name,
        'cover': cover_link,
        'singer': singer,
        'desc': desc,
        'links': [],
        }

    for item in soup.findAll('div', 'song-item'):
        idx = item.find('span', 'index-num').string.strip()
        a = item.find('span', 'song-title').find('a')
        href = a['href']
        title = a['title'].strip()

        alb['links'].append({
            'idx': idx,
            'title': title,
            'href': href,
            })

    return alb

def fetch_album(url):
    page = wget(url)
    alb = parse_album(page)

    path = os.path.join(esc(alb['singer']), esc(alb['name']))
    alb['path'] = path

    for link in alb['links']:
        fname = '%s_%s.mp3' % (link['idx'], esc(link['title']))
        link['fname'] = fname

    alb['links'].append({'url': alb['cover']})
    return alb

def init_album(alb):
    path = alb['path']
    makedirs(path)

    with open(os.path.join(path, 'meta'), 'w') as f:
        f.write(json.dumps(alb))

    if alb['desc']:
        with open(os.path.join(path, 'desc'), 'w') as f:
            f.write(alb['desc'])

    '''
id int primary key,

done int, # 0: initial 1:done 2:continue -1:insane <-1: error
code int, # error code

at datetime, # start time
cost int, # seconds
size int, # bytes

priority int key,
singer text,
album text,

path text,
fname text,

url text,
songid text
    '''

def insert_into_db(dbname, alb, priority):
    conn = sqlite3.connect(dbname, isolation_level=None)
    c = conn.cursor()
    try:
        c.execute('select count(*) from jobs where album=?', (alb['name'],))
    except sqlite3.OperationalError:
        c.execute('''create table jobs(
id int primary key,
done int,
priority int key,
fname text,
singer text,
album text,
path text,
url text
,songid text
)''')
        c.execute('select count(*) from jobs where album=?', (alb['name'],))
    if c.fetchone()[0] > 0:
        print 'already in'
        return

    c.execute('select max(id) from jobs')
    old = c.fetchone()[0]
    print 'old max id:', old
    if old:
        id_ = itertools.count(old+1)
    else:
        id_ = itertools.count(1)

    sql = 'insert into jobs(id,done,priority,songid,fname,singer,album,path,url) values(?,?,?,?,?,?,?,?,?)'
    params = [(
        id_.next(),
        0,
        priority,
        job['href'] if 'href' in job else '',
        job['fname'] if 'fname' in job else '',
        alb['singer'],
        alb['name'],
        alb['path'],
        job['url'] if 'url' in job else '',
        ) for job in alb['links'] ]
    c.executemany(sql, params)
    print 'insert %d rows' % len(params)


def getopt():
    parser = argparse.ArgumentParser(description='load download jobs into db')
    parser.add_argument('file_list', nargs='+', type=os.path.abspath, help='files to load')
    parser.add_argument('--priority', type=int, default=0, help='download priority')
    parser.add_argument('--db', type=os.path.abspath, default='songs.db', help='db name')
    return parser.parse_args()

def main():
    args = getopt()

    print 'about to load into db', args.db
    for fname in args.file_list:
        for line in open(fname):
            line = line.strip()
            if line.startswith('#') or not line:
                continue

            url = line
            if not url.startswith(BASE):
                url = BASE + url
            alb = fetch_album(url)
            print '='*10, alb['name']
            init_album(alb)
            insert_into_db(args.db, alb, args.priority)


if __name__ == '__main__':
    main()

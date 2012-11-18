import os
import re
import sys
import json
import string
import sqlite3
import itertools
from utils import wget, makedirs
from urlparse import urlparse
from pprint import pprint as pp
from BeautifulSoup import BeautifulSoup as BS


BASE = 'http://music.baidu.com'
DBNAME = 'songs.db'


def esc(txt):
    txt = txt.strip()
    txt = re.sub(r'[^a-zA-Z0-9_]', '_', txt)
    txt = re.sub(r'_+', '_', txt)
    txt = txt.strip('_')
    return txt


def parse_album(html):
    soup = BS(html)
    album_name = soup.find('h2', 'album-name').string.strip()
    cover_link = soup.find('span', 'cover').find('img')['src']
    singer = soup.find('span', 'author_list')['title'].strip()
    node = soup.find('span', 'description-all')
    if node:
        desc = node.string.strip()
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


def download1(alb):
    yield '''cat > meta <<EOF
%s
EOF''' % json.dumps(alb)

    if alb['desc']:
        yield '''cat > desc <<EOF
%s
EOF''' % alb['desc']

    yield 'wget "%s"' % alb['cover']

    yield 'BASE="%s"' % BASE
    for song in alb['list']:
        yield 'wget "$BASE%s/download" -O %s.download' % (song['href'], song['idx'])
        yield 'sleep 2'


def parse_download(html):
    soup = BS(html)
    return soup.find('a', 'btn-download')['href']


def download2(alb):
    yield 'BASE="%s"' % BASE

    for song in alb['list']:
        fname = '%s.download' % song['idx']
        href = parse_download(open(fname).read())

        fname = '%s_%s.mp3' % (song['idx'], song['title'])
        yield 'wget "$BASE%s" -O "%s"' % (href, fname)
        yield 'sleep 10'


def fetch_album(url):
    page = wget(url)
    alb = parse_album(page)

    path = os.path.join(alb['singer'], alb['name'])
    alb['path'] = path
    alb['jobs'] = jobs = [{'url': alb['cover']}]

    for link in alb['links']:
        dlink = '%s%s/download' % (BASE, link['href'])
        page2 = wget(dlink)
        href = parse_download(page2)
        url = BASE + href
        fname = '%s_%s.mp3' % (link['idx'], link['title'])
        jobs.append({'url': url, 'fname': fname})
    return alb

def init_album(alb):
    path = alb['path']
    makedirs(path)

    with open(os.path.join(path, 'meta'), 'w') as f:
        f.write(json.dumps(alb))

    if alb['desc']:
        with open(os.path.join(path, 'desc'), 'w') as f:
            f.write(alb['desc'])


def insert_into_db(alb, priority):
    conn = sqlite3.connect(DBNAME, isolation_level=None)
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

    sql = 'insert into jobs(id,done,priority,fname,singer,album,path,url) values(?,?,?,?,?,?,?,?)'
    params = [(
        id_.next(),
        0,
        priority,
        job['fname'] if 'fname' in job else '',
        alb['singer'],
        alb['name'],
        alb['path'],
        job['url'],
        ) for job in alb['jobs'] ]
    c.executemany(sql, params)
    print 'insert %d rows' % len(params)


def main():
    if len(sys.argv) > 1:
        priority = int(sys.argv[1])
    else:
        priority = 0

    for line in sys.stdin:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        url = line
        if not url.startswith(BASE):
            url = BASE + url
        alb = fetch_album(url)
        init_album(alb)
        insert_into_db(alb, priority)


if __name__ == '__main__':
    main()

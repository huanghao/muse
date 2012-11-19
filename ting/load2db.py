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
    return txt.strip().replace(os.sep, '_')

def text(node):
    html = str(node)
    html = re.sub(r'<[^>]*>', '', html)
    return html

def parse_album(html):
    soup = BS(html)
    album_name = soup.find('h2', 'album-name').string.strip()
    cover_link = soup.find('span', 'cover').find('img')['src']
    singer = soup.find('span', 'author_list')['title'].strip()
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

def parse_download(html):
    soup = BS(html)
    return soup.find('a', 'btn-download')['href'].strip()

def fetch_download_url(songid, force=False):
    dlink = '%s%s/download' % (BASE, songid)
    page = wget(dlink, force)
    return BASE + parse_download(page)

def fetch_album(url):
    page = wget(url)
    alb = parse_album(page)

    path = os.path.join(esc(alb['singer']), esc(alb['name']))
    alb['path'] = path
    alb['jobs'] = jobs = [{'url': alb['cover']}]

    for link in alb['links']:
        url = fetch_download_url(link['href'], FORCE)
        fname = '%s_%s.mp3' % (link['idx'], esc(link['title']))
        jobs.append({'url': url, 'fname': fname, 'songid': link['href']})
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
        job['songid'] if 'songid' in job else '',
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
        print '='*10, alb['name']
        init_album(alb)
        insert_into_db(alb, priority)


if __name__ == '__main__':
    FORCE = False
    main()

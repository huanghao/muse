#!/usr/bin/env python
import sys
import json
import itertools
from util import wget
from BeautifulSoup import BeautifulSoup as BS


BASE = 'http://music.baidu.com'
URL = BASE + '/data/user/getalbums?start=%d&ting_uid=%s'

def get_albums(ting_uid):
    whole = []
    for start in itertools.count(step=10):
        url = URL % (start, ting_uid)
        page = wget(url)
        albums = parse(page)
        if not albums:
            break
        whole.extend(albums)
    return whole


def parse(page):
    data = json.loads(page)
    html = data['data']['html']
    soup = BS(html)

    alb = []
    for div in soup.findAll('div', 'title'):
        a = div.find('a')
        href = a['href']
        title = a['title']
        alb.append({'title': title, 'href': href})
    return alb


def main():
    albums = get_albums(sys.argv[1])
    for i, alb in enumerate(albums):
        print '#%d: %s' % (i+1, alb['title'].encode('utf8'))
        print BASE + alb['href']



if __name__ == '__main__':
    main()

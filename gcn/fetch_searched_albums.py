#coding: utf8
import os
os.environ['DJANGO_SETTINGS_MODULE'] = "orpheus.settings"

import urllib, sys, re
from pprint import pprint

from utils import urlopen, unescape


cache = {}

def fetch_albums(url):
    html = urlopen(url)

    found = re.findall(r'<td class="Title".*?<a href="/music/url\?q=(/music/album\?id%3D.*?)".*?>(.*?)</a>', html)
    print '# albums:', len(found), urllib.unquote(url)
    for link, title in found:
        link = 'http://www.google.cn'+link.split('&')[0]
        title = unescape(title)
        print urllib.unquote(link), '|', title

    found = re.findall(r'<td>.*?<a class="imglink" href="/music/url\?q=(.*?)"', html)
    pages = [ 'http://www.google.cn'+urllib.unquote(i.split('&amp;')[0]) for i in found ]

    cache[url] = True
    for page in pages:
        if page not in cache:
            cache[page] = False

    another_page = None
    for page, done in cache.iteritems():
        if not done:
            another_page = page
            break

    if another_page:
        fetch_albums(another_page)

    
if __name__ == '__main__':
    fetch_albums(sys.argv[1])

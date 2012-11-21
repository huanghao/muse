#coding: utf8
import os
os.environ['DJANGO_SETTINGS_MODULE'] = "orpheus.settings"

import urllib, sys, re

from utils import urlopen, unescape


def trim_title(html):
    title = re.findall(r'<title>(.*)',
                       html.split('</title>', 1)[0])[0]
    return unescape(title.split('- 谷歌', 1)[0].strip())


def artist(url):
    html = urlopen(url)
    
    found = re.findall(r'<a href="/music/url\?q=(/music/album\?.*?)&.*?>(.*?)</a>',
                       html.split('所有专辑', 1)[1])
    albums = dict(found)
    artist = trim_title(html)
    print artist, 'albums', len(albums)
    
    for href, title in sorted(albums.items(), lambda i,j: cmp(i[1],j[1])):
        url = 'http://www.google.cn%s' % urllib.unquote(href)
        print '%s |%s' % (url, unescape(title))

    
if __name__ == '__main__':
    artist(sys.argv[1])

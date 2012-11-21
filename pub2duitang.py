#coding: utf8
import urllib2
import urllib
import os
import re
from urlparse import urlparse
import time
import getopt
import sys

from lxml import etree, html
from lxml.cssselect import CSSSelector as sel


def esc_tag(tag):
    return tag.strip().replace(' ', '_').replace('\t', '_').replace('\n', '_')

def fetch(url):
    fname = os.path.join('cache', os.path.basename(url.rstrip('/')))
    if os.path.exists(fname):
        page = open(fname).read()
    else:
        page = urllib2.urlopen(url).read()
        with open(fname, 'w') as f:
            print >> f, page
    return page


def wsj(url):
    page = fetch(url)
    dom = html.fromstring(page)
    title = sel('title')(dom)[0].text
    tags = map(esc_tag,
        title.replace(u'：', '|').replace('-', '|').replace('_', '|').split('|'))

    pics = []
    items = sel('#sliderBox li')(dom)
    sz = len(items)
    for i, li in enumerate(items):
        img = sel('img')(li)[0]
        p = sel('p')(li)[0]
        src = img.attrib['src']
        src = '/'.join(filter(lambda i: i != '..', src.split('/')))
        img = 'http://cn.wsj.com/%s' % src
        msg = '(%d/%d) %s' % (i+1, sz, p.text)

        yield title, tags, url, msg, img


def padmag(url):
    page = fetch(url)
    dom = html.fromstring(page)
    title = sel('title')(dom)[0].text.strip()
    tags = map(esc_tag, title.split(' - '))

    def extract_desc():
        desc = []

        def exclude(a):
            for k in ['attachment_id=', 'tag=', 'cat=']:
                if a.find(k) >= 0:
                    return True
            return False

        for p in sel('div.content p')(dom):
            if p.text:
                desc.append(p.text)
            for a in sel('a')(p):
                href = a.attrib['href']
                if href and not exclude(href):
                    desc.append(href)

        return '\n'.join(filter(None, map(lambda i:i.strip(), desc)))

    desc = extract_desc()
    pics = []
    i = 1
    for img in sel('div.content img')(dom):
        src = img.attrib['src']
        if not src.startswith('http://www.padmag.cn/wp-content/'):
            continue
        msg = '(%d): %s' % (i, desc)
        i += 1
        yield title, tags, url, msg, src

def leica(url):
    page = fetch(url)
    dom = html.fromstring(page)
    title = sel('title')(dom)[0].text.strip()
    pos = title.find(u'』')
    tags = map(esc_tag, [title[:pos+1], title[pos+1:], u'Leica中文摄影杂志'])

    pics = []
    for i, img in enumerate(sel('p img.insertimage')(dom)):
        src = img.attrib['src']
        msg = '[%d]%s' % (i+1, title)
        yield title, tags, url, msg, src



url_add = 'http://www.duitang.com/people/mblog/add/'
headers = {
    'Origin': 'http://www.duitang.com',
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7',
    'Referer': 'http://www.duitang.com/collect/',
    'Cookie': 'sessionid=fcdf6b64128cd278e67b18d571ece126; sg=prenum%3D1; csrftoken=d85d0975a7ea0fc56368d9feb080b2c7; js=1; sgm=usedtags%3D%25u5BB6%25u5C45%253B%25u8BBE%25u8BA1%253B%25u63D2%25u753B%253B%25u7535%25u5F71%253B%25u65C5%25u884C%253B%25u624B%25u5DE5%253B%25u5973%25u88C5%253B%25u7537%25u88C5%253B%25u914D%25u9970%253B%25u7F8E%25u98DF%253B%25u6444%25u5F71%253B%25u827A%25u672F%253B%257C%253Btags_test%253B2012%253B%25u91D1%25u5BB6%25u738B%25u671D%253B%25u548C%25u4F60%25u5728%25u4E00%25u8D77%253B%25u9648%25u7EEE%25u8D1E%253B%25u5409%25u4ED6%25u8C31%253B%25u4F0A%25u62C9%25u514B%25u6218%25u4E89%253B%25u5C01%25u9762%253B%25u52A8%25u6F2B%253B%25u6000%25u65E7%253B%25u8857%25u62CD%253B%25u5C0F%25u5B69%253B%25u5BA0%25u7269%253B%25u690D%25u7269%253B%25u4EBA%25u7269%253B%25u5C01%25u9762%253B%25u52A8%25u6F2B%253B%25u6000%25u65E7%253B%25u8857%25u62CD%253B%25u5C0F%25u5B69%253B%25u5BA0%25u7269%253B%25u690D%25u7269%253B%25u4EBA%25u7269; __utma=74400135.1325608017.1323870708.1326015370.1326027384.18; __utmb=74400135.17.10.1326027384; __utmc=74400135; __utmz=74400135.1326027384.18.13.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/',
    }

def duitang(items):

    for title, tags, url, msg, img in items:
        tag = ' '.join(tags)
        data = [(k,v.encode('utf8') if isinstance(v, unicode) else str(v)) for k,v in {
            'source_title': title,
            'tags': tag,
            'source_link': url,
            'msg': msg,
            'image_src': img,
            'csrfmiddlewaretoken': 'd85d0975a7ea0fc56368d9feb080b2c7',
            'source': 'tool',
            'album': '',
            'photo_id': '',
            'group': '',
            }.items()]

        if DRY:
            print 'sending...', '-'*40
            print '\n'.join([('%s=%s' % (k,v)) for k,v in data])
        else:
            post = urllib.urlencode(data)
            req = urllib2.Request(url_add, post, headers)
            print urllib2.urlopen(req).read()
            time.sleep(30)


if __name__ == '__main__':
    DRY = False

    opts, args = getopt.getopt(sys.argv[1:], "n")
    for opt, val in opts:
        if opt == '-n':
            DRY = True

    site, url = args[:2]
    parser = locals()[site]
    duitang(parser(url))

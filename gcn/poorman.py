#coding: utf8
import os
os.environ['DJANGO_SETTINGS_MODULE'] = "orpheus.settings"

import urllib, re, hashlib, sys, time, datetime, getopt
#from MySQLdb import IntegrityError
from django.db.utils import IntegrityError

from orpheus.gcn.models import Gotcha
from utils import urlopen, unescape


DOWNLOAD_DIR = 'cache/download'
DEBUG = False

def trim_name(url):
    return urllib.unquote(str(url.split('/')[-1])).decode('utf8')

def url2fname(url, url_hash):
    dirname = os.path.join(DOWNLOAD_DIR,
                           url_hash[-6:-4],
                           url_hash[-4:-2],
                           url_hash[-2:])
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError:
            pass
    basename = trim_name(url)
    fname = os.path.join(dirname, basename)
    return fname


def gotcha(album_url):
    html = urlopen(album_url)
    name = re.findall(r'<span class="Title">(.*?)</span>', html)[0]
    desc = re.findall(r'<td .*? class="Description">(.*?)</td>', html, re.S)[0]
    match = re.findall(r'歌手.*?(<a .*?>(.*?)</a>|<span.*?>(.*?)</span>)', desc, re.S)[0]
    singer = match[1] or match[2]
    y,m,d = re.findall(r'出版时间.*?(\d+)&#24180;(\d+)&#26376;(\d+)&#26085;', desc, re.S)[0]
    pub = datetime.date(*map(int, [y,m,d]))
    company = re.findall(r'唱片公司:(.*?)$', desc, re.S)[0].strip()
    print '-'*10
    print unescape(singer), unescape(name), pub, unescape(company)

    s = 0
    gid = None
    for number, title, script in re.findall(r'<td class="number .*?>(.*?)</td>.*?<td class="Title .*?<a .*?>(.*?)</a>.*?<td class="Icon.*?<a .*?title="下载".*?onclick="(.*?)"', html, re.S):
        if s:
            print datetime.datetime.now(), 'take a rest ..', s
            time.sleep(s)
            
        m = re.findall(r'download.html(\?id%3D.*?)\\x26', script, re.S)
        if not m:
            print 'no download for this song'
            continue
        q = m[0]
        iframe = "http://www.google.cn/music/top100/musicdownload" + urllib.unquote(q)
        
        html = urlopen(iframe)
        url = re.findall(r'<a href="/music/top100/url\?q=(.*?)"', html, re.S)[0].split('&', 1)[0]
        url = urllib.unquote(url)
        url_hash = hashlib.md5(url).hexdigest().upper()
        fname = url2fname(url, url_hash)
        
        print number, unescape(title), url, fname
        b = time.time()
        if DEBUG:
            print 'pretend to fetch audio file ...'
        else:
            urlopen(url, fname)
        d = time.time() - b
        s = max(60*3.1 - d, 30)
        #s = 60

        m = Gotcha(number=number.strip('.'),
                   title=unescape(title),
                   singer=unescape(singer),
                   album=unescape(name),
                   pub=pub,
                   company=unescape(company),
                   url=url,
                   url_hash=url_hash,
                   path=fname.replace(DOWNLOAD_DIR, '').lstrip('/'),
                   start=datetime.datetime.fromtimestamp(b),
                   duration=d,
                   )
        if DEBUG:
            print 'pretend to save ', m
            gid = 0
        else:
            try:
                m.save()
                gid = m.id
            except IntegrityError:
                print >> sys.stderr, 'duplicate'
                s = 0
    return gid
        


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'd')
    for opt, val in opts:
        if opt == '-d':
            DEBUG = True

    url = args[0]
    gotcha(url)

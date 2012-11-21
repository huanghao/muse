import sys
import urllib2
from getopt import getopt
from re import findall, S, sub


def GET(url, headers={}, *args, **kw):
    req = urllib2.Request(url)                                                               
    for key, val in headers.items():
        req.add_header(key, val)
    f = urllib2.urlopen(req, *args, **kw)                                                    
    return f.read()

def escape(s):
    return ''.join(sub(r'<.*?>', '', s).split())

def unquote(s):
    return s.replace(u'：', ':').replace(u'，', ',').replace('&nbsp;', '')

class NationalMeteoCenter(object):

    URLS = {
        'BJ': 'http://www.nmc.gov.cn/publish/forecast/ABJ/beijing_iframe.html',
        'SH': 'http://www.nmc.gov.cn/publish/forecast/ASH/shanghai_iframe.html',
        'JX': 'http://www.nmc.gov.cn/publish/forecast/AZJ/jiaxing_iframe.html',
        'CS': 'http://www.nmc.gov.cn/publish/forecast/AHN/changsha_iframe.html',
    }

    def GET(self, url):
        headers = {
            'Cookie': '__utma=111119386.2080013731.1320315479.1320315479.1320315479.1; __utmb=111119386.4.10.1320315479; __utmc=111119386; __utmz=111119386.1320315479.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); city=58367',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.106 Safari/535.2',
        }
        html = GET(url, headers=headers, timeout=10)
        charset = findall(r'<meta .*charset=(.*?)"', html, S)[0]
        charset = 'gb2312'
        return html.decode(charset)

    @staticmethod
    def current(page):
        dt = findall(r"setRealWeatherDate\('(.*?)'", page, S)[0]

        w365 = findall(r'<div class="w365".*?>(.*?)</div>', page, S)
        city = '\n'.join(filter(None, map(unicode.strip, map(unquote, map(escape, w365)))))

        temp_pic = page[page.find(u'<div class="temp_pic" style') : page.find('<div class="vessel"')]
        desc = '\n'.join(map(unquote, map(escape, temp_pic.split('<br/>'))))
        return dt, city, desc.strip()

    @staticmethod
    def forecast(page, num):
        page = sub(r'<div class="spritesweather".*?</div>', '', page)

        el = findall(r'<div class="weather_div".*?<div class="name".*?>(.*?)</div>.*?<div class="weather">(.*?)</div>', page, S)
        msg = [ (escape(name) + '\n' + ''.join(map(escape, findall(r'<li .*?>(.*?)</li>', weather, S)))) \
                for name, weather in el[:num] ]
        return msg

    def query(self, city):
        url1 = self.URLS[city]
        page1 = self.GET(url1)

        url2 = url1.replace('_iframe', '')
        page2 = self.GET(url2)

        dt, city, desc = self.current(page1)
        fc = self.forecast(page2, 3)
        msg = dt + '\n' + '\n'.join(fc) + '\n\n' + city + '\n' + desc
        return msg

def main(city):
    msg = NationalMeteoCenter().query(city)
    raw = msg.encode('utf8')
    print >> sys.stderr, '---- len:%d, %s:' % (len(raw), city)
    print '[test]'+raw

def test():
    html = open('beijing.html').read().decode('gb18030')
    txt = NationalMeteoCenter.forecast(html, 3)
    print txt.encode('utf8')
    sys.exit(0)


if __name__ == '__main__':
    #test()

    if len(sys.argv) > 1:
        city = sys.argv[1].upper()
    else:
        city = 'BJ'

    main(city)

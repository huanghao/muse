#coding: utf8
import os, sys, urllib2, re, htmlentitydefs


CACHE_DIR = 'cache'


class URLOpen(object):
    
    def __init__(self, root=CACHE_DIR):
        self.root = root
    
    def cache(self, fname):
        if os.path.exists(fname):
            with open(fname) as f:
                return f.read()
        return None
    
    def download(self, url, fname):
        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except OSError:
                pass

        with open(fname, 'w') as f:
            content = urllib2.urlopen(url).read()
            f.write(content)
        return content
        
    def __call__(self, url, fname=None):
        if not fname:
            fname = os.path.join(self.root, re.sub('.*?://', '', url))
        cache = self.cache(fname)
        if cache is not None:
            print >> sys.stderr, 'fetch ...', url, 'from', fname
            return cache
        print >> sys.stderr, 'fetch ...', url, 'to', fname
        return self.download(url, fname)

urlopen = URLOpen()



def unescape(html, coding='utf8'):
    def trans(m):
        if m.group(2):
            u = unichr(int(m.group(2)[1:]))
        elif m.group(3):
            u = unichr(htmlentitydefs.name2codepoint[m.group(3)])
        return u.encode(coding) if coding else u
    return re.sub(r'&((#\d+)|(\w+));', trans, html)

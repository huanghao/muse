#coding: utf8
import os
os.environ['DJANGO_SETTINGS_MODULE'] = "orpheus.settings"

import sys
from orpheus.gcn.models import Gotcha
from poorman import DOWNLOAD_DIR

LIB_DIR = '/home/huanghao/Music'


def deposit(gid):
    g = Gotcha.objects.get(pk=gid)
    album = Gotcha.objects.filter(singer=g.singer,
                                  album=g.album,
                                  status=0,
                                  )
    album_name = g.album
    for c in (u'》', u'《', '<b>', '</b>', '.', '\\', '/', '<', '>'):
        album_name = album_name.replace(c, '')
    album_dir = os.path.join(LIB_DIR, 
                             g.singer,
                             album_name).encode('utf8')
    if not os.path.exists(album_dir):
        try:
            os.makedirs(album_dir)
        except OSError:
            pass
    
    for s in album:
        suffix = s.path.split('.')[-1]
        basename = '%02d.%s.%s' % (s.number, s.title, suffix)
        for c in ('\\', '<b>', '</b>', '/', '<', '>'):
            basename = basename.replace(c, '')
        basename = basename.encode('utf8')
        path = os.path.join(album_dir, basename)
        oldpath = os.path.join(DOWNLOAD_DIR, s.path)
        print oldpath, '->', path
        os.rename(oldpath, path)
        s.status = 1
        s.save()

if __name__ == '__main__':
    deposit(int(sys.argv[1]))

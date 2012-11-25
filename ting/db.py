#!/usr/bin/env python
import os
import sys
import sqlite3
import argparse


def summary(c):
    print

    complete = 0
    c.execute('select done, count(*) from jobs group by done order by done');
    print '%4s %10s' % ('done', 'count')
    for done, count in c.fetchall():
        if done == 1:
            complete = count
        print '%4d %10d' % (done, count)

    c.execute('select count(*) from jobs')
    total = c.fetchone()[0]
    ratio = complete * 100. / total
    print '-'*15
    print '%4s %10d %3d%%' % ('SUM', total, ratio)



def group_by_album(c, args):
    num = {}
    c.execute('select singer,album,count(*) from jobs group by singer,album')
    for singer, album, total in c.fetchall():
        key = (singer, album)
        num[key] = [total, 100, 0] # ratio, todo

    c.execute('select singer,album,count(*) from jobs where done=0 group by singer,album')
    for singer, album, todo in c.fetchall():
        key = (singer, album)
        val = num[key]

        total = val[0]
        done = total - todo
        ratio = done*100./total
        val[1], val[2] = ratio, todo

    def header():
        if args.acc:
            print '%4s %4s %5s %5s %15s    %s' % ('%', 'todo', 'total', 'acc', 'singer', 'album')
        else:
            print '%4s %4s %5s %15s    %s' % ('%', 'todo', 'total', 'singer', 'album')

    two_part = True
    acc = 0
    def sort_func(i, j):
        (singer1, album1), (total1, ratio1, _) = i
        (singer2, album2), (total2, ratio2, _) = j
        r = cmp(ratio2, ratio1)
        if r != 0: return r
        r = cmp(singer2, singer1)
        if r != 0: return r
        r = cmp(total2, total1)
        if r != 0: return r
        r = cmp(album2, album1)
        return r

    for (singer, album), (total, ratio, todo) in sorted(num.iteritems(), cmp=sort_func):
        if not args.all and ratio == 100:
            continue

        if two_part and ratio != 100:
            two_part = False
            header()

        if args.acc:
            acc += total
            print '%3d%% %4d %5d %5d %15s    %s' % (ratio, todo, total, acc, singer, album)
        else:
            print '%3d%% %4d %5d %15s    %s' % (ratio, todo, total, singer, album)

def what_done(c):
    def col1(sql):
        return [ i[0] for i in c.execute(sql).fetchall() ]

    all = set(col1('select distinct singer from jobs'))
    not_done = set(col1('select distinct singer from jobs where done!=1'))
    done = sorted(all - not_done)
    print '\n'.join(done)

def what_error(c):
    for row in c.execute('select * from jobs where done < 0').fetchall():
        print ' '.join([ i.encode('utf8') if isinstance(i, unicode) else str(i) for i in row ])

def getopt():
    parser = argparse.ArgumentParser(description='db helper')
    parser.add_argument('db', nargs='?', default='songs.db', type=os.path.abspath, help='db file')
    parser.add_argument('--acc', action='store_true', help='show accumulate total')
    parser.add_argument('-a', '--all', action='store_true', help='show all albums including finish')
    parser.add_argument('--done', action='store_true', help='show done artists')
    parser.add_argument('--error', action='store_true', help='show error songs')
    return parser.parse_args()


def main():
    args = getopt()
    conn = sqlite3.connect(args.db, isolation_level=None)
    c = conn.cursor()
    if args.error:
        what_error(c)
    elif args.done:
        what_done(c)
    else:
        group_by_album(c, args)
    summary(c)


if __name__ == '__main__':
    main()

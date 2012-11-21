import sys
import sqlite3



def summary(c):
    print

    c.execute('select done, count(*) from jobs group by done order by done');
    print '%4s %10s' % ('done', 'count')
    for row in c.fetchall():
        print '%4d %10d' % row

    c.execute('select count(*) from jobs')
    print '-'*15
    print '%4s %10d' % ('SUM', c.fetchone()[0])



def group_by_album(c):
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
        print '%4s %4s %5s %5s %15s %s' % ('%', 'todo', 'total', 'acc', 'singer', 'album')

    two_part = True
    acc = 0
    for (singer, album), (total, ratio, todo) in sorted(num.iteritems(), key=lambda i:i[1][1], reverse=True):
        if two_part and ratio != 100:
            two_part = False
            header()

        acc += total
        print '%3d%% %4d %5d %5d %15s %s' % (ratio, todo, total, acc, singer, album)


def main():
    if len(sys.argv) > 1:
        dbname = sys.argv[1]
    else:
        dbname = 'songs.db'

    conn = sqlite3.connect(dbname, isolation_level=None)
    c = conn.cursor()
    group_by_album(c)
    summary(c)


if __name__ == '__main__':
    main()

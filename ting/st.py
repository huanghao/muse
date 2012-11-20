import sqlite3

DBNAME = 'songs.db'

def main():
    conn = sqlite3.connect(DBNAME, isolation_level=None)
    c = conn.cursor()

    c.execute('select count(*) from jobs')
    print 'TOTAL:', c.fetchone()[0]

    c.execute('select done, count(*) from jobs group by done order by done');
    print '%4s %10s' % ('done', 'count')
    for row in c.fetchall():
        print '%4d %10d' % row

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

    def cmp_func(i, j):
        r = cmp(j, i)
        if r != 0 and i==100 or j==100:
            return -r
        return r

    acc = 0
    print '%4s %4s %5s %5s %15s %s' % ('%', 'todo', 'total', 'acc', 'singer', 'album')
    for (singer, album), (total, ratio, todo) in sorted(num.iteritems(), key=lambda i:i[1][1], cmp=cmp_func):
        acc += total
        print '%3d%% %4d %5d %5d %15s %s' % (ratio, todo, total, acc, singer, album)


if __name__ == '__main__':
    main()
    

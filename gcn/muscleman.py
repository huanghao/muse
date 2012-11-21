#coding: utf8
import time, traceback, os

from poorman import gotcha
from dustman import deposit


class Todo(object):
    
    def __init__(self, fname):
        self.fname = fname
    
    def get(self):
        with open(self.fname) as f:
            return f.readline()
    
    def pop(self):
        with open(self.fname, 'r') as f:
            c = ''.join(f.readlines()[1:])
        with open(self.fname, 'w') as f:
            f.write(c)
    
    def __iter__(self):
        while True:
            line = self.get()
            if not line:
                break
            yield line
            self.pop()


class TodoDir(object):
    
    def __init__(self, dname):
        self.dname = dname
    
    def __iter__(self):
        while True:
            try:
                fname = sorted(os.listdir(self.dname))[0]
            except:
                raise StopIteration
            
            todo = Todo(os.path.join(self.dname, fname))
            for line in todo:
                yield line
            
            os.unlink(os.path.join(self.dname, fname))


class Done(object):

    def __init__(self, fname):
        self.fname = fname
        
    def push(self, line):
        with open(self.fname, 'a') as f:
            f.write(line)


def hardwork():
    done = Done('album.done.txt')
    for line in TodoDir('todo'):
        url = line.split('|')[0].strip()

        if not url.startswith('http'):
            print 'ignore', line,
            done.push(line)
            continue
        
        gid = gotcha(url)
        deposit(gid)
        
        line2 = '|'.join(line.strip().split('|') + [str(gid)]) + '\n'
        done.push(line2)


def test():
    for i in TodoDir('bak'):
        print i,



if __name__ == '__main__':
    hardwork()

#! /mit/sashacf/bin/python3.4

from conlang.conlangApp import *
from core import *

ar = soundChanger.applyRules

lf = lambda f, pre='.': loadFile(pre + '/files/' + f)

def last(name):
    return ('.' + name).rsplit('.', 1)[0][1:]

def step(start, end):
    '''\
provides the next step between start and end. does not check if they are
linearly connected.'''
    if start != '':
        start += '.'
    return start + end[len(start):].split('.')[0]

def asc(word, pairs, debug=0, pre='.'):
    '''\
pairs format: [['a', 'a.b'], ['b', 'b.c']]
debug = 0: don't show anything
debug = 1: word at end of each pair
debug > 2: word at end of each file
debug > 3: word at end of each rule'''
    db = ''
    for p in pairs:
        if p[1].startswith(p[0]):
            cur, end = p
            while cur != end:
                cur = step(cur, end)
                word, steps = ar(word, lf(cur, pre))
                if debug > 2:
                    db += steps
                if debug > 1:
                    db += cur + ':' + word + '\n'
        else:
            raise Exception(p[1] + ' does not start with ' + p[0])
        if debug == 1:
            db += p[1] + ':' + word + '\n'
    return word, db

saj = 'prt.west.sajura'


if __name__ == '__main__':
    print('Content-Type: text/html')
    print('')
    print(FILE_PATH + '/files/' + 'fluf')
    with open(FILE_PATH + '/files/' + 'fluf') as f:
        for l in f.read():
            print l
    print(reencode(asc('tət', [['', 'fluf.harmony.pron']], pre=FILE_PATH)[0]))
#! /usr/bin/env python3.4  # lint:ok

import sys
sys.path.insert(0, '/home/sasha/Dropbox/Public/python/conlang')
sys.path.insert(0, '/mit/sashacf/Dropbox/Public/python/conlang')

from conlang.conlangApp import *

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

def asc(word, start, end, showSteps=False):
    if start == end:
        return word
    else:
        return ar(asc(word, start, last(end), showSteps), lf(end), showSteps)


def asc2(word, pairs, showSteps=0):
    '''\
pairs format: [['a', 'a.b'], ['b', 'b.c']]
showSteps = 0: don't show anything
showSteps = 1: print word at end of each pair
showSteps > 2: print word at end of each file
showSteps > 3: print word at end of each rule'''
    for p in pairs:
        if p[1].startswith(p[0]):
            cur, end = p
            while cur != end:
                cur = step(cur, end)
                word = ar(word, lf(cur), showSteps > 2)
                if showSteps > 1:
                    print(cur, ':', word)
        else:
            raise Exception(p[1] + ' does not start with ' + p[0])
        if showSteps == 1:
            print(p[1], ':', word)
    return word

saj = 'prt.west.sajura'

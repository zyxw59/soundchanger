#! /usr/bin/env python3.4  # lint:ok

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

def asc(word, pairs, showSteps=0, pre='.'):
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
                word = ar(word, lf(cur, pre), showSteps > 2)
                if showSteps > 1:
                    print(cur, ':', word)
        else:
            raise Exception(p[1] + ' does not start with ' + p[0])
        if showSteps == 1:
            print(p[1], ':', word)
    return word

saj = 'prt.west.sajura'

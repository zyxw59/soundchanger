#! /usr/bin/env python3

import argparse
import asc
import cgi
import cgitb
from core import *
import os
import sys

print('Content-Type: text/html')
print('')
form = cgi.FieldStorage(encoding='utf-8')

html = False
debug = 0

print(form['word'])

if 'word' in form:
    sys.stdout = Reencoder(sys.stdout)
    cgitb.enable()
    word = form['word'].value
    startd = {}
    endd = {}
    start = []
    end = []
    if 'debug' in form:
        debug = int(form['debug'].value)
    html = True
    FILE_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
else:
    parser = argparse.ArgumentParser()
    parser.add_argument('--word', '-w')
    parser.add_argument('--start', '-s', nargs='+')
    parser.add_argument('--end', '-e', nargs='+')
    parser.add_argument('--debug', '-d', type=int, default=0)
    parser.add_argument('--html', '-t', action='store_true')
    args = parser.parse_args()
    if args.word is None:
        word = input()
    else:
        word = args.word
    debug = args.debug
    if args.html:
        sys.stdout = Reencoder(sys.stdout)
        html = True
    start = args.start
    end = args.end

for f in form:
    if f[0] == 's':
        startd[f] = form[f].value
        if startd[f] == ' ':
            startd[f] = ''
    elif f[0] == 'e':
        endd[f] = form[f].value
        if endd[f] == ' ':
            endd[f] = ''

#start = start or [v for k, v in sorted(startd.items())]
#end = end or [v for k, v in sorted(endd.items())]

#pairs = list(zip(start, end))

#word, db = asc.asc(word, pairs, debug, FILE_PATH)

if html:
    print('<pre>')
print(word)
#print(db)
if html:
    print('</pre>')
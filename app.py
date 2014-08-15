#! /mit/sashacf/bin/python3.4

import argparse
import asc
import cgi
import cgitb
from core import *
import os
import sys

form = cgi.FieldStorage(encoding='utf-8')

word = None
w = False
html = False
debug = 0
FILE_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

if 'word' in form:
    sys.stdout = Reencoder(sys.stdout)
    print('Content-Type: text/html')
    print('')
    print(FILE_PATH)
    word = form['word'].value
    startd = {}
    endd = {}
    start = []
    end = []
    if 'debug' in form:
        debug = int(form['debug'].value)
    html = True
else:
    parser = argparse.ArgumentParser()
    parser.add_argument('--word', '-w')
    parser.add_argument('--start', '-s', action='append')
    parser.add_argument('--end', '-e', action='append')
    parser.add_argument('--debug', '-d', type=int, default=0)
    parser.add_argument('--html', '-t', action='store_true')
    args = parser.parse_args()
    word = args.word
    if word is None:
        w = True
    debug = args.debug
    if args.html:
        sys.stdout = Reencoder(sys.stdout)
        html = True
    start = args.start
    end = args.end

if html:
    cgitb.enable()

for f in form:
    if f[0] == 's':
        startd[f] = form[f].value
        if startd[f] == ' ':
            startd[f] = ''
    elif f[0] == 'e':
        endd[f] = form[f].value
        if endd[f] == ' ':
            endd[f] = ''

start = start or [v for k, v in sorted(startd.items())]
end = end or [v for k, v in sorted(endd.items())]

pairs = list(zip(start, end))

while True:
    if w:
        try:
            word = input()
        except KeyboardInterrupt:
            break
    word, db = asc.asc(word, pairs, debug, FILE_PATH)

    if html:
        print('<pre>')
    print(word)
    print(db, end='')  # lint:ok
    if html:
        print('</pre>')
    if not w:
        break
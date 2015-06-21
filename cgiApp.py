#!./.interpreter.sh

import argparse
import cgi
import cgitb
import os
import sys
from conlang import soundChangeApp, workers


word = None
stdin = False
html = False
debug = 0
FILE_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

if 'REQUEST_METHOD' in os.environ:
    # It's being run as a cgi script
    # Encode all non-ascii characters with xml escapes
    sys.stdout = workers.Reencoder(sys.stdout)
    print('Content-Type: text/html')
    print('')
    form = cgi.FieldStorage(encoding='utf-8')
    word = form['word'].value
    startd = {}
    endd = {}
    for f in form:
        try:
            # just get the number from the form key
            n = int(f.split('-')[1])
            v = form[f].value
            if f[0] == 's':
                startd[n] = v if v != ' ' else ''
            elif f[0] == 'e':
                endd[n] = v if v != ' ' else ''
        except IndexError:
            # there wasn't a '-' in f, so it wasn't a start or end key
            continue
    start = [v for k, v in sorted(startd.items())]
    end = [v for k, v in sorted(endd.items())]
    if 'debug' in form:
        debug = int(form['debug'].value)
    html = True
else:
    # It's being run from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--word', '-w')
    parser.add_argument('--start', '-s', action='append', default=[], nargs='?')
    parser.add_argument('--end', '-e', action='append', default=[], nargs='?')
    parser.add_argument('--debug', '-d', type=int, default=0)
    parser.add_argument('--html', '-t', action='store_true')
    args = parser.parse_args()
    word = args.word
    if word is None:
        # take input from stdin
        stdin = True
    debug = args.debug
    if args.html:
        # encode all non-ascii characters with xml escapes
        sys.stdout = Reencoder(sys.stdout)
        html = True
    start = [x if x else '' for x in args.start]
    end = [x if x else '' for x in args.end]

if html:
    # html formatted error messages
    cgitb.enable()
else:
    # plain error messages
    cgitb.enable(format='plain')

pairs = list(zip(start, end))

while True:
    if stdin:
        try:
            word = input()
        except (KeyboardInterrupt, EOFError):
            break
    word, db = soundChangeApp.applyRuleFiles(word, pairs, debug)
    if html:
        print('<pre>')
    print(word)
    print(db, end='')
    if html:
        print('</pre>')
    if not stdin:
        break

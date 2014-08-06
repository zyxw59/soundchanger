#! /mit/sashacf/bin/python3.4

from asc import asc
import cgi
import cgitb
from core import *

cgitb.enable()

print('Content-Type: text/html')
print('')

form = cgi.FieldStorage(encoding='utf-8')

start = {}
end = {}
word = form['word'].value
if 'debug' in form:
    debug = int(form['debug'].value)
else:
    debug = 0

for f in form:
    if f[0] == 's':
        start[f] = form[f].value
        if start[f] == ' ':
            start[f] = ''
    elif f[0] == 'e':
        end[f] = form[f].value
        if end[f] == ' ':
            end[f] = ''

start = [v for k, v in sorted(start.items())]
end = [v for k, v in sorted(end.items())]

pairs = list(zip(start, end))
print(reencode(word), pairs, debug, FILE_PATH)

word, db = asc(word, pairs, debug, FILE_PATH)

print('<pre>')
print(reencode(word))
print(reencode(db))
print('</pre>')
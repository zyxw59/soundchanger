#! /mit/sashacf/bin/python3.4

#from asc import asc2
import cgi
import cgitb

cgitb.enable()

print('Content-Type: text/html')
print('')

form = cgi.FieldStorage(encoding='utf-8')

start = {}
end = {}

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

print(pairs)
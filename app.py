#! /mit/sashacf/bin/python3.4

from asc import asc2
import cgi
import cgitb

cgitb.enable()

print('Content-Type: text/html')
print('')

form = cgi.FieldStorage()

print(form)
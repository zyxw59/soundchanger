#! /mit/sashacf/bin/python3.4

import cgitb
import os

cgitb.enable()

FILE_PATH = '/mit/sashacf/Dropbox/Public/python/conlang/asc/files'

print('Content-Type: text/html')
print('')

files = sorted(os.listdir(FILE_PATH))

print('''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Sound Change Applier</title>
</head>
<body>
<select>''')
for f in files:
    print('<option value="' + f + '">' + f + '</option>')
print('''
</body>
</html>''')
#! /mit/sashacf/bin/python3.4

import cgitb
import os
from core import *

cgitb.enable()

print('Content-Type: text/html')
print('')

files = sorted([' '] + os.listdir(FILE_PATH + '/files/'))
fs = ['.' * f.count('.') + ('.' + f).rsplit('.', 1)[1] for f in files]

with open('chars.txt', encoding='utf-8') as cf:
    chars = [l.split(' ') for l in cf.read().split('\n')]

#chars = ['á', 'ɓ', 'β', 'ɗ', 'd͜ʑ', 'đ', 'é', 'ɛ', 'ɜ', 'ɘ', 'ə', 'ɠ', 'ɣ', 'ħ', 'ɦ',
     #'ɨ', 'ñ', 'ŋ', 'ɲ', 'ó', 'ɔ', 'ɾ', 'ɕ', 't͜ɕ', 'ŧ', 'ú', 'ʷ', 'ʑ', 'ʔ', 'ˈ']

print('''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport"
  content="width=device-width,
  minimum-scale=1.0, maximum-scale=1.0" />
<title>Sound Change Applier</title>
<script>
files = [\'''' + '\', \''.join(files) + '''\'];
fs = [\'''' + '\', \''.join(fs) + '''\'];
numFiles = files.length;
numPairs = 0;
</script>
<link rel="stylesheet" media="screen and (min-device-width: 800px)" href="main.css" />
<link rel="stylesheet" media="screen and (max-device-width: 800px)" href="phone.css" />
<script src="main.js" ></script>
</head>
<body>
<div class="container">
<div class="top">
<form id="main" action="app.py" target="app">
<input id="word" name="word" class="form-control"/>
<select id="debug" name="debug">''')
for i in range(4):
    print('<option value="' + str(i) + '">' + str(i) + '</option>')
print('''</select>
<input type="submit" value="apply" />
</form>
<div>''')
for l in chars:
    print('<select onblur="insert(this.value)">')
    for c in l:
        print('<option value="' + c + '">' + c + '</option>')
    print('</select>')
print('''</div>
<form id="pairs">\
<div id="pair-0">\
<select id="start-0" name="start-0" form="main">''')
for i in range(len(files)):
    f, s = files[i], fs[i]
    print('<option value="' + f + '">' + s + '</option>')
print('''</select>\
<select id="end-0" name="end-0" form="main">''')
for i in range(len(files)):
    f, s = files[i], fs[i]
    print('<option value="' + f + '">' + s + '</option>')
print('''</select>
</div>\
</form>
<input type="button" value="+" onclick="addMenu()" />
<input type="button" value="-" onclick="removeMenu()" />
</div>
<div class="content">
<iframe name="app" seamless></iframe>
</div>
</div>
</body>
</html>''')
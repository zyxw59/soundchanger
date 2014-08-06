#! /mit/sashacf/bin/python3.4

import cgitb
import os
from core import *

cgitb.enable()

print('Content-Type: text/html')
print('')

files = sorted([''] + os.listdir(FILE_PATH + 'files/'))
fs = ['.' * f.count('.') + ('.' + f).rsplit('.', 1)[1] for f in files]

chars = ['á', 'ɓ', 'β', 'ɗ', 'd͜ʑ', 'đ', 'é', 'ɛ', 'ɜ', 'ɘ', 'ɠ', 'ɣ', 'ħ', 'ɦ',
     'ɨ', 'ñ', 'ŋ', 'ɲ', 'ó', 'ɔ', 'ɾ', 'ɕ', 't͜ɕ', 'ŧ', 'ú', 'ʷ', 'ʑ', 'ʔ', 'ˈ']

print('''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Sound Change Applier</title>
<script>
files = [\'''' + '\', \''.join(files) + '''\'];
fs = [\'''' + '\', \''.join(fs) + '''\'];
numFiles = files.length;
numPairs = 0;
</script>
<script src="main.js" ></script>
</head>
<body>
<form id="main" action="app.py" target="app">
<input id="word" name="word" />
<input type="submit" value="apply" />
</form>
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
<div><iframe name="app"></iframe></div>
</body>
</html>''')
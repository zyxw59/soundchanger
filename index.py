#!./.interpreter.sh

import cgitb
import os
from os import path
import sys
from soundchanger.conlang import workers

def main():
    cgitb.enable()

    sys.stdout = workers.Reencoder(sys.stdout)

    print('Content-Type: text/html')
    print('')

    files = sorted([' '] + [f for f in os.listdir(path.join(workers.FILE_PATH, 'files')) if not f.startswith('.')])
    fs = ['.' * f.count('.') + ('.' + f).rsplit('.', 1)[1] for f in files]

    with open('chars.txt', encoding='utf-8') as cf:
        chars = [l.split(' ') for l in cf.read().split('\n')]

    print('<!DOCTYPE html>'
          '<html>\n'
          '<head>\n'
          '<meta charset="utf-8" />\n'
          '<meta name="viewport"'
          'content="width=device-width, minimum-scale=1.0, maximum-scale=1.0" />\n'
          '<title>Sound Change Applier</title>\n'
          '<script>\n'
          "files = ['" + "', '".join(files) + "'];\n"
          "fs = ['" + "', '".join(fs) + "'];\n"
          'numFiles = files.length;\n'
          'numPairs = 0;\n'
          '</script>\n'
          '<link rel="stylesheet" media="screen and (min-device-width: 800px)" href="main.css" />\n'
          '<link rel="stylesheet" media="screen and (max-device-width: 800px)" href="phone.css" />\n'
          '<script src="main.js" ></script>\n'
          '</head>\n'
          '<body>\n'
          '<div class="container">\n'
          '<div class="top">\n'
          '<form id="main" action="cgi_app.py" target="app">\n'
          '<input id="word" name="word" class="form-control"/>\n'
          '<select id="debug" name="debug">')
    for i in range(4):
        print('<option value="' + str(i) + '">' + str(i) + '</option>')
    print('</select>\n'
          '<input type="submit" value="apply" />\n'
          '</form>\n'
          '<div>\n')
    for l in chars:
        print('<select onblur="insert(this.value)">')
        for c in l:
            print('<option value="' + c + '">' + c + '</option>')
        print('</select>')
    print('</div>\n'
          '<form id="pairs">\n'
          '<div id="pair-0">\n'
          '<select id="start-0" name="start-0" form="main">')
    for i in range(len(files)):
        f, s = files[i], fs[i]
        print('<option value="' + f + '">' + s + '</option>')
    print('</select>'
          '<select id="end-0" name="end-0" form="main">')
    for i in range(len(files)):
        f, s = files[i], fs[i]
        print('<option value="' + f + '">' + s + '</option>')
    print('</select></div></form>\n'
          '<input type="button" value="+" onclick="addMenu()" />\n'
          '<input type="button" value="-" onclick="removeMenu()" />\n'
          '</div>\n'
          '<div class="content">\n'
          '<iframe name="app" seamless></iframe>\n'
          '</div>\n'
          '</div>\n'
          '</body>\n'
          '</html>')


if __name__ == '__main__':
    main()

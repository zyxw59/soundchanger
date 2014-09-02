#!../.interpreter.sh

import argparse
import cgitb
import collections
import sys

cgitb.enable(format='none')


parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i')
parser.add_argument('--output', '-o')
parser.add_argument('--style', '-s', default='gmp.css')
parser.add_argument('--escape', '-e', action='store_true')

args = parser.parse_args()

class Reencoder():

    def __init__(self, stream=sys.__stdout__):
        self.stream = stream

    def write(self, *a):
        return self.stream.write(*(reencode(s) for s in a))

    def flush(self):
        return self.stream.flush()

reencode = lambda s: s.encode('ascii', 'xmlcharrefreplace').decode()

if args.input is None:
    inFile = sys.stdin
else:
    inFile = open(args.input, 'r')
if args.output is not None:
    sys.stdout = open(args.output, 'w')
if args.escape:
    sys.stdout = Reencoder(sys.stdout)

title = inFile.readline()[:-1]
lines = inFile.read().splitlines()
inFile.close()

h2 = {}
h3 = {}

table = []
untaggedIndex = 0

tCells = []
lastMerged = {}
lastSplit = collections.defaultdict(dict)

tableOpen = False

for i in range(len(lines)):
    if lines[i][:3] == '!!!':
        h3[len(table)] = lines[i][3:]
    elif lines[i][:2] == '!!':
        h2[len(table)] = lines[i][2:].split('#')
        if len(h2[len(table)]) == 1:
            h2[len(table)].append('untagged-' + str(untaggedIndex))
            untaggedIndex += 1
    elif lines[i][0] == '#':
        continue
    else:
        table.append([c.split('\\', 1) for c in lines[i].split('|')])

for i in range(len(table)):
    tCells.append([None] * len(table[i]))
    for j in range(len(table[i])):
        if len(table[i][j]) == 2:
            tCells[i][j] = [0, 0]
            if table[i][j][0] != '':
                lastSplit[j][0] = i
            tCells[lastSplit[j][0]][j][0] += 1
            if table[i][j][1] != '':
                lastSplit[j][1] = i
            tCells[lastSplit[j][1]][j][1] += 1
        else:
            tCells[i][j] = [0]
            if table[i][j][0] != '':
                lastMerged[j] = [i]
            tCells[lastMerged[j][0]][j][0] += 1

print('''\
<!DOCTYPE html>
<html>
<meta charset='utf-8' />
<title>''' + title + '''</title>
<link rel=stylesheet href=''' + args.style + '''>
</head>
<body>
<h1>''' + title + '''</h1>
<ul id=toc>''')

for i in range(len(table)):
    if i in h2:
        print('<li><a href="#' + h2[i][1] + '">' + h2[i][0] + '</a></li>')

print('</ul>')

for i in range(len(table)):
    if i in h2:
        if tableOpen:
            print('</table>')
            tableOpen = False
        print('<h2 id="' + h2[i][1] + '">' + h2[i][0] + '</h2>')
    if not tableOpen:
        print('<table>')
        tableOpen = True
    if i in h3:
        print('<tr><th colspan="' + str(len(table[i]) * 2) +
              '">' + h3[i] + '</th></tr>')
    print('<tr>')
    for j in range(len(table[i])):
        if len(tCells[i][j]) == 2:
            if table[i][j][0] == '0':
                tbw = ''
            else:
                tbw = table[i][j][0]
            if tCells[i][j][0] > 1:
                print('<td class="c' + str(j) + ' s0" rowspan="' +
                      str(tCells[i][j][0]) + '">' + tbw + '</td>')
            elif tCells[i][j][0] == 1:
                print('<td class="c' + str(j) + ' s0">' + tbw + '</td>')
            if table[i][j][1] == '0':
                tbw = ''
            else:
                tbw = table[i][j][1]
            if tCells[i][j][1] > 1:
                print('<td class="c' + str(j) + ' s1" rowspan="' +
                      str(tCells[i][j][1]) + '">' + tbw + '</td>')
            elif tCells[i][j][1] == 1:
                print('<td class="c' + str(j) + ' s1">' + tbw + '</td>')
        else:
            if table[i][j][0] == '0':
                tbw = ''
            else:
                tbw = table[i][j][0]
            if tCells[i][j][0] > 1:
                print('<td class="c' + str(j) + ' m" colspan="2" rowspan="' +
                      str(tCells[i][j][0]) + '">' + tbw + '</td>')
            elif tCells[i][j][0] == 1:
                print('<td class="c' + str(j) + ' m" colspan="2">' + tbw +
                  '</td>')
    print('</tr>')

if tableOpen:
    print('</table>')

print('</body>\n</html>')
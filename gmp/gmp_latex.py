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

def make_cline(segments):
    out = []
    nl = True
    for i, s in enumerate(segments):
        if nl:
            if s:
                out.append([i + 1])
                nl = False
        else:
            if not s:
                out[-1].append(i)
                nl = True
    if not nl:
        out[-1].append(i + 1)
    return ''.join(r'\cmidrule{{{0[0]}-{0[1]}}}'.format(l) for l in out)


if args.input is None:
    in_file = sys.stdin
else:
    in_file = open(args.input, 'r')
if args.output is not None:
    sys.stdout = open(args.output, 'w')
if args.escape:
    sys.stdout = Reencoder(sys.stdout)

title = in_file.readline()[:-1]
lines = in_file.read().splitlines()
in_file.close()

h2 = {}
h3 = {}

table = []

table_open = False

for i, line in enumerate(lines):
    if line[:3] == '!!!':
        h3[len(table)] = line[3:]
    elif line[:2] == '!!':
        h2[len(table)] = line[2:].split('#')[0]
    elif line[0] == '#':
        continue
    else:
        table.append([c.split('\\', 1) for c in line.split('|')])

# preamble, title, toc
print(r'''
\documentclass[12pt]{article}
\usepackage{fontspec}
\usepackage{booktabs}
\usepackage{tabu}
\usepackage{longtable}
\usepackage[hidelinks]{hyperref}
\usepackage{fullpage}
\usepackage{amssymb}
\setmainfont{CMU Serif}
\setcounter{secnumdepth}{0}

\catcode`∅=13
\def ∅{$\varnothing$}
\catcode`⁓=13
\def ⁓{\ –\ }
\catcode`₁=13
\def ₁{\textsubscript{1}}
\catcode`₂=13
\def ₂{\textsubscript{2}}
\def ~{\textasciitilde{}}

\title{''' + title + r'''}
\date{}
\begin{document}
\pagenumbering{roman}
\maketitle
\tableofcontents
\clearpage
\pagenumbering{arabic}
''')

for i, row in enumerate(table):
    if i in h2:
        if table_open:
            print(r'\bottomrule')
            print(r'\end{longtabu}')
            table_open = False
        print(r'\section{' + h2[i] + '}')
    if not table_open:
        print(r'\begin{longtabu}{*{6}{l}}')
        table_open = True
    if i in h3:
        print(r'\toprule')
        print(r'\multicolumn{6}{c}{\bfseries ' + h3[i] + r'}\\ \midrule')
    row_out = []
    segments = []
    for j, cell in enumerate(row):
        if len(cell) == 1:
            segments += (not not cell[0],) * 2
            if cell[0] == '0':
                cell[0] = ''
            row_out.append(r'\multicolumn{2}{l}{' + cell[0] + '}')
        else:
            segments += not not cell[0], not not cell[1]
            if cell[0] == '0':
                cell[0] = ''
            if cell[1] == '0':
                cell[1] = ''
            row_out.append('&'.join(cell))
    print(make_cline(segments))
    print('&'.join(row_out) + r'\\')


if table_open:
    print(r'\bottomrule')
    print(r'\end{longtabu}')

print(r'\end{document}')

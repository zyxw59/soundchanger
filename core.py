#! /mit/sashacf/bin/python3.4

import cgitb
import sys
cgitb.enable()

import asc

FILE_PATH = '/mit/sashacf/web_scripts/soundchanger'

class Reencoder():

    def __init__(self, stream=sys.__stdout__):
        self.stream = stream

    def write(self, *a):
        return self.stream.write(*(reencode(s) for s in a))

    def flush(self):
        return self.stream.flush()

reencode = lambda s: s.encode('ascii', 'xmlcharrefreplace').decode()

if __name__ == '__main__':
    print('Content-Type: text/html')
    print('')
    print(reencode(asc.asc('sˈezuza sˈewa', [('prt.west.sajura', 'prt.west.sajura.purrub.middle.em.modern.orth')], 0, '/mit/sashacf/web_scripts/soundchanger')[0]))
#! /mit/sashacf/bin/python3.4


import sys
import cgitb
cgitb.enable()

import asc

FILE_PATH = '/mit/sashacf/web_scripts/soundchanger'

class Reencoder():

    def write(self, *a):
        return sys.__stdout__.write(*(reencode(s) for s in a))

    def flush(self):
        return sys.__stdout__.flush()

sys.stdout = Reencoder()

reencode = lambda s: s.encode('ascii', 'xmlcharrefreplace').decode()

if __name__ == '__main__':
    print('Content-Type: text/html')
    print('')
    print(reencode(asc.asc('sˈezuza sˈewa', [('prt.west.sajura', 'prt.west.sajura.purrub.middle.em.modern.orth')], 0, '/mit/sashacf/web_scripts/soundchanger')[0]))
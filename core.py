#! /mit/sashacf/bin/python3.4


import cgitb
cgitb.enable()
import asc

FILE_PATH = '/mit/sashacf/web_scripts/soundchanger'

def reencode(s):
    return s.encode('ascii', 'xmlcharrefreplace').decode()

if __name__ == '__main__':
    print('Content-Type: text/html')
    print('')
    print(reencode(asc.asc('sˈezuza sˈewa', [('prt.west.sajura', 'prt.west.sajura.purrub.middle.em.modern.orth')])[0]))
#! /mit/sashacf/bin/python3.4


import cgitb
cgitb.enable()

FILE_PATH = '/mit/sashacf/web_scripts/soundchanger'

def reencode(s):
    return s.encode('ascii', 'xmlcharrefreplace').decode()

if __name__ == '__main__':
    print('Content-Type: text/html')
    print('')
    print(FILE_PATH + '/files/' + 'fluf')
    f = open(FILE_PATH + '/files/fluf')
    r = f.read()
    print(reencode(f))
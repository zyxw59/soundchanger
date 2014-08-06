#! /usr/bin/env python3.4  # lint:ok

FILE_PATH = '/mit/sashacf/web_scripts/soundchanger'

def reencode(s):
    return s.encode('ascii', 'xmlcharrefreplace').decode()
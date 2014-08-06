#! /usr/bin/env python3.4  # lint:ok

FILE_PATH = '/mit/sashacf/Dropbox/Public/python/conlang/asc/files'

def reencode(s):
    return s.encode('ascii', 'xmlcharrefreplace').decode()
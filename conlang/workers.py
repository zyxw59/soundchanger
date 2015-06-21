import cgitb
import sys
import os

FILE_PATH = '/mit/sashacf/web_scripts/soundchanger'

def addPad(l, n, item):
    """Adds item to list l at position n, padding l with the value None, if
    necessary"""
    if n >= len(l):
        l += [None] * (n + 1 - len(l))
    if l[n] is None:
        l[n] = item


def flipDict(d):
    """Returns a dict with values and keys reversed"""
    return {v: k for k, v in d.items()}


class Reencoder():
    """A stream that uses 'xmlcharrefreplace' to reencode it's output."""

    def __init__(self, stream=sys.__stdout__):
        self.stream = stream

    def write(self, *a):
        return self.stream.write(*(reencode(s) for s in a))

    def flush(self):
        return self.stream.flush()


reencode = lambda s: s.encode('ascii', 'xmlcharrefreplace').decode()


def sliceReplace(word, sl, repl):
    """Returns word with the slice indicated by sl replaced with repl"""
    return word[:sl[0]] + repl + word[sl[1]:]


#! /usr/bin/env python3.3  # lint:ok


def addPad(l, n, item):
    '''adds item to list l at position n, padding l with the value None, if
    necessary'''
    if n >= len(l):
        l += [None] * (n + 1 - len(l))
    if l[n] is None:
        l[n] = item


def flipDict(d):
    '''returns a dict with values and keys reversed'''
    return {v: k for k, v in d.items()}


class LoopBreak(Exception):
    pass


def sliceReplace(word, sl, repl):
    '''returns word with the slice indicated by sl replaced with repl'''
    return word[:sl[0]] + repl + word[sl[1]:]

#! /usr/bin/env python3.3  # lint:ok

import json
from . import soundChanger, dictionary, inflections


def customEncode(obj):
    '''Custom JSON encoder for Dictionary and Entry classes'''
    if isinstance(obj, dictionary.Dictionary):
        key = '__{!s}__'.format(obj.__class__.__name__)
        return {key: list(obj)}
    elif isinstance(obj, dictionary.Entry):
        key = '__{!s}__'.format(obj.__class__.__name__)
        return {key: obj.items()}
    else:
        raise TypeError("obj {} of type {}".format(obj, type(obj)))


def classHook(dct):
    """JSON object hook to decode classes"""
    if len(dct) == 1:
        className, value = next(iter(dct.items()))
        className = className.strip('_')
        if className == 'Dictionary':
            return dictionary.Dictionary(value)
        elif className == 'Entry':
            return dictionary.Entry(value)
    return dct


def loadFile(fileName):
    '''Returns specified file as a Dictionary or Entry if it is a json file,
    or a list of lines otherwise'''
    with open(fileName) as f:
        if fileName.split('.')[-1] in ['json', 'js']:
            return json.load(f, object_hook=classHook)
        else:
            return [l.strip('\n') for l in f if len(l.strip('\n')) and l[:1] != '//']


def saveFile(d, fileName, override=False):
    '''Saves the specified Dictionary to the specifed filename'''
    try:
        f = open(fileName, 'x')
    except FileExistsError:
        if not override:
            print('File exists, overwrite? [Y/n]', end=' ')  # lint:ok
            if 'n' in input():
                return
        f = open(fileName, 'w')
    finally:
        json.dump(d, f, default=customEncode)
        f.close()


def addEntry(d, fields=('word', 'pron', 'pos', 'cl', 'subcl', 'de')):
    '''Prompts user to enter specified fields, or, if none are specified,
    word, pron, pos, cl, subcl, de'''
    e = dictionary.Entry()
    for f in fields:
        print(f, end=': ')
        e[f] = input()
        if e[f] == '':
            del e[f]
    d.append(dictionary.Entry(e))


def applyRules(d, rc, field='pron', field2=None):
    '''Returns a copy of d with field2 replaced by field with the list of rules
    applied. field defaults to pron, and field2 defaults to whatever field is'''
    out = dictionary.Dictionary()
    for e in d:
        o = dictionary.Entry(e)
        if field2 is None:
            field2 = field
        o[field2] = soundChanger.applyRules(o[field], rc)
        out.append(o)
    return out


def sortFields(d, fields):
    for i in range(len(d)):
        e = dictionary.Entry()
        for f in fields:
                e[f] = d[i][f]
        d[i] = e

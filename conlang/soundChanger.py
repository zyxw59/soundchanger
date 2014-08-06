#! /usr/bin/env python3.4  # lint:ok

import regex
from . import workers

def reencode(s):
    return s.encode('ascii', 'xmlcharrefreplace').decode()

# rules are stored as dicts:
# {'from': '', 'to': '', 'before': '', 'after': '',
# 'unbefore': '', 'unafter': ''}

# all cats would be included in a dict with keys being the cat name,
# and the values being arrays of the members of that cat
# e.g. {'nasal':['m', 'n', 'ŋ'], 'vlplos':['p', 't', 'k'], ...}


def parseSoundChange(l, cats):
    out = {}
    if len(l.split(' = ')) == 2:
        out['catName'] = l.split(' = ')[0].strip()
        category = l.split(' = ')[1]
        for c in cats:
            category = category.replace('{' + c + '}',
                                        ' '.join(x if x else '0' for x in cats[c]))
        out['category'] = category.split()
    else:
        try:
            out['from'] = l.split(' > ')[0].split(' / ')[0].split(' ! ')[0]
            if out['from'] == '0':
                out['from'] = ''
            out['from'] = out['from'].replace('#', r'((?<=^|\s)|(?=$|\s))')
            out['to'] = l.split(' > ')[1].split(' / ')[0].split(' ! ')[0]
            out['to'].replace('#', r'((?<=^|\s)|(?=$|\s))')
            if out['to'] == '0':
                out['to'] = ''
        except IndexError:
            out['to'] = ''
        try:
            out['before'] = l.split(' / ')[1].split('_')[0]
            out['before'] = out['before'].replace('#', r'((?<=^|\s)|(?=$|\s))')
            out['after'] = l.split(' / ')[1].split('_')[1].split(' ! ')[0]
            out['after'] = out['after'].replace('#', r'((?<=^|\s)|(?=$|\s))')
        except IndexError:
            pass
        try:
            out['unbefore'] = l.split(' ! ')[1].split('_')[0]
            out['unbefore'] = out['unbefore'].replace('#', r'((?<=^|\s)|(?=$|\s))')
            out['unafter'] = l.split(' ! ')[1].split('_')[1]
            out['unafter'] = out['unafter'].replace('#', r'((?<=^|\s)|(?=$|\s))')
        except IndexError:
            pass
    return out


def checkNumCats(m, ruleStr, cats):
    # now u test the match to see if it matches with numbered categories
    # matched = m.group(1)
    catIndex = []
    iNc = 0
    for c in regex.finditer(r'\{(\d+):([^}]*)}', ruleStr):
        # now what? maybe i should have it search the matched
        # string for this category, find which it is, and determine
        # which index for which numbered category
        cNum = int(c.group(1))
        cCat = c.group(2)
        cNc = 'nc' + str(iNc)
        cMatch = m.group(cNc)
        if cCat in cats:
            if len(catIndex) > cNum and catIndex[cNum] is not None:
                if cats[cCat][catIndex[cNum]] != cMatch:
                    return None
                    # if anything has the wrong number,
                    # quit out of this match
            else:
                workers.addPad(catIndex, cNum,
                               cats[cCat].index(cMatch))
            iNc += 1
    return catIndex


def findMatch(word, rule, cats):
    """Applies a specified rule to the given word,\
    making category replacements if necessary"""
    # create match, ignoring numbered categories
    matchStr = '('
    if 'before' in rule and rule['before'] != '':
        matchStr += '(?<=(?P<before>' + rule['before'] + '))'
    if 'unbefore' in rule and rule['unbefore'] != '':
        matchStr += '(?<!' + rule['unbefore'] + ')'
    matchStr += '(?P<from>' + rule['from'] + ')'
    if 'after' in rule and rule['after'] != '':
        matchStr += '(?=(?P<after>' + rule['after'] + '))'
    if 'unafter' in rule and rule['unafter'] != '':
        matchStr += '(?!' + rule['unafter'] + ')'
    matchStr += ')'
    ruleStr = matchStr
    # replace categories
    nc = [0]

    def catReplace(m):
        if m.group(2) in cats:
            out = '('
            if m.group(1) == '':
                out += '|'.join(cats[m.group(2)])
            else:
                out += '?P<nc' + str(nc[0]) + '>' + '|'.join(cats[m.group(2)])
                nc[0] += 1
            return out + ')'
        else:
            return m.group(0)

    matchStr = regex.sub(r'\{(\d*):?([^}]*)}', catReplace, matchStr)
    try:
        match = list(regex.finditer(matchStr, word))
    except regex._regex_core.error as e:
        raise type(e)(*(reencode(a) for a in e.args + (matchStr, word)))
    catIndex = []
    if nc[0] and match != []:
        for m in range(len(match)):
            catIndex.append(checkNumCats(match[m], ruleStr, cats))
    return (match, matchStr, ruleStr, catIndex)


def applyRule(word, rule, cats):
    match, matchStr, ruleStr, catIndex = findMatch(word, rule, cats)
    if match == []:
        return word
    i = [-1]

    def fromToTo(m):
        # now, replace from (m.group('from')) with to
        toStr = rule['to']

        i[0] += 1

        if checkNumCats(m, ruleStr, cats) is None:
            return m.group()

        def toCatReplace(c):
            cNum = int(c.group(1))
            cCat = c.group(2)
            if cCat in cats:
                if len(catIndex[i[0]]) > cNum and catIndex[i[0]][cNum] is not None:
                    if cats[cCat][catIndex[i[0]][cNum]] == '0':
                        return ''
                    return cats[cCat][catIndex[i[0]][cNum]]

        return regex.sub(r'\{(\d+):([^}]*)}', toCatReplace, toStr)

    word = regex.sub(matchStr, fromToTo, word)
    return word


def applyRules(word, soundChanges):
    cats = {}
    debug = ''
    try:
        for l in soundChanges:
            rc = parseSoundChange(l, cats)
            if 'catName' in rc:
                cats[rc['catName']] = rc['category']
            else:
                word = applyRule(word, rc, cats)
                debug += l + ' ' + word + '\n'
    except TypeError:
        for w in range(len(word)):
            word[w] = applyRules(word[w], soundChanges)
    return word, debug


def getCats(soundChanges):
    cats = {}
    for l in soundChanges:
        rc = parseSoundChange(l, cats)
        if 'catName' in rc:
            cats[rc['catName']] = rc['category']
    return cats
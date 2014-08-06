#! /usr/bin/env python3.3  # lint:ok

import regex
from . import workers

# rules are stored as dicts:
# {'from': '', 'to': '', 'before': '', 'after': '',
# 'unbefore': '', 'unafter': ''}

# all cats would be included in a dict with keys being the cat name,
# and the values being arrays of the members of that cat
# e.g. {'nasal':['m', 'n', 'ŋ'], 'vlplos':['p', 't', 'k'], ...}


def parseSoundChange(l, cats):
    out = {}
    if len(l.split(' = ')) == 2:
        out['catName'] = l.split(' = ')[0]
        category = l.split(' = ')[1]
        for c in cats:
            category = category.replace('{' + c + '}', ' '.join(cats[c]))
        out['category'] = category.split(' ')
    else:
        out['from'] = l.split(' > ')[0]
        if out['from'] == '0':
            out['from'] = ''
        out['from'] = out['from'].replace('#', '\\b')
        out['to'] = l.split(' > ')[1].split(' / ')[0].split(' ! ')[0]
        out['to'].replace('#', '\\b')
        if out['to'] == '0':
            out['to'] = ''
        try:
            out['before'] = l.split(' / ')[1].split('_')[0]
            out['before'] = out['before'].replace('#', '\\b')
            out['after'] = l.split(' / ')[1].split('_')[1].split(' ! ')[0]
            out['after'] = out['after'].replace('#', '\\b')
        except IndexError:
            pass
        try:
            out['unbefore'] = l.split(' ! ')[1].split('_')[0]
            out['unbefore'] = out['unbefore'].replace('#', '\\b')
            out['unafter'] = l.split(' ! ')[1].split('_')[1]
            out['unafter'] = out['unafter'].replace('#', '\\b')
        except IndexError:
            pass
    return out


def applyRule(word, rule, cats):
    """Applies a specified rule to the given word,\
    making category replacements if necessary"""
    # create match, ignoring numbered categories
    match = '('
    if 'before' in rule and rule['before'] != '':
        match += '(?<=(?P<before>' + rule['before'] + '))'
    if 'unbefore' in rule and rule['unbefore'] != '':
        match += '(?<!' + rule['unbefore'] + ')'
    if 'from' in rule:
        match += '(?P<from>' + rule['from'] + ')'
    if 'after' in rule and rule['after'] != '':
        match += '(?=(?P<after>' + rule['after'] + '))'
    if 'unafter' in rule and rule['unafter'] != '':
        match += '(?!' + rule['unafter'] + ')'
    match += ')'
    ruleStr = match
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

    match = regex.sub('\\{(\\d*):?([^}]*)}', catReplace, match)

    def fromToTo(m):
        # now u test the match to see if it matches with numbered categories
        # matched = m.group(1)
        catIndex = []
        if nc[0]:
            iNc = 0
            for c in regex.finditer('\\{(\\d+):([^}]*)}', ruleStr):
                # now what? maybe i should have it search the matched
                # string for this category, find which it is, and determine
                # which index for which numbered category
                cNum = int(c.group(1))
                cCat = c.group(2)
                cNc = 'nc' + str(iNc)
                cMatch = m.group(cNc)
                if cCat in cats:
                    if len(catIndex) < cNum and catIndex[cNum] is not None:
                        if cats[cCat][catIndex[cNum]] != cMatch:
                            return m.group(0)
                            # if anything has the wrong number,
                            # quit out of this match
                    else:
                        workers.addPad(catIndex, cNum,
                                       cats[cCat].index(cMatch))
                    iNc += 1
        # now, replace from (m.group('from')) with to
        toStr = rule['to']

        def toCatReplace(c):
            cNum = int(c.group(1))
            cCat = c.group(2)
            if cCat in cats:
                if len(catIndex) > cNum and catIndex[cNum] is not None:
                    return cats[cCat][catIndex[cNum]]

        return regex.sub('\\{(\\d+):([^}]*)}', toCatReplace, toStr)

    word = regex.sub(match, fromToTo, word)
    return word


def applyRules(word, soundChanges, showSteps=False):
    cats = {}
    for l in soundChanges:
        rc = parseSoundChange(l, cats)
        if 'catName' in rc:
            cats[rc['catName']] = rc['category']
        else:
            word = applyRule(word, rc, cats)
            if showSteps:
                print(rc, word)
    return word
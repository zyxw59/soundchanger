import os
from . import soundChanger, workers

def parseRule(l, cats):
    """Given a line l with the format 'a > b / c_d ! e_f' produces a dict of
    the form {'from': 'a', 'to': 'b', 'before': 'c', 'after': 'd', 'unbefore':
    'e', 'unafter': 'f'}. If l is of the form 'a = b c d', the output is a dict
    of the form {'catName': 'a', 'category': ['b', 'c', 'd']}. Category names
    in curly brackets are expanded."""
    wordBoundary = r'((?<=^|\s)|(?=$|\s))'
    out = {}
    if len(l.split(' = ')) == 2:
        # If there is an equals sign, it's a category
        out['catName'] = l.split(' = ')[0].strip()
        category = l.split(' = ')[1]
        # expand categories
        for c in cats:
            category = category.replace('{' + c + '}', ' '.join(cats[c]))
        out['category'] = category.split()
    else:
        # Otherwise, it's a sound change rule
        try:
            # Attempt to set 'from' and 'to'. If there isn't a ' > ', it will 
            # raise an IndexError when trying to set 'to', so 'from' will be
            # set, but 'to' will not. This could be used when parsing a rule to
            # be used as a search pattern, and not as a sound change. Need to
            # split on ' / ' and ' ! ' in case it is being used in this way.
            out['from'] = l.split(' > ')[0].split(' / ')[0].split(' ! ')[0]
            # Treat '0' like ''
            if out['from'] == '0':
                out['from'] = ''
            out['from'] = out['from'].replace('#', wordBoundary)
            out['to'] = l.split(' > ')[1].split(' / ')[0].split(' ! ')[0]
            out['to'].replace('#', wordBoundary)
            # Treat '0' like ''
            if out['to'] == '0':
                out['to'] = ''
        except IndexError:
            pass
        try:
            # Attempt to set 'before' and 'after'. If there isn't a ' / ', it
            # will raise an IndexError, and neither will be set. If there isn't
            # a '_', it will raise an IndexError when trying to set 'after', so
            # 'before' will be set, but 'after' will not.
            out['before'] = l.split(' / ')[1].split('_')[0].split(' ! ')[0]
            out['before'] = out['before'].replace('#', wordBoundary)
            out['after'] = l.split(' / ')[1].split('_')[1].split(' ! ')[0]
            out['after'] = out['after'].replace('#', wordBoundary)
        except IndexError:
            pass
        try:
            # Attempt to set 'unbefore' and 'unafter'. Same comments apply as
            # for 'before' and 'after'. Note that the negative conditions must
            # come after the positive conditions, if both exist.
            out['unbefore'] = l.split(' ! ')[1].split('_')[0]
            out['unbefore'] = out['unbefore'].replace('#', wordBoundary)
            out['unafter'] = l.split(' ! ')[1].split('_')[1]
            out['unafter'] = out['unafter'].replace('#', wordBoundary)
        except IndexError:
            pass
    return out


def applyRuleList(word, lines):
    """Applies the list of rules specified by lines to word. Returns a tuple of
    the final word and debug, which lists the outcome of each rule."""
    cats = {}
    debug = ''
    for l in lines:
        rc = parseRule(l, cats)
        if 'catName' in rc:
            cats[rc['catName']] = rc['category']
            debug += l + '\n'
        else:
            word = soundChanger.applyRule(word, rc, cats)
            debug += l + ' ' + word
    return word, debug


def loadTextFile(filename):
    """Loads a text file as a list of lines, ignoring blank lines and lines
    starting with '//'."""
    with open(os.path.expanduser(filename), encoding='utf-8') as f:
        return [l.strip('\n') for l in f if l.strip() and l[:1] != '//']


lf = lambda f: loadTextFile(workers.FILE_PATH + '/files/' + f)


def step(start, end):
    """Provides the next step between start and end. Does not check if they are
    linearly connected."""
    if start != '':
        # add a dot after nonempty strings before adding the next step. the dot
        # can't come from end, because we get the next step using .split('.'),
        # which necessarily will not contain a '.'
        start += '.'
    return start + end[len(start):].split('.')[0]


def applyRuleFiles(word, pairs, debug=0):
    """pairs format: (('a', 'a.b.c'), ('c', 'c.d')) or (('a', '.b.c'), ('c',
    '.d')), where FILE_PATH/files/a.b, FILE_PATH/files/a.b.c, and
    FILE_PATH/files/c.d each contain a list of sound change rules.
    debug = 0: don't show anything
    debug = 1: word at end of each pair
    debug = 2: word at end of each file
    debug = 3: word at end of each rule
    Returns a tuple of the final word and the debug info."""
    # if any debug info is to be shown, start by adding the initial word
    if len(pairs) > 0:
        db = pairs[0][0] + ': ' + word + '\n' if debug else ''
    for p in pairs:
        if len(p[1]) > 0 and p[1][0] == '.':
            # handle relative filenames
            p[1] = p[0] + p[1]
        if p[1].startswith(p[0]):
            cur, end = p
            while cur != end:
                cur = step(cur, end)
                word, steps = applyRuleList(word, lf(cur))
                if debug > 2:
                    db += steps
                if debug > 1:
                    db += cur + ': ' + word + '\n'
        else:
            # if the members of a pair aren't directly related, it can't do
            # anything
            raise Exception(p[1] + ' does not start with ' + p[0])
        if debug == 1:
            db += p[1] + ': ' + word + '\n'
    return word, db

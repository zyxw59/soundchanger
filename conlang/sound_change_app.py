import os
from . import sound_changer, workers

def parse_rule(l, cats):
    """Parses a sound change rule or category.

    Given a line l with the format 'a > b / c_d ! e_f' produces a dict of
    the form
    {
        'from': 'a',
        'to': 'b',
        'before': 'c',
        'after': 'd',
        'unbefore': 'e',
        'unafter': 'f'
    }.
    If l is of the form 'a = b c d', the output is a dict of the form
    {
        'cat_name': 'a',
        'category': ['b', 'c', 'd']
    }. Category names in curly brackets are expanded.

    Args:
        l: The line of text to parse
        cats: The dict of categories to use in the rule.

    Returns:
        A dict representing either a sound change rule or category.
    """
    word_boundary = r'((?<=^|\s)|(?=$|\s))'
    out = {}
    if len(l.split(' = ')) == 2:
        # If there is an equals sign, it's a category
        out['cat_name'] = l.split(' = ')[0].strip()
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
            out['from'] = out['from'].replace('#', word_boundary)
            out['to'] = l.split(' > ')[1].split(' / ')[0].split(' ! ')[0]
            out['to'].replace('#', word_boundary)
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
            out['before'] = out['before'].replace('#', word_boundary)
            out['after'] = l.split(' / ')[1].split('_')[1].split(' ! ')[0]
            out['after'] = out['after'].replace('#', word_boundary)
        except IndexError:
            pass
        try:
            # Attempt to set 'unbefore' and 'unafter'. Same comments apply as
            # for 'before' and 'after'. Note that the negative conditions must
            # come after the positive conditions, if both exist.
            out['unbefore'] = l.split(' ! ')[1].split('_')[0]
            out['unbefore'] = out['unbefore'].replace('#', word_boundary)
            out['unafter'] = l.split(' ! ')[1].split('_')[1]
            out['unafter'] = out['unafter'].replace('#', word_boundary)
        except IndexError:
            pass
    return out


def apply_rule_list(word, lines):
    """Applies a list of sound change rules.

    Args:
        word: The word to apply the rules to.
        lines: The list of sound changes to apply.

    Returns:
        A tuple of the final result of the sound changes, and the debug info,
        which lists each rule along with its outcome.
    """
    cats = {}
    debug = []
    for l in lines:
        rc = parse_rule(l, cats)
        if 'cat_name' in rc:
            cats[rc['cat_name']] = rc['category']
            debug.append(l)
        else:
            word = sound_changer.apply_rule(word, rc, cats)
            debug.append(l + ' ' + word)
    return word, '\n'.join(debug)


def load_text_file(filename):
    """Loads a text file as a list of lines.

    Args:
        filename: The path to the file.

    Returns:
        A list of the lines of the file, leaving out blank lines, and lines
        starting with '//'.
    """
    with open(os.path.expanduser(filename), encoding='utf-8') as f:
        return [l.strip('\n') for l in f if l.strip() and l[:1] != '//']


lf = lambda f: load_text_file(workers.FILE_PATH + '/files/' + f)


def apply_rule_files(word, pairs, debug=0):
    """Applies a set of sound change files.

    Args:
        word: The word to apply the changes to.
        pairs: A list of pairs of languages to be used as start and end points
            for the sound changes. For example, to go from language a to its
            descendant c, with intermediate b, pairs would be [['a', '.b.c']].
            To apply changes from a different tree on top of those changes, say
            from x to y, that pair would be included as the second element of
            pairs.
        debug: (Optional) The level of debug info to be included in the output.
            0 (Default): Don't include anything
            1: Include the word at the endpoint of each pair
            2: Include the word at the end of each file
            3: Include the full debug output from apply_rule_list

    Returns:
        A tuple of the final result of the sound changes, and the debug info.
    """
    db = []
    # if any debug info is to be output, and there is at least one change to be
    # applied, start by adding the initial language and word.
    if pairs and debug:
        db.append(pairs[0][0] + ': ' + word)
    for p in pairs:
        cur, end = p
        if p[1][0] != '.':
            if p[1].startswith(p[0]):
                end = ('.' if not cur else '') + end[len(cur):]
            else:
                raise Exception('{0[1]} does not start with {0[0]}'.format(p))
        while end:
            cur = (cur and cur + '.') + end.split('.')[1]
            try:
                end = '.' + end.split('.', 2)[2]
            except IndexError:
                end = ''
            word, steps = apply_rule_list(word, lf(cur))
            if debug > 2:
                db.append(steps)
            if debug > 1:
                db.append(cur + ': ' + word)
        if debug == 1:
            db.append(p[1] + ': ' + word)
    return word, '\n'.join(db)


import os
from os import path
from soundchanger.conlang import cache, sound_changer, workers

def parse_rule(l, cats):
    """Parses a sound change rule or category.

    Given a line l with the format 'a > b / c_d ! e_f', produces a dict of
    the form
    {
        'from': 'a',
        'to': 'b',
        'before': 'c',
        'after': 'd',
        'unbefore': 'e',
        'unafter': 'f'
    }.
    If l is of the form 'a > b / c_d ! e_f | g > h / i_j ! k_l', the output is
    a list of the '|' delimited rules.
    If l is of the form 'a = b c d', the output is a dict of the form
    {
        'cat_name': 'a',
        'category': ['b', 'c', 'd']
    }. Category names in curly brackets are expanded.

    Args:
        l: The line of text to parse.
        cats: The dict of categories to use in the rule.

    Returns:
        A dict representing either a sound change rule or category, or a list
        of several sound changes.
    """
    word_start = r'(?<=^|\s)'
    word_end = r'(?=$|\s)'
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
        if len(l.split(' | ')) > 1:
            # It's a list of sound changes
            return [parse_rule(ll, cats) for ll in l.split(' | ')]
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
            out['to'] = l.split(' > ')[1].split(' / ')[0].split(' ! ')[0]
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
            out['before'] = out['before'].replace('#', word_start)
            out['after'] = l.split(' / ')[1].split('_')[1].split(' ! ')[0]
            out['after'] = out['after'].replace('#', word_end)
        except IndexError:
            pass
        try:
            # Attempt to set 'unbefore' and 'unafter'. Same comments apply as
            # for 'before' and 'after'. Note that the negative conditions must
            # come after the positive conditions, if both exist.
            out['unbefore'] = l.split(' ! ')[1].split('_')[0]
            out['unbefore'] = out['unbefore'].replace('#', word_start)
            out['unafter'] = l.split(' ! ')[1].split('_')[1]
            out['unafter'] = out['unafter'].replace('#', word_start)
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
        try:
            rc = parse_rule(l, cats)
        except AttributeError:
            # l wasn't a string, but rather a dict
            rc = l
        if 'cat_name' in rc:
            cats[rc['cat_name']] = rc['category']
            debug.append(l)
        else:
            if 'from' in rc:
                word = sound_changer.apply_rule(word, rc, cats)
            else:
                word = sound_changer.apply_alternate_rules(word, rc, cats)
            debug.append(l + ' ' + word)
    return word, '\n'.join(debug)


def apply_rule_files(word, pairs, debug=0, file_loader=workers.lf):
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
            1: Include the word at the end of each file
            2: Include the full debug output from apply_rule_list
        file_loader: (Optional) A function that accepts filenames and returns
            lists of sound changes. Defaults to loading the file from
            wokers.FILE_PATH + '/files/'

    Returns:
        A tuple of the final result of the sound changes, and the debug info.
    """
    db = []
    # if any debug info is to be output, and there is at least one change to be
    # applied, start by adding the initial language and word.
    if pairs and debug:
        db.append(pairs[0][0] + ': ' + word)
    for cur in pair_iterator(pairs):
        word, steps = apply_rule_list(word, file_loader(cur))
        if debug > 1:
            db.append(steps)
        if debug:
            db.append(cur + ': ' + word)
    return word, '\n'.join(db)


class SoundChangeCache(cache.ModifiedCache):
    """A sound change cache.

    """
    def __init__(self, max_size=-1, file_cache_max_size=-1):
        """Initializes the cache.

        Args:
            max_size: (Optional) The maximum number of entries in the cache. If
                set to -1 (default), the cache has no limit.
            file_cache_max_size: (Optional) The maximum number of entries in
                the file cache. If set to -1 (default), the file cache has no
                limit.
        """
        self.file_cache = workers.FileCache(file_cache_max_size)
        funct = lambda word, pairs: apply_rule_files(word, pairs, 0,
                                                     self.file_cache)[0]
        mod = lambda word, pairs: modified(pairs)
        super().__init__(funct, mod, max_size)


def modified(pairs):
    """Returns the latest modification time from any file in a list of pairs.

    Args:
        pairs: The list of pairs to check, in the same format as
            apply_sound_change_files.

    Returns:
        The latest modification time from any file in the chain.
    """
    # gets the modification time from a file
    key = lambda cur: path.getmtime(workers.path_to_file(cur))
    # get max modification time from all the files
    return max(map(key, pair_iterator(pairs)))


def pair_iterator(pairs):
    """Iterates through a list of pairs.

    Args:
        pairs: The list of pairs to iterate through, in the same format as
            apply_sound_change_files.

    Yields:
        For each pair, each step on the way from the start to the end of that
        pair.
    """
    for p in pairs:
        cur, end = p
        if end[0] != '.':
            # if end is not relative
            if end.startswith(cur):
                # prepend '.' if cur is '', then add everything in end that
                # comes after cur, including the '.'
                end = ('.' if not cur else '') + end[len(cur):]
            else:
                raise Exception('{} does not start with {}'.format(end, cur))
        while end:
            # if cur != '', append '.', then append the first segment of end,
            # which is the segment *after* the initial '.', hence [1]
            cur = (cur and cur + '.') + end.split('.')[1]
            try:
                # '.' + the remaining portions of end (i.e. those after the
                # second '.')
                end = '.' + end.split('.', 2)[2]
            except IndexError:
                # there was nothing left.
                end = ''
            yield cur

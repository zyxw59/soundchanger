import os
import regex
from os import path
from soundchanger.conlang import cache, workers

regex.DEFAULT_VERSION = regex.VERSION1

cat_matcher = regex.compile(r'\{(\d*):?(\w*)\}')


def cat_replace(m, cats):
    """Replaces categories with regular expressions that will match them.

    Args:
        m: The match object. It should have two groups, the first one a
            (possibly zero-length) string of digits (the number for a numbered
            category), and the second a string of word characters (the name of
            the category).
        cats: The dict of categories to use in replacement.

    Returns:
        If there is no number, a pattern that simply matches every item in the
        category. If there is a number, the pattern will additionally capture
        the match to a named group, 'nc' + n + '_' + c, where n is the number,
        and c is the name of the category. If the name of the category is not
        found in cats, the original string is returned.
    """
    n, c = m.groups()
    if c in cats:
        if not n:
            return '(' + '|'.join(cats[c]) + ')'
        return '(?P<nc{}_{}>{})'.format(n, c, '|'.join(sorted(cats[c],
                                                              key=len,
                                                              reverse=True)))
    return m.group(0)


def to_cat_replace(m, cats, indices):
    """Performs numbered category replacement in the output of a sound change.

    Args:
        m: The match object. It should have two groups, the first one a
            non-zero-length) string of digits (the number of the numbered
            category), and the second a string of word characters (the name of
            the category).
        cats: The dict of categories to use in replacement.
        indices: The dict of numbered category indices to use in replacement.
            It's keys should be of the form 'nc' + n, where n is a number, and
            it's values should be the index associated with that numbered
            category.

    Returns:
        The appropriate element of the specified category. If that element is
        '0', it is replaced with ''. If the category isn't in cats, or the
        number isn't present in indices, the original string is returned.
    """
    n, c = m.groups()
    if c in cats and n != '' and 'nc' + n in indices:
        # treat '0' as '', to allow for categories with gaps
        if cats[c][indices['nc' + n]] == '0':
            return ''
        return cats[c][indices['nc' + n]]
    return m.group(0)

def compile_rule(rule, cats):
    """Converts a rule into a regex pattern

    Args:
        rule: The rule to search for. Should be a dict with the following:
                'from': The pattern to match.
                'before': (Optional) The pattern to match before 'from'.
                'unbefore': (Optional) The pattern to not match before 'from'.
                'after': (Optional) The pattern to match after 'from'.
                'unafter': (Optional) The patterrn to not match after 'from'.
        cats: The dict of categories to use in matching.

    Returns:
        A regex pattern that will match where the rule applies.
    """
    pattern = ''
    if 'before' in rule and rule['before'] != '':
        pattern += '(?<=(?P<before>' + rule['before'] + '))'
    if 'unbefore' in rule and rule['unbefore'] != '':
        pattern += '(?<!' + rule['unbefore'] + ')'
    pattern += '(?P<from>' + rule['from'] + ')'
    if 'after' in rule and rule['after'] != '':
        pattern += '(?=(?P<after>' + rule['after'] + '))'
    if 'unafter' in rule and rule['unafter'] != '':
        pattern += '(?!' + rule['unafter'] + ')'
    # Next, replace all the categories in the pattern with real regex
    pattern = cat_matcher.sub(lambda m: cat_replace(m, cats), pattern)
    return pattern


def find_matches(word, rule, cats):
    """Finds all matches of a rule in a word.

    Args:
        word: The word to search in.
        rule: The rule to search for. Should be a dict with the following:
                'from': The pattern to match.
                'before': (Optional) The pattern to match before 'from'.
                'unbefore': (Optional) The pattern to not match before 'from'.
                'after': (Optional) The pattern to match after 'from'.
                'unafter': (Optional) The patterrn to not match after 'from'.
        cats: The dict of categories to use in matching.

    Returns:
        A tuple of a list of match objects, and a list of the corresponding
        numbered category index dicts.
        In each match object, the sequences matched by the 'before', 'after',
        and 'from' patterns, if present are accessible as named capture groups.
        The numbered category index dicts have keys of the format 'nc' + n,
        where n is the number of that category, and values corresponding to the
        index associated with that numbered category.
    """
    # First, generate a regex pattern to search for
    pattern = compile_rule(rule, cats)
    # Now pattern is a valid regex
    matches = []
    cat_index = []
    for m in regex.finditer(pattern, word):
        # For each match, check that the numbered categories match, and
        # populate cat_index with the indices associate with each one
        try:
            cat_index.append(numbered_categories(m, cats))
            matches.append(m)
        except ValueError:
            # The numbered categories didn't match
            pass
    # Each match in matches is a valid match, since those that had mismatching
    # numbered categories were never added to it.
    return matches, cat_index


def numbered_categories(m, cats):
    """Returns a dict of the indices associated with each numbered category.

    Args:
        m: A match object. If any numbered categories are present in the match,
            they should exist as named captures of the form 'nc' + n + '_' + c,
            where n is the associated number, and c is the category.
        cats: The dict of categories to check against.

    Returns:
        A dict of the indices associated with each numbered category, with keys
        of the form 'nc' + n, where n is the number, and values corresponding
        to the indices associated with that numbered category.

    Raises:
        ValueError: The numbered categories didn't match.
    """
    captures = m.capturesdict()
    indices = {}
    for nc in captures:
        if nc.startswith('nc'):
            n, c = nc.split('_', 1)
            if len(set(captures[nc])) > 1:
                # the same number/category pair matched multiple strings
                raise ValueError()
            if n in indices:
                if cats[c][indices[n]] != captures[nc][0]:
                    # a previous number/category pair had a different index
                    raise ValueError()
            else:
                idx = [i for i, item in enumerate(cats[c])
                        if regex.match('^{}$'.format(item), captures[nc][0])]
                if not idx:
                    raise ValueError()
                indices[n] = idx[0]
    return indices


def apply_rule(word, rule, cats):
    """Applies a sound change to a word.

    Args:
        word: The word to apply the rule to.
        rule: The rule to search for. Should be a dict with the following:
                'from': The pattern to match.
                'to': The string to replace it with.
                'before': (Optional) The pattern to match before 'from'.
                'unbefore': (Optional) The pattern to not match before 'from'.
                'after': (Optional) The pattern to match after 'from'.
                'unafter': (Optional) The patterrn to not match after 'from'.
        cats: The dict of categories to use in search and replacement.

    Returns:
        The result of the sound change.
    """
    matches, cat_index = find_matches(word, rule, cats)
    return apply_to_matches(word, rule['to'], cats, matches, cat_index)


def apply_to_matches(word, to, cats, matches, cat_index):
    """Applies a sound change to a word, after matches have been found.

    Args:
        word: The word to apply the rule to.
        to: The 'to' field of the rule.
        cats: The dict of categories to use in replacement.
        matches: The list of matches.
        cat_index: The list of numbered category indices for the matches.

    Returns:
        The result of the sound change.
    """
    if not matches:
        # there were no matches, so no changes need to be applied
        return word
    # starting from the end of the string, replace each match with the output
    # of the rule
    for match, indices in zip(reversed(matches), reversed(cat_index)):
        # produce the appropriate replacement, given numbered categories, and
        # insert it into the word
        word = workers.slice_replace(
            word, match.span(),
            cat_matcher.sub(lambda m: to_cat_replace(m, cats, indices), to))
    return word


def apply_alternate_rules(word, rules, cats):
    """Applies the first matching rule to a word.

    Args:
        word: The word to apply the rule to.
        rules: A list of rules to attempt to apply. The first one that matches
            the word is applied.
        cats: The dict of categories to use in search and replacement.

    Returns:
        The result of the first matching rule. If none of the rules match, the
        word is returned unchanged.
    """
    for rule in rules:
        matches, cat_index = find_matches(word, rule, cats)
        if matches:
            return apply_to_matches(word, rule['to'], cats, matches, cat_index)


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
                word = apply_rule(word, rc, cats)
            else:
                word = apply_alternate_rules(word, rc, cats)
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

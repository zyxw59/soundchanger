import regex
from soundchanger.conlang import workers

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

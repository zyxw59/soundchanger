import regex
from . import workers

catMatcher = regex.compile(r'\{(\d*):?(\w*)\}')


def catReplace(m, cats):
    """Replaces categories and numbered categories from cats with regex strings
    that will match them appropriately"""
    n, c = m.groups()
    if c in cats:
        if n == '':
            return '(' + '|'.join(cats[c]) + ')'
        return '(?P<nc' + n + '_' + c + '>' + '|'.join(cats[c]) + ')'
    return m.group(0)


def toCatReplace(m, cats, indices):
    """Replaces numbered categories in a match with the appropriate element of
    a category"""
    n, c = m.groups()
    if c in cats and n != '':
        # treat '0' as '', to allow for categories with gaps
        if cats[c][indices['nc' + n]] == '0':
            return ''
        return cats[c][indices['nc' + n]]
    return m.group(0)


def findMatches(word, rule, cats):
    """Finds all matches of rule in word"""
    # First, generate a regex pattern to search for:
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
    pattern = catMatcher.sub(lambda m: catReplace(m, cats), pattern)
    # Now pattern is a valid regex
    matches = []
    catIndex = []
    for m in regex.finditer(pattern, word):
        # For each match, check that the numbered categories match, and
        # populate catIndex with the indices associate with each one
        try:
            catIndex.append(numberedCategories(m, cats))
            matches.append(m)
        except ValueError:
            # The numbered categories didn't match
            pass
    # Each match in matches is a valid match, since those that had mismatching
    # numbered categories were never added to it.
    return matches, catIndex


def numberedCategories(m, cats):
    """Returns a dict of the indices associated with each numbered category, of
    the form {'nc0': 1, 'nc1': 2, ...}"""
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
                indices[n] = cats[c].index(captures[nc][0])
    return indices


def applyRule(word, rule, cats):
    """Applies the sound change specified by rule to word"""
    matches, catIndex = findMatches(word, rule, cats)
    if len(matches) == 0:
        # there were no matches, so no changes need to be applied
        return word
    # starting from the end of the string, replace each match with the output
    # of the rule
    for match, indices in zip(reversed(matches), reversed(catIndex)):
        # produce the appropriate replacement, given numbered categories, and
        # insert it into the word
        word = workers.sliceReplace(word, match.span(),
                catMatcher.sub(lambda m: toCatReplace(m, cats, indices),
                    rule['to']))
    return word


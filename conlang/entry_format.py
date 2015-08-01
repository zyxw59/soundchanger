import regex
from soundchanger.conlang import workers

var_matcher = lambda s: r'(?<!\$)(?:\$\$)*\$(' + s + ')'
var_match = regex.compile(var_matcher(r'\w+'))
var_group = lambda s: '(?P<' + s + '>.*?)'

def match(pat, pat_args):
    """Generates a regular expression to match a dictionary entry.

    In pat, '$foo' matches the contents of pat_args['foo'] or nothing, if
    pat_args['foo'] exists. If it doesn't exist, it matches /.*?/. In
    pat_args['foo'], '$foo' matches /.*?/, and '$bar' is expanded as it would
    be in pat.

    Args:
        pat: The format of the entry.
        pat_args: The expansions for variables.

    Returns:
        A regular expression which will match a dictionary entry in the
        specified format. Fields mentioned in the pattern with '$' can be
        accessed as named capture groups of the match object.
    """
    args = {}
    for f in pat_args:
        args[f] = regex.escape(pat_args[f], True).replace(r'\$', '$')
        m = regex.search(var_matcher(f), args[f])
        while m is not None:
            sp = (m.start(1) - 1, m.end(1))
            args[f] = workers.slice_replace(args[f], sp, var_group(f))
            m = regex.search(var_matcher(f), args[f])
    pat = '^' + regex.escape(pat, True).replace(r'\$', '$') + '$'
    m = var_match.search(pat)
    while m is not None:
        sp = (m.start(1) -1, m.end(1))
        f = m.group(1)
        pat = workers.slice_replace(pat, sp,
                                    '({})?'.format(args.get(f, var_group(f))))
        m = var_match.search(pat)
    pat = pat.replace(' ', r'\s+')
    return regex.compile(pat)

def output(entry, pat, pat_args):
    """Generates a string from an entry using the specified format.

    In pat, if 'foo' is a field in the entry, '$foo' expands recursively to
    pat_args['foo'] if 'foo' is in pat_args, or entry['foo'] otherwise. In
    pat_args['foo'], '$foo' simply expands to entry['foo'].

    Args:
        entry: The dictionary entry to be stringified.
        pat: The format to use.
        pat_args: The expansions for variables.
    """
    args = {}
    for f in pat_args:
        args[f] = pat_args[f]
        m = regex.search(var_matcher(f), args[f])
        while m is not None:
            sp = (m.start(1) - 1, m.end(1))
            args[f] = workers.slice_replace(args[f], sp, entry.get(f) or '')
            m = regex.search(var_matcher(f), args[f])
    out = pat
    m = var_match.search(out)
    while m is not None:
        sp = (m.start(1) -1, m.end(1))
        f = m.group(1)
        if f in entry and entry[f] is not None:
            out = workers.slice_replace(out, sp, args.get(f, entry[f]))
        else:
            out = workers.slice_replace(out, sp, '')
        m = var_match.search(out)
    return out



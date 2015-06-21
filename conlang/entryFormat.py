import regex
from .workers import sliceReplace

varMatcher = lambda s: r'(?<!\$)(?:\$\$)*\$(' + s + ')'
varMatch = regex.compile(varMatcher(r'\w+'))
varGroup = lambda s: '(?P<' + s + '>.*?)'

def match(pat, patArgs):
    """In pat, '$foo' expands recursively to '(' + patArgs['foo'] ')?', if
    'foo' is in patArgs, or '(?P<foo>.*?)' otherwise. In patArgs['foo'], '$foo'
    expands to '(?P<foo>.*?)'. '^' and '$' are circumpended. ' ' expands to
    '\\s+'."""
    args = {}
    for f in patArgs:
        args[f] = regex.escape(patArgs[f], True).replace(r'\$', '$')
        m = regex.search(varMatcher(f), args[f])
        while m is not None:
            sp = (m.start(1) - 1, m.end(1))
            args[f] = sliceReplace(args[f], sp, varGroup(f))
            m = regex.search(varMatcher(f), args[f])
    pat = '^' + regex.escape(pat, True).replace(r'\$', '$') + '$'
    m = varMatch.search(pat)
    while m is not None:
        sp = (m.start(1) -1, m.end(1))
        f = m.group(1)
        pat = sliceReplace(pat, sp, '(' + args.get(f, varGroup(f)) + ')?')
        m = varMatch.search(pat)
    pat = pat.replace(' ', r'\s+')
    return regex.compile(pat)

def output(entry, pat, patArgs):
    """In pat, if 'foo' is in entry, '$foo' expands recursively to
    patArgs['foo'] if 'foo' is in patArgs, or entry['foo'] otherwise. In
    patArgs['foo'], '$foo' expands to entry['foo']."""
    args = {}
    for f in patArgs:
        args[f] = patArgs[f]
        m = regex.search(varMatcher(f), args[f])
        while m is not None:
            sp = (m.start(1) - 1, m.end(1))
            args[f] = sliceReplace(args[f], sp, entry.get(f) or '')
            m = regex.search(varMatcher(f), args[f])
    out = pat
    m = varMatch.search(out)
    while m is not None:
        sp = (m.start(1) -1, m.end(1))
        f = m.group(1)
        if f in entry and entry[f] is not None:
            out = sliceReplace(out, sp, args.get(f, entry[f]))
        else:
            out = sliceReplace(out, sp, '')
        m = varMatch.search(out)
    return out



import regex
import collections
import json
import os
from . import entryFormat, soundChanger, soundChangeApp


def customEncode(obj):
    """Custom JSON encoder for Dictionary and Entry classes"""
    if isinstance(obj, Dictionary):
        key = '__{!s}__'.format(obj.__class__.__name__)
        return {key: [list(obj), obj.alpha, obj.pat, obj.patArgs]}
    elif isinstance(obj, Entry):
        key = '__{!s}__'.format(obj.__class__.__name__)
        return {key: [obj.items(), obj.pat, obj.patArgs]}
    else:
        raise TypeError("obj {} of type {}".format(obj, type(obj)))


def classHook(dct):
    """JSON object hook to decode classes"""
    if len(dct) == 1:
        className, value = next(iter(dct.items()))
        className = className.strip('_')
        if className == 'Dictionary':
            return Dictionary(*value)
        elif className == 'Entry':
            return Entry(*value)
    return dct


class Dictionary(collections.UserList):
    """A dictionary containing entries in a conlang"""

    def __init__(self, l=[], alpha=None, pat=None, patArgs={}):
        self.alpha = alpha
        self.pat = pat
        self.patArgs = patArgs
        super().__init__()
        for e in l:
            self.append(Entry(e, pat, patArgs))

    @classmethod
    def fromJSON(cls, filename):
        """Loads a Dictionary from a JSON file."""
        with open(os.path.expanduser(filename), encoding='utf-8') as f:
            return json.load(f, object_hook=classHook)

    def __add__(self, d):
        return Dictionary(super().__add__(d), self.alpha, self.pat,
                self.patArgs)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return Dictionary(super().__getitem__(i),
                    self.alpha, self.pat, self.patArgs)
        elif isinstance(i, str):
            return StringList(self, i)
        elif isinstance(i, tuple):
            return Dictionary([e[i] for e in self], self.alpha, self.pat,
                    self.patArgs)
        else:
            return super().__getitem__(i)

    def __mul__(self, n):
        return Dictionary(super().__mul__(n), self.alpha, self.pat,
                self.patArgs)

    def __setitem__(self, index, data):
        if isinstance(index, str):
            for e in range(len(self)):
                self[e][index] = data[e]
        else:
            try:
                for f in range(len(index)):
                    try:
                        self.__setitem__(index[f], data[f])
                    except TypeError:
                        self.__setitem__(index[f], data[index[f]])
            except TypeError:
                super().__setitem__(index, data)

    def __str__(self):
        return self.formatString()

    def applyRuleList(self, lines, field1='pron', field2=None):
        """Applies the list of rules specified by lines to field1 in each entry
        of the dictionary, and sets field2 of each entry to the result. field1
        defaults to 'pron', and field2 defaults to whatever field1 is."""
        if field2 is None:
            field2 = field1
        for e in self:
            # soundChangeApp.applyRuleList returns a tuple of the word and the
            # debug lines, but we only want the word
            e[field2] = soundChangeApp.applyRuleList(e[field1], lines)[0]

    def applyRuleFiles(self, pairs, field1='pron', field2=None):
        """Applies the specified sound change files specified by pairs (as in
        soundChangeApp.applyRuleFiles) to field1 of each entry, setting field2
        the entry to the result. field1 defaults to 'pron', and field2 defaults
        to whatever field1 is."""
        if field2 is None:
            field2 = field1
        for e in self:
            # soundChangeApp.applyRuleFiles returns a tuple of the word and the
            # debug lines, but we only want the word
            e[field2] = soundChangeApp.applyRuleFiles(e[field1], pairs)[0]

    def delete(self, entry):
        """Removes an entry from the dictionary"""
        del self[self.index(entry)]

    def formatString(self, pat=None, patArgs={}):
        if pat is None:
            pat = self.pat
            if patArgs == {}:
                patArgs = self.patArgs
        return '\n'.join(e.formatString(pat, patArgs) for e in self)

    def orderFields(self, fields):
        """Orders the fields of each entry according to fields. If an entry
        lacks one of the fields, it is set to a value of ''."""
        for i in range(len(self)):
            e = Entry()
            for f in fields:
                e[f] = self[i].get(f, '')
            self[i] = e

    def search(self, s, field='word', cats=None):
        """Searches the dictionary for the specified string in the specified
        field and returns all matches. field defaults to 'word'"""
        out = Dictionary(alpha=self.alpha, pat=self.pat, patArgs=self.patArgs)
        for e in self:
            if e.check(s, field, cats):
                out.append(e)
        return out

    def sort(self, field='word', order=None):
        """Returns the dictionary's entries sorted on the specified field, by
        the ordering function passed, or default string ordering if none is
        passed. field defaults to 'word'"""
        if field == 'word' and order is None:
            order = self.alpha
        return Dictionary(sorted(self, key=lambda x: x.orderKey(field, order)),
                self.alpha, self.pat, self.patArgs)

    def toJSON(self, filename, override=False):
        """Saves the dictionary to the specified file"""
        try:
            f = open(os.path.expanduser(filename), 'x', encoding='utf-8')
        except FileExistsError:
            if not override:
                print('File exists, overwrite? [Y/n]', end=' ')
                if 'n' in input().lower():
                    return
            f = open(os.path.expanduser(fileName), 'w', encoding='utf-8')
        finally:
            json.dump(self, f, default=customEncode)
            f.close()


class Entry(collections.UserList):
    """A dictionary entry"""

    def __init__(self, e=[], pat=None, patArgs={}):
        if pat is None:
            self.pat = r'$word$pron$pos$cl$de'
            if patArgs == {}:
                self.patArgs = {}
                self.patArgs['pron'] = ' /$pron/'
                self.patArgs['pos'] = ' - $pos'
                self.patArgs['cl'] = ' ($cl$subcl)'
                self.patArgs['subcl'] = '.$subcl'
                self.patArgs['de'] = ': $de'
            else:
                self.patArgs = patArgs
        else:
            self.pat = pat
            self.patArgs = patArgs
        try:
            matcher = entryFormat.match(self.pat, self.patArgs)
            m = matcher.match(e)
            if m is not None:
                e = m.groupdict()
                for f in self.patArgs:
                    if '?P<' + f + '>' not in matcher.pattern:
                        e[f] = self.patArgs[f]
            else:
                e = {}
        except TypeError:
            pass
        try:
            super().__init__(e.items())
        except AttributeError:
            super().__init__(e)
        self.lookup = dict(self.data)

    def __add__(self, e):
        try:
            return Entry(super().__add__(e.items()), self.pat, self.patArgs)
        except AttributeError:
            return Entry(super().__add__(e), self.pat, self.patArgs)

    def __contains__(self, i):
        return i in self.lookup

    def __delitem__(self, i):
        try:
            del self.data[i]
        except TypeError:
            del self.data[self.keys().index(i)]
        self.lookup = dict(self.data)

    def __getitem__(self, i):
        try:
            if isinstance(i, slice):
                return Entry(super().__getitem__(i), self.pat, self.patArgs)
            else:
                return super().__getitem__(i)
        except TypeError:
            if isinstance(i, str):
                return self.lookup[i]
            else:
                return Entry([(f, self.lookup[f]) for f in i if f in self],
                        self.pat, self.patArgs)

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        return '{' + ', '.join(repr(k) + ': ' + repr(v) for k, v in l) + '}'

    def __setitem__(self, i, v):
        try:
            self.data[i] = v
            self.lookup = dict(self.data)
        except TypeError:
            try:
                self.data[self.keys().index(i)] = (i, v)
            except ValueError:
                self.data.append((i, v))
            self.lookup[i] = v

    def __str__(self):
        return self.formatString()

    def check(self, s, field, cats=None):
        """Checks to see if the entry contains the specified string in the
        specified field"""
        if cats is None:
            if field in self.lookup and self.lookup[field] is not None:
                return regex.search(s, self.lookup[field]) is not None
            else:
                return False
        else:
            try:
                try:
                    m = soundChanger.findMatches(self.lookup[field], s, cats)
                except TypeError:
                    s = soundChangeApp.parseRule(s, cats)
                    m = soundChanger.findMatches(self.lookup[field], s, cats)
                return m[0] is not None
            except KeyError:
                return False

    def formatString(self, pat=None, patArgs={}):
        if pat is None:
            pat = self.pat
            if patArgs == {}:
                patArgs = self.patArgs
        return entryFormat.output(self, pat, patArgs)

    def get(self, key, default=None):
        return self.lookup.get(key, default)

    def items(self):
        return self.data

    def keys(self):
        return [k for k, v in self.data]

    def orderKey(self, field, order=None):
        """Returns a key based on the ordering function passed, or based on
        default string ordering if none is passed"""
        try:
            return order(self.lookup[field])
        except TypeError:
            try:
                return sortKey(order)(self.lookup[field])
            except AttributeError:
                return self.lookup[field]

    def reorderFields(self, fields):
        """Returns an Entry with the fields reordered in the order specified by
        fields"""
        e = Entry(pat=self.pat, patArgs=self.patArgs)
        for f in fields:
            e[f] = self.get(f, '')
        return e

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default

    def values(self):
        return [v for k, v in self.data]


class StringList(collections.UserList):

    def __init__(self, d, field):
        self.d = d
        self.field = field
        self.data = [e[field] for e in d if field in e]

    def __delitem__(self, i):
        del self.d[i][self.field]

    def __setitem__(self, i, data):
        self.d[i][self.field] = data


def sortKey(alpha):
    """Returns a key for sorting in the alphabetical order in dict alpha, which
    has the format {'a': 1, 'b': 2 ...}. If a character or sequence of
    characters is to be ignored in alphabetization, it should correspond to a
    value of None in this dict. Characters not in this dict will be sorted at
    position -1"""
    a = sorted(alpha.keys(), key=lambda x: -len(x))

    def key(word):
        out = []
        for m in regex.finditer('(' + '|'.join(a) + ')|.', word):
            if m.group(1):
                if alpha[m[0]] is not None:
                    out.append(alpha[m[0]])
            else:
                out.append(-1)
        return out

    return key

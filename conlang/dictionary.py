#! /usr/bin/env python3.3  # lint:ok

import regex
import collections
from . import soundChanger


class Dictionary(collections.UserList):
    """A dictionary containing entries in a conlang"""

    def __add__(self, d):
        return Dictionary(super().__add__(d))

    def __getitem__(self, i):
        if isinstance(i, slice):
            return Dictionary(super().__getitem__(i))
        elif isinstance(i, str):
            return StringList(self, i)
        elif isinstance(i, tuple):
            return Dictionary([e[i] for e in self])
        else:
            return super().__getitem__(i)

    def __mul__(self, n):
        return Dictionary(super().__mul__(n))

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
        return '\n'.join([str(e) for e in self])

    def delete(self, entry):
        """Removes an entry from the dictionary"""
        del self[self.index(entry)]

    def formatString(self, fFunct=None):
        if fFunct is None:
            return str(self)
        return '\n'.join([e.formatString(fFunct) for e in self])

    def search(self, s, field='word', cats=None):
        """Searches the dictionary for the specified string in the specified\
         field and returns all matches. field defaults to 'word'"""
        out = Dictionary()
        for e in self:
            if e.check(s, field, cats):
                out.append(e)
        return out

    def sort(self, field='word', order=None):
        """Returns the dictionary's entries sorted on the specified field,\
        by the ordering function passed, or default string ordering if none is\
        passed. field defaults to 'word'"""
        return Dictionary(sorted(self, key=lambda x: x.orderKey(field, order)))


class Entry(collections.UserList):
    """A dictionary entry"""

    def __init__(self, e=[]):
        try:
            super().__init__(e.items())
        except AttributeError:
            super().__init__(e)
        self.lookup = dict(self.data)

    def __add__(self, e):
        try:
            return Entry(super().__add__(e.items()))
        except AttributeError:
            return Entry(super().__add__(e))

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
                return Entry(super().__getitem__(i))
            else:
                return super().__getitem__(i)
        except TypeError:
            if isinstance(i, str):
                return self.lookup[i]
            else:
                return Entry([(f, self.lookup[f]) for f in i if f in self])

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        return repr(self.lookup)

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
        out = ''
        if 'word' in self.lookup:
            out += self.lookup['word']
        if 'pron' in self.lookup and self.lookup['pron']:
            out += '(' + self.lookup['pron'] + ')'
        if 'pos' in self.lookup and self.lookup['pos']:
            out += ' - ' + self.lookup['pos']
        if 'cl' in self.lookup and self.lookup['cl']:
            out += '(' + self.lookup['cl']
            if 'subcl' in self.lookup and self.lookup['subcl']:
                out += '.' + self.lookup['subcl']
            out += ')'
        if 'de' in self.lookup and self.lookup['de']:
            out += ': ' + self.lookup['de']
        return out

    def check(self, s, field, cats=None):
        """Checks to see if the entry contains the specified string\
        in the specified field"""
        if cats is None:
            return (field in self.lookup) and (s in self.lookup[field])
        else:
            try:
                try:
                    m = soundChanger.findMatch(self.lookup[field], s, cats)
                except TypeError:
                    s = soundChanger.parseSoundChange(s, cats)
                    m = soundChanger.findMatch(self.lookup[field], s, cats)
                return m[0] is not None
            except KeyError:
                return False

    def formatString(self, fFunct=__str__):
        return fFunct(self)

    def get(self, key, default=None):
        return self.lookup.get(key, default)

    def items(self):
        return self.data

    def keys(self):
        return [k for k, v in self.data]

    def orderKey(self, field, order=None):
        """Returns a key based on the ordering function passed,\
        or based on default string ordering if none is passed"""
        try:
            return order(self.lookup[field])
        except TypeError:
            return self.lookup[field]

    def reorderFields(self, fields):
        """Returns an Entry with the fields reordered in the order specified by
        fields"""
        e = Entry()
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
    """Returns a key for sorting in the alphabetical order in list alpha"""
    a = sorted(alpha, key=lambda x: len(x))

    def key(word):
        out = []
        for m in regex.finditer('|'.join(a) + '.', word):
            try:
                out.append(alpha.index(m[0]))
            except ValueError:
                out.append(-1)
        return out

    return key

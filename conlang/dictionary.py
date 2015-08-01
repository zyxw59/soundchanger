import collections
import os
import json
import regex
from soundchanger.conlang import entry_format, sound_changer, sound_change_app


def custom_encode(obj):
    """Custom JSON encoder for Dictionary and Entry classes.

    Args:
        obj: The Dictionary or Entry object to be encoded

    Returns:
        A dict with one entry. It's key is '__Dictionary__' for a Dictionary,
        or '__Entry__' for an Entry.
        For a Dictionary, the entry's value is:
        [list(obj), obj.alpha, obj.pat, obj.pat_args].
        For an Entry, the entry's value is:
        [obj.items(), obj.pat, obj.pat_args].

    Raises:
        TypeError: obj not of type Dictionary or Entry."""
    if isinstance(obj, Dictionary):
        key = '__{!s}__'.format(obj.__class__.__name__)
        return {key: [list(obj), obj.alpha, obj.pat, obj.pat_args]}
    elif isinstance(obj, Entry):
        key = '__{!s}__'.format(obj.__class__.__name__)
        return {key: [obj.items(), obj.pat, obj.pat_args]}
    else:
        raise TypeError("obj {} of type {}".format(obj, type(obj)))


def class_hook(dct):
    """JSON object hook to decode classes.

    Args:
        dct: The dict generated from the JSON

    Returns:
        If dct has one entry, whose key is either '__Dictionary__' or
        '__Entry__', the Dictionary or Entry encoded by the JSON, or dct
        otherwise."""
    if len(dct) == 1:
        class_name, value = next(iter(dct.items()))
        class_name = class_name.strip('_')
        if class_name == 'Dictionary':
            return Dictionary(*value)
        elif class_name == 'Entry':
            return Entry(*value)
    return dct


class Dictionary(collections.UserList):
    """A dictionary containing entries in a conlang.

    Attributes:
        alpha: The default alphabetical ordering to use when sorting on the
            'word' field. It should be a dict, with key/value pairs
            corresponding to characters or sequences of characters, and the
            order they should be sorted at. Characters not in alpha will be
            sorted at position -1. Characters or sequences of characters to be
            ignored in sorting (for example, combining diacritics) should be
            assigned to a value of None.
        pat: The default pattern to use when printing the Dictionary, using
            the format specified in the entry_format module.
        pat_args: The default pattern arguments to use when printing the
            Dictionary, using the format specified in the entry_format module.
    """

    def __init__(self, l=None, alpha=None, pat=None, pat_args={}):
        """Initializes a Dictionary with a list.

        Args:
            l: The list of Entries to initialize the Dictionary with. Defaults
                to an empty list.
            alpha: The alphabetical ordering for the Dictionary.
            pat: The default pattern for printing the Dictionary.
            pat_args: The default pattern arguments for printing the
                Dictionary.
        """
        if l is None:
            l = []
        self.alpha = alpha
        self.pat = pat
        self.pat_args = pat_args
        super().__init__()
        for e in l:
            self.append(Entry(e, pat, pat_args))

    @classmethod
    def from_JSON(cls, filename):
        """Loads a Dictionary from a JSON file.

        Args:
            filename: The path to the file to load from.
        """
        with open(os.path.expanduser(filename), encoding='utf-8') as f:
            return json.load(f, object_hook=class_hook)

    def __add__(self, d):
        return Dictionary(super().__add__(d), self.alpha, self.pat,
                self.pat_args)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return Dictionary(super().__getitem__(i),
                    self.alpha, self.pat, self.pat_args)
        elif isinstance(i, str):
            return StringList(self, i)
        elif isinstance(i, tuple):
            return Dictionary([e[i] for e in self], self.alpha, self.pat,
                    self.pat_args)
        else:
            return super().__getitem__(i)

    def __mul__(self, n):
        return Dictionary(super().__mul__(n), self.alpha, self.pat,
                self.pat_args)

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
        return self.format_string()

    def append(self, entry):
        if isinstance(entry, Entry):
            super().append(entry)
        else:
            super().append(Entry(entry, pat=self.pat, pat_args=self.pat_args))

    def apply_rule_list(self, lines, field1='pron', field2=None):
        """Applies a list of sound change rules.

        Applies a list of sound change rules to each Entry in the Dictionary.

        Args:
            lines: The list of rules to apply.
            field1: The field of each Entry to apply the rules to. Defaults to
                'pron'.
            field2: The field of each Entry to assign the result of the sound
                change to. Defaults to whatever field1 is.
        """
        if field2 is None:
            field2 = field1
        for e in self:
            # sound_change_app.apply_rule_list returns a tuple of the word and the
            # debug lines, but we only want the word
            e[field2] = sound_change_app.apply_rule_list(e[field1], lines)[0]

    def apply_rule_files(self, pairs, field1='pron', field2=None):
        """Applies a set of sound change files.

        Applies the specified sound change files specified by pairs (as in
        sound_change_app.apply_rule_files) to each Entry in the Dictionary.

        Args:
            pairs: The sequence of sound change files to apply. For each pair,
                the necessary sound change files are sourced to go from the
                language specified by the first item of the pair to the one
                specified by the second item of the pair.
            field1: The field of each Entry to apply the rules to. Defaults to
                'pron'.
            field2: The field of each Entry to assign the result of the sound
                change to. Defaults to whatever field1 is.
        """
        if field2 is None:
            field2 = field1
        for e in self:
            # sound_change_app.apply_rule_files returns a tuple of the word and
            # the debug lines, but we only want the word
            e[field2] = sound_change_app.apply_rule_files(e[field1], pairs)[0]

    def format_string(self, pat=None, pat_args={}):
        """Formats the Dictionary using a specified pattern.

        Args:
            pat: The pattern to use, using the format specified in the
                entry_format module. Defaults to self.pat.
            pat_args: The pattern arguments to use, using the format specified
                in the entry_format module. If pat is unspecified, defaults to
                self.pat_args. Otherwise, defaults to {}.

        Returns:
            The Dictionary formatted as a string, with one Entry per line.
        """
        if pat is None:
            pat = self.pat
            if pat_args == {}:
                pat_args = self.pat_args
        return '\n'.join(e.format_string(pat, pat_args) for e in self)

    def search(self, s, field='word', cats=None):
        """Searches the Dicitonary.

        Args:
            s: The string to search for. If cats is specified, can use sound
                change rule syntax.
            field: The field to search for the string in. Defaults to 'word'.
            cats: (Optional) The categories to use if searching using sound
                change rule syntax.

        Returns:
            A Dictionary containing all the Entries that match the string.
        """
        out = Dictionary(alpha=self.alpha, pat=self.pat,
                         pat_args=self.pat_args)
        for e in self:
            if e.check(s, field, cats):
                out.append(e)
        return out

    def sort(self, field='word', order=None):
        """Sorts the Dictionary.

        Args:
            field: The field to sort on. Defaults to 'word'
            order: The order function or dict to sort by. If it is a dict,
                it should have key/value pairs corresponding to characters or
                sequences of characters, and the order they should be sorted
                at. Characters not in the dict will be sorted at position -1.
                Characters or sequences of characters to be ignored in sorting
                (for example, combining diacritics) should be assigned to a
                value of None. Defaults to standard string ordering.
        """
        if field == 'word' and order is None:
            order = self.alpha
        self.data = sorted(self, key=lambda x: x.order_key(field, order))

    def standardize(self, fields, pat=None, pat_args=None):
        """Standardizes the order of fields in Entries.

        Uniformly orders the fields of each Entry. If a field is not present in
        an Entry, it's value will be set to ''. Additionally, the pat and
        pat_args attributes of each Entry will be set.

        Args:
            fields: The ordering of fields to use.
            pat: The format pattern for printing. Defaults to self.pat
            pat_args: The pattern arguments for printing. Defaults to
                self.pat_args.
        """
        if pat is None:
            pat = self.pat
        if pat_args is None:
            pat_args = self.pat_args
        for i in range(len(self)):
            e = Entry(pat=pat, pat_args=pat_args)
            for f in fields:
                e[f] = self[i].get(f, '')
            self[i] = e

    def to_JSON(self, filename, override=False):
        """Saves the dictionary to the specified file.

        Args:
            filename: The path to the file to write to.
            override: If set to True, the file will be written, even if it
                exists. Otherwise, if the file exists, the user will be
                prompted to overwrite it. Defaults to False.
        """
        try:
            f = open(os.path.expanduser(filename), 'x', encoding='utf-8')
        except FileExistsError:
            if not override:
                print('File exists, overwrite? [Y/n]', end=' ')
                if 'n' in input().lower():
                    return
            f = open(os.path.expanduser(filename), 'w', encoding='utf-8')
        finally:
            json.dump(self, f, default=custom_encode)
            f.close()

    def to_text(self, filename, override=False, pat=None, pat_args={}):
        """Saves the dictionary as text using the specified format.

        Args:
            filename: the path to the file to write to.
            override: If set to True, the file will be written, even if it
                exists. Otherwise, if the file exists, the user will be
                prompted to overwrite it. Defaults to False.
            pat: The pattern to use, using the format specified in the
                entry_format module. Defaults to self.pat.
            pat_args: The pattern arguments to use, using the format specified
                in the entry_format module. Defaults to self.pat_args.
        """
        try:
            f = open(os.path.expanduser(filename), 'x', encoding='utf-8')
        except FileExistsError:
            if not override:
                print('File exists, overwrite? [Y/n]', end=' ')
                if 'n' in input().lower():
                    return
            f = open(os.path.expanduser(filename), 'w', encoding='utf-8')
        finally:
            f.write(self.format_string(pat, pat_args))
            f.close()


class Entry(collections.UserList):
    """A dictionary entry.

    Attributes:
        pat: The default pattern to use when printing the Entry, using
            the format specified in the entry_format module.
        pat_args: The default pattern arguments to use when printing the
            Entry, using the format specified in the entry_format module.
    """

    def __init__(self, e=[], pat=None, pat_args={}):
        if pat is None:
            self.pat = r'$word$pron$pos$cl$de'
            if pat_args == {}:
                self.pat_args = {
                    'pron': '/$pron/',
                    'pos': ' - $pos',
                    'cl': ' ($cl$subcl)',
                    'subcl': '.$subcl',
                    'de': ': $de'
                }
            else:
                self.pat_args = pat_args
        else:
            self.pat = pat
            self.pat_args = pat_args
        try:
            matcher = entry_format.match(self.pat, self.pat_args)
            m = matcher.match(e)
            if m is not None:
                e = m.groupdict()
                for f in self.pat_args:
                    if '?P<' + f + '>' not in matcher.pattern:
                        e[f] = self.pat_args[f]
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
            return Entry(super().__add__(e.items()), self.pat, self.pat_args)
        except AttributeError:
            return Entry(super().__add__(e), self.pat, self.pat_args)

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
                return Entry(super().__getitem__(i), self.pat, self.pat_args)
            else:
                return super().__getitem__(i)
        except TypeError:
            if isinstance(i, str):
                return self.lookup[i]
            else:
                return Entry([(f, self.lookup[f]) for f in i if f in self],
                        self.pat, self.pat_args)

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        return '{' + ', '.join(repr(k) + ': ' + repr(v) for k, v in
                self.items()) + '}'

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
        return self.format_string()

    def check(self, s, field='word', cats=None):
        """Checks whether the Entry matches a string.

        Args:
            s: The string to check for. If cats is specified, can use sound
                change rule syntax.
            field: The field to check for the string in. Defaults to 'word'.
            cats: (Optional) The categories to use if searching using sound
                change rule syntax.
        """
        if cats is None:
            if field in self and self[field] is not None:
                return regex.search(s, self[field]) is not None
            else:
                return False
        else:
            try:
                try:
                    m = sound_changer.find_matches(self.lookup[field], s, cats)
                except TypeError:
                    s = sound_change_app.parse_rule(s, cats)
                    m = sound_changer.find_matches(self.lookup[field], s, cats)
                return m[0] is not None
            except KeyError:
                return False

    def format_string(self, pat=None, pat_args={}):
        """Formats the Entry using a specified pattern.

        Args:
            pat: The pattern to use, using the format specified in the
                entry_format module. Defaults to self.pat.
            pat_args: The pattern arguments to use, using the format specified
                in the entry_format module. If pat is unspecified, defaults to
                self.pat_args. Otherwise, defaults to {}.

        Returns:
            The Entry formatted as a string.
        """
        if pat is None:
            pat = self.pat
            if pat_args == {}:
                pat_args = self.pat_args
        return entry_format.output(self, pat, pat_args)

    def get(self, key, default=None):
        return self.lookup.get(key, default)

    def items(self):
        return self.data

    def keys(self):
        return [k for k, v in self.data]

    def order_key(self, field='word', order=None):
        """Returns a key to sort on.

        Args:
            field: The field to base the key on. Defaults to 'word'
            order: The order function or dict to sort by. If it is a dict,
                it should have key/value pairs corresponding to characters or
                sequences of characters, and the order they should be sorted
                at. Characters not in the dict will be sorted at position -1.
                Characters or sequences of characters to be ignored in sorting
                (for example, combining diacritics) should be assigned to a
                value of None. Defaults to standard string ordering.

        Returns:
            A key that can be used in sorting.
        """
        try:
            return order(self[field])
        except TypeError:
            try:
                return sort_key(order)(self[field])
            except AttributeError:
                return self[field]

    def reorder_fields(self, fields):
        """Reorders the fields of the Entry.

        Args:
            fields: The ordering of fields to use.
        """
        e = []
        for f in fields:
            e.append((f, self.get(f, '')))
        self.data = e

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default

    def values(self):
        return [v for k, v in self.data]


class StringList(collections.UserList):
    """A single field in a Dictionary.

    Represents a single field in a Dictionary as a list of strings. The nth
    string is that field in the nth Entry of the Dictionary.

    Attributes:
        d: The Dictionary to which the Entries belong.
        field: The field represented.
    """

    def __init__(self, d, field):
        self.d = d
        self.field = field
        self.data = [e[field] for e in d if field in e]

    def __delitem__(self, i):
        del self.d[i][self.field]

    def __setitem__(self, i, data):
        self.d[i][self.field] = data


def sort_key(alpha):
    """Converts a dict to a sorting key function.

    Args:
        alpha: A dict, with key/value pairs corresponding to characters or
            sequences of characters, and the order they should be sorted at.
            Characters not in the dict will be sorted at position -1.
            Characters or sequences of characters to be ignored in sorting
            (for example, combining diacritics) should be assigned to a value
            of None.
            Alternatively, an iterable, with the characters or sequences of
            characters in the order they should be sorted. This does not allow
            for ignoring characters or sequences of characters, or sorting
            multiple different characters or sequences of characters at the
            same index.

    Returns:
        A function, which when applied to a string, generates a sort key.
    """
    if not isinstance(alpha, dict):
        alpha = {alpha[i]: i for i in range(len(alpha))}
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

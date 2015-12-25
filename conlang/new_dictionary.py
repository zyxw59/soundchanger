import collections
import itertools
import os
import json
import regex
from soundchanger.conlang import (cache, entry_format, sound_changer,
                                  sound_change_app)


def custom_encode(obj):
    """Custom JSON encoder for Dictionary and Entry classes.

    Args:
        obj: The Dictionary or Entry object to be encoded

    Returns:
        For a Dictionary, a dict with one entry, whose key is '__Dictionary__',
        and whose value is [list(obj), obj.alpha, obj.pat, obj.pat_args,
        obj.auto_fields]. For an Entry, obj.data.

    Raises:
        TypeError: obj not of type Dictionary or Entry.
    """
    if isinstance(obj, DictionaryMethods):
        key = '__Dictionary__'
        return {key: [list(obj), obj.alpha, obj.pat, obj.pat_args,
                      obj.auto_fields]}
    elif isinstance(obj, Entry):
        return obj.data
    else:
        raise TypeError("obj {} of type {}".format(obj, type(obj)))


def class_hook(dct):
    """JSON object hook to decode classes.

    Args:
        dct: The dict generated from the JSON

    Returns:
        If dct has one entry, whose key is '__Dictionary__' the Dictionary
        encoded by the JSON, or dct otherwise."""
    if len(dct) == 1:
        class_name, value = next(iter(dct.items()))
        class_name = class_name.strip('_')
        if class_name == 'Dictionary':
            return Dictionary(*value)
    return dct


class DictionaryMethods(object):
    """Methods for a Dictionary.

    """

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
            # sound_change_app.apply_rule_list returns a tuple of the word and
            # the debug lines, but we only want the word
            e[field2] = sound_change_app.apply_rule_list(e[field1], lines)

    def apply_rule_files(self, pairs, field1='pron', field2=None):
        """Applies a set of sound change files.

        Applies the set of sound change files specified by pairs (as in
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
            e[field2] = self.cache(e[field1], pairs)[0]

    def format_string(self, pat=None, pat_args=None):
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
            if pat_args is None:
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
            A DictionaryView containing all the Entries that match the string.
        """
        indices = (i for i, v in enumerate(self) if v.check(s, field, cats))
        return DictionaryView(self, indices)

    def sorted(self, field='word', order=None):
        """Returns a sorted view of the Dictionary.

        Args:
            field: The field to sort on. Defaults to 'word'
            order: The order function or dict to sort by. If it is a dict,
                it should have key/value pairs corresponding to characters or
                sequences of characters, and the order they should be sorted
                at. Characters not in the dict will be sorted at position -1.
                Characters or sequences of characters to be ignored in sorting
                (for example, combining diacritics) should be assigned to a
                value of None. Defaults to self.alpha, or if that is None,
                standard string ordering.

        Returns:
            A sorted DictionaryView.
        """
        if field == 'word' and order is None:
            order = self.alpha
        if order is None:
            indices = sorted(range(len(self)), key=lambda x: self[x][field])
        else:
            indices = sorted(range(len(self)),
                             key=lambda x: self[x].order_key(field, order))
        return DictionaryView(self, indices)

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

    def to_text(self, filename, override=False, pat=None, pat_args=None):
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


class Dictionary(DictionaryMethods, collections.UserList):
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
        auto_fields: Fields to be automatically generated for each Entry.
            A dict whose keys are the fields to be automatically generated, and
            whose values are tuples of the field from which it is generated,
            and a tuple that can be passed to
            sound_change_app.apply_rule_files.
    """

    def __init__(self, l=None, alpha=None, pat=None, pat_args=None,
                 auto_fields=None):
        """Initializes a Dictionary with a list.

        Args:
            l: The list of Entries to initialize the Dictionary with. Defaults
                to an empty list.
            alpha: The alphabetical ordering for the Dictionary.
            pat: The default pattern for printing the Dictionary.
            pat_args: The default pattern arguments for printing the
                Dictionary.
            auto_fields: Fields to be automatically generated for each Entry.
                Should be a dict whose keys are the fields to be automatically
                generated, and whose values are tuples of the field from which
                it is generated, and a tuple that can be passed to
                sound_change_app.apply_rule_files.
        """
        if l is None:
            l = []
        self.alpha = alpha
        self.pat = pat
        self.pat_args = pat_args
        self.auto_fields = auto_fields or {}
        for f in self.auto_fields:
            pairs = self.auto_fields[f][1]
            self.auto_fields[f][1] = tuple(tuple(p) for p in pairs)
        self.cache = sound_change_app.SoundChangeCache()
        super().__init__()
        for e in l:
            self.append(e)

    @classmethod
    def from_JSON(cls, filename):
        """Loads a Dictionary from a JSON file.

        Args:
            filename: The path to the file to load from.

        Returns:
            A Dictionary.
        """
        with open(os.path.expanduser(filename), encoding='utf-8') as f:
            return json.load(f, object_hook=class_hook)

    @classmethod
    def from_text(cls, filename, alpha=None, pat=None, pat_args=None,
                  auto_fields=None):
        """Loads a Dictionary from a text file.

        Args:
            filename: The path to the file to load from.
            alpha: (Optional) The alphabetical ordering for the Dictionary.
                Defaults to standard string ordering.
            pat: (Optional) The pattern to use when reading the file. Defaults
                to the default behavior of entry_format.match.
            pat_args: (Optional) The pattern arguments to use when reading the
                file.  Defaults to the default behavior of entry_format.match.
            auto_fields: (Optional) Fields to be automatically generated for
                each Entry. Defaults to {}
        """
        with open(os.path.expanduser(filename), encoding='utf-8') as f:
            return cls(f, alpha, pat, pat_args)

    def __add__(self, d):
        return type(self)(super().__add__(d), self.alpha, self.pat,
                self.pat_args, self.auto_fields)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return DictionaryView(self, i)
        return super().__getitem__(i)

    def __mul__(self, n):
        return type(self)(super().__mul__(n), self.alpha, self.pat,
                self.pat_args)

    def __setitem__(self, index, data):
        super().__setitem__(index, data)

    def __str__(self):
        return self.format_string()

    def append(self, entry):
        e = Entry(entry, self)
        if e:
            super().append(Entry(entry, self))

    def sort(self, field='word', order=None):
        """Sorts the Dictionary in place.

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
        self.data = list(self.sorted(field, order))


class DictionaryView(DictionaryMethods, collections.MappingView,
                     collections.Set):
    """A view of a Dictionary.

    """

    def __init__(self, parent, selection):
        """Initializes a DictionaryView

        Args:
            parent: The Dicitonary or DictionaryView to be viewed.
            selection: The selection of the Dictionary to view. Either a slice
                or an iterable that generates indices to include in the view.
        """
        super().__init__(parent)
        if isinstance(selection, slice):
            self.selection = range(*selection.indices(len(parent)))
        else:
            # convert selection to a list for three reasons:
            # 1: defined length
            # 2: subscriptable
            # 3: doesn't run out
            self.selection = list(selection)

    @classmethod
    def _from_iterable(cls, it):
        if isinstance(it, cls):
            it = it.selection
        return set(it)

    def __contains__(self, item):
        for e in self:
            if e == item:
                return True
        return False

    def __getattr__(self, attr):
        # Get these from the parent, but only if they haven't been set manually
        # __getattr__ is only called if attr isn't found normally in the object
        if attr in ['alpha', 'pat', 'pat_args', 'auto_fields']:
            return self._mapping.__getattribute__(attr)
        # If __getattr__ is being called, attr wasn't found, so if it's not one
        # of the above,
        raise AttributeError

    def __getitem__(self, i):
        if isinstance(i, slice):
            # deal with slice - we need to generate another DictionaryView
            # self.selection is either a range or a list, so it is
            # subscriptable
            return type(self)(self._mapping, self.selection[i])
        # deal with plain integers. again, self.selection is guaranteed to be
        # subscriptable
        return self._mapping[self.selection[i]]

    def __iter__(self):
        return (self._mapping[i] for i in self.selection)

    def __len__(self):
        return len(self.selection)

    def __repr__(self):
        return 'DictionaryView({!r}, {!r})'.format(self._mapping,
                                                   self.selection)

    def __str__(self):
        return '\n'.join(str(e) for e in self)


class Entry(collections.UserDict):
    """A dictionary entry.

    Attributes:
        parent: The Dictionary it is an entry in.
    """

    def __init__(self, e=None, parent=None):
        """Initializes an Entry.

        Args:
            e: A dict or str to initialize the Entry with. If a str, it is
                converted to an Entry using parent.pat and parent.pat_args.
                Otherwise, it is initialized as if e was passed to dict().
                Defaults to {}.
            parent: The Dictionary that contains the Entry. Defaults to a new,
                empty Dictionary.
        """
        self.parent = Dictionary() if parent is None else parent
        if e is None:
            e = {}
        if isinstance(e, str):
            matcher = entry_format.match(self.parent.pat, self.parent.pat_args)
            m = matcher.match(e)
            if m is not None:
                e = m.groupdict()
            else:
                e = {}
        super().__init__(e)

    def __contains__(self, key):
        return super().__contains__(key) or key in self.parent.auto_fields

    def __getitem__(self, key):
        if key in self.data:
            return super().__getitem__(key)
        src, pairs = self.parent.auto_fields[key]
        return self.parent.cache(self[src], pairs)

    def __iter__(self):
        yield from self.data.keys() | self.parent.auto_fields.keys()

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
        f = self[field]
        if cats is None:
            # treat s as plain regex
            return regex.search(s, f) is not None
        # s is a sound change rule
        try:
            # parse s
            s = sound_change_app.parse_rule(s, cats)
        except AttributeError:
            # s is a dict (i.e. already parsed)
            pass
        return bool(sound_changer.find_matches(f, s, cats)[0])

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
            pat = self.parent.pat
            if pat_args == {}:
                pat_args = self.parent.pat_args
        return entry_format.output(self, pat, pat_args)

    def get(self, key, default=None):
        return self[key] if key in self else default

    def items(self):
        yield from ((k, self[k]) for k in self)

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

    def values(self):
        return (self[k] for k in self.keys())


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
        # alpha *should* be a dict, but if passed a list or a string, treat it
        # as an ordering
        try:
            alpha = {k: v for v, k in enumerate(alpha)}
        except TypeError:
            # alpha isn't iterable, and is therefore useless as a key
            alpha = {}
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

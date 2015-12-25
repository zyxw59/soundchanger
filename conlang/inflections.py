import collections
from soundchanger.conlang import sound_change_app

class DotDict(dict):
    """A nested dict whose entries can be accessed using keys with '.'

    """
    def __contains__(self, k):
        if '.' in k:
            k = k.split('.', 1)
            return k[0] in self and k[1] in self[k[0]]
        return super().__contains__(k)

    def __delitem__(self, k):
        if '.' in k:
            k = k.split('.', 1)
            del self[k[0]][k[1]]
        else:
            super().__delitem__(k)

    def __getitem__(self, k):
        if '.' in k:
            k = k.split('.', 1)
            return self[k[0]][k[1]]
        return super().__getitem__(k)

    def __setitem__(self, k, v):
        if '.' in k:
            k = k.split('.', 1)
            if k[0] not in self:
                self[k[0]] = type(self)()
                self[k[0]].parent = self
            self[k[0]][k[1]] = v
        else:
            super().__setitem__(k, v)
            try:
                v.parent = self
            except AttributeError:
                # if v doesn't have a parent attribute, don't bother setting it
                pass

    def deepiter(self):
        """Iterates through all nested keys.

        Yields:
            Each key that can be used to return a plain value from the DotDict
            (as opposed to returning another DotDict). Nested keys are
            delimited with '.'.
        """
        for k in self.keys():
            try:
                for kk in self[k].deepiter():
                    yield k + '.' + kk
            except AttributeError:
                yield k

    def format_keys(self, *sep):
        """Produces a display of the keys of the table.

        Args:
            *sep: (Optional) The characters to delimit elements of the table.
                Each argument will be used for one level of the table, and the
                last argument will be used for all following levels. For
                example, if the only argument is '\\t', then all levels will
                use '\\t' to delimit their elements. If the first argument is
                '\\n', and the second argument is '\\t', then the top level
                will use '\\n' to delimit it's elements, and all following
                levels will use '\\t'. Defaults to ('\\n', '\\t')

        Returns:
            A string containing the formatted table of keys.
        """
        if not sep:
            sep = ('\n', '\t')
        elif not sep[1:]:
            sep *= 2
        out = []
        for k in self:
            try:
                out.append(k + sep[1] + self[k].format_keys(*sep[1:]))
            except AttributeError:
                out.append(k)
        return sep[0].join(out)

    def format_values(self, *sep):
        """Produces a display of the values of the table.

        Args:
            *sep: (Optional) The characters to delimit elements of the table.
                Each argument will be used for one level of the table, and the
                last argument will be used for all following levels. For
                example, if the only argument is '\\t', then all levels will
                use '\\t' to delimit their elements. If the first argument is
                '\\n', and the second argument is '\\t', then the top level
                will use '\\n' to delimit it's elements, and all following
                levels will use '\\t'. Defaults to ('\\n', '\\t')

        Returns:
            A string containing the formatted table of values.
        """
        if not sep:
            sep = ('\n', '\t')
        elif not sep[1:]:
            sep *= 2
        out = []
        for k in self:
            try:
                out.append(self[k].format_values(*sep[1:]))
            except AttributeError:
                out.append(self[k])
        return sep[0].join(out)


    def get(self, k, v=None):
        if k in self:
            return self[k]
        return v


class OrderedDotDict(DotDict, collections.OrderedDict):
    pass


class Inflection(OrderedDotDict):
    """A table of functions that inflects a word.

    """
    def __call__(self, entry):
        """Inflects a word.

        Args:
            entry: The word (as a dictionary.Entry) to inflect.

        Returns:
            An InflectionTable of the inflected forms of the word.
        """
        return InflectionTable((k, v(entry)) for k, v in self.items())


class InflectionRuleTable(Inflection):
    """A table of rules to inflect a word.

    Attributes:
        common: A list of sound changes and categories to be applied for every
            inflection.
        field: The field of entries to apply the rules to. Defaults to 'word'.
    """
    def __init__(self, *args, **kwargs):
        """Initializes an empty InflectionRuleTable."""
        self._common = []
        self.parent = None
        super().__init__(*args, **kwargs)

    def __getattr__(self, attr):
        if attr == 'field':
            if self.parent is None:
                return 'word'
            return self.parent.field
        if attr == 'common':
            if self.parent is None:
                return self._common
            return self.parent.common + self._common
        raise AttributeError

    def __getitem__(self, k):
        if k not in self:
            self[k] = type(self)()
        return super().__getitem__(k)

    def __setattr__(self, attr, v):
        if attr == 'common':
            super().__setattr__('_common', v)
        else:
            super().__setattr__(attr, v)

    def __setitem__(self, k, v):
        if '.' in k:
            k = k.split('.', 1)
            if k[0] not in self:
                self[k[0]] = type(self)()
                self[k[0]].parent = self
            self[k[0]][k[1]] = v
        else:
            if isinstance(v, dict):
                super().__setitem__(k, type(self)(v))
            else:
                super().__setitem__(k, InflectionRule(v))
            self[k].parent = self


class InflectionRule(list):
    """A callable object that inflects a function based on sound change rules.

    Attributes:
        common: Additional rules to apply before rules.
        field: The field of an entry to apply the rules to.
        rules: The list of rules to apply.
    """
    def __init__(self, rules=None):
        """Initializes an InflectionRule object.

        Args:
            rules: (Optional) The list of rules to apply.
        """
        super().__init__(rules or [])
        self._common = []
        self.parent = None

    def __call__(self, entry):
        """Inflects a dictionary entry.

        Args:
            entry: The entry to inflect. Alternatively, a string to inflect.

        Returns:
            The inflected form of the word.
        """
        rules = self.common + self
        try:
            word = entry[self.field]
        except TypeError:
            word = entry
        return sound_change_app.apply_rule_list(word, rules)[0]

    def __getattr__(self, attr):
        if attr == 'field':
            if self.parent is None:
                return 'word'
            return self.parent.field
        if attr == 'common':
            if self.parent is None:
                return self._common
            return self.parent.common + self._common
        raise AttributeError

    def __setattr__(self, attr, v):
        if attr == 'common':
            super().__setattr__('_common', v)
        else:
            super().__setattr__(attr, v)


class InflectionTable(OrderedDotDict):
    """A table of inflected forms of a word.

    """
    def __str__(self):
        return self.format_values()

import collections
from soundchanger.conlang import sound_change_app

class DotDict(dict):
    """A recursive dict whose entries can be accessed using keys with '.'"""

    def __contains__(self, k):
        """dd.__contains__(k) <==> k in dd"""
        if '.' in k:
            k = k.split('.', 1)
            return k[0] in self and k[1] in self[k[0]]
        return super().__contains__(k)

    def __delitem__(self, k):
        """dd.__delitem__(k) <==> del dd[k]"""
        if '.' in k:
            k = k.split('.', 1)
            del self[k[0]][k[1]]
        else:
            super().__delitem__(k)

    def __getitem__(self, k):
        """dd.__getitem__(k) <==> dd[k]"""
        if '.' in k:
            k = k.split('.', 1)
            return self[k[0]][k[1]]
        return super().__getitem__(k)

    def __setitem__(self, k, v):
        """dd.__setitem__(k, v) <==> dd[k] = v"""
        if '.' in k:
            k = k.split('.', 1)
            if k[0] not in self:
                self[k[0]] = type(self)()
            self[k[0]][k[1]] = v
        else:
            super().__setitem__(k, v)

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

    def get(self, k, v=None):
        """dd.get(k, v) -> dd[k] if k in dd else v. v defaults to None."""
        if k in self:
            return self[k]
        return v

    def transpose(self):
        """Transposes the first level of nested keys.

        Keys nested one level (e.g. 'foo.bar') are transposed (e.g. to
        'bar.foo'). Keys that are not nested (e.g. 'baz') are left as they are,
        and keys nested two or more levels (e.g. 'a.b.c') are only transposed
        at the first level (e.g. to 'b.a.c')

        Returns:
            A DotDict with the first level of nesting transposed.
        """
        out = type(self)()
        for k in self.deepiter():
            ks = k.split('.', 2)
            ks[:2] = ks[1::-1]
            out['.'.join(ks)] = self[k]
        return out


class OrderedDotDict(DotDict, collections.OrderedDict):
    pass


class Inflection(OrderedDotDict):
    """A table of functions that inflect a word."""

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
        self.common = []
        self.field = 'word'
        super().__init__(*args, **kwargs)

    def __setitem__(self, k, v):
        """irt.__setitem__(k, v) <==> irt[k] = v"""
        if '.' in k:
            k = k.split('.', 1)
            if k[0] not in self:
                self[k[0]] = type(self)()
            self[k[0]][k[1]] = v
        else:
            if isinstance(v, dict):
                super().__setitem__(k, type(self)(v))
            else:
                super().__setitem__(k, InflectionRule(v, self.field))
            self[k].common = self.common
            self[k].field = self.field

    def formatted(self, *sep):
        """Produces a display of the keys of the table.

        Args:
            *sep: (Optional) The characters to delimit elements of the table.
                Each argument will be used for one level of the table, and the
                last argument will be used for all following levels. For
                example, if the only argument is '\t', then all levels will use
                '\t' to delimit their elements. If the first argument is '\n',
                and the second argument is '\t', then the top level will use
                '\n' to delimit it's elements, and all following levels will
                use '\t'. Defaults to ('\n', '\t')

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
                out.append(k + sep[1] + self[k].formatted(*sep[1:]))
            except AttributeError:
                out.append(k)
        return sep[0].join(out)


class InflectionTable(OrderedDotDict):
    """A table of inflected forms of a word."""

    def formatted(self, *sep):
        """Produces a display of the table.

        Args:
            *sep: (Optional) The characters to delimit elements of the table.
                Each argument will be used for one level of the table, and the
                last argument will be used for all following levels. For
                example, if the only argument is '\t', then all levels will use
                '\t' to delimit their elements. If the first argument is '\n',
                and the second argument is '\t', then the top level will use
                '\n' to delimit it's elements, and all following levels will
                use '\t'. Defaults to ('\n', '\t')

        Returns:
            A string containing the formatted table.
        """
        if not sep:
            sep = ('\n', '\t')
        elif not sep[1:]:
            sep *= 2
        out = []
        for k in self:
            try:
                out.append(self[k].formatted(*sep[1:]))
            except AttributeError:
                out.append(self[k])
        return sep[0].join(out)


class InflectionRule(list):
    """A callable object that inflects a function based on sound change rules.

    Attributes:
        common: Additional rules to apply before rules.
        field: The field of an entry to apply the rules to.
        rules: The list of rules to apply.
    """
    def __init__(self, rules=None, field='word'):
        """Initializes an InflectionRule object.

        Args:
            rules: (Optional) The list of rules to apply.
            field: (Optional) The field of an entry to apply the rules to.
                Defaults to 'word'.
        """
        super().__init__(rules)
        self.field = field
        self.common = []

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

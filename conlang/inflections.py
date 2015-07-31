import collections

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

    def __call__(self, entry):
        """Inflects a word.

        Args:
            entry: The word (as a dictionary.Entry) to inflect.

        Returns:
            A dict of the inflected forms of the word.
        """
        return InflectionTable((k, v(entry)) for k, v in self.items())


class InflectionTable(OrderedDotDict):
    pass

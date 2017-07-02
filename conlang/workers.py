from os import path
import sys
from soundchanger.conlang import cache

FILE_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))


def add_pad(l, n, item):
    """Adds an item to a list at an index, padding the list if necessary.

    If the specified index is already occupied by a value other than None,
    nothing happens.

    Args:
        l: The list to modify.
        n: The index to add the value to.
        item: The item to add.
    """
    if n >= len(l):
        l += [None] * (n + 1 - len(l))
    if l[n] is None:
        l[n] = item


class FileCache(cache.ModifiedCache):
    """A cache for files.

    """
    def __init__(self, max_size=-1):
        """Initializes the cache.

        Args:
            max_size: (Optional) The maximum number of entries in the cache. If
                set to -1 (default), the cache has no limit.
        """
        super().__init__(lf, lambda f: path.getmtime(path_to_file(f)),
                         max_size)


def flip_dict(d):
    """Returns a dict with values and keys reversed.

    Args:
        d: The dict to flip the values and keys of.

    Returns:
        A dict whose keys are the values of the original dict, and whose values
        are the corresponding keys.
    """
    return {v: k for k, v in d.items()}


def load_text_file(filename):
    """Loads a text file as a list of lines.

    Args:
        filename: The path to the file.

    Returns:
        A list of the lines of the file, leaving out blank lines, and lines
        starting with '//'.
    """
    with open(path.expanduser(filename), encoding='utf-8') as f:
        return [l.strip('\n') for l in f if l.strip() and not l.startswith('//')]


def lf(filename):
    """Shorthand for load_text_file(path_to_file(filename))."""
    return load_text_file(path_to_file(filename))


def path_to_file(filename):
    """Returns a file path prefixed with FILE_PATH + '/files/'."""
    return path.join(FILE_PATH, 'files', filename)


class Reencoder():
    """A stream that uses 'xmlcharrefreplace' to reencode it's output.

    Attributes:
        stream: The stream to write to.
    """

    def __init__(self, stream=sys.__stdout__):
        """Creates a new Reencoder instance.

        Args:
            stream: The stream to write to. Defaults to sys.__stdout__.
        """
        self.stream = stream

    def write(self, *a):
        """Writes to the stream after reencoding using 'xmlcharrefreplace'.

        Args:
            *a: The args to be passed to stream.write.
        """
        return self.stream.write(*(reencode(s) for s in a))

    def flush(self):
        return self.stream.flush()


def reencode(s):
    """Reencodes a string using xmlcharrefreplace."""
    return s.encode('ascii', 'xmlcharrefreplace').decode()


def slice_replace(word, sl, repl):
    """Replaces a slice of a string.

    Args:
        word: The string to replace a slice of.
        sl: The slice to replace.
        repl: The string to replace the slice with.

    Returns:
        The string with the slice replaced.
    """
    return word[:sl[0]] + repl + word[sl[1]:]


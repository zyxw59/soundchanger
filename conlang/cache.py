import time

class Cache(object):
    """A cache of computed values.

    Attributes:
        cache: The cache as a dict, whose keys are the arguments to the
            function the cache computes, and whose values are tuples of the
            last modified time, and the result of the funciton.
        funct: The function whose results the cache stores.
        max_size: An int. If the cache has more than max_size entries, the
            oldest entries are purged. If set to -1, the cache has unlimited
            size.
        mod_times: A list of keys, in order of last modification time, oldest
            first.
    """
    def __init__(self, funct, max_size=-1):
        """Initializes a cache.

        Args:
            funct: The function whose results the cache stores.
            max_size: (Optional) The maximum number of entries in the cache. If
                set to -1 (default), the cache has no limit.
        """
        super().__init__()
        self.cache = {}
        self.funct = funct
        self.max_size = max_size
        self.mod_times = []

    def __call__(self, *args):
        """Calls the function or returns a cached value.

        If *args exists as a key of self.cache, the cached value is returned.
        Otherwise, self.funct is called, and the result is cached.

        Args:
            *args: The arguments to be passed to self.funct or to be looked up
                in self.cache.

        Returns:
            The result of the function or a cached value.
        """
        if args not in self.cache:
            # it's not cached, so cache it
            self.update(*args)
        # retrieve cached value. if it wasn't already cached, it is now
        return self.cache[args][1]

    def purge(self, num=-1):
        """Purges the cache.

        Args:
            num: (Optional) The number of entries to purge. If set to -1
                (default), all entries are purged. Otherwise, num entries are
                purged, starting with the oldest.
        """
        if num == -1:
            num = len(self.cache)
        for k in self.mod_times[:num]:
            del self.cache[k]
        self.update_mod_times

    def update(self, *args):
        """Updates a value in the cache.

        If the value is not in the cache already, and adding it causes the
        cache to excede max_size, the oldest entry is purged from the cache.

        Args:
            *args: The arguments to self.funct.
        """
        self.cache[args] = time.time(), self.funct(*args)
        if self.max_size != -1 and len(self.cache) > self.max_size:
            self.purge(len(self.cache) - self.max_size)
        else:
            # self.update_mod_times() is called by self.purge(), so we only
            # need to call it if self.purge() isn't called.
            self.update_mod_times()

    def update_mod_times(self):
        """Updates self.mod_times."""
        d = self.cache
        self.mod_times = sorted(d, key=lambda k: d[k][0])


class ModifiedCache(Cache):
    """A cache that can check if values need to be updated.

    Attributes:
        cache: The cache as a dict, whose keys are the arguments to the
            function the cache computes, and whose values are tuples of the
            last modified time, and the result of the funciton.
        funct: The function whose results the cache stores.
        max_size: An int. If the cache has more than max_size entries, the
            oldest entries are purged. If set to -1, the cache has unlimited
            size.
        mod_times: A list of keys, in order of last modification time, oldest
            first.
        modified: A function that checks whether a cached value needs to be
            updated, by returning a timestamp to compare with the last modified
            time of the cached value. Should take the same arguments as funct.
    """
    def __init__(self, funct, modified, max_size=-1):
        """Initializes a cache.

        Args:
            funct: The function whose results the cache stores.
            modified: The function to check whether a cached value needs to be
                updated. Should take the same arguments as funct, and return
                something that can be compared to a timestamp returned by
                time.time().
            max_size: (Optional) The maximum number of entries in the cache. If
                set to -1 (default), the cache has no limit.
        """
        super().__init__(funct, max_size)
        self.modified = modified

    def __call__(self, *args):
        """Calls the function or returns a cached value.

        If *args exists as a key of self.cache, and has not been modified, the
        cached value is returned. Otherwise, self.funct is called, and the
        result is cached.

        Args:
            *args: The arguments to be passed to self.funct or to be looked up
                in self.cache.

        Returns:
            The result of the function or a cached value.
        """
        if (args not in self.cache or
            self.modified(*args) > self.cache[args][0]):
            # it needs to be updated
            self.update(*args)
        # retrieve cached value
        return self.cache[args][1]

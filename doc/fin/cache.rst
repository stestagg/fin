:mod:`fin.cache`
-------------------

:mod:`cache` is designed to make caching the results of slow method simple, and painless.  
It's very similar in nature to the common python @memoize pattern, but the results
are stored on an object, rather than inside a closure, making caching of class-specific
method results much simpler and easier.

An obvious example would be a database connection::

    class DB(object):

        def __init__(self, dsn):
            self.dsn = dsn

        @fin.cache.depends("dsn")
        @fin.cache.property
        def connection(self):
            return dblibrary.connect(self.dsn)

In this example, the connection attribute is cached for each DB instance, allowing for very natural usage::

    >>> db1 = DB("test")
    >>> db1.connection
    <dblibrary.Connection at 0x7f904012fb90>
    >>> db1.connection
    <dblibrary.Connection at 0x7f904012fb90>
    >>> db2 = DB("test")
    <dblibrary.Connection at 0x1a111111de55>

The ```@fin.cache.depends``` part means that if the dsn changes for a DB, the next time db.connection is requested, the class will
create a *new* connection, using the new dsn, update the cache, and start using that instead.   This allows code to be written in a
very natural fashion, and not to worry about state management.


Code Docs
=========


.. automodule:: fin.cache
    :members: property, method, depends, uncached_property, invalidates, generator
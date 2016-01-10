===========
fin - adding a bit more awesome to python
===========

About
=====

Fin is a small utility library for Python.  It has several modules for doing common things, with a focus on keeping users' code clean and simple.  With fin (:mod:`fin.contextlog`), producing the following is trivial:

.. image:: contextlog.gif

.. rst-class:: html-toggle

Source
--------

The above graphic was produced by the following code::

    import fin.contextlog
    import functools

    Log = functools.partial(fin.contextlog.Log, theme="mac")

    ...

    def main():
        left = 10
        with Log("Processing Users"):
            for user in NAMES:
                with Log(user):
                    with Log("Creating account"):
                        time.sleep(random.random()/4)
                    with Log("Setting up homedir"):
                        time.sleep(random.random()/4)
                    with Log("Creating primary key") as l:
                        time.sleep(random.random()/5)
                        left -= 1
                        if left == 0:
                            raise RuntimeError("Not enough entropy")
                        l.output(random.choice(keys).strip())


    if __name__ == '__main__':
        main()



Notable Modules
===============

.. toctree::
    :maxdepth: 1

    fin/cache
    fin/color
    fin/contextlog
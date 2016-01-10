======
:mod:`fin.contextlog` 
======

It's not uncommon for a python script that runs for a long time to produce hard-to-debug errors:

Let's assume there is a script that configures and starts a set of servers, and running it gives this error::

    Traceback (most recent call last):
      File "test.py", line 31, in <module>
        main()
      File "test.py", line 28, in main
        setup_servers()
      File "test.py", line 12, in setup_servers
        start_server(server)
      File "test.py", line 16, in start_server
        configure_replication(server)
      File "test.py", line 24, in configure_replication
        subprocess.check_call(['replication_agent', machine_from, machine_to])
      File "/usr/lib/python2.7/subprocess.py", line 535, in check_call
        retcode = call(*popenargs, **kwargs)
      File "/usr/lib/python2.7/subprocess.py", line 522, in call
        return Popen(*popenargs, **kwargs).wait()
      File "/usr/lib/python2.7/subprocess.py", line 710, in __init__
        errread, errwrite)
      File "/usr/lib/python2.7/subprocess.py", line 1335, in _execute_child
        raise child_exception
    OSError: [Errno 2] No such file or directory


We can see that calling a subprocess has failed.  But for which server?  Which replication was it configuring? There is a lot of critical information missing from this traceback.

The solution is typically to use logging to track progress, but this can also be confusing::

    Starting database
    Starting app_server
    Booting Image
    Configured database > app_server replication
    Starting cache
    Booting Image
    Configured database > cache replication
    Starting http_server
    Booting Image
    Traceback (most recent call last):
      File "test.py", line 31, in <module>
     ...

Was the app still running the 'starting http_server' step?  what exact step did it actually fail on?  Do you add logging before AND after every step in the process? This approach also produces a lot of noise that may not be relevant to debugging the problem.  

fin.contextlog is designed to solve this in a nice, elegant way.  It provides two context managers that log when the manager is entered, and exited, and can be used to pinpoint *exactly* where in the script the failure happened::

    Setting-up servers: 
    | database: 
    | | Booting Image: OK
    | | Configuring replication: OK
    | `- OK
    | app_server: 
    | | Booting Image: OK
    | | Configuring replication: 
    | | | Configuring replication database > app_server: OK
    | | `- OK
    | `- OK
    ...
    | http_server: 
    | | Booting Image: OK
    | | Configuring replication: 
    | | | Configuring replication database > http_server: FAIL
    | | `- FAIL
    | `- FAIL
    `- FAIL
    Traceback (most recent call last):
      File "test.py", line 36, in <module>
        main()
    ...
      File "/usr/lib/python2.7/subprocess.py", line 1335, in _execute_child
        raise child_exception
    OSError: [Errno 2] No such file or directory

This output also makes following the progress of a long-running script very easy.

It may be that you don't want all of this noisy output, and prefer your app to only produce output if there's an error to report.  This can be done with the :class:`fin.contextlog.CLog` class, which only outputs information related to failing steps (or steps that produce output)::

    Setting-up servers: 
    | http_server: 
    | | Configuring replication: 
    | | | Configuring replication database > http_server: 
    | | | `- FAIL
    | | `- FAIL
    | `- FAIL
    `- FAIL
    Traceback (most recent call last):
      File "test.py", line 36, in <module>
    ...

Usage
-----

Usage is simple, import either the Log or CLog class, and use them as a context manager::

    from fin.contextlog import Log
    with Log("foo"):
        with Log("bar") as log:
            log.output('baz')


If a custom theme is required, or other customization (a specific stream etc.) it's common to wrap the Log or CLog constructors in a functools.partial call::

    import fin.contextlog
    import functools

    Log = functools.partial(fin.contextlog.Log, theme="mac")

    with Log('Even prettier output'):
        pass


Code Docs
=====


.. automodule:: fin.contextlog
    :members:


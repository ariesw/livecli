Livecli
=======

|TravisCI| |codecov.io| |pypi.python.org|

-  Website: https://livecli.github.io/index.html
-  Latest release: https://github.com/livecli/livecli/releases/latest
-  GitHub: https://github.com/livecli/livecli
-  Issue tracker: https://github.com/livecli/livecli/issues
-  Kodi version: https://github.com/livecli/repo
-  PyPI: https://pypi.python.org/pypi/livecli
-  Free software: Simplified BSD license

Livecli is a *Command-line interface* utility that pipes videos from
online streaming services to a variety of video players.

The main purpose of livecli is to convert CPU-heavy flash plugins to a
less CPU-intensive format, also allow to watch livestreams on less
powerful devices.

Livecli is a fork of the
`Streamlink <https://github.com/streamlink/streamlink>`__ and
`Livestreamer <https://github.com/chrippa/livestreamer>`__ project

`Installation <https://livecli.github.io/install.html>`__
=========================================================

Installation via Python pip
^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    pip install livecli

Manual installation via Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    git clone https://github.com/livecli/livecli
    cd livecli
    pip install -U .

Features
========

Livecli is built via a plugin system which allows new services to be
easily added.

A list of all supported plugins can be found on the `plugin
page <https://livecli.github.io/plugin_matrix.html>`__.

There is also a generic plugin that will try to open a stream on every website.

Quickstart
==========

After installing, simply use:

::

    livecli STREAMURL best

Livecli will automatically open the stream in its default video player!

See `Livecli's detailed
documentation <https://livecli.github.io/cli.html>`__ for all available
configuration options, CLI parameters and usage examples.

Kodi
====

Livecli can be used with Kodi Leia

-  `Livecli Kodi Repository <https://github.com/livecli/repo>`__.

For more information see
`service.livecli.proxy <https://github.com/livecli/service.livecli.proxy>`__

Contributing
============

All contributions are welcome. Feel free to open a new thread on the
issue tracker or submit a new pull request. Please read
`CONTRIBUTING.md <https://github.com/livecli/livecli/blob/master/CONTRIBUTING.md>`__
first. Thanks!

Please be aware that plugins for streaming services that are using DRM
protections, websites from not official or not authored third party
**will not be implemented**.

.. |TravisCI| image:: https://api.travis-ci.org/livecli/livecli.svg?branch=master
   :target: https://travis-ci.org/livecli/livecli
.. |codecov.io| image:: https://codecov.io/gh/livecli/livecli/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/livecli/livecli
.. |pypi.python.org| image:: https://img.shields.io/pypi/v/livecli.svg?style=flat-square
   :target: https://pypi.python.org/pypi/livecli

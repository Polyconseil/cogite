**Cogite** is a program that helps you create, manage and merge
pull/merge requests and push upstream from the command line. It works
on projects that use Git. For now, only GitHub is supported. Support
for GitLab will come soon.

Basic usage looks like:

.. code-block:: console

    $ git checkout -b jsmith/feature
    $ # add/edit/remove files, git add/rm/commit as you usually do
    $ cogite pr add
    $ cogite status  # checks build status and reviews
    $ cogite pr merge

That's it. **Cogite** is opinionated in that it does not add merge
commits: it uses ``git rebase`` instead. More precisely, here is what
``cogite pr merge`` does to merge the branch ``jsmith/feature`` to
``master`` and push it upstream.

.. code-block:: console

    $ git checkout master
    $ git pull --rebase            # update local "master" branch from upstream
    $ git checkout jsmith/feature  # back to the feature branch
    $ git rebase master            # may fail with conflicts, to be resolved as usual
    $ git push --force-with-lease
    $ git checkout master
    $ git rebase jsmith/feature    # rebase your work on the "master" branch...
    $ git push                     # ...and push it upstream
    $ git branch --delete jsmith/feature       # clean up the feature branch locally
    $ git push --delete origin jsmith/feature  # ditto upstream

This workflow makes sure that the Git host (e.g. GitHub) rightfully
sees that the pull/merge request has indeed been merged.

**Cogite** could be extended to use ``git merge`` through a
configuration option. This is not how the main author uses Git, so
this feature would need to be an external contribution. Could it be
yours? ;)


Demo
====

FIXME (dbaty): make another demo where I type more carefully...

.. image:: https://raw.githubusercontent.com/polyconseil/cogite/master/docs/_static/demo.gif
   :width: 100%


Features
========

Here is a list of commands in **Cogite**:

- ``cogite pr add``: create a pull/merge request
- ``cogite pr draft``: create a draft pull request (shortcut for ``pr add --draft``);
- ``cogite pr ready``: mark a draft pull request as ready;
- ``cogite pr browse``: open the current pull request on the Git host (e.g. GitHub) in a web browser;
- ``cogite pr reqreview``: ask for review (also available from ``cogite pr add``);
- ``cogite pr status``: show build (CI) status and reviews;
- ``cogite pr rebase``: update the local branches with respect to upstream master;
- ``cogite pr merge``: merge the pull request.
- ``cogite ci browse``: open the CI for the current branch in a web browser;
- ``cogite auth add``: configure authentication for the current Git host;
- ``cogite auth add``: delete authentication credentials for the current Git host.

A key feature of **Cogite** is its extensibility: you can easily write
plugins to extend commands.

**Cogite** is not and will never be a replacement for tools like
``hub`` or ``gh`` from GitHub. It focuses on pull requests and aims at
supporting GitHub, GitLab and possibly other Git hosts.


Installation
============

**Cogite** is written in Python. Python 3.6 or further is
required. Python 2 is not supported.

You may install **Cogite** with:

.. code-block:: console

    $ pip install cogite

As usual, it is preferable to install in a virtual environment.


Getting started
===============

The instructions below work if your project is hosted on
GitHub.com. Otherwise, please refer to the `full documentation`_.

1. Move to the directory where you have a checkout of a Git repository.

2. Run ``cogite auth add`` and follow instructions.

That's it, you are ready to use **Cogite**.


Further details
===============

The `full documentation`_ has (a lot) more details about installation,
configuration options, commands, how to write your own plugins to
extend **Cogite**, etc.


License
=======

**Cogite** is written by `Polyconseil`_ and is licensed under the
3-clause BSD license, a copy of which is included in the source.

.. _Polyconseil: https://opensource.polyconseil.fr

.. _full documentation: https://cogite.readthedocs.io

What is Cogite?
===============

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

That's it. **Cogite** is not a replacement for tools like ``hub`` or
``gh`` from GitHub. It focuses on pull requests and aims at supporting
GitHub, GitLab and possibly other Git hosts.

**Cogite** is opinionated in that it does not add merge commits: it
uses ``git rebase`` instead. More precisely, here is what ``cogite pr
merge`` does to merge the branch ``jsmith/feature`` to ``master`` and
push it upstream.

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

This workflow makes sure that the Git host (e.g. GitHub) properly sees
that the pull/merge request has indeed been merged.


Demo
----

FIXME (dbaty): make another demo where I type more carefully...

.. image:: https://raw.githubusercontent.com/polyconseil/cogite/master/docs/_static/demo.gif
   :width: 100%


Interested?
-----------

It's suggested that you first look at the :doc:`getting_started`
section. You may then read a bit about the :doc:`features`, take a
look at the :doc:`commands` and the :doc:`configuration`.

A key feature of **Cogite** is its extensibility: you can easily write
plugins to extend commands and other functions. For more details, see
:doc:`extending`.


License
-------

**Cogite** is written by `Polyconseil`_ and is licensed under the
3-clause BSD license, a copy of which is included in the source.

.. _Polyconseil: https://opensource.polyconseil.fr

.. _full documentation: https://cogite.readthedocs.io

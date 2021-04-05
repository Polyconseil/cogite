Cogite - Your pull requests from the command line
=================================================

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


.. toctree::
   :maxdepth: 1
   :caption: Table of contents

   intro.rst
   getting_started.rst
   features.rst
   commands.rst
   configuration.rst
   extending.rst
   faq.rst
   contributing.rst
   changes.rst

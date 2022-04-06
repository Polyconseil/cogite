Getting started
===============

You must have Python 3.7 or later, and a relatively recent version of
Git. Git 2.30 is known to work, but older versions will most likely
work as well.


Installation
------------

It is recommended to install **Cogite** within a Python virtual
environment. If you are not familiar with that, the following should
do the trick:

.. code-block:: bash

    $ mkdir --parents ~/.venv
    $ python3 -m venv ~/.venv/cogite
    $ ~/.venv/cogite/bin/pip install --upgrade pip cogite
    $ alias cogite="~/.venv/cogite/bin/cogite"

This may not be optimal but should let you start right away.


Minimal configuration
---------------------

1. Move to the directory where you have a checkout of a Git repository.

2. Run ``cogite auth add`` and follow instructions.

   FIXME: explain the two current options : manual token or automatic configuration.

   For further details about authentication-related commands, see
   :ref:`features_authentication` and :ref:`commands_auth`.

That's it, you are ready to use **Cogite**.


How to use
----------

Here we describe how to use **Cogite** in a feature branch workflow
(even though **Cogite** could work with other workflows).

1. Create your feature branch with ``git checkout -b new-feature``.

2. Work on your branch and create commits as you usually do.

3. When ready, create a pull request with ``cogite pr add``.

   The command will guide you through, proposing to modify the title
   and the description of the pull request, and asking whether you
   want to select reviewers.

   Here is an example output::

       $ cogite pr add
       ✔ Pushed local branch to upstream.
       Confirm title and body:
       | Update README
       Continue [Y/e/n]?
       ✔ Created pull request on Git host
       Reviewers (leave blank if none, tab to complete, space to select, enter to validate):
       Created #21 at https://github.com/dbaty/sandbox/pull/21

   For further details, see :ref:`commands_pr_add`.

3. If you use a supported CI platform (such as CircleCI or GitHub
   Actions), you can show their status with ``cogite status``. This
   command also shows the status of each review. Here is an example
   output::

       $ cogite status
       Checks:
         ✔ ci/circleci: Run quality checks (https://circleci.com/gh/dbaty/sandbox/11670
         ✔ ci/circleci: Run tests (https://circleci.com/gh/dbaty/sandbox/11671
       Reviews:
         … jsmith

   For further details, see :ref:`commands_status`.

4. When ready to merge this pull request, run ``cogite pr merge``.
   Here is an example output::

       $ cogite pr merge
       You are about to rebase new-feature on master and push master upstream.
       Continue [y/N]? y
       ✔ git checkout master
       ✔ git pull --rebase
       ✔ git checkout new-feature
       ✔ git rebase master
       ✔ git push --force-with-lease
       ✔ git checkout master
       ✔ git rebase new-feature
       ✔ git push
       ✔ git branch --delete new-feature
       ✔ git push --delete origin new-feature
       ✔ Your pull request has been merged to master and the corresponding branches (local and upstream) have been deleted.

   As you can see, **Cogite** shows exactly what it does. If the
   process fails at some point, you can always rollback local changes
   or fallback to manual operations.

   For further details, see :ref:`features_merge` and
   :ref:`commands_pr_merge`.

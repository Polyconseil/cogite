List of all commands
====================

Each **Cogite** command looks like ``cogite <group> <action>``,
e.g. ``cogite pr merge``. All commands are listed below:


.. contents::
   :local:
   :depth: 2


.. _commands_auth:

cogite auth
-----------

**Cogite** uses the HTTP API of the Git host to perform some actions.
As such, it needs to be authenticated against each host in the first
place.


.. _commands_auth_add:

cogite auth add
...............

FIXME

Usage::

    usage: cogite auth add [-h]

    optional arguments:
      -h, --help  show this help message and exit


If you have authorized the **Cogite** application on GitHub, you can
see the permissions that you granted to **Cogite** on `this settings
page
<https://github.com/settings/connections/applications/2b46ebae56793d920b69>`_.


.. _commands_auth_delete:

cogite auth delete
..................

This command deletes the authentication token that has been set up for
the Git host of the current Git checkout.


Usage::

    usage: cogite auth delete [-h]

    optional arguments:
      -h, --help  show this help message and exit


.. _commands_ci:

cogite ci
---------

All commands of this group relate to continuous integration (CI)
systems, e.g. tests run by CircleCi, GitHub Actions, Jenkins, etc.


.. _commands_ci_browse:

cogite ci browse
................

FIXME


.. _commands_pr:

cogite pr
---------

All commands of this group relate to pull requests and expect that an
open pull request exists, except ``cogite pr add``.


.. _commands_pr_add:

cogite pr add
.............

FIXME

.. _commands_pr_browse:

cogite pr browse
................

FIXME

.. _commands_pr_draft:

cogite pr draft
...............

An alias for ``cogite pr add --draft``. It accepts the same arguments.

Usage::

    usage: cogite pr draft [-h] [--base BASE_BRANCH]

    optional arguments:
      -h, --help          show this help message and exit
      --base BASE_BRANCH  branch where changes should be applied. Defaults to the
                          master branch.


.. _commands_pr_merge:

cogite pr merge
...............

FIXME

.. _commands_pr_ready:

cogite pr ready
...............

FIXME

.. _commands_pr_rebase:

cogite pr rebase
................

FIXME


.. _commands_pr_reqreview:

cogite pr reqreview
...................

Ask others to review the current pull request.

Usage::

    usage: cogite pr reqreview [-h]

    optional arguments:
      -h, --help  show this help message and exit


.. _commands_status:

cogite status
-------------

This is special group that has only one command: ``cogite status``.
Because rules must be broken, sometimes. Sorry.

Usage::

    usage: cogite status [-h] [-p]

    optional arguments:
      -h, --help  show this help message and exit
      -p, --poll  If set, regularly poll CI host until the job is complete.

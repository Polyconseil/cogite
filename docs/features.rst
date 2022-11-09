Features
========


Supported platforms
-------------------

As of now, **Cogite** supports GitHub only. Support for GitLab will
come soon.

Also, **Cogite** automatically detects and supports the following
continuous integration (CI) platforms: CircleCI and GitHub Actions.
If you use another platform, you need to configure **Cogite** (see
FIXME).


.. _features_authentication:

Authentication
--------------

**Cogite** uses the HTTP API of the Git host to create pull requests
and, more generally, retrieve information from the host. For this to
work, it needs to authenticate itself. You need only do so once for
each host.

There are two ways to authenticate:

- Use the default, guided, semi-automatic mechanism (known as "OAuth
  device flow" or "OAuth Device Authorization Grant") that defines a
  new, properly configured authentication token that you can revoke at
  any time. Basically, **Cogite** will display a one-time verification
  code and open a browser window for you, where you can enter this
  code to validate your token on the requested Git host.

  FIXME: include screencast

- If you already have a properly configured authentication token, or
  if you don't trust **Cogite** mechanism above, you can use your own
  authentication token. It MUST grant the "repo" scope. It is probably
  a good idea to define a specific token for **Cogite** instead of
  re-using the same token for many applications. That way, you can
  revoke the token of a single application without affecting other
  applications.


.. _features_merge:

What **Cogite** does when merging
---------------------------------

FIXME


.. _features_conflict_resolution:

Conflict resolution
-------------------

FIXME


.. _shell_completion:

Shell completion
----------------

FIXME: document ZSH completion

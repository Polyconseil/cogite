Extending Cogite with plugins
=============================

**Cogite** can be extended by two mechanisms:

- new commands or command arguments;

- automatic resolution of CI URL.


New commands or command arguments
---------------------------------

Here is a working example of a new ``cogite ci tweak`` command:


.. code:: python

    def tweak_jenkins_job(context):
        print("This is the 'ci tweak' command")

    class CiTweakCommand(BaseCommandPlugin):
        def install(self, parser):
            ci_subparser = self.get_command_subparsers(parser, 'ci')
            tweak = ci_subparser.add_parser('tweak', help='Tweak a CI job.')
            tweak.set_defaults(callback=tweak_jenkins_job)

See :ref:`registering_plugins` below to complete the process.


Automatic resolution of CI URL
------------------------------

Currently, **Cogite** auto-detects and resolves URL for branch builds
on GitHub Actions and CircleCI. If you use a CI system where the URL
of the build cannot be guessed by from the name of the branch, you
need a plugin.

Here is a working example of such a plugin:

.. code:: python

    import re
    from cogite.plugins import BaseCiUrlGetter


    def get_job_name_for_branch(repository, branch):
        # Some characters cannot be used in the name of a Jenkins job.
        forbidden = '?*/\\%!@#$^&|<>[]:;'
        sanitized_branch = re.sub('[' + re.escape(forbidden) + ']', '_', branch)
        return f"z-{repository}-{sanitized_branch}"

    class CustomCiUrlGetter(BaseCiUrlGetter):
        def get_url(self, context, branch):
            if context.owner != 'Your Organization':
                return None  # not handled by this plugin

            if branch == 'master':
                job_name = context.repository
            else:
                job_name = get_job_name_for_branch(context.repository, context.branch)
            return f"https://ci.example.com/job/{job_name}"


See :ref:`registering_plugins` below to complete the process.


.. _registering_plugins:

Registering plugins
-------------------

The proper way to distribute your plugins is to create a fully fledged
Python package (or incorporate your plugin in an existing package) and
add the following line in the ``setup.cfg`` file (or a similar
construction if you use a ``setup.py``):

.. code:: toml

    [options.entry_points]
    cogite.plugins.ci_url_getter =
      CustomCiUrlGetter = yourpackage.yourmodule:CustomCiUrlGetter

    cogite.plugins.commands =
      CiTweakCommand = blease.cogite:CiTweakCommand


.. note::

    I am aware that the instructions above could be overwhelming for
    someone who has never created a Python package (even though it's
    not as hard as some make it seem). It may be possible in the
    future to just add the path of your plugin file to the
    configuration file of **Cogite**. Something like::

        [plugins]
        commands = [
          "/home/jsmith/cogite_plugins.py:CustomCiUrlGetter",
        ]

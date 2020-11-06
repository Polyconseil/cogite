import argparse

import pkg_resources


NAMESPACE_CI_URL_GETTER = 'cogite.plugins.ci_url_getter'
NAMESPACE_COMMANDS = 'cogite.plugins.commands'


def get_ci_url_getters():
    return _get_plugins(NAMESPACE_CI_URL_GETTER)


def get_extra_commands():
    return _get_plugins(NAMESPACE_COMMANDS)


def _get_plugins(namespace):
    entry_points = pkg_resources.iter_entry_points(namespace)
    return [entry_point.resolve() for entry_point in entry_points]


class BaseCiUrlGetter:
    def get_url(self, context, branch):
        raise NotImplementedError()


class BaseCommandPlugin:
    def get_command_main_parser(self, parser, command):
        for action in parser._subparsers._actions:
            if isinstance(action, argparse._SubParsersAction):
                try:
                    return action._name_parser_map[command]
                except KeyError:
                    continue
        raise ValueError('Could not find main parser for command "{command}"')

    def get_command_subparsers(self, parser, command):
        main_parser = self.get_command_main_parser(parser, command)
        for action in main_parser._subparsers._actions:
            if isinstance(action, argparse._SubParsersAction):
                return action
        raise ValueError('Could not find subparsers for command "{command}"')

    def install(self, parser):
        raise NotImplementedError()

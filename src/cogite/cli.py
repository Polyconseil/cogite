import argparse
import os
import os.path
import sys

from . import api
from . import commands
from . import config
from . import context
from . import errors
from . import interaction
from . import plugins
from . import version


def get_parser():
    parser = argparse.ArgumentParser(
        description=(
            'Cogite is a program that helps you create, manage and merge '
            'pull/merge requests and push upstream from the command line. '
            'More info at https://cogite.readthedocs.io/'
        )
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%%(prog)s {version.VERSION}',
    )

    # Yo dawg, I'm going to put subparsers in your subparsers.
    main_subparsers = parser.add_subparsers()

    # auth (add|delete)
    auth_help = 'Commands related to authentication'
    auth = main_subparsers.add_parser('auth', help=auth_help, description=auth_help)
    auth_subparsers = auth.add_subparsers()
    auth_add_help = 'Interactively configure authentication.'
    auth_add = auth_subparsers.add_parser('add', help=auth_add_help, description=auth_add_help)
    auth_add.set_defaults(callback=commands.add_auth)

    auth_delete = auth_subparsers.add_parser('delete', help='Delete authentication token.')
    auth_delete.set_defaults(callback=commands.delete_auth)

    # pr (add|browse|draft|merge|ready|rebase|reqreview)
    pr_help = 'Commands related to pull requests'
    pr = main_subparsers.add_parser('pr', help=pr_help, description=pr_help)
    pr_subparsers = pr.add_subparsers()

    pr_add_help = "Interactively create a new pull/merge request."
    pr_add = pr_subparsers.add_parser('add', help=pr_add_help, description=pr_add_help)
    pr_draft_help = "Interactively create a draft pull request."
    pr_draft = pr_subparsers.add_parser(
        'draft', help=pr_draft_help, description=pr_draft_help
    )
    for subparser in (pr_add, pr_draft):
        subparser.add_argument(
            '--base',
            dest='base_branch',
            help='branch where changes should be applied. Defaults to the master branch.',
        )
        subparser.add_argument(
            '--ignore-template',
            action='store_true',
            dest='ignore_template',
            help='Ignore (i.e. do not use) pull request template.',
        )

    pr_add.add_argument(
        '--draft',
        action='store_true',
        dest='draft',
        help="Mark as a draft pull request.",
    )
    pr_add.set_defaults(callback=commands.add_pull_request)

    pr_draft.set_defaults(callback=commands.add_draft_pull_request)

    pr_browse_help = 'Open current pull request in a browser.'
    pr_browse = pr_subparsers.add_parser(
        'browse', help=pr_browse_help, description=pr_browse_help
    )
    pr_browse.set_defaults(callback=commands.browse_pull_request)
    pr_browse.add_argument('branch', type=str, action='store', nargs='?')

    pr_merge_help = 'Merge (actually rebase and push) a pull request.'
    pr_merge = pr_subparsers.add_parser(
        'merge', help=pr_merge_help, description=pr_merge_help
    )
    pr_merge.set_defaults(callback=commands.merge_pull_request)

    pr_ready_help = 'Mark a draft pull request as ready.'
    pr_ready = pr_subparsers.add_parser(
        'ready', help=pr_ready_help, description=pr_ready_help
    )
    pr_ready.set_defaults(callback=commands.mark_pull_request_as_ready)

    pr_rebase_help = 'Rebase a pull request.'
    pr_rebase = pr_subparsers.add_parser('rebase', help=pr_rebase_help, description=pr_rebase_help)
    pr_rebase.set_defaults(callback=commands.rebase_branch)

    # FIXME: "reqreview" is long to type, can we find a shorter alias?
    pr_reqreview = 'Ask for reviews.'
    pr_reqreview = pr_subparsers.add_parser('reqreview', help=pr_reqreview, description=pr_reqreview)
    pr_reqreview.set_defaults(callback=commands.request_reviews)

    # ci (browse)
    ci_help = 'Commands related to CI.'
    ci = main_subparsers.add_parser('ci', help=ci_help, description=ci_help)
    ci_subparsers = ci.add_subparsers()

    ci_browse = ci_subparsers.add_parser(
        'browse', help='Open CI job in browser (defaults to current branch)'
    )
    ci_browse.set_defaults(callback=commands.browse_ci)
    ci_browse.add_argument('branch', type=str, action='store', nargs='?')

    # status (no sub-commands)
    status_help = 'Show status of the pull request.'
    status = main_subparsers.add_parser(
        'status', help=status_help, description=status_help
    )
    status.set_defaults(callback=commands.show_status)
    status.add_argument(
        '-p',
        '--poll',
        action='store_true',
        help='If set, regularly poll CI host until the job is complete.',
    )

    return parser


def parse_args():
    parser = get_parser()
    for command in plugins.get_extra_commands():
        command().install(parser)
    args = parser.parse_args()
    if not hasattr(args, 'callback'):
        parser.print_usage()
        sys.exit(os.EX_USAGE)
    return args


def _main():
    try:
        ctx = context.get_context()
    except errors.ContextError as exc:
        raise errors.FatalError(exc) from exc
    configuration = config.get_configuration(ctx)
    client = api.get_client(configuration, ctx)

    if not client:
        sys.exit(f"Could not find any backend for platform '{configuration.host_platform}'")

    args = dict(vars(parse_args()))
    callback = args.pop('callback')

    # Include `client` and `configuration` in the context to simplify
    # the signature of all command functions.
    ctx.client = client
    ctx.configuration = configuration
    callback(ctx, **args)


def main():
    try:
        _main()
    except errors.FatalError as error:
        sys.exit(interaction.interpret_rich_text(str(error)))


if __name__ == '__main__':
    main()

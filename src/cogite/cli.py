import argparse
import os
import os.path
import sys

from . import api
from . import commands
from . import config
from . import context
from . import errors
from . import plugins
from . import version


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--version', action='version', version=f'%%(prog)s {version.VERSION}'
    )

    # Yo dawg, I'm going to put subparsers in your subparsers.
    main_subparsers = parser.add_subparsers()

    # auth (add|delete)
    auth = main_subparsers.add_parser('auth', help='Commands related to authentication.')
    auth_subparsers = auth.add_subparsers()
    auth_add = auth_subparsers.add_parser('add', help='Configure authentication.')
    auth_add.set_defaults(callback=commands.add_auth)

    auth_delete = auth_subparsers.add_parser('delete', help='Delete authentication token.')
    auth_delete.set_defaults(callback=commands.delete_auth)

    # pr (add|browse|draft|merge|ready|rebase|reqreview)
    pr = main_subparsers.add_parser('pr', help='Commands related to pull requests.')
    pr_subparsers = pr.add_subparsers()

    pr_add = pr_subparsers.add_parser('add', help='Add a pull request.')
    pr_draft = pr_subparsers.add_parser(
        'draft', help='Add a draft pull request (alias to `pr add --draft`).'
    )
    for subparser in (pr_add, pr_draft):
        subparser.add_argument(
            '--base',
            dest='base_branch',
            default='master',
            help='branch where changes should be applied. Defaults to master.',
        )

    pr_add.add_argument(
        '--draft',
        action='store_true',
        dest='draft',
        help="Mark as a draft pull request.",
    )
    pr_add.set_defaults(callback=commands.add_pull_request)

    pr_draft.set_defaults(callback=commands.add_draft_pull_request)

    pr_browse = pr_subparsers.add_parser(
        'browse', help='Browse a pull request on GitHub (defaults to current PR)'
    )
    pr_browse.set_defaults(callback=commands.browse_pull_request)
    pr_browse.add_argument('branch', type=str, action='store', nargs='?')

    pr_merge = pr_subparsers.add_parser(
        'merge', help='Merge (actually rebase and push) a pull request.'
    )
    pr_merge.set_defaults(callback=commands.merge_pull_request)

    pr_ready = pr_subparsers.add_parser(
        'ready', help='Mark a draft pull request as ready.'
    )
    pr_ready.set_defaults(callback=commands.mark_pull_request_as_ready)

    pr_rebase = pr_subparsers.add_parser('rebase', help='Rebase a pull request.')
    pr_rebase.set_defaults(callback=commands.rebase_branch)

    # FIXME: "reqreview" is long to type, can we find a shorter alias?
    pr_reqreview = pr_subparsers.add_parser('reqreview', help='Ask for reviews.')
    pr_reqreview.set_defaults(callback=commands.request_reviews)

    # ci (browse)
    ci = main_subparsers.add_parser('ci', help='Commands related to CI.')
    ci_subparsers = ci.add_subparsers()

    ci_browse = ci_subparsers.add_parser(
        'browse', help='Open CI job in browser (defaults to current branch)'
    )
    ci_browse.set_defaults(callback=commands.browse_ci)
    ci_browse.add_argument('branch', type=str, action='store', nargs='?')

    # status (no sub-commands)
    status = main_subparsers.add_parser(
        'status', help='Show status of the pull request (defauls to current branch)'
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
        sys.exit(f"Could not find any backend for platform '{configuration.platform}'")

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
        sys.exit(str(error))


if __name__ == '__main__':
    main()

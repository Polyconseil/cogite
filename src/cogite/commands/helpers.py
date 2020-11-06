from cogite import errors


def assert_current_branch_is_not_master(branch):
    if branch == 'master':
        raise errors.FatalError(
            "You are on the master branch, "
            "this command must be run from a feature branch."
        )

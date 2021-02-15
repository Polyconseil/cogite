from cogite import errors


def assert_current_branch_is_feature_branch(branch, master_branch):
    if branch == master_branch:
        raise errors.FatalError(
            "You are on the master branch, "
            "this command must be run from a feature branch."
        )

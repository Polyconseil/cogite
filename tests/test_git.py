import pathlib

from cogite import git


def test_get_git_root():
    assert git.get_git_root() == str(pathlib.Path('.').resolve())

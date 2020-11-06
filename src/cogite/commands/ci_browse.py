import pathlib
import webbrowser

from cogite import errors
from cogite import plugins


CI_PLATFORM_URL = {
    'circleci': 'https://app.circleci.com/pipelines/{configuration.host_platform}/{owner}/{repository}?branch={branch}',
    'github': 'https://github.com/{owner}/{repository}/actions?query=branch={branch}',
}



def _detect_platform():
    """Try to detect CI platform."""
    if pathlib.Path('.circleci').exists():
        return 'circleci'
    if pathlib.Path('.github/workflows').exists():
        return 'github'
    return None


def _get_ci_url(context, branch):
    if context.configuration.ci_url:
        return context.configuration.ci_url
    platform = context.configuration.ci_platform
    if not platform:
        platform = _detect_platform()
    if platform:
        return CI_PLATFORM_URL[platform]
    for getter in plugins.get_ci_url_getters():
        url = getter().get_url(context, branch)
        if url:
            return url
    return None


def browse_ci(context, *, branch=None):
    branch = branch or context.branch
    url = _get_ci_url(context, branch=None)
    if not url:
        raise errors.FatalError("Could not find CI URL.")
    url_pattern_kwargs = context.as_dict()
    url_pattern_kwargs['branch'] = branch
    url = url.format(**url_pattern_kwargs)
    webbrowser.open(url)

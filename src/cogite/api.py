from . import backends
from .config import Configuration
from .context import Context


def get_client(configuration: Configuration, context: Context):
    backend = None
    if configuration.host_platform == 'github':
        backend = backends.GitHubApiClient
    if not backend:
        return None
    return backend(configuration, context)

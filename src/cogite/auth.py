import getpass

from cogite import backends
from cogite import config
from cogite import interaction


AUTH_TOKEN_DIR = config.COGITE_CONFIG_DIR / "auth"


def _get_path_for_domain(host_domain):
    return AUTH_TOKEN_DIR / host_domain


def get_token(host_domain):
    """Return the authentication token to use.

    If none has been configured yet, return ``None``.
    """
    path = _get_path_for_domain(host_domain)
    if not path.exists():
        return None
    return path.read_text().strip()


def save_token(host_domain, token):
    """Save the token on disk."""
    if not AUTH_TOKEN_DIR.exists():
        AUTH_TOKEN_DIR.mkdir(0o700, parents=True)
    path = _get_path_for_domain(host_domain)
    path.touch(0o600)
    path.write_text(token)


def delete_token(host_domain):
    path = _get_path_for_domain(host_domain)
    path.unlink()


class UserInputTokenGetter:
    def get_token(self):
        interaction.display(
            "You must have an existing personal access token, "
            "for which the `repo` scope has been granted."
        )
        token = getpass.getpass("Type your access token: ")
        return token.strip()


def get_token_getters(configuration: config.Configuration):
    default = ('Use an existing access token', UserInputTokenGetter)
    if configuration.host_platform == 'github':
        # XXX: OAuthDeviceFlowTokenGetter won't work on an instance
        # of GitHub Enteprise.
        return [
            (
                'Automatically create a token (with OAuth device flow) [recommended]',
                backends.GitHubOAuthDeviceFlowTokenGetter,
            ),
            default
        ]
    return [default]

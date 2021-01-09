import dataclasses
import os
import pathlib
from typing import Optional

import toml


USER_CONFIG_HOME = pathlib.Path(
    os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")
)
COGITE_CONFIG_DIR = USER_CONFIG_HOME / "cogite"


@dataclasses.dataclass
class Configuration:
    host_platform: str = "github"
    host_api_url: str = "https://api.github.com"
    status_poll_frequency: int = 10  # seconds

    enable_pre_merge_checks: bool = True

    ci_url: Optional[str] = None
    ci_platform: Optional[str] = None


def read_toml(path: pathlib.Path, section: str = None):
    d = toml.loads(path.read_text())
    if section:
        return d.get(section, {})
    return d


def _replace_dashes(options: dict) -> dict:
    """Recursively replace dashes by underscores in dictonary keys."""
    if not isinstance(options, dict):
        return options
    return {
        option.replace("-", "_"): _replace_dashes(value)
        for option, value in options.items()
    }


def _quote_for_path(url: str) -> str:
    return url.replace('/', '_')


def get_configuration(context):
    config = {}

    user_project_dir = COGITE_CONFIG_DIR / _quote_for_path(context.remote_url)
    locations_sections = (
        (COGITE_CONFIG_DIR / 'config.toml', None),
        (user_project_dir / 'config.toml', None),
        (pathlib.Path('./pyproject.toml'), 'tool.cogite'),
        (pathlib.Path('./cogite.toml'), None)
    )
    for location, section in locations_sections:
        if not location.exists():
            continue
        config.update(**_replace_dashes(read_toml(location, section)))

    return Configuration(**config)

from unittest import mock

from cogite import plugins


def test_get_ci_url_getters():
    # Cogite itself does not register plugins and I don't want to do
    # that just for tests. Fortunately, one of the development
    # dependencies to register plugins. Yes, it's a bit ugly.
    with mock.patch("cogite.plugins.NAMESPACE_CI_URL_GETTER", "sphinx.html_themes"):
        results = plugins.get_ci_url_getters()
    assert "sphinx_rtd_theme" in {module.__name__ for module in results}


def test_get_extra_commands():
    # See comment in test above. Yes, it's ugly here, too.
    with mock.patch("cogite.plugins.NAMESPACE_COMMANDS", "sphinx.html_themes"):
        results = plugins.get_extra_commands()
    assert "sphinx_rtd_theme" in {module.__name__ for module in results}

from cogite import context


class TestExtractDomainFromRemoteUrl:
    def test_ssh(self):
        url = "git@github.com:Polyconseil/cogite.git"
        domain, path = context._extract_domain_and_path(url)
        assert domain == "github.com"
        assert path == "Polyconseil/cogite.git"

    def test_https(self):
        url = "https://github.com/Polyconseil/cogite"
        domain, path = context._extract_domain_and_path(url)
        assert domain == "github.com"
        assert path == "Polyconseil/cogite"


def test_get_context():
    ctx = context.get_context()
    assert ctx.host_domain == 'github.com'
    assert ctx.repository == 'cogite'
    # Unfortunately, it's hard to test more than that:
    # - remote_url: could be HTTP or SSH, could be the origin
    #   repository or a fork.
    # - owner: could be Polyconseil, or the owner of the fork
    # - branch: the current branch, which we don't control.

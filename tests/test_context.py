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

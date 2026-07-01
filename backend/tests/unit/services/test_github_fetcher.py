from talkingcode.services.ingestion.github_fetcher import GitHubFetcher


def test_github_fetcher_creates():
    fetcher = GitHubFetcher(github_token="test")
    assert fetcher is not None

"""CWI SGF source URL security checks and file parsing tests."""
import pytest

from src.cwi_source import CWI_CHOICES, fetch_cwi_sgf, validate_cwi_url


def test_curated_cwi_links_are_allowed():
    assert len(CWI_CHOICES) == 3
    for url in CWI_CHOICES.values():
        assert validate_cwi_url(url) == url


@pytest.mark.parametrize("url", [
    "http://homepages.cwi.nl/~aeb/go/games/games/AlphaGo/LeeSedol/1.sgf",
    "https://evil.example/~aeb/go/games/games/a.sgf",
    "https://homepages.cwi.nl.evil.example/~aeb/go/games/games/a.sgf",
    "https://homepages.cwi.nl/~aeb/go/games/games/../private.sgf",
    "https://homepages.cwi.nl/~aeb/go/games/games/AlphaGo/",
    "https://homepages.cwi.nl/~aeb/go/games/games/a.sgf?token=1",
    "file:///etc/passwd",
])
def test_untrusted_urls_are_rejected(url):
    with pytest.raises(ValueError):
        validate_cwi_url(url)


def test_fetch_small_sgf_without_disk_write(monkeypatch):
    class DummyResponse:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self, limit):
            assert limit == 2_000_001
            return b"(;FF[4]GM[1]SZ[19];B[pd];W[dd])"

    class DummyOpener:
        def open(self, request, timeout):
            assert timeout == 15
            return DummyResponse()

    monkeypatch.setattr("src.cwi_source.build_opener", lambda *args: DummyOpener())
    raw, name = fetch_cwi_sgf(CWI_CHOICES["이세돌 vs 알파고 · 제1국 (2016-03-09)"])
    assert raw.startswith(b"(;")
    assert name == "1.sgf"


def test_fetch_rejects_html_response(monkeypatch):
    class DummyResponse:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self, limit):
            return b"<html>not a SGF</html>"

    class DummyOpener:
        def open(self, request, timeout):
            return DummyResponse()

    monkeypatch.setattr("src.cwi_source.build_opener", lambda *args: DummyOpener())
    with pytest.raises(ValueError, match="SGF"):
        fetch_cwi_sgf(next(iter(CWI_CHOICES.values())))

"""Open a CWI-hosted SGF directly in the study app, without saving it to disk.

Only HTTPS SGF links inside the CWI games archive are accepted. The original
file is held in Streamlit session state, not committed to GitHub.
"""
import ssl
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import truststore

from sgfmill import sgf

ARCHIVE_URL = "https://homepages.cwi.nl/~aeb/go/games/games/"
ALPHAGO_URL = ARCHIVE_URL + "AlphaGo/index.html"
CWI_ROOT = "/~aeb/go/games/games/"
MAX_SGF_BYTES = 2_000_000

# A few directly linked originals. For any other game, paste its SGF URL.
CWI_CHOICES = {
    "이세돌 vs 알파고 · 제1국 (2016-03-09)": ARCHIVE_URL + "AlphaGo/LeeSedol/1.sgf",
    "이세돌 vs 알파고 · 제4국 (2016-03-13)": ARCHIVE_URL + "AlphaGo/LeeSedol/4.sgf",
    "이세돌 vs 알파고 · 제5국 (2016-03-15)": ARCHIVE_URL + "AlphaGo/LeeSedol/5.sgf",
}


def validate_cwi_url(url: str) -> str:
    """Reject non-CWI hosts, HTTP, redirects, traversal, or non-SGF URLs."""
    url = url.strip()
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "homepages.cwi.nl"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("CWI 공식 HTTPS 기보 링크만 지원합니다.")
    path = unquote(parsed.path)
    if (
        not path.startswith(CWI_ROOT)
        or ".." in PurePosixPath(path).parts
        or not path.lower().endswith(".sgf")
        or "\\" in path
    ):
        raise ValueError("CWI 기보 목록에서 .sgf 파일의 직접 주소를 복사해 주세요.")
    return url


class _RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("다른 사이트로 이동하는 기보 링크는 사용할 수 없습니다.")


def fetch_cwi_sgf(url: str) -> tuple[bytes, str]:
    """Fetch at most 2 MB, validate SGF, and return (bytes, filename)."""
    checked = validate_cwi_url(url)
    opener = build_opener(_RejectRedirect(), HTTPSHandler(context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)))
    request = Request(checked, headers={"User-Agent": "BadukInsight/0.1 (SGF study)"})
    try:
        with opener.open(request, timeout=15) as response:
            raw = response.read(MAX_SGF_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        message = str(exc)
        if "CERTIFICATE_VERIFY_FAILED" in message:
            raise ValueError(
                "Windows의 신뢰 인증서로도 CWI HTTPS 인증에 실패했습니다. "
                "브라우저에서 CWI 원본 SGF를 내려받아 '내 컴퓨터 파일 업로드'를 사용해 주세요."
            ) from exc
        raise ValueError(f"CWI 연결 실패: {exc}. 원본 링크에서 직접 SGF를 받아 업로드할 수 있습니다.") from exc

    if len(raw) > MAX_SGF_BYTES or not raw.lstrip().startswith(b"(;"):
        raise ValueError("받은 파일이 SGF가 아니거나 크기 제한(2MB)을 초과했습니다.")
    try:
        game = sgf.Sgf_game.from_bytes(raw)
        if game.get_size() not in (9, 13, 19):
            raise ValueError("현재 앱에서 지원하지 않는 바둑판 크기입니다.")
    except Exception as exc:
        raise ValueError(f"유효한 SGF 기보가 아닙니다: {exc}") from exc

    return raw, PurePosixPath(unquote(urlsplit(checked).path)).name

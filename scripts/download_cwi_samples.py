"""Download Lee Sedol vs AlphaGo game records from the CWI archive.

The files remain on the user's own computer and are not committed to Git.
This standalone helper is optional; the current Streamlit UI opens original\nCWI SGF URLs directly using src.cwi_source.
"""
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sgfmill import sgf

BASE = "https://homepages.cwi.nl/~aeb/go/games/games/AlphaGo/LeeSedol/"
GAMES = {
    "lee_sedol_alphago_game_1.sgf": "1.sgf",  # 2016-03-09
    "lee_sedol_alphago_game_4.sgf": "4.sgf",  # 2016-03-13
    "lee_sedol_alphago_game_5.sgf": "5.sgf",  # 2016-03-15
}
DEST = Path(__file__).resolve().parents[1] / "data" / "sgf"


def valid_sgf(data: bytes) -> bool:
    """Avoid saving HTML/error pages that look like SGF downloads."""
    if not 10 <= len(data) <= 2_000_000 or not data.lstrip().startswith(b"(;"):
        return False
    try:
        game = sgf.Sgf_game.from_bytes(data)
        return game.get_size() == 19
    except Exception:
        return False


def download_samples(dest: Path = DEST) -> tuple[list[Path], list[str]]:
    """Download any missing/invalid samples and report successes and errors.

    Existing *valid* SGFs are left unchanged. Failures are returned instead of
    being swallowed, so the Streamlit UI can show an actionable error message.
    """
    dest.mkdir(parents=True, exist_ok=True)
    good, failures = [], []
    for name, source in GAMES.items():
        path = dest / name
        try:
            if path.is_file() and valid_sgf(path.read_bytes()):
                good.append(path)
                continue
            request = Request(BASE + source, headers={"User-Agent": "Mozilla/5.0 BadukInsight/0.1"})
            with urlopen(request, timeout=20) as response:
                content = response.read(2_000_001)
            if not valid_sgf(content):
                raise ValueError("다운로드 파일이 유효한 19x19 SGF가 아닙니다.")
            path.write_bytes(content)
            good.append(path)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            failures.append(f"{name}: {exc}")
    return good, failures


def main() -> None:
    good, failures = download_samples()
    for path in good:
        print("READY:", path.name, path.stat().st_size, "bytes")
    for message in failures:
        print("FAILED:", message)
    print(f"Downloaded or existing: {len(good)}/{len(GAMES)}")
    print("Source:", BASE)
    if failures:
        print("Fallback: open CWI AlphaGo page in a browser, download an SGF, then choose Upload SGF in the app.")


if __name__ == "__main__":
    main()

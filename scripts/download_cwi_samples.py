"""Download three verified CWI archive links for professional game records.

Games: Lee Sedol vs AlphaGo (2016), match games 1, 4 and 5.
SGF content is downloaded on the user's computer, not committed to Git.
"""
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://homepages.cwi.nl/~aeb/go/games/games/AlphaGo/LeeSedol/"
GAMES = {
    "lee_sedol_alphago_game_1.sgf": "1.sgf",  # 2016-03-09
    "lee_sedol_alphago_game_4.sgf": "4.sgf",  # 2016-03-13
    "lee_sedol_alphago_game_5.sgf": "5.sgf",  # 2016-03-15
}
DEST = Path(__file__).resolve().parents[1] / "data" / "sgf"

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    successful = 0
    for name, source in GAMES.items():
        destination = DEST / name
        if destination.exists():
            print("SKIP:", name)
            successful += 1
            continue
        try:
            request = Request(BASE + source, headers={"User-Agent": "BadukInsight/0.1"})
            with urlopen(request, timeout=25) as response:
                content = response.read(2_000_001)
            if len(content) > 2_000_000 or b"(;" not in content[:500]:
                raise ValueError("Response is not a valid-sized SGF document")
            destination.write_bytes(content)
            successful += 1
            print("OK:", name, len(content), "bytes")
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            print("FAILED:", name, exc)
    print(f"Downloaded or existing: {successful}/{len(GAMES)}")
    print("Source:", BASE)
    if successful == 0:
        print("Tip: download SGFs manually from the CWI AlphaGo archive and load them in the app.")

if __name__ == "__main__":
    main()

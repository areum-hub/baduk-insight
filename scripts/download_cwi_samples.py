"""Download three sample SGF files from the CWI archive."""
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE = "https://homepages.cwi.nl/~aeb/go/games/games/people/Cho_Hunhyun/"
FILES = ("1990-01-04.sgf", "1990-01-08.sgf", "1990-01-10.sgf")
DEST = Path(__file__).resolve().parents[1] / "data" / "sgf"

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        path = DEST / name
        if path.exists():
            print("SKIP:", name)
            continue
        try:
            with urlopen(BASE + name, timeout=20) as response:
                content = response.read(2_000_001)
            if len(content) > 2_000_000 or b"(;" not in content[:500]:
                raise ValueError("Invalid or oversized SGF response")
            path.write_bytes(content)
            print("OK:", name, len(content), "bytes")
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            print("FAILED:", name, exc)
    print("Source:", BASE)

if __name__ == "__main__":
    main()

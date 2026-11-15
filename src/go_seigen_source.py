"""Load Go Seigen records from CWI for local study, without redistributing SGFs.

Only files inside the source archive's Go_Seigen directory are imported.
The app's default game selector looks exclusively inside data/sgf/go_seigen/.
"""
from __future__ import annotations

import io
import ssl
import tarfile
from pathlib import Path, PurePosixPath
from functools import lru_cache

from sgfmill import sgf, sgf_moves
from urllib.request import HTTPSHandler, Request, build_opener

import truststore

GO_SEIGEN_ARCHIVE_URL = "https://homepages.cwi.nl/~aeb/go/games/go_seigen.tgz"
GO_SEIGEN_DIR_NAME = "go_seigen"
MAX_ARCHIVE_BYTES = 20_000_000
MAX_SGF_BYTES = 2_000_000
MAX_FILES = 2000


@lru_cache(maxsize=4)
def _validated_go_seigen_paths(
    fingerprints: tuple[tuple[str, int, int], ...],
) -> tuple[str, ...]:
    """Return only Go Seigen games whose complete main line can be replayed.

    Cache by file metadata to avoid replaying ~900 SGFs on Streamlit reruns.
    """
    accepted = []
    for filename, _, _ in fingerprints:
        try:
            game = sgf.Sgf_game.from_bytes(Path(filename).read_bytes())
            if game.get_size() not in (9, 13, 19):
                continue
            root = game.get_root()
            players = [
                str(root.get(prop)).strip().casefold()
                for prop in ("PB", "PW")
                if root.has_property(prop)
            ]
            if "go seigen" not in players:
                continue
            board, moves = sgf_moves.get_setup_and_moves(game)
            if not moves:
                continue
            for colour, point in moves:
                if point is not None:
                    board.play(point[0], point[1], colour)
            accepted.append(filename)
        except (ValueError, TypeError, IndexError, KeyError):
            # A damaged or non-replayable SGF must not break the dashboard.
            continue
    return tuple(accepted)


def local_go_seigen_games(data_dir: Path) -> list[Path]:
    """Only show complete, playable Go Seigen games in the default selector."""
    folder = data_dir / GO_SEIGEN_DIR_NAME
    fingerprints = tuple(
        (str(path), path.stat().st_mtime_ns, path.stat().st_size)
        for path in sorted(folder.glob("*.sgf"))
        if path.is_file()
    )
    return [Path(name) for name in _validated_go_seigen_paths(fingerprints)]


def import_go_seigen_archive(raw: bytes, target: Path) -> int:
    """Import a Go Seigen .tgz into a dedicated local directory (not GitHub)."""
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("압축파일이 허용 용량을 초과했습니다.")
    records: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            for member in archive:
                parts = PurePosixPath(member.name).parts
                if (
                    not member.isfile()
                    or len(parts) != 2
                    or parts[0] != "Go_Seigen"
                    or not parts[1].lower().endswith(".sgf")
                ):
                    continue
                name = parts[1]
                if name in records:
                    raise ValueError(f"중복 SGF 파일명: {name}")
                if member.size > MAX_SGF_BYTES or len(records) >= MAX_FILES:
                    raise ValueError("SGF 크기 또는 파일 개수 제한을 초과했습니다.")
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise ValueError(f"기보를 읽을 수 없습니다: {name}")
                data = extracted.read(MAX_SGF_BYTES + 1)
                if len(data) > MAX_SGF_BYTES or not data.lstrip().startswith(b"(;"):
                    raise ValueError(f"SGF 형식을 확인해 주세요: {name}")
                records[name] = data
    except (tarfile.TarError, EOFError) as exc:
        raise ValueError("유효한 오청원 TGZ 압축파일이 아닙니다.") from exc

    if not records:
        raise ValueError("압축파일의 Go_Seigen 폴더에 SGF 기보가 없습니다.")

    target.mkdir(parents=True, exist_ok=True)
    for name, data in records.items():
        (target / name).write_bytes(data)
    return len(records)


def import_go_seigen(target: Path) -> int:
    """Download the archive from CWI and save its SGFs for local use."""
    request = Request(
        GO_SEIGEN_ARCHIVE_URL,
        headers={"User-Agent": "BadukInsight/0.1 (personal Go study)"},
    )
    opener = build_opener(HTTPSHandler(context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)))
    with opener.open(request, timeout=25) as response:
        raw = response.read(MAX_ARCHIVE_BYTES + 1)
    return import_go_seigen_archive(raw, target)

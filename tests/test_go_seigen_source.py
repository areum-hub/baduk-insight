"""Tests for the Go Seigen-only default SGF collection.

All records are small synthetic fixtures; no remote downloads or copyrighted
professional game records are needed.
"""
import io
import tarfile

from src.go_seigen_source import import_go_seigen_archive, local_go_seigen_games


def _archive(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, raw in files.items():
            info = tarfile.TarInfo("Go_Seigen/" + name)
            info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))
    return buffer.getvalue()


def test_local_default_selector_shows_only_playable_go_seigen_games(tmp_path):
    folder = tmp_path / "go_seigen"
    folder.mkdir()
    (folder / "01_go.sgf").write_bytes(
        b"(;FF[4]GM[1]SZ[19]PB[Go Seigen]PW[Opponent];B[dd];W[pp])"
    )
    (folder / "02_other.sgf").write_bytes(
        b"(;FF[4]GM[1]SZ[19]PB[Another Player]PW[Opponent];B[dd])"
    )
    (folder / "03_empty.sgf").write_bytes(
        b"(;FF[4]GM[1]SZ[19]PB[Go Seigen]PW[Opponent])"
    )
    games = local_go_seigen_games(tmp_path)
    assert [game.name for game in games] == ["01_go.sgf"]


def test_tgz_import_stores_sgfs_locally_in_dedicated_folder(tmp_path):
    data = _archive({
        "go.sgf": b"(;FF[4]GM[1]SZ[19]PB[Go Seigen]PW[Opponent];B[dd])",
    })
    destination = tmp_path / "go_seigen"
    assert import_go_seigen_archive(data, destination) == 1
    assert (destination / "go.sgf").is_file()
    assert [game.name for game in local_go_seigen_games(tmp_path)] == ["go.sgf"]

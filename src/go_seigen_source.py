"""Download Go Seigen SGFs from the CWI-hosted archive for local private study.

The repository contains this downloader, not a redistributed SGF dataset.
"""
from __future__ import annotations

import io
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

GO_SEIGEN_ARCHIVE_URL = "https://homepages.cwi.nl/~aeb/go/games/go_seigen.tgz"
MAX_ARCHIVE_BYTES = 20_000_000
MAX_SGF_BYTES = 2_000_000
MAX_FILES = 2000


def import_go_seigen(target: Path) -> int:
    """Fetch archive from its original provider and import SGFs locally.

    Only basename-only .sgf files are extracted, never paths from the archive.
    Existing SGFs in target are left intact; users can choose to remove them.
    """
    request = Request(GO_SEIGEN_ARCHIVE_URL, headers={"User-Agent": "BadukInsight/0.1 (personal study)"})
    with urlopen(request, timeout=45) as response:
        raw = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("기보 압축파일이 허용 용량을 초과했습니다.")
    items: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive:
            if not member.isfile() or not member.name.lower().endswith(".sgf"):
                continue
            name = Path(member.name).name
            if name in items:
                raise ValueError(f"중복 기보 파일명: {name}")
            if member.size > MAX_SGF_BYTES or len(items) >= MAX_FILES:
                raise ValueError("기보 파일 크기 또는 개수 제한을 초과했습니다.")
            file = archive.extractfile(member)
            if file is None:
                continue
            data = file.read(MAX_SGF_BYTES + 1)
            if len(data) > MAX_SGF_BYTES or not data.lstrip().startswith(b"(;"):
                raise ValueError(f"SGF 형식이 올바르지 않습니다: {name}")
            items[name] = data
    if not items:
        raise ValueError("SGF 기보를 찾지 못했습니다.")
    target.mkdir(parents=True, exist_ok=True)
    for name, data in items.items():
        (target / name).write_bytes(data)
    return len(items)

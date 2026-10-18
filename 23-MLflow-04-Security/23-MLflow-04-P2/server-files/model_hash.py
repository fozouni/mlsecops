import hashlib
from pathlib import Path

SKIP = {"registered_model_meta"}


def sha256_dir(path: str) -> str:

    root = Path(path)
    files = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.name not in SKIP),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    h = hashlib.sha256()
    for p in files:
        name = p.relative_to(root).as_posix().encode("utf-8")
        h.update(len(name).to_bytes(8, "big"))
        h.update(name)
        fh = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                fh.update(chunk)
        h.update(fh.digest())
    return h.hexdigest()

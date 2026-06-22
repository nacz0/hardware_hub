from pathlib import Path
import os


_LOADED = False


def load_environment() -> None:
    global _LOADED

    if _LOADED:
        return

    backend_root = Path(__file__).resolve().parents[1]
    repo_root = backend_root.parent
    for env_file in (backend_root / ".env", repo_root / ".env"):
        load_env_file(env_file)

    _LOADED = True


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        os.environ[key] = clean_env_value(value)


def clean_env_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        return cleaned[1:-1]
    return cleaned

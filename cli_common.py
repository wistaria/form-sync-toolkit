from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv


BOOTSTRAP_SKIP_ENV = "FORM_SYNC_TOOLKIT_NO_AUTO_VENV"
MIN_PYTHON = (3, 10)
PROJECT_VENV_NAME = "form-sync-toolkit"


def ensure_project_venv() -> None:
    """Create/use the temp virtual environment before third-party imports."""
    _require_supported_python()

    if os.getenv(BOOTSTRAP_SKIP_ENV):
        return

    project_root = Path(__file__).resolve().parent
    venv_dir = _default_venv_dir()
    venv_python = _venv_python(venv_dir)
    requirements = project_root / "requirements.txt"

    _remove_venv_if_unsupported(venv_dir)

    if not venv_python.exists():
        print(f"Creating virtual environment: {venv_dir}", file=sys.stderr)
        try:
            venv.EnvBuilder(with_pip=True).create(venv_dir)
        except OSError as exc:
            print(
                f"Error: Failed to create virtual environment: {exc}", file=sys.stderr
            )
            raise SystemExit(1) from exc

    if requirements.exists() and _requirements_changed(requirements, venv_dir):
        print("Installing dependencies from requirements.txt...", file=sys.stderr)
        try:
            subprocess.check_call(
                [str(venv_python), "-m", "pip", "install", "-r", str(requirements)]
            )
        except subprocess.CalledProcessError as exc:
            print(f"Error: Failed to install dependencies: {exc}", file=sys.stderr)
            raise SystemExit(exc.returncode) from exc
        _write_requirements_marker(requirements, venv_dir)

    if _running_in_venv(venv_dir):
        return

    os.execv(str(venv_python), [str(venv_python), *sys.argv])


def _require_supported_python(version_info=None) -> None:
    if version_info is None:
        version_info = sys.version_info

    if tuple(version_info[:2]) >= MIN_PYTHON:
        return

    print(
        "Error: Form Sync Toolkit requires Python "
        f"{_format_python_version(MIN_PYTHON)}+, but this is "
        f"Python {_format_python_version(version_info)}. "
        "Install Python 3.10 or newer, then run the command with that Python.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _remove_venv_if_unsupported(venv_dir: Path) -> None:
    version = _venv_python_version(venv_dir)
    if version is None or tuple(version[:2]) >= MIN_PYTHON:
        return

    print(
        "Removing virtual environment created with Python "
        f"{_format_python_version(version)}: {venv_dir}",
        file=sys.stderr,
    )
    shutil.rmtree(venv_dir)


def _venv_python_version(venv_dir: Path) -> tuple[int, ...] | None:
    pyvenv_cfg = venv_dir / "pyvenv.cfg"
    try:
        lines = pyvenv_cfg.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for line in lines:
        key, sep, value = line.partition("=")
        if sep and key.strip() == "version":
            return _parse_python_version(value.strip())
    return None


def _parse_python_version(value: str) -> tuple[int, ...] | None:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError:
        return None


def _format_python_version(version_info) -> str:
    return ".".join(str(part) for part in tuple(version_info[:3]))


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _default_venv_dir() -> Path:
    if hasattr(os, "getuid"):
        return _temp_root() / str(os.getuid()) / PROJECT_VENV_NAME
    return _temp_root() / PROJECT_VENV_NAME


def _temp_root() -> Path:
    if sys.platform == "darwin" and Path("/private/tmp").is_dir():
        return Path("/private/tmp")
    return Path(tempfile.gettempdir()).resolve()


def _running_in_venv(venv_dir: Path) -> bool:
    return Path(sys.prefix).resolve() == venv_dir.resolve()


def _requirements_changed(requirements: Path, venv_dir: Path) -> bool:
    marker = _requirements_marker(venv_dir)
    try:
        return marker.read_text(encoding="utf-8").strip() != _file_sha256(requirements)
    except OSError:
        return True


def _write_requirements_marker(requirements: Path, venv_dir: Path) -> None:
    _requirements_marker(venv_dir).write_text(
        _file_sha256(requirements), encoding="utf-8"
    )


def _requirements_marker(venv_dir: Path) -> Path:
    return venv_dir / ".requirements.sha256"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

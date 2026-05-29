from pathlib import Path

import pytest

import cli_common


def test_require_supported_python_rejects_python_39(capsys):
    with pytest.raises(SystemExit) as exc:
        cli_common._require_supported_python((3, 9, 6))

    assert exc.value.code == 1
    assert "requires Python 3.10+" in capsys.readouterr().err


def test_require_supported_python_allows_python_310():
    cli_common._require_supported_python((3, 10, 0))


def test_venv_python_version_reads_pyvenv_cfg(tmp_path):
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = 3.11.8\n", encoding="utf-8"
    )

    assert cli_common._venv_python_version(venv_dir) == (3, 11, 8)


def test_remove_venv_if_unsupported_removes_old_managed_venv(tmp_path, capsys):
    venv_dir = tmp_path / "venv"
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir(parents=True)
    (venv_dir / "pyvenv.cfg").write_text("version = 3.9.6\n", encoding="utf-8")
    (bin_dir / "python").write_text("", encoding="utf-8")

    cli_common._remove_venv_if_unsupported(venv_dir)

    assert not venv_dir.exists()
    assert "created with Python 3.9.6" in capsys.readouterr().err


def test_remove_venv_if_unsupported_keeps_supported_venv(tmp_path):
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text("version = 3.10.13\n", encoding="utf-8")

    cli_common._remove_venv_if_unsupported(venv_dir)

    assert Path(venv_dir).exists()

# Form Sync Toolkit

[English](README.md) | [日本語](README-ja.md)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Google Forms API](https://img.shields.io/badge/Google%20Forms-API-673AB7?logo=googleforms&logoColor=white)](https://developers.google.com/forms/api)
[![Google Drive API](https://img.shields.io/badge/Google%20Drive-API-4285F4?logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![Config](https://img.shields.io/badge/config-YAML-000000?logo=yaml&logoColor=white)](yaml.md)
[![Author](https://img.shields.io/badge/author-Synge%20Todo-blue)](https://github.com/wistaria)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A CLI toolkit for creating, updating, exporting, listing, and checking Google Forms from YAML.

## Features

- Create or update a Google Form from a YAML definition
- Export an existing Google Form to YAML
- Compare a Google Form with a YAML definition and print a unified diff
- List Google Forms in Google Drive with full Drive paths
- Move created forms into a Drive folder path from YAML

## Requirements

- Python 3.10+
- Google OAuth client credentials
- Network access on first run to install Python runtime dependencies

## Setup

The scripts create a virtual environment in the system temp directory and install runtime dependencies from `requirements.txt` automatically on first run. On macOS, the path is `/private/tmp/$UID/form-sync-toolkit`.

Get OAuth client credentials by following [oauth.md](oauth.md). On the first authenticated run, the CLI prompts you to paste the downloaded OAuth client credentials JSON and saves it to `~/.config/form-sync-toolkit/credentials.json` with mode `600`.

If you change credentials or scopes, remove the saved credentials and token files, then run a command again:

```bash
rm -f ~/.config/form-sync-toolkit/credentials.json
rm -f ~/.config/form-sync-toolkit/token.json
```

The first authenticated run opens a browser. Select your Google account, allow access, and continue past the unverified-app warning for your own OAuth app.

## Usage

Create or update a form from YAML:

```bash
python3 sync_form.py FORM.yaml
```

Export a form to YAML:

```bash
python3 export_form.py --form-id FORM_ID
```

Write the exported YAML to a specific file:

```bash
python3 export_form.py --form-id FORM_ID --output FORM.yaml
```

Compare a form with YAML:

```bash
python3 check_form.py --form-id FORM_ID FORM.yaml
```

List Google Forms in Drive:

```bash
python3 list_form.py
```

See [yaml.md](yaml.md) for the YAML format.

## Script Behavior

- `sync_form.py`
  - Finds an existing form by `path` and `title`
  - Creates the form when no match exists
  - Updates the form when exactly one match exists
  - Fails when multiple matches make the target ambiguous
- `export_form.py`
  - Reads a Google Form by Form ID and writes normalized YAML
- `check_form.py`
  - Compares normalized YAML with the live Google Form
  - Checks titles, descriptions, paths, question types, options, and required flags
- `list_form.py`
  - Prints form names, IDs, timestamps, URLs, and full Drive paths

## Notes

- `requirements.txt` contains runtime dependencies installed by the scripts.
- `requirements-dev.txt` contains development tools such as `pytest` and `ruff`.
- Set `FORM_SYNC_TOOLKIT_NO_AUTO_VENV=1` to skip automatic virtual environment setup.
- OAuth client credentials are stored in `~/.config/form-sync-toolkit/credentials.json` with mode `600`.
- OAuth tokens are stored in `~/.config/form-sync-toolkit/token.json` with mode `600`.

## Development

For local development, create your own environment and install both runtime and development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.

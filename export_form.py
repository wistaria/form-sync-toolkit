#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

if __name__ == "__main__":
    from cli_common import ensure_project_venv

    ensure_project_venv()

"""Form Sync Toolkit CLI for exporting Google Forms to YAML."""

import argparse
from pathlib import Path

from googleapiclient.discovery import build

from form_common import (
    SCOPES_BODY_DRIVE_READONLY,
    dump_yaml_config,
    export_form_yaml,
    get_credentials as get_shared_credentials,
    form_to_yaml_config,
    normalize_export_path,
    question_to_yaml_item,
)


__all__ = [
    "dump_yaml_config",
    "export_form_yaml",
    "form_to_yaml_config",
    "normalize_export_path",
    "question_to_yaml_item",
]


class _PrettyYamlDumper:  # re-exported via dump_yaml_config in form_common
    pass


def get_credentials():
    return get_shared_credentials(SCOPES_BODY_DRIVE_READONLY)


def main():
    parser = argparse.ArgumentParser(
        description="Form Sync Toolkit: export a Google Form to YAML."
    )
    parser.add_argument("--form-id", required=True, help="Target Google Form ID.")
    parser.add_argument(
        "--output",
        help="Output YAML path. Default: <form_id>.yml",
    )

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else Path(f"{args.form_id}.yml")

    creds = get_credentials()
    forms_service = build("forms", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    config = export_form_yaml(forms_service, drive_service, args.form_id)
    yaml_text = dump_yaml_config(config)
    output_path.write_text(yaml_text, encoding="utf-8")

    print("Exported YAML configuration")
    print(f"Form ID: {args.form_id}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()

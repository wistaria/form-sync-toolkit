#!/usr/bin/env python3

"""Form Sync Toolkit CLI for comparing Google Forms against YAML."""

import argparse
import difflib

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from form_common import (
    SCOPES_BODY_DRIVE_READONLY,
    dump_yaml_config,
    export_form_yaml,
    get_credentials as get_shared_credentials,
    load_yaml as load_form_yaml,
    make_question_item,
    normalize_export_path,
    question_to_yaml_item,
)


def get_credentials():
    return get_shared_credentials(SCOPES_BODY_DRIVE_READONLY)


def normalize_yaml_config(raw_config):
    normalized = {"title": raw_config["title"]}

    description = raw_config.get("description")
    if description:
        normalized["description"] = description

    normalized_path = normalize_export_path(raw_config.get("path"))
    if normalized_path != "/":
        normalized["path"] = normalized_path

    document_title = raw_config.get("documentTitle")
    if document_title and document_title != normalized["title"]:
        normalized["documentTitle"] = document_title

    questions = []
    for question in raw_config.get("questions", []):
        questions.append(question_to_yaml_item(make_question_item(question)))

    if questions:
        normalized["questions"] = questions

    return normalized


def compare_yaml_config_to_form(yaml_config, form_config):
    expected_yaml = dump_yaml_config(normalize_yaml_config(yaml_config))
    actual_yaml = dump_yaml_config(form_config)

    if expected_yaml == actual_yaml:
        return True, ""

    diff = difflib.unified_diff(
        expected_yaml.splitlines(),
        actual_yaml.splitlines(),
        fromfile="yaml_file",
        tofile="google_form",
        lineterm="",
    )
    return False, "\n".join(diff)


def check_form_against_yaml(forms_service, drive_service, form_id, yaml_config):
    try:
        live_config = export_form_yaml(forms_service, drive_service, form_id)
    except HttpError as exc:
        if getattr(exc.resp, "status", None) == 404:
            return False, f"ERROR: Google Form not found: {form_id}"
        raise

    return compare_yaml_config_to_form(yaml_config, live_config)


def main():
    parser = argparse.ArgumentParser(
        description="Form Sync Toolkit: compare a Google Form against YAML."
    )
    parser.add_argument("yaml_file", help="Path to form definition YAML file.")
    parser.add_argument("--form-id", required=True, help="Target Google Form ID.")

    args = parser.parse_args()

    raw_config = load_form_yaml(args.yaml_file)
    creds = get_credentials()
    forms_service = build("forms", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    match, diff = check_form_against_yaml(
        forms_service=forms_service,
        drive_service=drive_service,
        form_id=args.form_id,
        yaml_config=raw_config,
    )

    if match:
        print("MATCH: Google Form matches the YAML file.")
        raise SystemExit(0)

    if diff.startswith("ERROR:"):
        print(diff)
        raise SystemExit(2)

    print("DIFF: Google Form differs from the YAML file.")
    if diff:
        print(diff)
    raise SystemExit(1)


if __name__ == "__main__":
    main()

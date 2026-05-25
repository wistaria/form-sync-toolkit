#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

if __name__ == "__main__":
    from cli_common import ensure_project_venv

    ensure_project_venv()

"""Form Sync Toolkit CLI for listing Google Forms in Drive."""

import argparse

from googleapiclient.discovery import build

from form_common import (
    SCOPES_BODY_DRIVE_READONLY,
    get_credentials as get_shared_credentials,
    get_folder_path,
)


def get_credentials():
    return get_shared_credentials(SCOPES_BODY_DRIVE_READONLY)


def list_forms(service, limit=100):
    query = (
        "mimeType='application/vnd.google-apps.form' "
        "and trashed=false"
    )

    response = service.files().list(
        q=query,
        pageSize=limit,
        fields="files(id,name,createdTime,modifiedTime,parents)",
        orderBy="modifiedTime desc",
    ).execute()

    return response.get("files", [])


def get_form_path(service, form, cache):
    parent_ids = form.get("parents", [])
    if not parent_ids:
        return f"/{form['name']}"

    folder_path = get_folder_path(service, parent_ids[0], cache)
    if folder_path == "/":
        return f"/{form['name']}"
    return f"{folder_path}/{form['name']}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)

    args = parser.parse_args()

    creds = get_credentials()
    drive_service = build("drive", "v3", credentials=creds)

    forms = list_forms(drive_service, limit=args.limit)
    folder_path_cache = {}

    for form in forms:
        form_id = form["id"]

        print("=" * 80)
        print(f"Name: {form['name']}")
        print(f"Path: {get_form_path(drive_service, form, folder_path_cache)}")
        print(f"ID: {form_id}")
        print(f"Modified: {form['modifiedTime']}")
        print(f"Edit URL: https://docs.google.com/forms/d/{form_id}/edit")
        print(f"Response URL: https://docs.google.com/forms/d/{form_id}/viewform")


if __name__ == "__main__":
    main()

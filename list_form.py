#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def get_credentials():
    token_path = Path("token.json")
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_json = os.environ["GOOGLE_CREDENTIALS_JSON"]
            client_config = json.loads(credentials_json)
            flow = InstalledAppFlow.from_client_config(
                client_config,
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())

    return creds


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


def get_folder_path(service, folder_id, cache):
    if folder_id == "root":
        return "/"

    if folder_id in cache:
        return cache[folder_id]

    folder = service.files().get(
        fileId=folder_id,
        fields="id,name,parents",
    ).execute()

    parent_ids = folder.get("parents", [])
    if not parent_ids:
        folder_path = f"/{folder['name']}"
    else:
        parent_path = get_folder_path(service, parent_ids[0], cache)
        if parent_path == "/":
            folder_path = f"/{folder['name']}"
        else:
            folder_path = f"{parent_path}/{folder['name']}"

    cache[folder_id] = folder_path
    return folder_path


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

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
    )

    args = parser.parse_args()

    creds = get_credentials()

    drive_service = build(
        "drive",
        "v3",
        credentials=creds,
    )

    forms = list_forms(
        drive_service,
        limit=args.limit,
    )
    folder_path_cache = {}

    for form in forms:
        form_id = form["id"]

        print("=" * 80)
        print(f"Name: {form['name']}")
        print(f"Path: {get_form_path(drive_service, form, folder_path_cache)}")
        print(f"ID: {form_id}")
        print(f"Modified: {form['modifiedTime']}")
        print(
            f"Edit URL: "
            f"https://docs.google.com/forms/d/{form_id}/edit"
        )
        print(
            f"Response URL: "
            f"https://docs.google.com/forms/d/{form_id}/viewform"
        )


if __name__ == "__main__":
    main()

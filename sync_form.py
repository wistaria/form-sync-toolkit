#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
]


def _escape_drive_query_value(value):
    return value.replace("'", "\\'")


def _split_drive_path(path):
    if not path:
        return []

    normalized = str(path).strip()
    if normalized in {"", "/"}:
        return []

    return [part for part in normalized.strip("/").split("/") if part]


def resolve_folder_id_by_path(drive_service, path, create_missing=False):
    folder_id = "root"

    for part in _split_drive_path(path):
        escaped_name = _escape_drive_query_value(part)
        query = (
            "mimeType='application/vnd.google-apps.folder' "
            f"and name='{escaped_name}' "
            f"and '{folder_id}' in parents "
            "and trashed=false"
        )

        response = drive_service.files().list(
            q=query,
            pageSize=2,
            fields="files(id,name)",
        ).execute()

        matches = response.get("files", [])
        if not matches:
            if not create_missing:
                raise ValueError(f"Folder path not found: {path}")

            created = drive_service.files().create(
                body={
                    "name": part,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [folder_id],
                },
                fields="id,name",
            ).execute()
            folder_id = created["id"]
            continue
        if len(matches) > 1:
            raise ValueError(f"Ambiguous folder path segment: {part}")

        folder_id = matches[0]["id"]

    return folder_id


def move_file_to_path(drive_service, file_id, path):
    target_folder_id = resolve_folder_id_by_path(
        drive_service,
        path,
        create_missing=True,
    )

    metadata = drive_service.files().get(
        fileId=file_id,
        fields="parents",
    ).execute()
    current_parents = metadata.get("parents", [])

    if current_parents == [target_folder_id]:
        return

    update_kwargs = {
        "fileId": file_id,
        "addParents": target_folder_id,
        "fields": "id,parents",
    }
    if current_parents:
        update_kwargs["removeParents"] = ",".join(current_parents)

    drive_service.files().update(**update_kwargs).execute()


def find_form_id_by_path_and_title(drive_service, path, title):
    if path:
        try:
            folder_id = resolve_folder_id_by_path(
                drive_service,
                path,
                create_missing=False,
            )
        except ValueError:
            return None
    else:
        folder_id = "root"

    escaped_title = _escape_drive_query_value(str(title))
    query = (
        "mimeType='application/vnd.google-apps.form' "
        f"and name='{escaped_title}' "
        f"and '{folder_id}' in parents "
        "and trashed=false"
    )

    response = drive_service.files().list(
        q=query,
        pageSize=2,
        fields="files(id,name)",
    ).execute()

    matches = response.get("files", [])
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous form target: multiple forms named '{title}' under path '{path or '/'}'"
        )

    return matches[0]["id"]


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


def load_form_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_question_item(q):
    qtype = q["type"]

    question = {"required": bool(q.get("required", False))}

    if qtype == "short":
        question["textQuestion"] = {"paragraph": False}

    elif qtype == "paragraph":
        question["textQuestion"] = {"paragraph": True}

    elif qtype == "radio":
        question["choiceQuestion"] = {
            "type": "RADIO",
            "options": [{"value": str(opt)} for opt in q["options"]],
            "shuffle": bool(q.get("shuffle", False)),
        }

    elif qtype == "checkbox":
        question["choiceQuestion"] = {
            "type": "CHECKBOX",
            "options": [{"value": str(opt)} for opt in q["options"]],
            "shuffle": bool(q.get("shuffle", False)),
        }

    elif qtype == "dropdown":
        question["choiceQuestion"] = {
            "type": "DROP_DOWN",
            "options": [{"value": str(opt)} for opt in q["options"]],
            "shuffle": False,
        }

    else:
        raise ValueError(f"Unsupported question type: {qtype}")

    item = {"title": q["title"], "questionItem": {"question": question}}

    if "description" in q:
        item["description"] = q["description"]

    return item


def create_form(service, config):
    form_body = {
        "info": {
            "title": config["title"],
            "documentTitle": config.get("documentTitle", config["title"]),
        }
    }

    created = service.forms().create(body=form_body).execute()
    form_id = created["formId"]

    requests = []

    if config.get("description"):
        requests.append(
            {
                "updateFormInfo": {
                    "info": {"description": config["description"]},
                    "updateMask": "description",
                }
            }
        )

    for index, q in enumerate(config.get("questions", [])):
        requests.append(
            {
                "createItem": {
                    "item": make_question_item(q),
                    "location": {"index": index},
                }
            }
        )

    if requests:
        service.forms().batchUpdate(
            formId=form_id, body={"requests": requests}
        ).execute()

    return form_id


def update_form(service, form_id, config):
    form = service.forms().get(formId=form_id).execute()

    requests = []

    requests.append(
        {
            "updateFormInfo": {
                "info": {
                    "title": config["title"],
                    "description": config.get("description", ""),
                },
                "updateMask": "title,description",
            }
        }
    )

    items = form.get("items", [])
    for index in range(len(items) - 1, -1, -1):
        requests.append({"deleteItem": {"location": {"index": index}}})

    for index, q in enumerate(config.get("questions", [])):
        requests.append(
            {
                "createItem": {
                    "item": make_question_item(q),
                    "location": {"index": index},
                }
            }
        )

    service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": requests,
            "includeFormInResponse": False,
        },
    ).execute()


def sync_form(service, drive_service, config):
    form_id = find_form_id_by_path_and_title(
        drive_service,
        path=config.get("path"),
        title=config["title"],
    )

    if form_id:
        update_form(service, form_id, config)
        action = "updated"
    else:
        form_id = create_form(service, config)
        action = "created"

    if "path" in config:
        move_file_to_path(
            drive_service=drive_service,
            file_id=form_id,
            path=config["path"],
        )

    return form_id, action


def main():
    parser = argparse.ArgumentParser(
        description="Create a Google Form from a YAML definition."
    )
    parser.add_argument("yaml_file", help="Path to form definition YAML file.")

    args = parser.parse_args()

    config = load_form_yaml(args.yaml_file)
    creds = get_credentials()
    service = build("forms", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    form_id, action = sync_form(service, drive_service, config)

    if action == "created":
        print("Created Google Form")
    else:
        print("Updated Google Form")
    print(f"Form ID: {form_id}")
    print(f"Edit URL: https://docs.google.com/forms/d/{form_id}/edit")
    print(f"Response URL: https://docs.google.com/forms/d/{form_id}/viewform")


if __name__ == "__main__":
    main()

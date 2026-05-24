#!/usr/bin/env python3

import argparse

from googleapiclient.discovery import build

from form_common import (
    SCOPES_BODY_DRIVE,
    find_form_id_by_path_and_title,
    get_credentials as get_shared_credentials,
    load_yaml as load_form_yaml,
    make_question_item,
    move_file_to_path,
    resolve_folder_id_by_path,
)


def get_credentials():
    return get_shared_credentials(SCOPES_BODY_DRIVE)


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

    for index, question in enumerate(config.get("questions", [])):
        requests.append(
            {
                "createItem": {
                    "item": make_question_item(question),
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

    requests = [
        {
            "updateFormInfo": {
                "info": {
                    "title": config["title"],
                    "description": config.get("description", ""),
                },
                "updateMask": "title,description",
            }
        }
    ]

    items = form.get("items", [])
    for index in range(len(items) - 1, -1, -1):
        requests.append({"deleteItem": {"location": {"index": index}}})

    for index, question in enumerate(config.get("questions", [])):
        requests.append(
            {
                "createItem": {
                    "item": make_question_item(question),
                    "location": {"index": index},
                }
            }
        )

    service.forms().batchUpdate(
        formId=form_id,
        body={"requests": requests, "includeFormInResponse": False},
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
    forms_service = build("forms", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    form_id, action = sync_form(forms_service, drive_service, config)

    print("Created Google Form" if action == "created" else "Updated Google Form")
    print(f"Form ID: {form_id}")
    print(f"Edit URL: https://docs.google.com/forms/d/{form_id}/edit")
    print(f"Response URL: https://docs.google.com/forms/d/{form_id}/viewform")


if __name__ == "__main__":
    main()

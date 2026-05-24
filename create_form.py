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


SCOPES = ["https://www.googleapis.com/auth/forms.body"]


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


def main():
    parser = argparse.ArgumentParser(
        description="Create a Google Form from a YAML definition."
    )
    parser.add_argument("yaml_file", help="Path to form definition YAML file.")

    args = parser.parse_args()

    config = load_form_yaml(args.yaml_file)
    creds = get_credentials()
    service = build("forms", "v1", credentials=creds)

    form_id = create_form(service, config)

    print("Created Google Form")
    print(f"Form ID: {form_id}")
    print(f"Edit URL: https://docs.google.com/forms/d/{form_id}/edit")
    print(f"Response URL: https://docs.google.com/forms/d/{form_id}/viewform")


if __name__ == "__main__":
    main()

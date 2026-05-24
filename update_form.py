#!/usr/bin/env python3

import argparse
from pathlib import Path

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/forms.body"]


def get_service(credentials_path: str, token_path: str):
    token_path = Path(token_path)
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())

    return build("forms", "v1", credentials=creds)


def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_question_item(q: dict) -> dict:
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

    item = {
        "title": q["title"],
        "questionItem": {"question": question},
    }

    if q.get("description"):
        item["description"] = q["description"]

    return item


def update_form(service, form_id: str, config: dict):
    form = service.forms().get(formId=form_id).execute()

    requests = []

    requests.append(
        {
            "updateFormInfo": {
                "info": {
                    "title": config["title"],
                    "documentTitle": config.get("documentTitle", config["title"]),
                    "description": config.get("description", ""),
                },
                "updateMask": "title,documentTitle,description",
            }
        }
    )

    # 既存項目を後ろから削除
    items = form.get("items", [])
    for item in reversed(items):
        requests.append({"deleteItem": {"location": {"index": item["index"]}}})

    # YAMLから項目を再作成
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


def main():
    parser = argparse.ArgumentParser(
        description="Update an existing Google Form from a YAML definition."
    )

    parser.add_argument(
        "yaml_file",
        help="Path to form definition YAML file.",
    )

    parser.add_argument(
        "--form-id",
        required=True,
        help="Target Google Form ID.",
    )

    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Path to OAuth client credentials JSON.",
    )

    parser.add_argument(
        "--token",
        default="token.json",
        help="Path to OAuth token cache.",
    )

    args = parser.parse_args()

    config = load_yaml(args.yaml_file)

    service = get_service(
        credentials_path=args.credentials,
        token_path=args.token,
    )

    update_form(
        service=service,
        form_id=args.form_id,
        config=config,
    )

    print("Updated Google Form")
    print(f"Form ID: {args.form_id}")
    print(f"Edit URL: https://docs.google.com/forms/d/{args.form_id}/edit")
    print(f"Response URL: https://docs.google.com/forms/d/{args.form_id}/viewform")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import json
import stat
import sys
from builtins import input
from pathlib import Path

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES_BODY = ["https://www.googleapis.com/auth/forms.body"]
SCOPES_BODY_DRIVE = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
]
SCOPES_BODY_DRIVE_READONLY = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


class PrettyYamlDumper(yaml.SafeDumper):
    # Keep list indentation under parent keys (same style as example.yml).
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


CONFIG_DIR = Path.home() / ".config" / "form-sync-toolkit"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "token.json"


def load_client_config():
    if CREDENTIALS_PATH.exists():
        return json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))

    client_config = prompt_client_config()

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.write_text(
        json.dumps(client_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    CREDENTIALS_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)

    return client_config


def prompt_client_config():
    prompt = (
        "OAuth client credentials JSON not found.\n"
        "Paste the OAuth client credentials JSON: "
    )
    lines = []

    while True:
        try:
            line = input(prompt if not lines else "")
        except EOFError as exc:
            raise ValueError("OAuth client credentials JSON input ended early.") from exc

        lines.append(line)
        raw_json = "\n".join(lines).strip()
        if not raw_json or not _looks_like_complete_json(raw_json):
            continue

        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid OAuth client credentials JSON.") from exc


def _looks_like_complete_json(raw_json):
    depth = 0
    in_string = False
    escape = False

    for char in raw_json:
        if escape:
            escape = False
            continue
        if char == "\\" and in_string:
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
            if depth < 0:
                return True

    return depth == 0 and not in_string


def get_credentials(scopes):
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = load_client_config()
            flow = InstalledAppFlow.from_client_config(
                client_config,
                scopes,
            )
            creds = flow.run_local_server(port=0)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        TOKEN_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)

    return creds


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def escape_drive_query_value(value):
    return value.replace("'", "\\'")


def split_drive_path(path):
    if not path:
        return []

    normalized = str(path).strip()
    if normalized in {"", "/"}:
        return []

    return [part for part in normalized.strip("/").split("/") if part]


def resolve_folder_id_by_path(drive_service, path, create_missing=False):
    folder_id = "root"

    for part in split_drive_path(path):
        escaped_name = escape_drive_query_value(part)
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

    escaped_title = escape_drive_query_value(str(title))
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


def get_form_folder_path(drive_service, form_id):
    metadata = drive_service.files().get(
        fileId=form_id,
        fields="id,name,parents",
    ).execute()

    parent_ids = metadata.get("parents", [])
    if not parent_ids:
        return "/", metadata["name"]

    cache = {}
    folder_path = get_folder_path(drive_service, parent_ids[0], cache)
    return folder_path, metadata["name"]


def normalize_export_path(path):
    if not path:
        return "/"

    if path == "/マイドライブ":
        return "/"

    if path.startswith("/マイドライブ/"):
        return path[len("/マイドライブ") :]

    return path


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


def question_to_yaml_item(item):
    question = item["questionItem"]["question"]
    yaml_item = {
        "title": item["title"],
        "required": bool(question.get("required", False)),
    }

    if "description" in item:
        yaml_item["description"] = item["description"]

    if "textQuestion" in question:
        yaml_item["type"] = "paragraph" if question["textQuestion"].get("paragraph") else "short"
        return yaml_item

    if "choiceQuestion" in question:
        choice = question["choiceQuestion"]
        choice_type = choice.get("type")
        if choice_type == "RADIO":
            yaml_item["type"] = "radio"
        elif choice_type == "CHECKBOX":
            yaml_item["type"] = "checkbox"
        elif choice_type == "DROP_DOWN":
            yaml_item["type"] = "dropdown"
        else:
            raise ValueError(f"Unsupported choiceQuestion type: {choice_type}")

        yaml_item["options"] = [opt.get("value", "") for opt in choice.get("options", [])]
        if yaml_item["type"] in {"radio", "checkbox"}:
            yaml_item["shuffle"] = bool(choice.get("shuffle", False))
        return yaml_item

    raise ValueError("Unsupported question kind")


def form_to_yaml_config(form, folder_path, document_title):
    info = form.get("info", {})
    config = {
        "title": info["title"],
    }

    description = info.get("description")
    if description:
        config["description"] = description

    normalized_path = normalize_export_path(folder_path)
    if normalized_path != "/":
        config["path"] = normalized_path

    if document_title and document_title != config["title"]:
        config["documentTitle"] = document_title

    questions = []
    for item in form.get("items", []):
        if "questionItem" not in item:
            print(
                f"Skip non-question item: {item.get('title', '(untitled)')}",
                file=sys.stderr,
            )
            continue
        try:
            questions.append(question_to_yaml_item(item))
        except ValueError as exc:
            print(
                f"Skip unsupported question: {item.get('title', '(untitled)')} ({exc})",
                file=sys.stderr,
            )

    if questions:
        config["questions"] = questions

    return config


def export_form_yaml(forms_service, drive_service, form_id):
    form = forms_service.forms().get(formId=form_id).execute()
    folder_path, document_title = get_form_folder_path(drive_service, form_id)
    return form_to_yaml_config(form, folder_path, document_title)


def format_questions_spacing(yaml_text):
    lines = yaml_text.splitlines()
    formatted = []
    in_questions = False
    first_question_seen = False

    for line in lines:
        if line == "questions:":
            if formatted and formatted[-1] != "":
                formatted.append("")
            in_questions = True
            first_question_seen = False
            formatted.append(line)
            continue

        if in_questions and line.startswith("  - title:"):
            if first_question_seen and formatted and formatted[-1] != "":
                formatted.append("")
            first_question_seen = True
            formatted.append(line)
            continue

        if in_questions and line and not line.startswith("  "):
            in_questions = False

        formatted.append(line)

    return "\n".join(formatted) + "\n"


def dump_yaml_config(config):
    yaml_text = yaml.dump(
        config,
        Dumper=PrettyYamlDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )

    return format_questions_spacing(yaml_text)

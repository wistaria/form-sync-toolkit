import list_form


class _ExecStub:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _FilesStub:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []
        self.get_calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return _ExecStub(self.payload)

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        file_id = kwargs["fileId"]
        if file_id == "folder-a":
            return _ExecStub({"id": "folder-a", "name": "Team", "parents": ["root"]})
        return _ExecStub({"id": file_id, "name": "Unknown", "parents": ["root"]})


class _ServiceStub:
    def __init__(self, payload):
        self.files_stub = _FilesStub(payload)

    def files(self):
        return self.files_stub


def test_list_forms_uses_expected_query_and_limit():
    payload = {
        "files": [
            {
                "id": "f1",
                "name": "Form 1",
                "createdTime": "x",
                "modifiedTime": "y",
                "parents": ["folder-a"],
            }
        ]
    }
    service = _ServiceStub(payload)

    forms = list_form.list_forms(service, limit=5)

    assert forms == payload["files"]
    assert len(service.files_stub.calls) == 1

    call = service.files_stub.calls[0]
    assert call["q"] == "mimeType='application/vnd.google-apps.form' and trashed=false"
    assert call["pageSize"] == 5
    assert call["fields"] == "files(id,name,createdTime,modifiedTime,parents)"
    assert call["orderBy"] == "modifiedTime desc"


def test_list_forms_returns_empty_when_no_files_key():
    service = _ServiceStub({})

    forms = list_form.list_forms(service)

    assert forms == []


def test_get_form_path_includes_folder_path():
    service = _ServiceStub({})
    cache = {}
    form = {"name": "Survey", "parents": ["folder-a"]}

    path = list_form.get_form_path(service, form, cache)

    assert path == "/Team/Survey"

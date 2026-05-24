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

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return _ExecStub(self.payload)


class _ServiceStub:
    def __init__(self, payload):
        self.files_stub = _FilesStub(payload)

    def files(self):
        return self.files_stub


def test_list_forms_uses_expected_query_and_limit():
    payload = {
        "files": [
            {"id": "f1", "name": "Form 1", "createdTime": "x", "modifiedTime": "y"}
        ]
    }
    service = _ServiceStub(payload)

    forms = list_form.list_forms(service, limit=5)

    assert forms == payload["files"]
    assert len(service.files_stub.calls) == 1

    call = service.files_stub.calls[0]
    assert call["q"] == "mimeType='application/vnd.google-apps.form' and trashed=false"
    assert call["pageSize"] == 5
    assert call["fields"] == "files(id,name,createdTime,modifiedTime)"
    assert call["orderBy"] == "modifiedTime desc"


def test_list_forms_returns_empty_when_no_files_key():
    service = _ServiceStub({})

    forms = list_form.list_forms(service)

    assert forms == []

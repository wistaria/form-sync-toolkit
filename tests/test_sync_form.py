import sync_form as create_form


class _ExecStub:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _FormsStub:
    def __init__(self):
        self.created_body = None
        self.created_count = 0
        self.get_calls = []
        self.batch_updates = []

    def create(self, body):
        self.created_body = body
        self.created_count += 1
        return _ExecStub({"formId": "form-new"})

    def get(self, formId):
        self.get_calls.append(formId)
        return _ExecStub({"items": [{"itemId": "i1"}, {"itemId": "i2"}]})

    def batchUpdate(self, formId, body):
        self.batch_updates.append({"formId": formId, "body": body})
        return _ExecStub({})


class _FormsServiceStub:
    def __init__(self):
        self.forms_stub = _FormsStub()

    def forms(self):
        return self.forms_stub


class _FilesStub:
    def __init__(self, existing_form_id=None, folder_exists=True):
        self.existing_form_id = existing_form_id
        self.folder_exists = folder_exists
        self.folder_id = "folder-1"
        self.list_calls = []
        self.get_calls = []
        self.update_calls = []
        self.create_calls = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        query = kwargs["q"]

        if "application/vnd.google-apps.folder" in query:
            if self.folder_exists:
                return _ExecStub({"files": [{"id": self.folder_id, "name": "Forms"}]})
            return _ExecStub({"files": []})

        if self.existing_form_id:
            return _ExecStub({"files": [{"id": self.existing_form_id, "name": "Survey"}]})
        return _ExecStub({"files": []})

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return _ExecStub({"parents": ["root"]})

    def update(self, **kwargs):
        self.update_calls.append(kwargs)
        return _ExecStub({})

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        self.folder_exists = True
        self.folder_id = "folder-created"
        return _ExecStub({"id": self.folder_id, "name": kwargs["body"]["name"]})


class _DriveServiceStub:
    def __init__(self, existing_form_id=None, folder_exists=True):
        self.files_stub = _FilesStub(
            existing_form_id=existing_form_id,
            folder_exists=folder_exists,
        )

    def files(self):
        return self.files_stub


def test_make_question_item_short_with_description():
    item = create_form.make_question_item(
        {
            "type": "short",
            "title": "Name",
            "required": True,
            "description": "Your full name",
        }
    )

    assert item == {
        "title": "Name",
        "description": "Your full name",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {"paragraph": False},
            }
        },
    }


def test_make_question_item_paragraph_with_description():
    item = create_form.make_question_item(
        {
            "type": "paragraph",
            "title": "Comment",
            "description": "例）改善案を記入してください",
        }
    )

    assert item == {
        "title": "Comment",
        "description": "例）改善案を記入してください",
        "questionItem": {
            "question": {
                "required": False,
                "textQuestion": {"paragraph": True},
            }
        },
    }


def test_create_form_builds_expected_requests():
    forms_service = _FormsServiceStub()
    config = {
        "title": "Survey",
        "description": "Please answer",
        "questions": [
            {"type": "short", "title": "Name"},
            {"type": "radio", "title": "Role", "options": ["Dev", "PM"]},
        ],
    }

    form_id = create_form.create_form(forms_service, config)

    assert form_id == "form-new"
    assert forms_service.forms_stub.created_body == {
        "info": {"title": "Survey", "documentTitle": "Survey"}
    }
    assert len(forms_service.forms_stub.batch_updates) == 1

    requests = forms_service.forms_stub.batch_updates[0]["body"]["requests"]
    assert requests[0] == {
        "updateFormInfo": {
            "info": {"description": "Please answer"},
            "updateMask": "description",
        }
    }
    assert requests[1]["createItem"]["location"] == {"index": 0}
    assert requests[2]["createItem"]["location"] == {"index": 1}


def test_sync_form_creates_when_not_found():
    forms_service = _FormsServiceStub()
    drive_service = _DriveServiceStub(existing_form_id=None, folder_exists=True)
    config = {"title": "Survey", "path": "/Forms"}

    form_id, action = create_form.sync_form(forms_service, drive_service, config)

    assert action == "created"
    assert form_id == "form-new"
    assert forms_service.forms_stub.created_count == 1
    assert len(forms_service.forms_stub.get_calls) == 0
    assert len(drive_service.files_stub.update_calls) == 1


def test_sync_form_updates_when_found():
    forms_service = _FormsServiceStub()
    drive_service = _DriveServiceStub(existing_form_id="form-existing", folder_exists=True)
    config = {
        "title": "Survey",
        "path": "/Forms",
        "description": "updated",
        "questions": [{"type": "short", "title": "Q1"}],
    }

    form_id, action = create_form.sync_form(forms_service, drive_service, config)

    assert action == "updated"
    assert form_id == "form-existing"
    assert forms_service.forms_stub.created_count == 0
    assert forms_service.forms_stub.get_calls == ["form-existing"]

    update_batch = forms_service.forms_stub.batch_updates[0]
    assert update_batch["formId"] == "form-existing"
    assert update_batch["body"]["requests"][0]["updateFormInfo"]["updateMask"] == "title,description"


def test_sync_form_creates_missing_folder_path():
    forms_service = _FormsServiceStub()
    drive_service = _DriveServiceStub(existing_form_id=None, folder_exists=False)
    config = {"title": "Survey", "path": "/Forms"}

    form_id, action = create_form.sync_form(forms_service, drive_service, config)

    assert action == "created"
    assert form_id == "form-new"
    assert len(drive_service.files_stub.create_calls) == 1
    assert drive_service.files_stub.create_calls[0]["body"]["name"] == "Forms"
    assert drive_service.files_stub.update_calls[0]["addParents"] == "folder-created"

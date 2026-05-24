import create_form


class _ExecStub:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _FormsStub:
    def __init__(self):
        self.created_body = None
        self.batch_form_id = None
        self.batch_body = None

    def create(self, body):
        self.created_body = body
        return _ExecStub({"formId": "form-123"})

    def batchUpdate(self, formId, body):
        self.batch_form_id = formId
        self.batch_body = body
        return _ExecStub({})


class _ServiceStub:
    def __init__(self):
        self.forms_stub = _FormsStub()

    def forms(self):
        return self.forms_stub


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


def test_make_question_item_unsupported_type_raises():
    try:
        create_form.make_question_item({"type": "date", "title": "When"})
    except ValueError as exc:
        assert "Unsupported question type" in str(exc)
    else:
        raise AssertionError("ValueError was not raised")


def test_create_form_builds_expected_requests():
    service = _ServiceStub()
    config = {
        "title": "Survey",
        "description": "Please answer",
        "questions": [
            {"type": "short", "title": "Name"},
            {"type": "radio", "title": "Role", "options": ["Dev", "PM"]},
        ],
    }

    form_id = create_form.create_form(service, config)

    assert form_id == "form-123"
    assert service.forms_stub.created_body == {
        "info": {"title": "Survey", "documentTitle": "Survey"}
    }
    assert service.forms_stub.batch_form_id == "form-123"

    requests = service.forms_stub.batch_body["requests"]
    assert requests[0] == {
        "updateFormInfo": {
            "info": {"description": "Please answer"},
            "updateMask": "description",
        }
    }
    assert requests[1]["createItem"]["location"] == {"index": 0}
    assert requests[1]["createItem"]["item"]["title"] == "Name"
    assert requests[2]["createItem"]["location"] == {"index": 1}
    assert requests[2]["createItem"]["item"]["title"] == "Role"


def test_create_form_skips_batch_update_when_no_description_and_no_questions():
    service = _ServiceStub()
    config = {"title": "Empty Form"}

    form_id = create_form.create_form(service, config)

    assert form_id == "form-123"
    assert service.forms_stub.batch_body is None

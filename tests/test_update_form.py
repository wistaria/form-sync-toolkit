import update_form


class _ExecStub:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _FormsStub:
    def __init__(self):
        self.batch_args = None

    def get(self, formId):
        assert formId == "form-abc"
        return _ExecStub(
            {
                "items": [
                    {"itemId": "i1"},
                    {"itemId": "i2"},
                    {"itemId": "i3"},
                ]
            }
        )

    def batchUpdate(self, formId, body):
        self.batch_args = {"formId": formId, "body": body}
        return _ExecStub({})


class _ServiceStub:
    def __init__(self):
        self.forms_stub = _FormsStub()

    def forms(self):
        return self.forms_stub


def test_update_form_replaces_all_items_and_updates_form_info():
    service = _ServiceStub()
    config = {
        "title": "Updated Survey",
        "description": "new description",
        "questions": [
            {"type": "short", "title": "Q1"},
            {"type": "checkbox", "title": "Q2", "options": ["A", "B"]},
        ],
    }

    update_form.update_form(service, "form-abc", config)

    batch = service.forms_stub.batch_args
    assert batch is not None
    assert batch["formId"] == "form-abc"
    assert batch["body"]["includeFormInResponse"] is False

    requests = batch["body"]["requests"]

    assert requests[0] == {
        "updateFormInfo": {
            "info": {
                "title": "Updated Survey",
                "description": "new description",
            },
            "updateMask": "title,description",
        }
    }

    assert requests[1] == {"deleteItem": {"location": {"index": 2}}}
    assert requests[2] == {"deleteItem": {"location": {"index": 1}}}
    assert requests[3] == {"deleteItem": {"location": {"index": 0}}}

    assert requests[4]["createItem"]["location"] == {"index": 0}
    assert requests[4]["createItem"]["item"]["title"] == "Q1"
    assert requests[5]["createItem"]["location"] == {"index": 1}
    assert requests[5]["createItem"]["item"]["title"] == "Q2"


def test_make_question_item_dropdown():
    item = update_form.make_question_item(
        {
            "type": "dropdown",
            "title": "Department",
            "options": ["Eng", "Sales"],
        }
    )

    assert item == {
        "title": "Department",
        "questionItem": {
            "question": {
                "required": False,
                "choiceQuestion": {
                    "type": "DROP_DOWN",
                    "options": [{"value": "Eng"}, {"value": "Sales"}],
                    "shuffle": False,
                },
            }
        },
    }

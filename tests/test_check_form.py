import check_form


class _ExecStub:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _FormsStub:
    def __init__(self, form_payload):
        self.form_payload = form_payload

    def get(self, formId):
        return _ExecStub(self.form_payload)


class _FormsServiceStub:
    def __init__(self, form_payload):
        self.forms_stub = _FormsStub(form_payload)

    def forms(self):
        return self.forms_stub


class _DriveServiceStub:
    def __init__(self, form_payload):
        self.forms_service = _FormsServiceStub(form_payload)

    def files(self):
        raise AssertionError("Drive service should not be used in this test")


def test_normalize_yaml_config_applies_defaults_and_path_normalization():
    raw_config = {
        "title": "Survey",
        "path": "/マイドライブ/Forms/Team",
        "questions": [
            {
                "type": "radio",
                "title": "Role",
                "options": ["Dev", "PM"],
                "required": True,
                "shuffle": True,
            },
            {
                "type": "paragraph",
                "title": "Comment",
                "description": "自由記述",
            },
        ],
    }

    normalized = check_form.normalize_yaml_config(raw_config)

    assert normalized == {
        "title": "Survey",
        "path": "/Forms/Team",
        "questions": [
            {
                "title": "Role",
                "required": True,
                "type": "radio",
                "options": ["Dev", "PM"],
                "shuffle": True,
            },
            {
                "title": "Comment",
                "required": False,
                "description": "自由記述",
                "type": "paragraph",
            },
        ],
    }


def test_compare_yaml_config_to_form_detects_difference():
    yaml_config = {
        "title": "Survey",
        "questions": [
            {"type": "short", "title": "Name"},
        ],
    }
    form_config = {
        "title": "Survey",
        "questions": [
            {"title": "Name changed", "required": False, "type": "short"},
        ],
    }

    match, diff = check_form.compare_yaml_config_to_form(yaml_config, form_config)

    assert match is False
    assert "Name" in diff
    assert "Name changed" in diff


def test_compare_yaml_config_to_form_matches_after_normalization():
    yaml_config = {
        "title": "Survey",
        "path": "/マイドライブ/Forms/Team",
        "questions": [
            {
                "type": "checkbox",
                "title": "Tools",
                "options": ["Excel", "Slack"],
                "required": True,
            }
        ],
    }
    form_config = {
        "title": "Survey",
        "path": "/Forms/Team",
        "questions": [
            {
                "title": "Tools",
                "required": True,
                "type": "checkbox",
                "options": ["Excel", "Slack"],
                "shuffle": False,
            }
        ],
    }

    match, diff = check_form.compare_yaml_config_to_form(yaml_config, form_config)

    assert match is True
    assert diff == ""


def test_check_form_against_yaml_returns_error_for_missing_form():
    yaml_config = {"title": "Survey"}

    form_payload = {
        "info": {"title": "Survey"},
        "items": [],
    }

    # export_form_yaml is called first; simulate missing form on that path.
    def fake_export_form_yaml(*_args, **_kwargs):
        from types import SimpleNamespace

        from googleapiclient.errors import HttpError

        response = SimpleNamespace(status=404, reason="Not Found")
        raise HttpError(response, b'{"error": {"message": "Not Found"}}')

    original_export_form_yaml = check_form.export_form_yaml
    check_form.export_form_yaml = fake_export_form_yaml
    try:
        match, diff = check_form.check_form_against_yaml(
            forms_service=_FormsServiceStub(form_payload),
            drive_service=_DriveServiceStub(form_payload),
            form_id="missing-form-id",
            yaml_config=yaml_config,
        )
    finally:
        check_form.export_form_yaml = original_export_form_yaml

    assert match is False
    assert "Google Form not found" in diff
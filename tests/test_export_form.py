import export_form


def test_question_to_yaml_item_text_and_choice_types():
    short_item = {
        "title": "Name",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {"paragraph": False},
            }
        },
    }
    radio_item = {
        "title": "Role",
        "questionItem": {
            "question": {
                "required": False,
                "choiceQuestion": {
                    "type": "RADIO",
                    "options": [{"value": "Dev"}, {"value": "PM"}],
                    "shuffle": True,
                },
            }
        },
    }

    assert export_form.question_to_yaml_item(short_item) == {
        "title": "Name",
        "required": True,
        "type": "short",
    }
    assert export_form.question_to_yaml_item(radio_item) == {
        "title": "Role",
        "required": False,
        "type": "radio",
        "options": ["Dev", "PM"],
        "shuffle": True,
    }


def test_form_to_yaml_config_includes_path_and_document_title_when_different(capsys):
    form = {
        "info": {
            "title": "Survey",
            "description": "Please answer",
        },
        "items": [
            {
                "title": "Q1",
                "questionItem": {
                    "question": {
                        "required": False,
                        "textQuestion": {"paragraph": True},
                    }
                },
            },
            {
                "title": "Section 1",
            },
        ],
    }

    config = export_form.form_to_yaml_config(
        form=form,
        folder_path="/Forms/Team",
        document_title="Survey 2026",
    )

    assert config["title"] == "Survey"
    assert config["description"] == "Please answer"
    assert config["path"] == "/Forms/Team"
    assert config["documentTitle"] == "Survey 2026"
    assert config["questions"] == [
        {
            "title": "Q1",
            "required": False,
            "type": "paragraph",
        }
    ]

    stderr = capsys.readouterr().err
    assert "Skip non-question item" in stderr


def test_form_to_yaml_config_omits_path_in_root_and_document_title_when_same():
    form = {
        "info": {
            "title": "Survey",
        },
        "items": [],
    }

    config = export_form.form_to_yaml_config(
        form=form,
        folder_path="/",
        document_title="Survey",
    )

    assert config == {
        "title": "Survey",
    }


def test_form_to_yaml_config_normalizes_my_drive_prefix():
    form = {
        "info": {
            "title": "Survey",
        },
        "items": [],
    }

    config = export_form.form_to_yaml_config(
        form=form,
        folder_path="/マイドライブ/Forms/業務アンケート",
        document_title="Survey",
    )

    assert config["path"] == "/Forms/業務アンケート"


def test_dump_yaml_config_matches_example_style_indentation():
    config = {
        "title": "Survey",
        "questions": [
            {
                "title": "Q1",
                "type": "radio",
                "required": True,
                "options": ["A", "B"],
            },
            {
                "title": "Q2",
                "type": "short",
                "required": False,
            }
        ],
    }

    yaml_text = export_form.dump_yaml_config(config)

    assert "title: Survey\n\nquestions:\n  - title: Q1" in yaml_text
    assert "options:\n      - A\n      - B" in yaml_text
    assert "      - B\n\n  - title: Q2" in yaml_text

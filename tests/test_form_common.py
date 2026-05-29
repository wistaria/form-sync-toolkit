import json
import stat

import form_common


class _FakeCreds:
    def __init__(self, valid=True, expired=False, refresh_token=None):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refresh_calls = 0

    def refresh(self, _request):
        self.refresh_calls += 1
        self.valid = True

    def to_json(self):
        return json.dumps({"token": "token-value"})


class _FakeFlow:
    def __init__(self, creds):
        self.creds = creds
        self.run_calls = []

    def run_local_server(self, port):
        self.run_calls.append(port)
        return self.creds


def test_get_credentials_prompts_and_persists_client_config(tmp_path, monkeypatch):
    config_dir = tmp_path / ".config" / "form-sync-toolkit"
    credentials_path = config_dir / "credentials.json"
    source_path = tmp_path / "downloaded-credentials.json"
    source_config = {
        "installed": {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "redirect_uris": ["http://localhost"],
        }
    }
    source_path.write_text(json.dumps(source_config), encoding="utf-8")

    fake_creds = _FakeCreds(valid=True)
    flow = _FakeFlow(fake_creds)
    flow_calls = []

    monkeypatch.setattr(form_common, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(form_common, "CREDENTIALS_PATH", credentials_path)
    monkeypatch.setattr(form_common, "input", lambda _prompt: str(source_path))
    monkeypatch.setattr(form_common.Credentials, "from_authorized_user_file", lambda *_args: None)
    monkeypatch.setattr(
        form_common.InstalledAppFlow,
        "from_client_config",
        lambda client_config, scopes: flow_calls.append((client_config, scopes)) or flow,
    )
    monkeypatch.chdir(tmp_path)

    creds = form_common.get_credentials(["scope-a"])

    assert creds is fake_creds
    assert flow_calls == [(source_config, ["scope-a"])]
    assert flow.run_calls == [0]
    assert json.loads(credentials_path.read_text(encoding="utf-8")) == source_config
    assert stat.S_IMODE(credentials_path.stat().st_mode) == 0o600
    assert json.loads((tmp_path / "token.json").read_text(encoding="utf-8")) == {
        "token": "token-value"
    }


def test_get_credentials_reuses_saved_client_config(tmp_path, monkeypatch):
    config_dir = tmp_path / ".config" / "form-sync-toolkit"
    credentials_path = config_dir / "credentials.json"
    saved_config = {
        "installed": {
            "client_id": "saved-client-id",
            "client_secret": "saved-client-secret",
            "redirect_uris": ["http://localhost"],
        }
    }
    config_dir.mkdir(parents=True)
    credentials_path.write_text(json.dumps(saved_config), encoding="utf-8")

    fake_creds = _FakeCreds(valid=True)
    flow = _FakeFlow(fake_creds)
    flow_calls = []

    monkeypatch.setattr(form_common, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(form_common, "CREDENTIALS_PATH", credentials_path)
    monkeypatch.setattr(
        form_common,
        "input",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("input should not be used")),
    )
    monkeypatch.setattr(form_common.Credentials, "from_authorized_user_file", lambda *_args: None)
    monkeypatch.setattr(
        form_common.InstalledAppFlow,
        "from_client_config",
        lambda client_config, scopes: flow_calls.append((client_config, scopes)) or flow,
    )
    monkeypatch.chdir(tmp_path)

    creds = form_common.get_credentials(["scope-b"])

    assert creds is fake_creds
    assert flow_calls == [(saved_config, ["scope-b"])]
    assert flow.run_calls == [0]
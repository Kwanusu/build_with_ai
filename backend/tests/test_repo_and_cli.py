import json
import subprocess
from pathlib import Path

import pytest

from lopper import repo
from lopper.cli import main
from lopper.repo import RepoError, RepoRef, parse_repo_url


@pytest.mark.parametrize(
    "raw",
    [
        "https://github.com/pallets/flask",
        "https://github.com/pallets/flask.git",
        "https://github.com/pallets/flask/",
        "github.com/pallets/flask",
        "  https://www.github.com/pallets/flask  ",
    ],
)
def test_accepts_public_github_urls(raw):
    assert parse_repo_url(raw) == RepoRef("pallets", "flask")
    assert parse_repo_url(raw).url == "https://github.com/pallets/flask"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "pallets/flask",
        "http://github.com/pallets/flask",
        "https://gitlab.com/pallets/flask",
        "https://github.com.evil.example/pallets/flask",
        "https://evil.example/github.com/pallets/flask",
        "https://user:pass@github.com/pallets/flask",
        "https://github.com/pallets",
        "https://github.com/pallets/flask/tree/main",
        "https://github.com/pallets/flask?x=1",
        "https://github.com/../flask",
        "file:///etc/passwd",
        "https://127.0.0.1/pallets/flask",
        "git@github.com:pallets/flask.git",
        "https://github.com/pallets/flask; rm -rf /",
        "https://github.com/pallets/fla sk",
    ],
)
def test_rejects_everything_else(raw):
    with pytest.raises(RepoError):
        parse_repo_url(raw)


def test_clone_failure_explains_what_happened_and_cleans_up(monkeypatch):
    created = []
    real_mkdtemp = repo.tempfile.mkdtemp

    def tracking_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(Path(path))
        return path

    monkeypatch.setattr(repo.tempfile, "mkdtemp", tracking_mkdtemp)
    monkeypatch.setattr(
        repo.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 128, "", "fatal: repository not found")
    )
    with pytest.raises(RepoError) as error:
        with repo.checkout(RepoRef("someone", "private-repo")):
            pass
    assert "public repos" in str(error.value) and "hasn't been changed" in str(error.value)
    assert created and not created[0].exists()


def test_clone_timeout_is_reported(monkeypatch):
    def slow(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=1)

    monkeypatch.setattr(repo.subprocess, "run", slow)
    with pytest.raises(RepoError, match="too long"):
        with repo.checkout(RepoRef("a", "b"), timeout=1):
            pass


def test_clone_command_is_read_only_and_never_prompts(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["env"] = kwargs["env"]
        Path(command[-1]).mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(repo.subprocess, "run", fake_run)
    with repo.checkout(RepoRef("pallets", "flask")) as folder:
        assert folder.is_dir()
    command = seen["command"]
    assert command[0] == "git" and "--depth" in command and "--" in command
    assert command[command.index("--") + 1] == "https://github.com/pallets/flask.git"
    assert "protocol.allow=never" in command and "core.hooksPath=" in command
    assert seen["env"]["GIT_TERMINAL_PROMPT"] == "0"


# ---------- CLI ----------


def make_project(root: Path) -> Path:
    (root / "src").mkdir()
    (root / "package.json").write_text(json.dumps({"name": "demo", "dependencies": {"left-pad": "1"}}))
    (root / "src" / "a.ts").write_text("export function dead() {}\n")
    return root


def test_cli_text_report_uses_plain_voice(tmp_path, capsys):
    assert main(["scan", str(make_project(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert "Found 2 unused items: 1 unused package, 1 unused export." in out
    assert "left-pad" in out and "No file under the repo root imports 'left-pad'" in out
    assert "Nothing was changed." in out and "!" not in out


def test_cli_json_output_matches_the_api_shape(tmp_path, capsys):
    assert main(["scan", str(make_project(tmp_path)), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["counts"]["unused-package"] == 1
    assert {"type", "package", "item", "file_path", "line", "evidence", "confidence", "language", "report_only"} <= set(data["findings"][0])


def test_cli_writes_to_a_file(tmp_path, capsys):
    out = tmp_path / "report.json"
    project = tmp_path / "p"
    project.mkdir()
    make_project(project)
    assert main(["scan", str(project), "--format", "json", "-o", str(out)]) == 0
    assert json.loads(out.read_text())["counts"]["unused-export"] == 1


def test_scan_exits_zero_by_default_and_one_with_strict(tmp_path):
    project = make_project(tmp_path)
    assert main(["scan", str(project)]) == 0
    assert main(["scan", str(project), "--strict"]) == 1


def test_strict_ignores_report_only_lint(tmp_path):
    (tmp_path / "a.py").write_text("import os\n")
    assert main(["scan", str(tmp_path), "--strict"]) == 0


def test_clean_project_says_so(tmp_path, capsys):
    (tmp_path / "a.py").write_text("print(1)\n")
    assert main(["scan", str(tmp_path)]) == 0
    assert "found no unused packages" in capsys.readouterr().out


def test_cli_reports_a_missing_folder(tmp_path, capsys):
    assert main(["scan", str(tmp_path / "nope")]) == 2
    err = capsys.readouterr().err
    assert "hasn't been changed" in err


def test_cli_rejects_a_bad_url_without_cloning(capsys):
    assert main(["scan", "--url", "https://evil.example/x/y"]) == 2
    assert "doesn't look like a GitHub repo URL" in capsys.readouterr().err


# ---------- cloning with a signed-in person's token ----------


def test_the_token_goes_through_the_environment_never_the_command_line(monkeypatch):
    import base64

    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["env"] = kwargs["env"]
        Path(command[-1]).mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(repo.subprocess, "run", fake_run)
    with repo.checkout(RepoRef("octo", "private-web"), token="gho_secret_value"):
        pass
    assert not any("gho_secret_value" in part for part in seen["command"])
    assert not any("gho_secret_value" in part or "x-access-token" in part for part in seen["command"])
    header = seen["env"]["GIT_CONFIG_VALUE_0"]
    assert header.startswith("AUTHORIZATION: basic ")
    assert base64.b64decode(header.split()[-1]).decode() == "x-access-token:gho_secret_value"
    assert seen["env"]["GIT_CONFIG_KEY_0"] == "http.https://github.com/.extraheader"


def test_no_token_means_no_credentials_are_sent(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):
        seen["env"] = kwargs["env"]
        Path(command[-1]).mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(repo.subprocess, "run", fake_run)
    monkeypatch.delenv("GIT_CONFIG_COUNT", raising=False)
    with repo.checkout(RepoRef("octo", "web")):
        pass
    assert "GIT_CONFIG_VALUE_0" not in seen["env"]


def test_a_failed_clone_never_repeats_the_token(monkeypatch):
    monkeypatch.setattr(
        repo.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 128, "", "fatal: could not read from https://x-access-token:gho_secret_value@github.com/"),
    )
    with pytest.raises(RepoError) as error:
        with repo.checkout(RepoRef("octo", "private-web"), token="gho_secret_value"):
            pass
    assert "gho_secret_value" not in str(error.value)
    assert "account you signed in with" in str(error.value)


def test_without_a_token_the_message_points_to_signing_in(monkeypatch):
    monkeypatch.setattr(repo.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 128, "", ""))
    with pytest.raises(RepoError) as error:
        with repo.checkout(RepoRef("octo", "private-web")):
            pass
    assert "sign in with GitHub" in str(error.value) and "hasn't been changed" in str(error.value)

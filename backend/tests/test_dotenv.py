import os

from lopper.dotenv import load_dotenv


def test_reads_names_and_values_and_skips_comments_and_blanks(tmp_path, monkeypatch):
    for name in ("LOP_A", "LOP_B", "LOP_C", "LOP_D", "LOP_E"):
        monkeypatch.delenv(name, raising=False)
    file = tmp_path / ".env"
    file.write_text(
        "# a comment\n\nLOP_A=plain\nLOP_B = \"quoted value\"\nexport LOP_C='single'\nLOP_D=trailing # note\nnot a setting\nLOP_E=a=b\n",
        encoding="utf-8",
    )
    loaded = load_dotenv(file)
    assert loaded == ["LOP_A", "LOP_B", "LOP_C", "LOP_D", "LOP_E"]
    assert os.environ["LOP_A"] == "plain"
    assert os.environ["LOP_B"] == "quoted value"
    assert os.environ["LOP_C"] == "single"
    assert os.environ["LOP_D"] == "trailing"
    assert os.environ["LOP_E"] == "a=b"
    for name in loaded:
        monkeypatch.delenv(name)


def test_a_variable_you_already_set_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("LOP_KEEP", "from the shell")
    (tmp_path / ".env").write_text("LOP_KEEP=from the file\n", encoding="utf-8")
    assert load_dotenv(tmp_path / ".env") == []
    assert os.environ["LOP_KEEP"] == "from the shell"


def test_a_missing_file_is_fine(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == []

"""別のリポジトリから依存として使うときの前提。部品は使う側の `parts/` にあり、viewer 系の依存
(extra `viewer`)は入っていないことがある。"""

import importlib.util

import pytest

from lab import cli, parts


def make_project(root, name="mini"):
    (root / "parts").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'consumer'\n")
    (root / "parts" / f"{name}.py").write_text(
        "from build123d import Box\n\n\ndef build(size=10.0):\n    return Box(size, size, size)\n"
    )


def test_project_root_is_found_from_a_subdirectory_of_the_consumer(tmp_path):
    make_project(tmp_path)
    sub = tmp_path / "docs" / "deep"
    sub.mkdir(parents=True)
    assert parts.project_root(sub) == tmp_path.resolve()


def test_lab_commands_work_in_a_consumer_project(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["list"]) == 0
    assert capsys.readouterr().out.split() == ["mini"]
    assert cli.main(["check", "--all"]) == 0
    assert cli.main(["export", "mini"]) == 0
    assert (tmp_path / "out" / "mini.3mf").is_file()  # 出力は実行したディレクトリの out/
    assert (tmp_path / "out" / "mini.step").is_file()


def hide(monkeypatch, *modules):
    real = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name, *a: None if name in modules else real(name, *a)
    )


@pytest.mark.parametrize("command", [["show", "mini"], ["viewer"], ["watch", "mini"]])
def test_viewer_commands_say_how_to_install_the_extra(command, tmp_path, monkeypatch):
    make_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    hide(monkeypatch, "ocp_viewer", "watchfiles")
    with pytest.raises(SystemExit) as exc:
        cli.main(command)
    message = str(exc.value)
    assert "ocp_viewer" in message
    assert "code-cad-lab[viewer]" in message


def test_check_and_export_do_not_need_the_viewer(tmp_path, monkeypatch):
    make_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    hide(monkeypatch, "ocp_viewer", "watchfiles")
    assert cli.main(["check", "mini"]) == 0
    assert cli.main(["export", "mini"]) == 0


def test_watch_follows_src_only_when_it_exists(tmp_path):
    make_project(tmp_path)
    assert cli.watch_paths(tmp_path) == [tmp_path / "parts"]
    (tmp_path / "src").mkdir()
    assert cli.watch_paths(tmp_path) == [tmp_path / "parts", tmp_path / "src"]

from pathlib import Path

import pytest

from onboarding import paths


def test_las_carpetas_salen_de_la_raiz_del_repo() -> None:
    assert (paths.REPO_ROOT / "src" / "onboarding" / "paths.py").exists()
    assert (paths.CORPUS_DIR / "organigrama.md").exists()
    assert paths.repo_relative(paths.REPO_ROOT / "src" / "onboarding") == "src/onboarding"


def test_lee_un_yaml_de_data_y_avisa_si_falta(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "people.yaml").write_text("- key: ana\n", encoding="utf-8")
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path)

    assert paths.load_data_yaml("people.yaml") == [{"key": "ana"}]
    assert paths.load_data_yaml("no-esta.yaml") == []
    with pytest.raises(FileNotFoundError, match="no-esta.yaml"):
        paths.load_data_yaml("no-esta.yaml", required=True)


def test_los_documentos_no_incluyen_el_readme(tmp_path: Path) -> None:
    for name in ("README.md", "b.md", "a.md"):
        (tmp_path / name).write_text("x", encoding="utf-8")

    assert [path.name for path in paths.markdown_documents(tmp_path)] == ["a.md", "b.md"]

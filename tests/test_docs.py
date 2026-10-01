import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [ROOT / "README.md", ROOT / "README.en.md", *sorted((ROOT / "docs").glob("*.md"))]


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda path: path.name)
def test_markdown_fences_are_balanced(document: Path):
    text = document.read_text(encoding="utf-8")
    assert text.count("```") % 2 == 0


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda path: path.name)
def test_local_markdown_links_exist(document: Path):
    text = document.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#")):
            continue
        path_text = target.split("#", 1)[0]
        assert (document.parent / path_text).resolve().exists(), (
            f"Broken link in {document}: {target}"
        )

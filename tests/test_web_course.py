"""Pipeline and app tests for the mobile web companion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.build_web_course import MODULES, blank_lines, build_module, parse_quiz, split_solution

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "webapp" / "content"
ASSESSMENT_DIR = REPO_ROOT / "assessments"

FLAGSHIP = "02_similarity_and_classification"


def test_split_solution_returns_none_without_markers():
    assert split_solution("x = 1\ny = 2\n") is None


def test_split_solution_partitions_the_marked_span():
    head, body, tail = split_solution(
        "before = 1\n### BEGIN SOLUTION\nmid = 2\n### END SOLUTION\nafter = 3\n"
    )
    assert head == "before = 1"
    assert body == ["mid = 2"]
    assert tail == "after = 3"


def test_blank_lines_prompts_on_assignments_only():
    lines = blank_lines(["matrix = to_matrix(gdf)", "for row in matrix:", "    total += row"])
    assert lines[0] == {
        "kind": "blank",
        "indent": "",
        "lhs": "matrix",
        "answer": "to_matrix(gdf)",
    }
    assert [line["kind"] for line in lines[1:]] == ["given", "given"]


def test_blank_lines_leaves_comparisons_alone():
    # `==` is not an assignment; blanking it would produce an unanswerable prompt.
    assert blank_lines(["assert a == b"])[0]["kind"] == "given"


@pytest.mark.parametrize("quiz_file", sorted({m[2] for m in MODULES if m[2]}))
def test_every_quiz_parses_with_exactly_one_correct_option(quiz_file):
    questions = parse_quiz(ASSESSMENT_DIR / quiz_file)
    assert questions, f"{quiz_file} produced no questions"
    for question in questions:
        correct = [o for o in question["options"] if o["correct"]]
        assert len(correct) == 1, f"{quiz_file} {question['id']}: {len(correct)} correct options"
        for option in question["options"]:
            assert option["text"], f"{quiz_file} {question['id']} {option['label']}: empty option"
            assert option["explanation_html"], (
                f"{quiz_file} {question['id']} {option['label']}: no explanation"
            )


def test_flagship_module_exercises_every_block_type():
    module = build_module(FLAGSHIP, "02-similarity", "02_similarity_classification_quiz.md")
    kinds = {block["type"] for block in module["blocks"]}
    assert {"prose", "code", "output", "blank", "trap"} <= kinds
    assert module["title"].startswith("Module 3")


def test_trap_block_carries_its_correction():
    module = build_module(FLAGSHIP, "02-similarity", "02_similarity_classification_quiz.md")
    trap = next(b for b in module["blocks"] if b["type"] == "trap")
    assert "WRONG" in trap["code"]
    # A trap without its explanation teaches the trap.
    assert "wrong" in trap["why_html"].lower()


def test_no_blank_ships_without_an_answer():
    module = build_module(FLAGSHIP, "02-similarity", "02_similarity_classification_quiz.md")
    blanks = [b for b in module["blocks"] if b["type"] == "blank"]
    assert blanks
    for block in blanks:
        prompts = [line for line in block["lines"] if line["kind"] == "blank"]
        assert prompts, "a blank block with nothing to fill in"
        assert all(line["answer"].strip() for line in prompts)


def test_colab_plumbing_is_not_shipped():
    module = build_module(FLAGSHIP, "02-similarity", "02_similarity_classification_quiz.md")
    code = "\n".join(b.get("code", "") for b in module["blocks"])
    assert "IN_COLAB" not in code
    assert "importlib.util" not in code


def test_committed_bundle_matches_the_notebooks():
    """The bundle is committed so the container build needs no geo stack -- keep it fresh."""
    index = json.loads((CONTENT_DIR / "index.json").read_text())
    assert [m["slug"] for m in index["modules"]] == [m[1] for m in MODULES]
    for stem, slug, quiz_file in MODULES:
        committed = json.loads((CONTENT_DIR / f"{slug}.json").read_text())
        assert committed == build_module(stem, slug, quiz_file), (
            f"{slug}.json is stale -- run `make web-content`"
        )


def test_every_referenced_figure_exists():
    for _, slug, _ in MODULES:
        module = json.loads((CONTENT_DIR / f"{slug}.json").read_text())
        for block in module["blocks"]:
            images = block.get("images") or block.get("output", {}).get("images", [])
            for src in images:
                assert (REPO_ROOT / "webapp" / src.lstrip("/")).is_file(), f"missing {src}"


def test_app_serves_health_and_modules():
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from webapp.app import app

    with fastapi_testclient.TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "modules": len(MODULES)}

        assert client.get("/").status_code == 200
        assert client.get("/m/02-similarity").status_code == 200
        assert client.get("/api/module/02-similarity").json()["slug"] == "02-similarity"
        assert client.get("/api/module/nope").status_code == 404
        # The bundle directory holds index.json next to the modules; neither a
        # direct nor an encoded traversal may reach anything the index omits.
        assert client.get("/api/module/index").status_code == 404
        assert client.get("/api/module/..%2findex").status_code == 404

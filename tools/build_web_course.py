"""Build the mobile web-course content bundle from the executed solution notebooks.

The web companion never runs Python. Every figure, printed table and stdout line it
shows was produced by `make execute-notebooks`, so the bundle is only ever as fresh
as `notebooks/solutions/executed_*.ipynb`. Interactive blocks (fill-in-the-blank,
multiple choice) carry their answer keys inline -- acceptable while the deployment is
single-user; move the checking server-side before it is opened up.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = REPO_ROOT / "notebooks" / "solutions"
ASSESSMENT_DIR = REPO_ROOT / "assessments"
WEBAPP_DIR = REPO_ROOT / "webapp"
CONTENT_DIR = WEBAPP_DIR / "content"
FIGURE_DIR = WEBAPP_DIR / "static" / "figures"

# Notebook stem -> (url slug, assessment file with the conceptual-error quiz).
# 05 has a rubric and a proposal template rather than a quiz, hence the None.
MODULES: list[tuple[str, str, str | None]] = [
    ("00_embedding_refresher", "00-refresher", "00_refresher_diagnostic.md"),
    ("00b_representation_inspection", "00b-representation", "00b_representation_quiz.md"),
    ("01_alphaearth_access_visualize", "01-access", "01_access_visualize_quiz.md"),
    ("02_similarity_and_classification", "02-similarity", "02_similarity_classification_quiz.md"),
    ("03_change_detection_and_validation", "03-change", "03_change_detection_quiz.md"),
    ("04_embedding_ecosystems", "04-ecosystems", "04_ecosystems_quiz.md"),
    ("05_capstone_artificialization", "05-capstone", None),
]

# `setup` is the Colab pip bootstrap -- meaningless in a browser that never runs Python.
SKIP_TAGS = {"setup"}

# The bootstrap cell defines IN_COLAB; the cells that branch on it are environment
# plumbing for a runtime the reader does not have. Dropping them keeps the reading
# path about embeddings rather than about pip.
COLAB_PLUMBING = re.compile(r"\bIN_COLAB\b")

SOLUTION_OPEN = "### BEGIN SOLUTION"
SOLUTION_CLOSE = "### END SOLUTION"

# `name = expression` on one line, which is what every solution span in this course is
# made of. Anything else (a `for`, a multi-line call) stays visible as given context.
ASSIGNMENT = re.compile(r"^(\s*)([A-Za-z_][\w.\[\]\"']*)\s*=\s*(?!=)(.+?)\s*$")

md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")


def render(text: str) -> str:
    return md.render(text.strip())


def cell_source(cell: dict) -> str:
    source = cell["source"]
    return source if isinstance(source, str) else "".join(source)


@dataclass
class FigureWriter:
    """Writes notebook PNG payloads to disk and hands back web paths."""

    slug: str
    counter: int = 0

    def write(self, payload: str) -> str:
        self.counter += 1
        target = FIGURE_DIR / self.slug
        target.mkdir(parents=True, exist_ok=True)
        name = f"fig-{self.counter:02d}.png"
        (target / name).write_bytes(base64.b64decode(payload))
        return f"/static/figures/{self.slug}/{name}"


def collect_output(cell: dict, figures: FigureWriter) -> dict | None:
    """Flatten a cell's outputs into one text blob plus any figures."""
    text_parts: list[str] = []
    images: list[str] = []
    for output in cell.get("outputs", []):
        kind = output.get("output_type")
        if kind == "stream":
            text_parts.append("".join(output.get("text", [])))
        elif kind in {"display_data", "execute_result"}:
            data = output.get("data", {})
            if "image/png" in data:
                payload = data["image/png"]
                images.append(figures.write(payload if isinstance(payload, str) else "".join(payload)))
            elif "text/plain" in data:
                text_parts.append("".join(data["text/plain"]))
        elif kind == "error":
            text_parts.append("\n".join(output.get("traceback", [])))
    text = "".join(text_parts).rstrip()
    if not text and not images:
        return None
    return {"type": "output", "text": text, "images": images}


def split_solution(source: str) -> tuple[str, list[str], str] | None:
    """Return (code before, solution lines, code after) for a marked cell."""
    if SOLUTION_OPEN not in source or SOLUTION_CLOSE not in source:
        return None
    head, rest = source.split(SOLUTION_OPEN, 1)
    body, tail = rest.split(SOLUTION_CLOSE, 1)
    return head.rstrip("\n"), body.strip("\n").split("\n"), tail.strip("\n")


def blank_lines(lines: list[str]) -> list[dict]:
    """Turn a solution span into per-line prompts.

    Assignments become a short input keyed on the right-hand side -- typing
    `to_matrix(gdf)` on a phone is tolerable, retyping a whole block is not.
    """
    out: list[dict] = []
    for line in lines:
        match = ASSIGNMENT.match(line)
        if match and line.strip() and not line.strip().startswith("#"):
            indent, target, expression = match.groups()
            out.append({"kind": "blank", "indent": indent, "lhs": target, "answer": expression})
        else:
            out.append({"kind": "given", "text": line})
    return out


def parse_quiz(path: Path) -> list[dict]:
    """Parse the `#### Qn.` / `- A.` / italic-explanation assessment format."""
    lines = path.read_text(encoding="utf-8").splitlines()
    heading = re.compile(r"^#### (Q\d+)\.\s*(.*)$")
    # Two hand-written variants live in assessments/: "- A. text" with an italic
    # *Correct - ...* verdict, and "- A) text" with a bold **Correct.** one.
    option = re.compile(r"^- ([A-Z])[.)]\s*(.*)$")

    questions: list[dict] = []
    current: dict | None = None
    current_option: dict | None = None
    mode = "idle"

    def close_option() -> None:
        nonlocal current_option
        if current_option is not None:
            finish_option(current_option)
            current_option = None

    def finish_option(opt: dict) -> None:
        text = "\n".join(opt.pop("_lines")).strip()
        explanation = ""
        # The verdict is the trailing italic paragraph: *Correct — ...* / *Incorrect — ...*
        verdict = re.search(r"^\s*\*{1,2}(Correct|Incorrect)\b(.*)$", text, re.MULTILINE | re.DOTALL)
        if verdict:
            explanation = verdict.group(0).strip().strip("*").strip()
            opt["correct"] = verdict.group(1) == "Correct"
            text = text[: verdict.start()].strip()
        else:
            opt["correct"] = False
        opt["text"] = text
        opt["explanation_html"] = render(explanation) if explanation else ""

    for raw in lines:
        head = heading.match(raw)
        if head:
            close_option()
            current = {"id": head.group(1), "prompt_lines": [head.group(2)], "options": []}
            questions.append(current)
            mode = "prompt"
            continue
        if current is None:
            continue
        opt = option.match(raw)
        if opt:
            close_option()
            current_option = {"label": opt.group(1), "_lines": [opt.group(2)]}
            current["options"].append(current_option)
            mode = "option"
            continue
        if raw.strip() == "---":
            close_option()
            current = None
            mode = "idle"
            continue
        if mode == "prompt" and raw.strip():
            current["prompt_lines"].append(raw.strip())
        elif mode == "option" and current_option is not None:
            current_option["_lines"].append(raw.strip())
    close_option()

    out = []
    for question in questions:
        if not question["options"]:
            continue
        out.append(
            {
                "id": question["id"],
                "prompt_html": render(" ".join(question.pop("prompt_lines")).strip()),
                "options": question["options"],
            }
        )
    return out


def load_cells(stem: str) -> list[tuple[dict, dict]]:
    """Pair authored cells with their executed counterparts.

    `nbstripout` strips the `### BEGIN/END SOLUTION` markers out of the executed
    copies, so the fill-in-the-blank spans only survive in the authored notebook --
    but only the executed copy carries outputs. nbformat 4.5 cell ids let us zip the
    two without guessing.
    """
    authored_path = NOTEBOOK_DIR / f"{stem}.ipynb"
    executed_path = NOTEBOOK_DIR / f"executed_{stem}.ipynb"
    for path in (authored_path, executed_path):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing -- run `make execute-notebooks` before building the web bundle"
            )
    authored = json.loads(authored_path.read_text(encoding="utf-8"))["cells"]
    executed = json.loads(executed_path.read_text(encoding="utf-8"))["cells"]
    authored_ids = [c.get("id") for c in authored]
    if authored_ids != [c.get("id") for c in executed]:
        raise ValueError(
            f"{stem}: authored and executed notebooks have diverged -- re-run "
            "`make execute-notebooks` so cell ids line up again"
        )
    return list(zip(authored, executed))


def build_module(stem: str, slug: str, quiz_file: str | None) -> dict:
    figures = FigureWriter(slug)
    shutil.rmtree(FIGURE_DIR / slug, ignore_errors=True)

    blocks: list[dict] = []
    title = slug
    cells = load_cells(stem)
    index = 0
    seen_title = False

    while index < len(cells):
        cell, executed = cells[index]
        index += 1
        tags = set(cell["metadata"].get("tags", []))
        source = cell_source(cell)

        if cell["cell_type"] == "markdown":
            stripped = source.strip()
            if not seen_title and stripped.startswith("# "):
                title = stripped.splitlines()[0][2:].strip()
                seen_title = True
                continue
            if stripped:
                blocks.append({"type": "prose", "html": render(stripped)})
            continue

        if cell["cell_type"] != "code" or tags & SKIP_TAGS or not source.strip():
            continue

        if COLAB_PLUMBING.search(source):
            continue

        if "wrong-conclusion" in tags:
            trap = {"type": "trap", "code": source.rstrip(), "why_html": ""}
            output = collect_output(executed, figures)
            trap["output"] = output or {"type": "output", "text": "", "images": []}
            # The "### Why this is wrong" markdown immediately follows the trap cell
            # and is the whole point of it; fold it in rather than letting a student
            # scroll past the trap without the correction.
            if index < len(cells) and cells[index][0]["cell_type"] == "markdown":
                trap["why_html"] = render(cell_source(cells[index][0]))
                index += 1
            blocks.append(trap)
            continue

        split = split_solution(source)
        if split is not None:
            head, solution, tail = split
            blocks.append(
                {
                    "type": "blank",
                    "before": head,
                    "lines": blank_lines(solution),
                    "after": tail,
                }
            )
        else:
            blocks.append(
                {
                    "type": "code",
                    "code": source.rstrip(),
                    "editable": "parameters" in tags,
                    "executed": "skip-execution" not in tags,
                }
            )

        output = collect_output(executed, figures)
        if output:
            blocks.append(output)

    quiz = parse_quiz(ASSESSMENT_DIR / quiz_file) if quiz_file else []
    return {
        "slug": slug,
        "stem": stem,
        "title": title,
        "blocks": blocks,
        "quiz": quiz,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append", help="Build a single slug (repeatable).")
    args = parser.parse_args(argv)

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    selected = [m for m in MODULES if not args.only or m[1] in args.only]
    if not selected:
        parser.error(f"no module matches {args.only!r}")

    index = []
    for stem, slug, quiz_file in selected:
        module = build_module(stem, slug, quiz_file)
        (CONTENT_DIR / f"{slug}.json").write_text(
            json.dumps(module, indent=1, ensure_ascii=False), encoding="utf-8"
        )
        counts: dict[str, int] = {}
        for block in module["blocks"]:
            counts[block["type"]] = counts.get(block["type"], 0) + 1
        index.append(
            {
                "slug": slug,
                "title": module["title"],
                "blocks": len(module["blocks"]),
                "blanks": counts.get("blank", 0),
                "quiz": len(module["quiz"]),
            }
        )
        print(f"{slug:18s} {module['title'][:44]:46s} {counts} quiz={len(module['quiz'])}")

    (CONTENT_DIR / "index.json").write_text(
        json.dumps({"modules": index}, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

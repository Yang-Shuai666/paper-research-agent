import json
from dataclasses import dataclass
from pathlib import Path

from app.config import PROJECT_ROOT

DEFAULT_DATASET = PROJECT_ROOT / "data" / "eval" / "qa.jsonl"


@dataclass(frozen=True)
class Evidence:
    file: str
    pages: tuple[int, ...]


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    type: str
    lang: str
    question: str
    question_en: str | None
    reference_answer: str
    evidence: tuple[Evidence, ...]
    answerable: bool


def load_questions(path: str | Path | None = None) -> list[EvalQuestion]:
    dataset_path = Path(path) if path else DEFAULT_DATASET
    questions: list[EvalQuestion] = []
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        questions.append(
            EvalQuestion(
                id=item["id"],
                type=item["type"],
                lang=item.get("lang", "zh"),
                question=item["question"],
                question_en=item.get("question_en"),
                reference_answer=item["reference_answer"],
                evidence=tuple(
                    Evidence(file=evidence["file"], pages=tuple(evidence["pages"]))
                    for evidence in item.get("evidence", [])
                ),
                answerable=item.get("answerable", True),
            )
        )
    return questions

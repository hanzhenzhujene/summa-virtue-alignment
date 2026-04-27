from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from summa_moral_graph.sft.config import DatasetBuildConfig

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mini_sft_fixture.jsonl"


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def load_fixture_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def materialize_sft_fixture(tmp_path: Path) -> dict[str, Path]:
    rows = load_fixture_rows()
    interim_dir = tmp_path / "data" / "interim"
    gold_dir = tmp_path / "data" / "gold"
    interim_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    questions: list[dict[str, Any]] = []
    articles: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    annotations_by_tract: dict[str, list[dict[str, Any]]] = {}

    for row in rows:
        kind = row["kind"]
        payload = {key: value for key, value in row.items() if key != "kind"}
        if kind == "question":
            payload["source_id"] = "fixture"
            payload["hash"] = _stable_hash(payload)
            questions.append(payload)
        elif kind == "article":
            payload["source_id"] = "fixture"
            payload["hash"] = _stable_hash(payload)
            articles.append(payload)
        elif kind == "segment":
            payload["source_id"] = "fixture"
            payload["char_count"] = len(payload["text"])
            payload["hash"] = _stable_hash(payload["text"])
            segments.append(payload)
        elif kind == "annotation":
            tract = str(payload.pop("tract"))
            annotations_by_tract.setdefault(tract, []).append(payload)
        else:
            raise ValueError(f"Unknown fixture kind: {kind}")

    _write_jsonl(interim_dir / "summa_moral_questions.jsonl", questions)
    _write_jsonl(interim_dir / "summa_moral_articles.jsonl", articles)
    _write_jsonl(interim_dir / "summa_moral_segments.jsonl", segments)
    for tract, tract_annotations in annotations_by_tract.items():
        _write_jsonl(
            gold_dir / f"{tract}_reviewed_doctrinal_annotations.jsonl",
            tract_annotations,
        )

    return {"interim_dir": interim_dir, "gold_dir": gold_dir}


def build_fixture_dataset_config(
    tmp_path: Path, *, ood_holdout_tracts: list[str] | None = None
) -> DatasetBuildConfig:
    paths = materialize_sft_fixture(tmp_path)
    payload = {
        "dataset_name": "mini_fixture_dataset",
        "description": "Mini Christian virtue SFT fixture dataset.",
        "system_prompt": (
            "Answer within the cited evidence and use Aquinas's doctrinal categories."
        ),
        "corpus": {
            "segments_path": str(paths["interim_dir"] / "summa_moral_segments.jsonl"),
            "questions_path": str(paths["interim_dir"] / "summa_moral_questions.jsonl"),
            "articles_path": str(paths["interim_dir"] / "summa_moral_articles.jsonl"),
        },
        "sources": [
            {
                "tract": "theological_virtues",
                "annotations_path": str(
                    paths["gold_dir"] / "theological_virtues_reviewed_doctrinal_annotations.jsonl"
                ),
            },
            {
                "tract": "prudence",
                "annotations_path": str(
                    paths["gold_dir"] / "prudence_reviewed_doctrinal_annotations.jsonl"
                ),
            },
            {
                "tract": "temperance_closure_161_170",
                "annotations_path": str(
                    paths["gold_dir"]
                    / "temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl"
                ),
            },
        ],
        "filters": {
            "allowed_review_statuses": ["approved"],
            "allowed_support_types": ["explicit_textual", "strong_textual_inference"],
            "required_edge_layer": "doctrinal",
        },
        "templates": {
            "passage_grounded_doctrinal_qa": {"enabled": True},
            "reviewed_relation_explanation": {"enabled": True},
            "virtue_concept_explanation": {
                "enabled": True,
                "max_supporting_passages": 2,
                "max_relations": 2,
                "excluded_relation_types": ["treated_in"],
            },
            "citation_grounded_moral_answer": {"enabled": True},
        },
        "splits": {
            "group_by": "question_id",
            "train_ratio": 0.6,
            "val_ratio": 0.2,
            "test_ratio": 0.2,
            "seed": 11,
            "stratify_by_tract": True,
            "min_eval_groups_per_tract": 0,
        },
        "ood_split": {
            "name": "ood_test",
            "held_out_tracts": ood_holdout_tracts or [],
        },
        "serialization": {
            "output_dir": str(tmp_path / "exports"),
            "sample_output_path": str(tmp_path / "sample.jsonl"),
            "sample_size": 4,
        },
    }
    return DatasetBuildConfig.model_validate(payload)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")

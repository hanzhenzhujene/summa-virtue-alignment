"""Typer CLI entrypoints for building and validating Summa Moral Graph artifacts."""

from __future__ import annotations

import json

import typer

from .annotations.connected_virtues_109_120 import (
    build_connected_virtues_109_120_annotation_artifacts,
)
from .annotations.connected_virtues_109_120_review import (
    build_connected_virtues_109_120_review_queue,
)
from .annotations.corpus import build_corpus_candidate_artifacts
from .annotations.corpus_review import build_corpus_review_artifacts
from .annotations.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_annotation_artifacts,
)
from .annotations.fortitude_closure_136_140_review import (
    build_fortitude_closure_136_140_review_queue,
)
from .annotations.fortitude_parts_129_135 import (
    build_fortitude_parts_129_135_annotation_artifacts,
)
from .annotations.fortitude_parts_129_135_review import (
    build_fortitude_parts_129_135_review_queue,
)
from .annotations.justice_core import build_justice_core_annotation_artifacts
from .annotations.justice_core_review import build_justice_core_review_queue
from .annotations.owed_relation_tract import build_owed_relation_tract_annotation_artifacts
from .annotations.owed_relation_tract_review import build_owed_relation_tract_review_queue
from .annotations.pilot import build_pilot_annotation_artifacts
from .annotations.pilot_review import build_pilot_review_artifacts
from .annotations.prudence import build_prudence_annotation_artifacts
from .annotations.religion_tract import build_religion_tract_annotation_artifacts
from .annotations.religion_tract_review import build_religion_tract_review_queue
from .annotations.review_queue import build_prudence_review_queue
from .annotations.temperance_141_160 import build_temperance_141_160_annotation_artifacts
from .annotations.temperance_141_160_review import build_temperance_141_160_review_queue
from .annotations.temperance_closure_161_170 import (
    build_temperance_closure_161_170_annotation_artifacts,
)
from .annotations.temperance_closure_161_170_review import (
    build_temperance_closure_161_170_review_queue,
)
from .annotations.theological_virtues import build_theological_virtues_annotation_artifacts
from .annotations.theological_virtues_review import build_theological_virtues_review_queue
from .graph.connected_virtues_109_120 import (
    build_connected_virtues_109_120_graph_artifacts,
)
from .graph.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_graph_artifacts,
)
from .graph.fortitude_parts_129_135 import build_fortitude_parts_129_135_graph_artifacts
from .graph.justice_core import build_justice_core_graph_artifacts
from .graph.owed_relation_tract import build_owed_relation_tract_graph_artifacts
from .graph.pilot import build_pilot_graph_artifacts
from .graph.prudence import build_prudence_graph_artifacts
from .graph.religion_tract import build_religion_tract_graph_artifacts
from .graph.temperance_141_160 import build_temperance_141_160_graph_artifacts
from .graph.temperance_closure_161_170 import (
    build_temperance_closure_161_170_graph_artifacts,
)
from .graph.theological_virtues import build_theological_virtues_graph_artifacts
from .ingest.corpus import build_corpus_structural_artifacts
from .ingest.pipeline import build_interim_artifacts
from .ingest.scope import build_scope_manifest
from .validation import (
    build_connected_virtues_109_120_reports,
    build_corpus_reports,
    build_fortitude_closure_136_140_reports,
    build_fortitude_parts_129_135_reports,
    build_justice_core_reports,
    build_owed_relation_tract_reports,
    build_pilot_validation_artifacts,
    build_prudence_reports,
    build_religion_tract_reports,
    build_temperance_141_160_reports,
    build_temperance_closure_161_170_reports,
    build_theological_virtues_reports,
    validate_interim_artifacts,
)

app = typer.Typer(add_completion=False, help="Build and validate Summa Moral Graph interim data.")


@app.command("build-interim")
def build_interim(refresh_cache: bool = typer.Option(False, help="Re-fetch source pages.")) -> None:
    """Build deterministic interim corpus artifacts."""
    summary = build_interim_artifacts(refresh_cache=refresh_cache)
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-interim")
def validate_interim() -> None:
    """Validate the interim corpus artifacts."""
    summary = validate_interim_artifacts()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("show-scope")
def show_scope(
    refresh_cache: bool = typer.Option(False, help="Re-fetch part index pages."),
) -> None:
    """Show the current in-scope question manifest."""
    manifest = build_scope_manifest(refresh_cache=refresh_cache)
    grouped: dict[str, list[int]] = {}
    for entry in manifest:
        grouped.setdefault(entry.part_id, []).append(entry.question_number)
    summary = {
        part_id: {
            "count": len(numbers),
            "first_question": min(numbers),
            "last_question": max(numbers),
        }
        for part_id, numbers in grouped.items()
    }
    typer.echo(
        json.dumps(
            {"summary": summary, "total_questions": len(manifest)},
            indent=2,
            sort_keys=True,
        )
    )


@app.command("build-prudence")
def build_prudence() -> None:
    """Build reviewed prudence tract annotations, graph exports, and reports."""

    summary = {
        "annotations": build_prudence_annotation_artifacts(),
        "graph": build_prudence_graph_artifacts(),
        "reports": build_prudence_reports(),
        "review_queue": build_prudence_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-prudence")
def validate_prudence() -> None:
    """Rebuild prudence validation and coverage reports."""

    summary = build_prudence_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-connected-virtues-109-120")
def build_connected_virtues_109_120() -> None:
    """Build the reviewed connected virtues block for II-II QQ. 109-120."""

    summary = {
        "annotations": build_connected_virtues_109_120_annotation_artifacts(),
        "graph": build_connected_virtues_109_120_graph_artifacts(),
        "reports": build_connected_virtues_109_120_reports(),
        "review_queue": build_connected_virtues_109_120_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-connected-virtues-109-120")
def validate_connected_virtues_109_120() -> None:
    """Rebuild connected virtues 109-120 coverage and validation reports."""

    summary = build_connected_virtues_109_120_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-fortitude-parts-129-135")
def build_fortitude_parts_129_135() -> None:
    """Build the reviewed fortitude-parts block for II-II QQ. 129-135."""

    summary = {
        "annotations": build_fortitude_parts_129_135_annotation_artifacts(),
        "graph": build_fortitude_parts_129_135_graph_artifacts(),
        "reports": build_fortitude_parts_129_135_reports(),
        "review_queue": build_fortitude_parts_129_135_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-fortitude-parts-129-135")
def validate_fortitude_parts_129_135() -> None:
    """Rebuild fortitude-parts 129-135 coverage and validation reports."""

    summary = build_fortitude_parts_129_135_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-fortitude-closure-136-140")
def build_fortitude_closure_136_140() -> None:
    """Build the reviewed fortitude-closure block for II-II QQ. 136-140."""

    summary = {
        "annotations": build_fortitude_closure_136_140_annotation_artifacts(),
        "graph": build_fortitude_closure_136_140_graph_artifacts(),
        "reports": build_fortitude_closure_136_140_reports(),
        "review_queue": build_fortitude_closure_136_140_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-fortitude-closure-136-140")
def validate_fortitude_closure_136_140() -> None:
    """Rebuild fortitude-closure 136-140 coverage and validation reports."""

    summary = build_fortitude_closure_136_140_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-temperance-141-160")
def build_temperance_141_160() -> None:
    """Build the reviewed temperance tract block for II-II QQ. 141-160."""

    summary = {
        "annotations": build_temperance_141_160_annotation_artifacts(),
        "graph": build_temperance_141_160_graph_artifacts(),
        "reports": build_temperance_141_160_reports(),
        "review_queue": build_temperance_141_160_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-temperance-141-160")
def validate_temperance_141_160() -> None:
    """Rebuild temperance 141-160 coverage and validation reports."""

    summary = build_temperance_141_160_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-temperance-closure-161-170")
def build_temperance_closure_161_170() -> None:
    """Build the reviewed temperance-closure block for II-II QQ. 161-170."""

    summary = {
        "annotations": build_temperance_closure_161_170_annotation_artifacts(),
        "graph": build_temperance_closure_161_170_graph_artifacts(),
        "reports": build_temperance_closure_161_170_reports(),
        "review_queue": build_temperance_closure_161_170_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-temperance-closure-161-170")
def validate_temperance_closure_161_170() -> None:
    """Rebuild temperance closure 161-170 coverage and validation reports."""

    summary = build_temperance_closure_161_170_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-theological-virtues")
def build_theological_virtues() -> None:
    """Build the reviewed theological virtues block for II-II QQ. 1-46."""

    summary = {
        "annotations": build_theological_virtues_annotation_artifacts(),
        "graph": build_theological_virtues_graph_artifacts(),
        "reports": build_theological_virtues_reports(),
        "review_queue": build_theological_virtues_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-justice-core")
def build_justice_core() -> None:
    """Build the reviewed justice core block for II-II QQ. 57-79."""

    summary = {
        "annotations": build_justice_core_annotation_artifacts(),
        "graph": build_justice_core_graph_artifacts(),
        "reports": build_justice_core_reports(),
        "review_queue": build_justice_core_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-religion-tract")
def build_religion_tract() -> None:
    """Build the reviewed religion tract block for II-II QQ. 80-100."""

    summary = {
        "annotations": build_religion_tract_annotation_artifacts(),
        "graph": build_religion_tract_graph_artifacts(),
        "reports": build_religion_tract_reports(),
        "review_queue": build_religion_tract_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-religion-tract")
def validate_religion_tract() -> None:
    """Rebuild religion tract coverage and validation reports."""

    summary = build_religion_tract_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-owed-relation-tract")
def build_owed_relation_tract() -> None:
    """Build the reviewed owed-relation tract block for II-II QQ. 101-108."""

    summary = {
        "annotations": build_owed_relation_tract_annotation_artifacts(),
        "graph": build_owed_relation_tract_graph_artifacts(),
        "reports": build_owed_relation_tract_reports(),
        "review_queue": build_owed_relation_tract_review_queue(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-owed-relation-tract")
def validate_owed_relation_tract() -> None:
    """Rebuild owed-relation tract coverage and validation reports."""

    summary = build_owed_relation_tract_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-justice-core")
def validate_justice_core() -> None:
    """Rebuild justice core coverage and validation reports."""

    summary = build_justice_core_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-theological-virtues")
def validate_theological_virtues() -> None:
    """Rebuild theological virtues coverage and validation reports."""

    summary = build_theological_virtues_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-pilot")
def build_pilot() -> None:
    """Build the pilot ontology, reviewed annotations, graph exports, and reports."""

    summary = {
        "annotations": build_pilot_annotation_artifacts(),
        "graph": build_pilot_graph_artifacts(),
        "validation": build_pilot_validation_artifacts(),
        "review": build_pilot_review_artifacts(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-pilot")
def validate_pilot() -> None:
    """Rebuild the pilot validation report."""

    summary = build_pilot_validation_artifacts()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("build-corpus")
def build_corpus(
    refresh_cache: bool = typer.Option(False, help="Re-fetch source pages for diagnostics."),
) -> None:
    """Build full-corpus structural manifests, candidates, reports, and review queues."""

    summary = {
        "structural": build_corpus_structural_artifacts(refresh_cache=refresh_cache),
        "candidates": build_corpus_candidate_artifacts(),
        "reports": build_corpus_reports(),
        "review_queue": build_corpus_review_artifacts(),
    }
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@app.command("validate-candidates")
def validate_candidates() -> None:
    """Rebuild corpus coverage and candidate validation reports."""

    summary = build_corpus_reports()
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


def main() -> None:
    app()

from __future__ import annotations

import json

import typer

from .ingest.pipeline import build_interim_artifacts
from .ingest.scope import build_scope_manifest
from .validation import validate_interim_artifacts

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


def main() -> None:
    app()

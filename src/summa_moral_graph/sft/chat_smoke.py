"""Lightweight qualitative smoke tests for Christian virtue chat behavior."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..utils.paths import REPO_ROOT
from .chat import (
    DEFAULT_CHAT_SYSTEM_PROMPT,
    ChatModelBundle,
    generate_chat_reply,
    generate_deterministic_chat_reply,
    load_chat_model_bundle,
)
from .config import InferenceConfig
from .run_layout import (
    build_environment_snapshot,
    create_timestamped_run_dir,
    dataset_manifest_path,
    iso_timestamp,
    write_config_snapshot,
    write_json,
    write_jsonl,
)

DEFAULT_CHAT_SMOKE_OUTPUT_ROOT = (
    REPO_ROOT / "runs" / "christian_virtue" / "qwen2_5_1_5b_instruct" / "full_corpus_chat_smoke"
)
DEFAULT_CHAT_SMOKE_FORBIDDEN_SUBSTRINGS = (
    "according to the reviewed passage",
    "according to the cited passage",
    "aquinas explicitly",
    "the passage states this directly",
    "the reviewed claim is framed as",
    "support type",
    "review layer",
)


@dataclass(frozen=True)
class ChatSmokeCase:
    case_id: str
    category: str
    prompt: str
    required_substrings: tuple[str, ...]
    required_citations: tuple[str, ...] = ()
    forbidden_substrings: tuple[str, ...] = DEFAULT_CHAT_SMOKE_FORBIDDEN_SUBSTRINGS


@dataclass(frozen=True)
class ChatSmokeCaseResult:
    case_id: str
    category: str
    prompt: str
    reply: str
    passed: bool
    missing_required_substrings: tuple[str, ...]
    missing_required_citations: tuple[str, ...]
    forbidden_hits: tuple[str, ...]
    used_model: bool


DEFAULT_CHAT_SMOKE_CASES: tuple[ChatSmokeCase, ...] = (
    ChatSmokeCase(
        case_id="prudence_definition",
        category="definition",
        prompt="What is prudence according to Aquinas?",
        required_substrings=("right reason applied to action", "practical reason"),
        required_citations=("st.ii-ii.q047.a008.resp",),
    ),
    ChatSmokeCase(
        case_id="justice_mercy_difference",
        category="comparison",
        prompt="How does justice differ from mercy?",
        required_substrings=("what is due", "responds to another's distress"),
        required_citations=("st.ii-ii.q058.a001.resp", "st.ii-ii.q030.a001.resp"),
    ),
    ChatSmokeCase(
        case_id="prudence_why",
        category="why",
        prompt="Why is prudence necessary for the moral life?",
        required_substrings=("necessary for the moral life", "right reason applied to action"),
        required_citations=("st.ii-ii.q047.a008.resp",),
    ),
    ChatSmokeCase(
        case_id="abstinence_classification",
        category="relation",
        prompt="How does Aquinas classify abstinence within temperance?",
        required_substrings=("subjective part of temperance",),
        required_citations=("st.ii-ii.q143.a001.resp",),
    ),
    ChatSmokeCase(
        case_id="sloth_opposition",
        category="relation",
        prompt="What virtue opposes sloth?",
        required_substrings=("charity is opposed to sloth",),
        required_citations=("st.ii-ii.q035.a003.resp",),
    ),
    ChatSmokeCase(
        case_id="justice_location",
        category="relation",
        prompt="Where does justice reside?",
        required_substrings=("justice resides in will",),
        required_citations=("st.ii-ii.q058.a004.resp",),
    ),
    ChatSmokeCase(
        case_id="anger_practical",
        category="practical",
        prompt="I struggle with anger. How should I respond according to Aquinas?",
        required_substrings=("bring it under right reason", "meekness checks"),
        required_citations=("st.ii-ii.q158.a001.resp", "st.ii-ii.q157.a001.resp"),
    ),
    ChatSmokeCase(
        case_id="envy_practical",
        category="practical",
        prompt="I am jealous of other people's success. What should I do?",
        required_substrings=("that is envy", "reorder the heart by charity"),
        required_citations=("st.ii-ii.q036.a001.resp", "st.ii-ii.q028.a001.resp"),
    ),
    ChatSmokeCase(
        case_id="temperance_practical",
        category="practical",
        prompt="I am tempted to overindulge in pleasure. How should I practice temperance?",
        required_substrings=(
            "let reason set the measure of pleasure",
            "needs of life rightly require",
        ),
        required_citations=("st.ii-ii.q141.a001.resp", "st.ii-ii.q141.a006.resp"),
    ),
    ChatSmokeCase(
        case_id="fear_courage_practical",
        category="practical",
        prompt="How should I think about fear and courage in a hard situation?",
        required_substrings=("not say courage means feeling no fear", "right reason requires"),
        required_citations=("st.ii-ii.q123.a001.resp", "st.ii-ii.q123.a012.resp"),
    ),
)
DEFAULT_CHAT_EXAMPLE_PROMPTS = (
    "What is prudence according to Aquinas?",
    "How does justice differ from mercy?",
    "Where does justice reside?",
    "What virtue opposes sloth?",
    "I struggle with anger. How should I respond according to Aquinas?",
    "I am jealous of other people's success. What should I do?",
)


def update_latest_run_link(root_dir: Path, run_dir: Path) -> Path:
    latest_path = root_dir / "latest"
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    latest_path.symlink_to(run_dir.name)
    return latest_path


def evaluate_chat_smoke_case(
    case: ChatSmokeCase,
    reply: str,
    *,
    used_model: bool,
) -> ChatSmokeCaseResult:
    lowered = reply.lower()
    missing_required_substrings = tuple(
        substring
        for substring in case.required_substrings
        if substring.lower() not in lowered
    )
    missing_required_citations = tuple(
        citation
        for citation in case.required_citations
        if citation not in reply
    )
    forbidden_hits = tuple(
        substring
        for substring in case.forbidden_substrings
        if substring.lower() in lowered
    )
    return ChatSmokeCaseResult(
        case_id=case.case_id,
        category=case.category,
        prompt=case.prompt,
        reply=reply,
        passed=not missing_required_substrings
        and not missing_required_citations
        and not forbidden_hits,
        missing_required_substrings=missing_required_substrings,
        missing_required_citations=missing_required_citations,
        forbidden_hits=forbidden_hits,
        used_model=used_model,
    )


def render_chat_smoke_report(
    results: list[ChatSmokeCaseResult],
    *,
    config: InferenceConfig,
    run_dir: Path,
    include_model: bool,
) -> str:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    manifest_path = dataset_manifest_path(config.dataset_dir)
    lines = [
        "# Christian Virtue Chat Smoke Report",
        "",
        f"- Run id: `{run_dir.name}`",
        f"- Mode: `{'full-model' if include_model else 'deterministic-only'}`",
        f"- Base model: `{config.model_name_or_path}`",
        (
            "- Adapter: "
            f"`{config.adapter_path}`" if config.adapter_path is not None else "- Adapter: `None`"
        ),
        f"- Dataset: `{config.dataset_dir}`",
        (
            f"- Dataset manifest: `{manifest_path}`"
            if manifest_path is not None
            else "- Dataset manifest: `None`"
        ),
        f"- Result: `{passed}/{total}` cases passed",
        "",
        "## Cases",
        "",
        "| Case | Category | Result |",
        "| --- | --- | --- |",
    ]
    for result in results:
        outcome = "PASS" if result.passed else "FAIL"
        lines.append(f"| `{result.case_id}` | `{result.category}` | `{outcome}` |")
    lines.append("")

    for result in results:
        lines.extend(
            [
                f"## {result.case_id}",
                "",
                f"- Prompt: `{result.prompt}`",
                f"- Category: `{result.category}`",
                f"- Result: `{'PASS' if result.passed else 'FAIL'}`",
            ]
        )
        if result.missing_required_substrings:
            lines.append(
                "- Missing required substrings: "
                + ", ".join(f"`{item}`" for item in result.missing_required_substrings)
            )
        if result.missing_required_citations:
            lines.append(
                "- Missing required citations: "
                + ", ".join(f"`{item}`" for item in result.missing_required_citations)
            )
        if result.forbidden_hits:
            lines.append(
                "- Forbidden template phrases present: "
                + ", ".join(f"`{item}`" for item in result.forbidden_hits)
            )
        lines.extend(
            [
                "",
                "```text",
                result.reply.strip(),
                "```",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def run_chat_smoke_suite(
    *,
    config: InferenceConfig,
    output_root: Path = DEFAULT_CHAT_SMOKE_OUTPUT_ROOT,
    include_model: bool = False,
    cases: tuple[ChatSmokeCase, ...] = DEFAULT_CHAT_SMOKE_CASES,
) -> dict[str, Any]:
    start_time = iso_timestamp()
    run_dir = create_timestamped_run_dir(output_root)
    update_latest_run_link(output_root, run_dir)
    write_config_snapshot(
        run_dir,
        config_path=config.config_path,
        payload=config.model_dump(mode="json"),
    )

    bundle: ChatModelBundle | None = None
    if include_model:
        bundle = load_chat_model_bundle(config)
        resolved_device = getattr(bundle.runtime, "resolved_device", None)
    else:
        resolved_device = config.runtime_backend

    environment = build_environment_snapshot(
        workspace_root=REPO_ROOT,
        resolved_device=resolved_device,
        torch_dtype=config.torch_dtype,
    )
    write_json(run_dir / "environment.json", environment)
    command_parts = [
        "python",
        "scripts/smoke_test_christian_virtue_chat.py",
    ]
    if config.config_path is not None:
        command_parts.extend(["--config", str(config.config_path)])
    if include_model:
        command_parts.append("--with-model")
    (run_dir / "command.log").write_text(" ".join(command_parts) + "\n", encoding="utf-8")

    results: list[ChatSmokeCaseResult] = []
    for case in cases:
        if include_model and bundle is not None:
            reply = generate_chat_reply(
                bundle,
                config,
                messages=[
                    {"role": "system", "content": DEFAULT_CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": case.prompt},
                ],
            )
        else:
            reply = generate_deterministic_chat_reply(case.prompt) or ""
        results.append(evaluate_chat_smoke_case(case, reply, used_model=include_model))

    results_payload = [asdict(result) for result in results]
    write_jsonl(run_dir / "smoke_results.jsonl", results_payload)
    pass_count = sum(1 for result in results if result.passed)
    manifest_path = dataset_manifest_path(config.dataset_dir)
    summary = {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "case_count": len(results),
        "config_path": str(config.config_path) if config.config_path is not None else None,
        "dataset_dir": str(config.dataset_dir),
        "dataset_manifest_path": str(manifest_path) if manifest_path is not None else None,
        "end_time": iso_timestamp(),
        "git_commit": environment["git_commit"],
        "include_model": include_model,
        "model_name_or_path": config.model_name_or_path,
        "pass_count": pass_count,
        "pass_rate": round(pass_count / len(results), 4) if results else 0.0,
        "run_dir": str(run_dir),
        "run_id": run_dir.name,
        "start_time": start_time,
    }
    write_json(run_dir / "metrics.json", summary)
    report_path = run_dir / "report.md"
    report_path.write_text(
        render_chat_smoke_report(
            results,
            config=config,
            run_dir=run_dir,
            include_model=include_model,
        ),
        encoding="utf-8",
    )
    run_manifest = {
        **summary,
        "config_snapshot_path": str(run_dir / "config_snapshot.yaml"),
        "environment_path": str(run_dir / "environment.json"),
        "report_path": str(report_path),
        "results_path": str(run_dir / "smoke_results.jsonl"),
    }
    write_json(run_dir / "run_manifest.json", run_manifest)
    return {
        "latest_path": str(output_root / "latest"),
        "metrics": summary,
        "report_path": str(report_path),
        "results": results_payload,
        "run_dir": str(run_dir),
        "run_manifest_path": str(run_dir / "run_manifest.json"),
    }

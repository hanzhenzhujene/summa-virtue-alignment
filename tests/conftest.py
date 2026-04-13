from __future__ import annotations

import pytest

from summa_moral_graph.annotations.connected_virtues_109_120 import (
    build_connected_virtues_109_120_annotation_artifacts,
)
from summa_moral_graph.annotations.connected_virtues_109_120_review import (
    build_connected_virtues_109_120_review_queue,
)
from summa_moral_graph.annotations.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_annotation_artifacts,
)
from summa_moral_graph.annotations.fortitude_closure_136_140_review import (
    build_fortitude_closure_136_140_review_queue,
)
from summa_moral_graph.annotations.fortitude_parts_129_135 import (
    build_fortitude_parts_129_135_annotation_artifacts,
)
from summa_moral_graph.annotations.fortitude_parts_129_135_review import (
    build_fortitude_parts_129_135_review_queue,
)
from summa_moral_graph.annotations.justice_core import build_justice_core_annotation_artifacts
from summa_moral_graph.annotations.justice_core_review import build_justice_core_review_queue
from summa_moral_graph.annotations.owed_relation_tract import (
    build_owed_relation_tract_annotation_artifacts,
)
from summa_moral_graph.annotations.owed_relation_tract_review import (
    build_owed_relation_tract_review_queue,
)
from summa_moral_graph.annotations.pilot import build_pilot_annotation_artifacts
from summa_moral_graph.annotations.pilot_review import build_pilot_review_artifacts
from summa_moral_graph.annotations.prudence import build_prudence_annotation_artifacts
from summa_moral_graph.annotations.religion_tract import (
    build_religion_tract_annotation_artifacts,
)
from summa_moral_graph.annotations.religion_tract_review import (
    build_religion_tract_review_queue,
)
from summa_moral_graph.annotations.review_queue import build_prudence_review_queue
from summa_moral_graph.annotations.temperance_141_160 import (
    build_temperance_141_160_annotation_artifacts,
)
from summa_moral_graph.annotations.temperance_141_160_review import (
    build_temperance_141_160_review_queue,
)
from summa_moral_graph.annotations.temperance_closure_161_170 import (
    build_temperance_closure_161_170_annotation_artifacts,
)
from summa_moral_graph.annotations.temperance_closure_161_170_review import (
    build_temperance_closure_161_170_review_queue,
)
from summa_moral_graph.annotations.theological_virtues import (
    build_theological_virtues_annotation_artifacts,
)
from summa_moral_graph.annotations.theological_virtues_review import (
    build_theological_virtues_review_queue,
)
from summa_moral_graph.graph.connected_virtues_109_120 import (
    build_connected_virtues_109_120_graph_artifacts,
)
from summa_moral_graph.graph.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_graph_artifacts,
)
from summa_moral_graph.graph.fortitude_parts_129_135 import (
    build_fortitude_parts_129_135_graph_artifacts,
)
from summa_moral_graph.graph.justice_core import build_justice_core_graph_artifacts
from summa_moral_graph.graph.owed_relation_tract import (
    build_owed_relation_tract_graph_artifacts,
)
from summa_moral_graph.graph.pilot import build_pilot_graph_artifacts
from summa_moral_graph.graph.prudence import build_prudence_graph_artifacts
from summa_moral_graph.graph.religion_tract import build_religion_tract_graph_artifacts
from summa_moral_graph.graph.temperance_141_160 import (
    build_temperance_141_160_graph_artifacts,
)
from summa_moral_graph.graph.temperance_closure_161_170 import (
    build_temperance_closure_161_170_graph_artifacts,
)
from summa_moral_graph.graph.theological_virtues import (
    build_theological_virtues_graph_artifacts,
)
from summa_moral_graph.validation.connected_virtues_109_120 import (
    build_connected_virtues_109_120_reports,
)
from summa_moral_graph.validation.corpus import build_corpus_reports
from summa_moral_graph.validation.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_reports,
)
from summa_moral_graph.validation.fortitude_parts_129_135 import (
    build_fortitude_parts_129_135_reports,
)
from summa_moral_graph.validation.justice_core import build_justice_core_reports
from summa_moral_graph.validation.owed_relation_tract import (
    build_owed_relation_tract_reports,
)
from summa_moral_graph.validation.pilot import build_pilot_validation_artifacts
from summa_moral_graph.validation.prudence import build_prudence_reports
from summa_moral_graph.validation.religion_tract import build_religion_tract_reports
from summa_moral_graph.validation.temperance_141_160 import (
    build_temperance_141_160_reports,
)
from summa_moral_graph.validation.temperance_closure_161_170 import (
    build_temperance_closure_161_170_reports,
)
from summa_moral_graph.validation.theological_virtues import (
    build_theological_virtues_reports,
)


@pytest.fixture(scope="session")
def prudence_artifacts() -> dict[str, object]:
    annotation_summary = build_prudence_annotation_artifacts()
    graph_summary = build_prudence_graph_artifacts()
    report_summary = build_prudence_reports()
    queue_summary = build_prudence_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def pilot_artifacts() -> dict[str, object]:
    annotation_summary = build_pilot_annotation_artifacts()
    graph_summary = build_pilot_graph_artifacts()
    validation_summary = build_pilot_validation_artifacts()
    review_summary = build_pilot_review_artifacts()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "validation": validation_summary,
        "review": review_summary,
    }


@pytest.fixture(scope="session")
def theological_virtues_artifacts() -> dict[str, object]:
    build_corpus_reports()
    annotation_summary = build_theological_virtues_annotation_artifacts()
    graph_summary = build_theological_virtues_graph_artifacts()
    report_summary = build_theological_virtues_reports()
    queue_summary = build_theological_virtues_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def justice_core_artifacts() -> dict[str, object]:
    build_corpus_reports()
    annotation_summary = build_justice_core_annotation_artifacts()
    graph_summary = build_justice_core_graph_artifacts()
    report_summary = build_justice_core_reports()
    queue_summary = build_justice_core_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def religion_tract_artifacts() -> dict[str, object]:
    build_corpus_reports()
    annotation_summary = build_religion_tract_annotation_artifacts()
    graph_summary = build_religion_tract_graph_artifacts()
    report_summary = build_religion_tract_reports()
    queue_summary = build_religion_tract_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def owed_relation_tract_artifacts() -> dict[str, object]:
    build_corpus_reports()
    annotation_summary = build_owed_relation_tract_annotation_artifacts()
    graph_summary = build_owed_relation_tract_graph_artifacts()
    report_summary = build_owed_relation_tract_reports()
    queue_summary = build_owed_relation_tract_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def connected_virtues_109_120_artifacts() -> dict[str, object]:
    build_corpus_reports()
    annotation_summary = build_connected_virtues_109_120_annotation_artifacts()
    graph_summary = build_connected_virtues_109_120_graph_artifacts()
    report_summary = build_connected_virtues_109_120_reports()
    queue_summary = build_connected_virtues_109_120_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def fortitude_parts_129_135_artifacts() -> dict[str, object]:
    build_corpus_reports()
    annotation_summary = build_fortitude_parts_129_135_annotation_artifacts()
    graph_summary = build_fortitude_parts_129_135_graph_artifacts()
    report_summary = build_fortitude_parts_129_135_reports()
    queue_summary = build_fortitude_parts_129_135_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def fortitude_closure_136_140_artifacts(
    fortitude_parts_129_135_artifacts: dict[str, object],
) -> dict[str, object]:
    build_corpus_reports()
    _ = fortitude_parts_129_135_artifacts
    annotation_summary = build_fortitude_closure_136_140_annotation_artifacts()
    graph_summary = build_fortitude_closure_136_140_graph_artifacts()
    report_summary = build_fortitude_closure_136_140_reports()
    queue_summary = build_fortitude_closure_136_140_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def temperance_141_160_artifacts() -> dict[str, object]:
    build_corpus_reports()
    annotation_summary = build_temperance_141_160_annotation_artifacts()
    graph_summary = build_temperance_141_160_graph_artifacts()
    report_summary = build_temperance_141_160_reports()
    queue_summary = build_temperance_141_160_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }


@pytest.fixture(scope="session")
def temperance_closure_161_170_artifacts(
    temperance_141_160_artifacts: dict[str, object],
) -> dict[str, object]:
    build_corpus_reports()
    _ = temperance_141_160_artifacts
    annotation_summary = build_temperance_closure_161_170_annotation_artifacts()
    graph_summary = build_temperance_closure_161_170_graph_artifacts()
    report_summary = build_temperance_closure_161_170_reports()
    queue_summary = build_temperance_closure_161_170_review_queue()
    return {
        "annotations": annotation_summary,
        "graph": graph_summary,
        "reports": report_summary,
        "queue": queue_summary,
    }

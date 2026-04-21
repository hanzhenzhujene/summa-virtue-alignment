"""Shared tract preset registry for route-aware viewer and dashboard navigation."""

from __future__ import annotations

from typing import TypedDict

from .connected_virtues_109_120 import CONNECTED_VIRTUES_109_120_PRESETS
from .fortitude_closure_136_140 import FORTITUDE_CLOSURE_136_140_PRESETS
from .fortitude_parts_129_135 import FORTITUDE_PARTS_129_135_PRESETS
from .justice_core import JUSTICE_CORE_PRESETS
from .owed_relation_tract import OWED_RELATION_TRACT_PRESETS
from .religion_tract import RELIGION_TRACT_PRESETS
from .temperance_141_160 import TEMPERANCE_141_160_PRESETS
from .temperance_closure_161_170 import TEMPERANCE_CLOSURE_161_170_PRESETS
from .theological_virtues import THEOLOGICAL_VIRTUES_PRESETS


class TractPreset(TypedDict):
    family: str
    key: str
    label: str
    start_question: int
    end_question: int


TRACT_PRESETS: dict[str, TractPreset] = {
    **{
        f"connected:{key}": {
            "family": "connected",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in CONNECTED_VIRTUES_109_120_PRESETS.items()
    },
    **{
        f"fortitude_closure:{key}": {
            "family": "fortitude_closure",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in FORTITUDE_CLOSURE_136_140_PRESETS.items()
    },
    **{
        f"fortitude:{key}": {
            "family": "fortitude",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in FORTITUDE_PARTS_129_135_PRESETS.items()
    },
    **{
        f"theological:{key}": {
            "family": "theological",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in THEOLOGICAL_VIRTUES_PRESETS.items()
    },
    **{
        f"justice:{key}": {
            "family": "justice",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in JUSTICE_CORE_PRESETS.items()
    },
    **{
        f"owed:{key}": {
            "family": "owed",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in OWED_RELATION_TRACT_PRESETS.items()
    },
    **{
        f"religion:{key}": {
            "family": "religion",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in RELIGION_TRACT_PRESETS.items()
    },
    **{
        f"temperance:{key}": {
            "family": "temperance",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in TEMPERANCE_141_160_PRESETS.items()
    },
    **{
        f"temperance_closure:{key}": {
            "family": "temperance_closure",
            "key": key,
            "label": value["label"],
            "start_question": value["start_question"],
            "end_question": value["end_question"],
        }
        for key, value in TEMPERANCE_CLOSURE_161_170_PRESETS.items()
    },
}


def preset_label(preset_name: str) -> str:
    return TRACT_PRESETS[preset_name]["label"]


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = TRACT_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


def preset_family(preset_name: str) -> str:
    return TRACT_PRESETS[preset_name]["family"]

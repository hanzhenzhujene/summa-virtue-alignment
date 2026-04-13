from __future__ import annotations

from collections.abc import MutableMapping

from .load import ViewerAppData

HOME_VIEW = "Home"
CONCEPT_VIEW = "Concept Explorer"
PASSAGE_VIEW = "Passage Explorer"
MAP_VIEW = "Overall Map"
STATS_VIEW = "Stats / Audit"

PRIMARY_VIEWS = (
    HOME_VIEW,
    CONCEPT_VIEW,
    PASSAGE_VIEW,
    MAP_VIEW,
    STATS_VIEW,
)

ACTIVE_VIEW_KEY = "smg_active_view"
ACTIVE_PRESET_KEY = "smg_active_preset"
CONCEPT_ID_KEY = "smg_selected_concept"
PASSAGE_ID_KEY = "smg_selected_passage"
EDGE_ID_KEY = "smg_selected_edge"
MAP_RANGE_KEY = "smg_map_range"
MAP_MODE_KEY = "smg_map_mode"
STATS_TAB_KEY = "smg_stats_tab"
ENTRYPOINT_KEY = "smg_entrypoint"

DEFAULT_STATE: dict[str, object] = {
    ACTIVE_VIEW_KEY: HOME_VIEW,
    ACTIVE_PRESET_KEY: "",
    CONCEPT_ID_KEY: "",
    PASSAGE_ID_KEY: "",
    EDGE_ID_KEY: "",
    MAP_RANGE_KEY: (1, 46),
    MAP_MODE_KEY: "Overall map",
    STATS_TAB_KEY: "Reader stats",
    "smg_concept_query": "",
    "smg_concept_node_types": [],
    "smg_concept_show_editorial_map": False,
    "smg_passage_query": "",
    "smg_passage_part": "",
    "smg_passage_question": "",
    "smg_passage_article": "",
    "smg_passage_segment_type": "",
    "smg_passage_limit": 18,
    "smg_home_start_concept": "",
    "smg_home_start_passage": "",
    "smg_home_start_preset": "",
    "smg_map_include_structural": False,
    "smg_map_include_editorial": False,
    "smg_map_include_candidate": False,
    "smg_map_relation_groups": [],
    "smg_map_relation_types": [],
    "smg_map_node_types": [],
    "smg_map_focus_tags": [],
    "smg_map_segment_types": [],
    "smg_map_question_spotlight": "",
    "smg_map_center_concept": "",
    "smg_stats_coverage_part": "",
    "smg_stats_coverage_status": ["parsed", "partial"],
    "smg_stats_coverage_query": "",
    "smg_stats_coverage_question": "",
    ENTRYPOINT_KEY: "",
}


def ensure_session_state(
    session_state: MutableMapping[str, object],
    data: ViewerAppData,
    *,
    default_view: str | None = None,
    default_stats_tab: str | None = None,
    entrypoint_id: str | None = None,
) -> None:
    for key, default in DEFAULT_STATE.items():
        if key not in session_state:
            session_state[key] = list(default) if isinstance(default, list) else default

    entrypoint_changed = (
        entrypoint_id is not None
        and str(session_state.get(ENTRYPOINT_KEY, "") or "") != entrypoint_id
    )

    if default_view in PRIMARY_VIEWS and entrypoint_changed:
        session_state[ACTIVE_VIEW_KEY] = default_view
    elif session_state.get(ACTIVE_VIEW_KEY) not in PRIMARY_VIEWS:
        session_state[ACTIVE_VIEW_KEY] = HOME_VIEW

    if default_stats_tab and entrypoint_changed:
        session_state[STATS_TAB_KEY] = default_stats_tab

    if entrypoint_id is not None:
        session_state[ENTRYPOINT_KEY] = entrypoint_id

    if session_state.get(CONCEPT_ID_KEY) not in data.bundle.registry:
        session_state[CONCEPT_ID_KEY] = (
            data.home_start_concepts[0]
            if data.home_start_concepts
            else next(iter(data.bundle.registry))
        )
    if session_state.get(PASSAGE_ID_KEY) not in data.bundle.passages:
        session_state[PASSAGE_ID_KEY] = (
            data.home_start_passages[0]
            if data.home_start_passages
            else next(iter(data.bundle.passages))
        )
    if session_state.get("smg_home_start_concept") not in data.bundle.registry:
        session_state["smg_home_start_concept"] = session_state[CONCEPT_ID_KEY]
    if session_state.get("smg_home_start_passage") not in data.bundle.passages:
        session_state["smg_home_start_passage"] = session_state[PASSAGE_ID_KEY]


def set_active_view(session_state: MutableMapping[str, object], view_name: str) -> None:
    if view_name in PRIMARY_VIEWS:
        session_state[ACTIVE_VIEW_KEY] = view_name


def open_concept(
    session_state: MutableMapping[str, object],
    concept_id: str,
    *,
    preset_name: str | None = None,
) -> None:
    session_state[CONCEPT_ID_KEY] = concept_id
    session_state["smg_map_center_concept"] = concept_id
    if preset_name is not None:
        session_state[ACTIVE_PRESET_KEY] = preset_name
    session_state[ACTIVE_VIEW_KEY] = CONCEPT_VIEW


def open_passage(
    session_state: MutableMapping[str, object],
    passage_id: str,
    *,
    preset_name: str | None = None,
) -> None:
    session_state[PASSAGE_ID_KEY] = passage_id
    if preset_name is not None:
        session_state[ACTIVE_PRESET_KEY] = preset_name
    session_state[ACTIVE_VIEW_KEY] = PASSAGE_VIEW


def open_map(
    session_state: MutableMapping[str, object],
    *,
    concept_id: str | None = None,
    edge_id: str | None = None,
    preset_name: str | None = None,
    mode: str | None = None,
) -> None:
    if concept_id is not None:
        session_state[CONCEPT_ID_KEY] = concept_id
        session_state["smg_map_center_concept"] = concept_id
    if edge_id is not None:
        session_state[EDGE_ID_KEY] = edge_id
    if preset_name is not None:
        session_state[ACTIVE_PRESET_KEY] = preset_name
    if mode is not None:
        session_state[MAP_MODE_KEY] = mode
    session_state[ACTIVE_VIEW_KEY] = MAP_VIEW


def open_stats(
    session_state: MutableMapping[str, object],
    *,
    tab_name: str | None = None,
) -> None:
    if tab_name is not None:
        session_state[STATS_TAB_KEY] = tab_name
    session_state[ACTIVE_VIEW_KEY] = STATS_VIEW

from __future__ import annotations

from collections.abc import MutableMapping

from ..utils.segments import USABLE_SEGMENT_TYPES
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
MAP_SELECTED_NODE_KEY = "smg_map_selected_node"
MAP_PENDING_ACTION_KEY = "smg_pending_map_action"
PENDING_WIDGET_UPDATES_KEY = "smg_pending_widget_updates"
STATS_TAB_KEY = "smg_stats_tab"
ENTRYPOINT_KEY = "smg_entrypoint"
DEFAULT_MAP_RANGE = (1, 46)

DEFAULT_STATE: dict[str, object] = {
    ACTIVE_VIEW_KEY: HOME_VIEW,
    ACTIVE_PRESET_KEY: "",
    CONCEPT_ID_KEY: "",
    PASSAGE_ID_KEY: "",
    EDGE_ID_KEY: "",
    MAP_RANGE_KEY: DEFAULT_MAP_RANGE,
    MAP_MODE_KEY: "Overall map",
    MAP_SELECTED_NODE_KEY: "",
    MAP_PENDING_ACTION_KEY: "",
    PENDING_WIDGET_UPDATES_KEY: {},
    STATS_TAB_KEY: "Reader stats",
    "smg_concept_query": "",
    "smg_concept_node_types": [],
    "smg_concept_show_editorial_map": False,
    "smg_concept_show_relation_labels": True,
    "smg_passage_query": "",
    "smg_passage_part": "",
    "smg_passage_question": "",
    "smg_passage_article": "",
    "smg_passage_segment_type": "",
    "smg_passage_page_size": 4,
    "smg_passage_page": 1,
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
    "smg_map_show_filters": False,
    "smg_map_show_relation_labels": True,
    "smg_stats_coverage_part": "",
    "smg_stats_coverage_status": ["parsed", "partial"],
    "smg_stats_coverage_query": "",
    "smg_stats_coverage_question": "",
    ENTRYPOINT_KEY: "",
}

MAP_FILTER_DEFAULTS: dict[str, object] = {
    MAP_RANGE_KEY: DEFAULT_MAP_RANGE,
    "smg_map_include_structural": False,
    "smg_map_include_editorial": False,
    "smg_map_include_candidate": False,
    "smg_map_relation_groups": [],
    "smg_map_relation_types": [],
    "smg_map_node_types": [],
    "smg_map_focus_tags": [],
    "smg_map_segment_types": [],
    "smg_map_question_spotlight": "",
}


def normalize_map_range(value: object) -> tuple[int, int]:
    if isinstance(value, int):
        start = end = value
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            start = int(value[0])
            end = int(value[1])
        except (TypeError, ValueError):
            return DEFAULT_MAP_RANGE
    else:
        return DEFAULT_MAP_RANGE

    start = max(1, min(182, start))
    end = max(1, min(182, end))
    if start > end:
        start, end = end, start
    return (start, end)


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
            if isinstance(default, list):
                session_state[key] = list(default)
            elif isinstance(default, dict):
                session_state[key] = dict(default)
            else:
                session_state[key] = default

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

    session_state[MAP_RANGE_KEY] = normalize_map_range(
        session_state.get(MAP_RANGE_KEY, DEFAULT_MAP_RANGE)
    )
    allowed_segment_types = {"", *USABLE_SEGMENT_TYPES}
    current_passage_segment_type = str(session_state.get("smg_passage_segment_type", "") or "")
    if current_passage_segment_type not in allowed_segment_types:
        session_state["smg_passage_segment_type"] = ""
    current_map_segment_types = session_state.get("smg_map_segment_types", [])
    if not isinstance(current_map_segment_types, list):
        session_state["smg_map_segment_types"] = []
    else:
        session_state["smg_map_segment_types"] = [
            value for value in current_map_segment_types if value in USABLE_SEGMENT_TYPES
        ]

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


def queue_widget_updates(
    session_state: MutableMapping[str, object],
    **updates: object,
) -> None:
    raw_pending = session_state.get(PENDING_WIDGET_UPDATES_KEY, {})
    pending = (
        {str(key): value for key, value in raw_pending.items()}
        if isinstance(raw_pending, dict)
        else {}
    )
    pending.update(updates)
    session_state[PENDING_WIDGET_UPDATES_KEY] = pending


def consume_widget_updates(session_state: MutableMapping[str, object]) -> None:
    pending = session_state.get(PENDING_WIDGET_UPDATES_KEY, {})
    if not isinstance(pending, dict):
        session_state[PENDING_WIDGET_UPDATES_KEY] = {}
        return
    for key, value in pending.items():
        session_state[key] = value
    session_state[PENDING_WIDGET_UPDATES_KEY] = {}


def reset_map_filters(
    session_state: MutableMapping[str, object],
    *,
    preserve_center: bool = True,
    preserve_mode: bool = True,
) -> None:
    center = session_state.get("smg_map_center_concept", "")
    mode = session_state.get(MAP_MODE_KEY, "Overall map")
    for key, default in MAP_FILTER_DEFAULTS.items():
        session_state[key] = list(default) if isinstance(default, list) else default
    if preserve_center:
        session_state["smg_map_center_concept"] = center
    if preserve_mode:
        session_state[MAP_MODE_KEY] = mode


def queue_map_action(session_state: MutableMapping[str, object], action: str) -> None:
    if action in {"clear_focus_tags", "reset_filters"}:
        session_state[MAP_PENDING_ACTION_KEY] = action


def consume_pending_map_action(session_state: MutableMapping[str, object]) -> str | None:
    action = str(session_state.pop(MAP_PENDING_ACTION_KEY, "") or "")
    if not action:
        return None
    if action == "clear_focus_tags":
        session_state["smg_map_focus_tags"] = []
    elif action == "reset_filters":
        reset_map_filters(session_state)
    return action


def select_map_node(session_state: MutableMapping[str, object], node_id: str) -> None:
    session_state[MAP_SELECTED_NODE_KEY] = node_id
    session_state[ACTIVE_VIEW_KEY] = MAP_VIEW


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
    session_state["smg_pending_concept_selectbox"] = concept_id
    if PENDING_WIDGET_UPDATES_KEY in session_state:
        queue_widget_updates(session_state, smg_map_center_concept=concept_id)
    else:
        session_state["smg_map_center_concept"] = concept_id
    if preset_name is not None:
        if PENDING_WIDGET_UPDATES_KEY in session_state:
            queue_widget_updates(session_state, **{ACTIVE_PRESET_KEY: preset_name})
        else:
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
        if PENDING_WIDGET_UPDATES_KEY in session_state:
            queue_widget_updates(session_state, **{ACTIVE_PRESET_KEY: preset_name})
        else:
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
        if PENDING_WIDGET_UPDATES_KEY in session_state:
            queue_widget_updates(
                session_state,
                smg_map_center_concept=concept_id,
                smg_map_show_relation_labels=True,
            )
        else:
            session_state["smg_map_center_concept"] = concept_id
            session_state["smg_map_show_relation_labels"] = True
    if edge_id is not None:
        session_state[EDGE_ID_KEY] = edge_id
    if preset_name is not None:
        if PENDING_WIDGET_UPDATES_KEY in session_state:
            queue_widget_updates(session_state, **{ACTIVE_PRESET_KEY: preset_name})
        else:
            session_state[ACTIVE_PRESET_KEY] = preset_name
    if mode is not None:
        if PENDING_WIDGET_UPDATES_KEY in session_state:
            queue_widget_updates(
                session_state,
                **{
                    MAP_MODE_KEY: mode,
                    "smg_map_show_relation_labels": True,
                },
            )
        else:
            session_state[MAP_MODE_KEY] = mode
            session_state["smg_map_show_relation_labels"] = True
    elif PENDING_WIDGET_UPDATES_KEY in session_state:
        queue_widget_updates(session_state, smg_map_show_relation_labels=True)
    else:
        session_state["smg_map_show_relation_labels"] = True
    session_state[ACTIVE_VIEW_KEY] = MAP_VIEW


def open_stats(
    session_state: MutableMapping[str, object],
    *,
    tab_name: str | None = None,
) -> None:
    if tab_name is not None:
        session_state[STATS_TAB_KEY] = tab_name
    session_state[ACTIVE_VIEW_KEY] = STATS_VIEW

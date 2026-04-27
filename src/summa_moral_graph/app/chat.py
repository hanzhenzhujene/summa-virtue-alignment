"""Render a user-friendly Streamlit chat page for the full-corpus Christian virtue adapter."""

from __future__ import annotations

import streamlit as st

from ..sft import (
    DEFAULT_CHAT_EXAMPLE_PROMPTS,
    DEFAULT_CHAT_OUTPUT_ROOT,
    DEFAULT_CHAT_SYSTEM_PROMPT,
    ChatModelBundle,
    InferenceConfig,
    LiveChatSession,
    create_live_chat_session,
    generate_chat_reply,
    load_chat_model_bundle,
    load_inference_config,
    record_chat_exchange,
    record_chat_reset,
)
from ..utils.paths import REPO_ROOT, repo_relative_path_str
from .gradio_chat import (
    DEFAULT_GRADIO_CHAT_GITHUB_URL,
    DEFAULT_GRADIO_CHAT_HF_URL,
    DEFAULT_GRADIO_CHAT_MODEL_NOTE,
    DEFAULT_GRADIO_CHAT_SPACE_URL,
    DEFAULT_GRADIO_CHAT_VIEWER_URL,
)
from .ui import (
    MetricCard,
    configure_page,
    render_key_value_card,
    render_metric_cards,
    render_pill_row,
    render_section_header,
    render_surface_card,
)

DEFAULT_CHAT_CONFIG_PATH = (
    REPO_ROOT / "configs" / "inference" / "qwen2_5_1_5b_instruct_full_corpus_adapter_test.yaml"
)
CHAT_SESSION_STATE_KEY = "smg_full_corpus_chat_session"
CHAT_TOKENS_STATE_KEY = "smg_full_corpus_chat_max_new_tokens"
CHAT_SAMPLE_PROMPTS = list(DEFAULT_CHAT_EXAMPLE_PROMPTS)


@st.cache_resource(show_spinner="Loading the full-corpus LoRA chat model...")
def load_cached_full_corpus_chat_backend(
    config_path: str,
) -> tuple[InferenceConfig, ChatModelBundle]:
    config = load_inference_config(config_path)
    bundle = load_chat_model_bundle(config)
    return config, bundle


def _chat_config(base_config: InferenceConfig) -> InferenceConfig:
    max_new_tokens = int(st.session_state.get(CHAT_TOKENS_STATE_KEY, 192))
    return base_config.model_copy(update={"max_new_tokens": max_new_tokens})


def _current_session() -> LiveChatSession | None:
    return st.session_state.get(CHAT_SESSION_STATE_KEY)


def _set_session(session: LiveChatSession | None) -> None:
    st.session_state[CHAT_SESSION_STATE_KEY] = session


def _create_session(config: InferenceConfig, bundle: ChatModelBundle) -> LiveChatSession:
    session = create_live_chat_session(
        config,
        output_root=DEFAULT_CHAT_OUTPUT_ROOT,
        system_prompt=DEFAULT_CHAT_SYSTEM_PROMPT,
        command_argv=["streamlit", "run", "streamlit_app.py"],
        runtime=bundle.runtime,
    )
    _set_session(session)
    return session


def _session_rows(
    session: LiveChatSession | None,
    config: InferenceConfig,
) -> list[tuple[str, str]]:
    adapter_label = repo_relative_path_str(config.adapter_path) if config.adapter_path else "None"
    rows = [
        ("Base model", config.model_name_or_path),
        ("Adapter", adapter_label),
        ("Dataset", repo_relative_path_str(config.dataset_dir)),
    ]
    if session is None:
        rows.append(("Logs", repo_relative_path_str(DEFAULT_CHAT_OUTPUT_ROOT)))
    else:
        rows.extend(
            [
                ("Run id", session.run_dir.name),
                ("Run dir", repo_relative_path_str(session.run_dir)),
                (
                    "Transcript",
                    repo_relative_path_str(session.session_paths.transcript_markdown_path),
                ),
            ]
        )
    return rows


def _render_transcript(session: LiveChatSession | None) -> None:
    if session is None or not session.transcript_entries:
        st.markdown(
            """
            <div class="smg-card">
              <div class="smg-section-copy" style="margin:0;">
                Your first message will start a timestamped logged session against the strongest
                repo-local full-corpus LoRA adapter.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for entry in session.transcript_entries:
        role = str(entry.get("role", "assistant"))
        if role not in {"user", "assistant"}:
            continue
        with st.chat_message(role):
            st.markdown(str(entry.get("content", "")).strip())


def render_chat_page() -> None:
    configure_page(
        page_title="Christian Virtue Chat",
        title="Christian Virtue Chat",
        description=(
            "Talk directly to the strongest repo-local full-corpus LoRA adapter, using prompts "
            "that cover definitions, doctrinal relations, and practical-moral questions. Every "
            "reply is logged to a timestamped transcript."
        ),
        eyebrow="Full-Corpus LoRA",
    )

    st.session_state.setdefault(CHAT_TOKENS_STATE_KEY, 192)

    try:
        base_config, bundle = load_cached_full_corpus_chat_backend(str(DEFAULT_CHAT_CONFIG_PATH))
    except Exception as exc:  # pragma: no cover - UI fallback
        render_surface_card(
            "Chat Unavailable",
            (
                "The full-corpus chat model could not be loaded in this Streamlit session. "
                "Confirm the local environment is set up and the adapter path exists."
            ),
            tone="alert",
        )
        st.exception(exc)
        return

    config = _chat_config(base_config)
    session = _current_session()

    render_metric_cards(
        [
            MetricCard("Base model", "Qwen2.5-1.5B", "Instruction-tuned starting point"),
            MetricCard("Adapter", "Full-corpus LoRA", "Train 1475 / val 175"),
            MetricCard("Held-out exact citation", "71.2%", "Current strongest repo-local result"),
            MetricCard("Chat logs", "Timestamped", "Saved under full_corpus_chat"),
        ],
        columns=4,
    )
    st.markdown(
        (
            f"{DEFAULT_GRADIO_CHAT_MODEL_NOTE}  \n"
            f"[GitHub]({DEFAULT_GRADIO_CHAT_GITHUB_URL}) · "
            f"[Hugging Face]({DEFAULT_GRADIO_CHAT_HF_URL}) · "
            f"[Online chat]({DEFAULT_GRADIO_CHAT_SPACE_URL}) · "
            f"[Graph viewer]({DEFAULT_GRADIO_CHAT_VIEWER_URL})"
        )
    )

    render_surface_card(
        "What this page is for",
        (
            "Use this page to probe virtue, vice, act, and doctrinal-relation behavior directly. "
            "Every conversation is logged so you can compare qualitative answers against the held-"
            "out benchmark reports."
        ),
    )

    conversation_col, control_col = st.columns([1.75, 1.0], gap="large")

    with control_col:
        render_section_header(
            "Session Controls",
            "Start a fresh run directory or clear the current conversation without leaving "
            "the page.",
        )
        if st.button("Start New Logged Session", use_container_width=True):
            _create_session(config, bundle)
            st.rerun()
        if st.button(
            "Clear Conversation",
            use_container_width=True,
            disabled=session is None or not session.history,
        ) and session is not None:
            record_chat_reset(session, config, runtime=bundle.runtime)
            st.rerun()
        st.slider(
            "Max reply tokens",
            min_value=96,
            max_value=384,
            value=int(st.session_state[CHAT_TOKENS_STATE_KEY]),
            step=32,
            key=CHAT_TOKENS_STATE_KEY,
            help="Shorter replies stay tighter; longer replies leave more room for explanation.",
        )
        render_key_value_card("Current Setup", _session_rows(session, config))
        with st.expander("Evidence-first system prompt", expanded=False):
            st.code(DEFAULT_CHAT_SYSTEM_PROMPT)
        render_pill_row(
            [
                "Passage-grounded",
                "Virtue-centered",
                "Timestamped transcripts",
                "Full-corpus adapter",
            ],
            tone="info",
        )

    with conversation_col:
        render_section_header(
            "Conversation",
            "Ask a normal question. The page reuses the same loaded model and appends each turn "
            "to the active transcript. The example prompts are grouped to make first-use testing "
            "faster.",
        )

        selected_prompt: str | None = None
        for row_start in range(0, len(CHAT_SAMPLE_PROMPTS), 3):
            row_prompts = CHAT_SAMPLE_PROMPTS[row_start : row_start + 3]
            sample_columns = st.columns(len(row_prompts))
            for index, sample_prompt in enumerate(row_prompts):
                if sample_columns[index].button(sample_prompt, use_container_width=True):
                    selected_prompt = sample_prompt

        typed_prompt = st.chat_input(
            "Ask a virtue, relation, or practical-moral question..."
        )
        user_prompt = typed_prompt or selected_prompt

        if user_prompt:
            if session is None:
                session = _create_session(config, bundle)
            prompt_messages: list[dict[str, str]] = []
            if session.system_prompt:
                prompt_messages.append({"role": "system", "content": session.system_prompt})
            prompt_messages.extend(session.history)
            prompt_messages.append({"role": "user", "content": user_prompt})
            with st.spinner("Thinking with the full-corpus LoRA adapter..."):
                assistant_text = generate_chat_reply(
                    bundle,
                    config,
                    messages=prompt_messages,
                )
            record_chat_exchange(
                session,
                config,
                runtime=bundle.runtime,
                user_text=user_prompt,
                assistant_text=assistant_text,
            )
            st.rerun()

        _render_transcript(session)

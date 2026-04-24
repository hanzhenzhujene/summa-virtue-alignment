"""Launch a Gradio chat surface for the full-corpus Christian virtue LoRA adapter."""

from __future__ import annotations

from functools import lru_cache
from html import escape
from pathlib import Path

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

DEFAULT_GRADIO_CHAT_CONFIG_PATH = (
    REPO_ROOT / "configs" / "inference" / "qwen2_5_1_5b_instruct_full_corpus_adapter_test.yaml"
)
DEFAULT_GRADIO_CHAT_TITLE = "Christian Virtue Chat"
DEFAULT_GRADIO_CHAT_GITHUB_URL = "https://github.com/hanzhenzhujene/summa-virtue-alignment"
DEFAULT_GRADIO_CHAT_HF_URL = "https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b"
DEFAULT_GRADIO_CHAT_SPACE_URL = "https://jennyzhu0822-summa-virtue-chat.hf.space"
DEFAULT_GRADIO_CHAT_VIEWER_URL = "https://summa-moral-graph.streamlit.app/"
DEFAULT_GRADIO_CHAT_MODEL_NOTE = (
    "Small-model demo: Qwen/Qwen2.5-1.5B-Instruct with the strongest repo-local full-corpus "
    "Christian virtue LoRA adapter."
)
DEFAULT_GRADIO_CHAT_DESCRIPTION = (
    "Talk directly to the strongest repo-local full-corpus LoRA adapter. Use the example prompts "
    "to probe definitions, doctrinal relations, and practical-moral questions. Each browser "
    "session writes a timestamped transcript and manifest under `runs/.../full_corpus_chat/`."
)
DEFAULT_GRADIO_CHAT_EXAMPLES = list(DEFAULT_CHAT_EXAMPLE_PROMPTS)
DEFAULT_GRADIO_CHAT_CSS = """
#smg-chat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.25rem;
  padding: 0.7rem 0 0.45rem 0;
}
#smg-chat-header .smg-chat-copy {
  max-width: 48rem;
}
#smg-chat-header .smg-chat-title {
  margin: 0;
  color: #12332b;
  font-size: 2.15rem;
  font-weight: 700;
  line-height: 1.08;
}
#smg-chat-header .smg-chat-note {
  margin: 0.5rem 0 0;
  color: #29443d;
  font-size: 1rem;
  line-height: 1.5;
}
#smg-chat-header .smg-chat-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.05rem;
}
#smg-chat-header .smg-chat-link {
  background: #f7faf8;
  border: 1px solid #cfdad5;
  border-radius: 999px;
  color: #12332b;
  font-size: 0.92rem;
  font-weight: 600;
  padding: 0.4rem 0.8rem;
  text-decoration: none;
  white-space: nowrap;
}
#smg-chat-header .smg-chat-link:hover {
  background: #eef5f1;
  border-color: #9ab8ad;
}
"""


def gradio_public_links() -> tuple[tuple[str, str], ...]:
    return (
        ("GitHub", DEFAULT_GRADIO_CHAT_GITHUB_URL),
        ("Hugging Face", DEFAULT_GRADIO_CHAT_HF_URL),
        ("Online chat", DEFAULT_GRADIO_CHAT_SPACE_URL),
        ("Graph viewer", DEFAULT_GRADIO_CHAT_VIEWER_URL),
    )


def gradio_header_html(
    title: str = DEFAULT_GRADIO_CHAT_TITLE,
    *,
    model_note: str = DEFAULT_GRADIO_CHAT_MODEL_NOTE,
) -> str:
    links_html = "".join(
        (
            f"<a class='smg-chat-link' href='{escape(url, quote=True)}' "
            "target='_blank' rel='noopener noreferrer'>"
            f"{escape(label)}</a>"
        )
        for label, url in gradio_public_links()
    )
    return (
        "<div id='smg-chat-header'>"
        "<div class='smg-chat-copy'>"
        f"<h1 class='smg-chat-title'>{escape(title)}</h1>"
        f"<p class='smg-chat-note'>{escape(model_note)}</p>"
        "</div>"
        f"<div class='smg-chat-links'>{links_html}</div>"
        "</div>"
    )


def gradio_session_status_markdown(
    config: InferenceConfig,
    session: LiveChatSession | None,
) -> str:
    adapter_label = repo_relative_path_str(config.adapter_path) if config.adapter_path else "None"
    lines = [
        "### Current Setup",
        "",
        f"- **Base model:** `{config.model_name_or_path}`",
        f"- **Adapter:** `{adapter_label}`",
        f"- **Dataset:** `{repo_relative_path_str(config.dataset_dir)}`",
    ]
    if session is None:
        lines.extend(
            [
                f"- **Logs root:** `{repo_relative_path_str(DEFAULT_CHAT_OUTPUT_ROOT)}`",
                "- **Active run:** starts with your first message or with `Start New Logged "
                "Session`.",
            ]
        )
    else:
        lines.extend(
            [
                f"- **Run id:** `{session.run_dir.name}`",
                f"- **Run dir:** `{repo_relative_path_str(session.run_dir)}`",
                (
                    "- **Transcript:** "
                    f"`{repo_relative_path_str(session.session_paths.transcript_markdown_path)}`"
                ),
                f"- **Turns logged:** `{session.turn_count}`",
            ]
        )
    return "\n".join(lines)


def gradio_chatbot_messages(session: LiveChatSession | None) -> list[dict[str, str]]:
    if session is None:
        return []
    messages: list[dict[str, str]] = []
    for entry in session.transcript_entries:
        role = str(entry.get("role", "assistant"))
        if role not in {"user", "assistant"}:
            continue
        messages.append(
            {
                "role": role,
                "content": str(entry.get("content", "")).strip(),
            }
        )
    return messages


@lru_cache(maxsize=2)
def load_cached_gradio_chat_backend(config_path: str) -> tuple[InferenceConfig, ChatModelBundle]:
    config = load_inference_config(config_path)
    bundle = load_chat_model_bundle(config)
    return config, bundle


def _chat_config(base_config: InferenceConfig, *, max_new_tokens: int) -> InferenceConfig:
    return base_config.model_copy(update={"max_new_tokens": int(max_new_tokens)})


def _create_session(
    config: InferenceConfig,
    bundle: ChatModelBundle,
    *,
    output_root: Path,
    command_argv: list[str],
) -> LiveChatSession:
    return create_live_chat_session(
        config,
        output_root=output_root,
        system_prompt=DEFAULT_CHAT_SYSTEM_PROMPT,
        command_argv=command_argv,
        runtime=bundle.runtime,
    )


def build_gradio_chat_app(
    *,
    config_path: Path = DEFAULT_GRADIO_CHAT_CONFIG_PATH,
    output_root: Path = DEFAULT_CHAT_OUTPUT_ROOT,
    title: str = DEFAULT_GRADIO_CHAT_TITLE,
    description: str = DEFAULT_GRADIO_CHAT_DESCRIPTION,
):
    import gradio as gr

    resolved_config_path = config_path.resolve()
    resolved_output_root = output_root.resolve()
    base_config, bundle = load_cached_gradio_chat_backend(str(resolved_config_path))
    command_argv = [
        "python",
        "scripts/gradio_christian_virtue_chat.py",
        "--config",
        str(config_path),
    ]

    def start_new_session(
        max_new_tokens: int,
    ) -> tuple[list[dict[str, str]], LiveChatSession, str, str]:
        config = _chat_config(base_config, max_new_tokens=max_new_tokens)
        session = _create_session(
            config,
            bundle,
            output_root=resolved_output_root,
            command_argv=command_argv,
        )
        return (
            gradio_chatbot_messages(session),
            session,
            gradio_session_status_markdown(config, session),
            "",
        )

    def clear_conversation(
        max_new_tokens: int,
        session: LiveChatSession | None,
    ) -> tuple[list[dict[str, str]], LiveChatSession | None, str]:
        config = _chat_config(base_config, max_new_tokens=max_new_tokens)
        if session is None:
            return [], None, gradio_session_status_markdown(config, None)
        record_chat_reset(session, config, runtime=bundle.runtime)
        return [], session, gradio_session_status_markdown(config, session)

    def submit_message(
        message: str,
        history: list[dict[str, str]] | None,
        max_new_tokens: int,
        session: LiveChatSession | None,
    ) -> tuple[str, list[dict[str, str]], LiveChatSession | None, str]:
        if not message.strip():
            config = _chat_config(base_config, max_new_tokens=max_new_tokens)
            return "", history or [], session, gradio_session_status_markdown(config, session)

        config = _chat_config(base_config, max_new_tokens=max_new_tokens)
        if session is None:
            session = _create_session(
                config,
                bundle,
                output_root=resolved_output_root,
                command_argv=command_argv,
            )
        prompt_messages: list[dict[str, str]] = []
        if session.system_prompt:
            prompt_messages.append({"role": "system", "content": session.system_prompt})
        prompt_messages.extend(session.history)
        prompt_messages.append({"role": "user", "content": message})
        assistant_text = generate_chat_reply(bundle, config, messages=prompt_messages)
        record_chat_exchange(
            session,
            config,
            runtime=bundle.runtime,
            user_text=message,
            assistant_text=assistant_text,
        )
        return (
            "",
            gradio_chatbot_messages(session),
            session,
            gradio_session_status_markdown(config, session),
        )

    with gr.Blocks(title=title, theme=gr.themes.Soft(), css=DEFAULT_GRADIO_CHAT_CSS) as demo:
        gr.HTML(gradio_header_html(title))
        gr.Markdown(description)
        with gr.Row():
            with gr.Column(scale=7):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    type="messages",
                    height=560,
                    show_copy_button=True,
                )
                prompt = gr.Textbox(
                    label="Ask about virtue, vice, acts, or doctrinal relation",
                    placeholder="I struggle with anger. How should I respond according to Aquinas?",
                    lines=2,
                    max_lines=6,
                    autofocus=True,
                    submit_btn="Send",
                )
                gr.Examples(
                    examples=[[value] for value in DEFAULT_GRADIO_CHAT_EXAMPLES],
                    inputs=[prompt],
                    label="Example prompts (definition, relation, practical)",
                )
            with gr.Column(scale=4):
                gr.Markdown(
                    "### Session Controls\n\n"
                    "- `Start New Logged Session` creates a fresh timestamped run directory.\n"
                    "- `Clear Conversation` resets the current transcript but keeps the same run.\n"
                    "- Replies are generated against the full-corpus LoRA adapter.\n"
                    "- Try both doctrinal prompts and practical-moral prompts.\n"
                )
                max_new_tokens = gr.Slider(
                    minimum=96,
                    maximum=384,
                    value=192,
                    step=32,
                    label="Max reply tokens",
                )
                status_markdown = gr.Markdown(
                    value=gradio_session_status_markdown(
                        _chat_config(base_config, max_new_tokens=192),
                        None,
                    )
                )
                new_session = gr.Button("Start New Logged Session", variant="primary")
                clear_button = gr.Button("Clear Conversation")
                gr.Markdown(
                    "### Evidence discipline\n\n"
                    "- passage-grounded\n"
                    "- virtue-centered\n"
                    "- timestamped transcripts\n"
                    "- full-corpus adapter\n"
                )

        session_state = gr.State(value=None)

        prompt.submit(
            submit_message,
            inputs=[prompt, chatbot, max_new_tokens, session_state],
            outputs=[prompt, chatbot, session_state, status_markdown],
        )
        new_session.click(
            start_new_session,
            inputs=[max_new_tokens],
            outputs=[chatbot, session_state, status_markdown, prompt],
        )
        clear_button.click(
            clear_conversation,
            inputs=[max_new_tokens, session_state],
            outputs=[chatbot, session_state, status_markdown],
        )

    return demo


def launch_gradio_chat_app(
    *,
    config_path: Path = DEFAULT_GRADIO_CHAT_CONFIG_PATH,
    output_root: Path = DEFAULT_CHAT_OUTPUT_ROOT,
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    inbrowser: bool = True,
    share: bool = False,
) -> None:
    demo = build_gradio_chat_app(config_path=config_path, output_root=output_root)
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        inbrowser=inbrowser,
        share=share,
        show_api=False,
    )

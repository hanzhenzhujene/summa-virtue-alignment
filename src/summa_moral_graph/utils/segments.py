from __future__ import annotations

import re

# The parser still recognizes the full article shape so it can find the doctrinal
# boundaries correctly, but only respondeo and reply sections are allowed into the
# exported corpus, graph pipeline, search index, and app.
ARTICLE_SECTION_TYPES = ("obj", "sc", "resp", "ad")
USABLE_SEGMENT_TYPES = ("resp", "ad")
EXCLUDED_SOURCE_SEGMENT_TYPES = ("obj", "sc")

DISALLOWED_PASSAGE_ID_RE = re.compile(
    r"st\.(?:i|i-ii|ii-ii|iii|supplement)\.q\d{3}\.a\d{3}\.(?:obj\d+|sc)\b"
)


def is_usable_segment_type(segment_type: str) -> bool:
    return segment_type in USABLE_SEGMENT_TYPES


def has_disallowed_passage_reference(text: str) -> bool:
    return DISALLOWED_PASSAGE_ID_RE.search(text) is not None


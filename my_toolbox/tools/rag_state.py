"""
rag_state.py
------------
Shared in-memory RAG state keyed by topic_slug.
Allows multiple topics to be active in the same session.
"""

import json
import os
from pyprojroot import here

_state: dict = {}   # { topic_slug: { retriever, parent, embedded_files } }

_RECENT_PATH  = str(here("data/recent_topics.json"))
_CATALOG_PATH = str(here("data/video_catalog.json"))
_MAX_RECENT   = 3


def get_state(topic_slug: str) -> dict | None:
    return _state.get(topic_slug)


def update_state(topic_slug: str, retriever, parent: list, filepath: str) -> None:
    if topic_slug not in _state:
        _state[topic_slug] = {"retriever": None, "parent": None, "embedded_files": []}
    _state[topic_slug]["retriever"] = retriever
    _state[topic_slug]["parent"]    = parent
    _state[topic_slug]["embedded_files"].append(filepath)
    _persist_recent(topic_slug)


def _persist_recent(topic_slug: str) -> None:
    description = _lookup_description(topic_slug)
    if description is None:
        return

    if os.path.exists(_RECENT_PATH):
        with open(_RECENT_PATH, "r", encoding="utf-8") as f:
            recent = json.load(f)
    else:
        recent = []

    recent = [e for e in recent if e.get("id") != topic_slug]
    recent.insert(0, {"id": topic_slug, "description": description})
    recent = recent[:_MAX_RECENT]

    with open(_RECENT_PATH, "w", encoding="utf-8") as f:
        json.dump(recent, f, ensure_ascii=False, indent=2)


def _lookup_description(topic_slug: str) -> str | None:
    if not os.path.exists(_CATALOG_PATH):
        return None
    with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    for entry in catalog:
        if entry.get("id") == topic_slug:
            return entry.get("description")
    return None


def is_ready(topic_slug: str) -> bool:
    state = _state.get(topic_slug)
    return state is not None and state["retriever"] is not None


def list_topics() -> list:
    """Return all topic slugs currently loaded in memory."""
    return list(_state.keys())


def reset(topic_slug: str = None) -> None:
    """Clear state for one topic or all topics if no slug given."""
    if topic_slug:
        _state.pop(topic_slug, None)
    else:
        _state.clear()

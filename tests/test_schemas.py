"""Task 5: schema and evidence contract tests (stdlib jsonschema if available, else structural)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCHEMAS = RC / "schemas"

REQUIRED_FILES = (
    "visual-evidence.schema.json",
    "vision-request.schema.json",
    "vision-client-result.schema.json",
    "collaboration-state.schema.json",
)


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_schema_files_exist():
    for name in REQUIRED_FILES:
        assert (SCHEMAS / name).is_file()


def test_evidence_allows_null_confidence_and_fact_objects():
    schema = _load("visual-evidence.schema.json")
    conf = schema["properties"]["confidence"]
    assert "null" in conf.get("type", []) or conf.get("type") == ["number", "null"] or (
        isinstance(conf.get("type"), list) and "null" in conf["type"]
    )
    facts = schema["properties"]["trusted_facts"]["items"]
    assert facts.get("type") == "object"
    assert "statement" in facts.get("properties", {})
    assert "confidence" in facts.get("properties", {})


def test_states_enumerated():
    schema = _load("collaboration-state.schema.json")
    states = schema["properties"]["state"]["enum"]
    for s in (
        "UNCONFIGURED",
        "AWAITING_UPLOAD_CONFIRMATION",
        "IN_PROGRESS",
        "SUCCEEDED",
        "FAILED",
        "STOPPED_UNCERTAIN",
    ):
        assert s in states


def test_example_evidence_validates_structurally():
    schema = _load("visual-evidence.schema.json")
    example = {
        "schema_version": "1.0.0",
        "task_id": "t1",
        "task_type": "describe",
        "selected_skill": "vision-recognition",
        "input_images": ["a.png"],
        "trusted_facts": [
            {
                "fact_id": "f1",
                "statement": "A red circle is visible.",
                "evidence_refs": ["r1"],
                "confidence": None,
                "confidence_source": "unknown",
            }
        ],
        "inferred": [],
        "not_visible": [],
        "uncertain": [],
        "regions": [],
        "confidence": None,
        "confidence_source": "unknown",
        "risk_level": "low",
        "recommended_next_action": "Ask user if more detail is needed.",
        "verification_required": False,
    }
    required = schema.get("required", [])
    for key in required:
        assert key in example
    # no secrets / absolute author paths
    blob = json.dumps(example)
    assert "sk-" not in blob
    banned = "E:" + "\\\\VibeCoding"
    assert banned not in blob


def test_request_schema_forbids_api_key():
    schema = _load("vision-request.schema.json")
    assert schema.get("additionalProperties") is False
    props = schema["properties"]
    assert "api_key" not in props
    assert "upload_confirmed" in props

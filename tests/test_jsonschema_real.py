"""Real Draft 2020-12 JSON Schema validation using jsonschema (dev only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator, ValidationError

RC = Path(__file__).resolve().parents[1]
SCHEMAS = RC / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_all_schemas_are_valid_meta():
    for path in SCHEMAS.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_valid_evidence_example_passes():
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
    Draft202012Validator(schema).validate(example)


def test_evidence_rejects_additional_property():
    schema = _load("visual-evidence.schema.json")
    bad = {
        "schema_version": "1.0.0",
        "task_id": "t1",
        "task_type": "describe",
        "selected_skill": "vision-recognition",
        "input_images": [],
        "trusted_facts": [],
        "inferred": [],
        "not_visible": [],
        "uncertain": [],
        "confidence": 0.5,
        "confidence_source": "unknown",
        "risk_level": "low",
        "recommended_next_action": "x",
        "verification_required": False,
        "extra": 1,
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_evidence_rejects_confidence_out_of_range():
    schema = _load("visual-evidence.schema.json")
    bad = {
        "schema_version": "1.0.0",
        "task_id": "t1",
        "task_type": "describe",
        "selected_skill": "vision-recognition",
        "input_images": [],
        "trusted_facts": [],
        "inferred": [],
        "not_visible": [],
        "uncertain": [],
        "confidence": 1.5,
        "confidence_source": "unknown",
        "risk_level": "low",
        "recommended_next_action": "x",
        "verification_required": False,
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_request_rejects_missing_required_and_bad_enum():
    schema = _load("vision-request.schema.json")
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate({"task": "describe"})
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(
            {
                "task": "nope",
                "image_paths": ["a.png"],
                "user_question": "q",
                "upload_confirmed": True,
            }
        )


def test_runtime_modules_do_not_import_jsonschema():
    import ast

    for rel in ("scripts/config.py", "scripts/vision_client.py", "scripts/doctor.py"):
        tree = ast.parse((RC / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] != "jsonschema"
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] != "jsonschema"

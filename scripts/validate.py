#!/usr/bin/env python3
"""Fail-closed structural safeguards for Anthropology of the Singularity."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_TOP_FILES = (
    "README.md",
    "AGENTS.md",
    "PROTOCOL.md",
    "FIELDNOTE_GUIDE.md",
    "LIFE_HISTORY_PROTOCOL.md",
    "ETHICS_AND_DATA_GOVERNANCE.md",
    "GOVERNANCE.md",
    "CONTRIBUTING.md",
    "LICENSING.md",
    "CITATION.cff",
)

REQUIRED_DIRECTORIES = (
    "instruments",
    "field-sites",
    "public",
    "schemas",
    "scripts",
    "tests",
    "docs",
    "governance",
    "governance/determinations",
    "governance/public-releases",
)

REQUIRED_SCHEMAS = (
    "schemas/fieldwork-readiness.schema.json",
    "schemas/governance-determination.schema.json",
    "schemas/field-note.schema.json",
    "schemas/life-history.schema.json",
    "schemas/public-artifact.schema.json",
    "schemas/public-release.schema.json",
)

REQUIRED_DETERMINATIONS = (
    "ethics_or_research_review",
    "consent_or_lawful_alternative",
    "data_management_plan",
    "privacy_and_deidentification_plan",
    "withdrawal_and_correction_process",
    "nonpublic_access_and_storage_plan",
    "public_release_and_disclosure_review",
    "responsible_research_role",
)

PROHIBITED_COMPONENTS = {
    "raw-data",
    "rawdata",
    "participant",
    "participants",
    "participant-data",
    "interview",
    "interviews",
    "transcript",
    "transcripts",
    "recording",
    "recordings",
    "audio",
    "video",
    "field-note",
    "field-notes",
    "life-history",
    "life-histories",
    "raw-transcript",
    "raw-transcripts",
    "consent-record",
    "consent-records",
    "consent-form",
    "consent-forms",
    "recruitment",
    "recruitment-list",
    "recruitment-lists",
    "private-message",
    "private-messages",
    "linkage-key",
    "linkage-keys",
    "identity-map",
    "identity-maps",
    "screenshot",
    "screenshots",
    "private-record",
    "private-records",
}

PROHIBITED_MEDIA_EXTENSIONS = {
    ".aac",
    ".avi",
    ".flac",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".wav",
    ".webm",
}

SCIENTIFIC_RECORD_SUFFIXES = (
    ".field-note.json",
    ".life-history.json",
    ".interview.json",
    ".participant.json",
)

SCHEMA_VERSION_RE = re.compile(r"Schema bundle version:\s*`([^`]+)`")
RELEASE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
PERMITTING_OUTCOMES = {"satisfied", "not_applicable_with_basis"}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_component(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.casefold()).strip("-")


def _type_matches(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "null":
        return instance is None
    if expected == "boolean":
        return isinstance(instance, bool)
    return False


def _resolve_schema_ref(root_schema: dict[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported schema reference: {reference}")
    current: Any = root_schema
    for token in reference[2:].split("/"):
        current = current[token.replace("~1", "/").replace("~0", "~")]
    return current


def _format_matches(value: str, format_name: str) -> bool:
    if format_name != "date-time":
        return True
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return "T" in value and parsed.tzinfo is not None
    except ValueError:
        return False


def validate_contract(
    instance: Any,
    schema: Any,
    location: str = "$",
    root_schema: dict[str, Any] | None = None,
) -> list[str]:
    """Validate the dependency-free JSON Schema subset used by this repository."""

    if not isinstance(schema, dict):
        return [] if schema is True else [f"{location}: schema rejected value"]
    if root_schema is None:
        root_schema = schema
    if "$ref" in schema:
        try:
            target = _resolve_schema_ref(root_schema, schema["$ref"])
        except (KeyError, TypeError, ValueError) as exc:
            return [f"{location}: invalid schema reference: {exc}"]
        return validate_contract(instance, target, location, root_schema)

    errors: list[str] = []
    if "allOf" in schema:
        for subschema in schema["allOf"]:
            errors.extend(validate_contract(instance, subschema, location, root_schema))
    if "anyOf" in schema and not any(
        not validate_contract(instance, subschema, location, root_schema)
        for subschema in schema["anyOf"]
    ):
        errors.append(f"{location}: value does not satisfy any allowed schema")
    if "if" in schema and not validate_contract(instance, schema["if"], location, root_schema):
        errors.extend(validate_contract(instance, schema.get("then", {}), location, root_schema))

    expected_type = schema.get("type")
    if expected_type is not None:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_matches(instance, expected) for expected in allowed):
            errors.append(f"{location}: expected type {allowed}, got {type(instance).__name__}")
            return errors
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{location}: value must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{location}: value is not in the allowed enum")

    if isinstance(instance, dict):
        for field in schema.get("required", []):
            if field not in instance:
                errors.append(f"{location}: missing required field {field!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for field in instance:
                if field not in properties:
                    errors.append(f"{location}: unexpected field {field!r}")
        for field, field_schema in properties.items():
            if field in instance:
                errors.extend(
                    validate_contract(instance[field], field_schema, f"{location}.{field}", root_schema)
                )

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{location}: array has fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{location}: array has more than {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in instance]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{location}: array items must be unique")
        if "items" in schema:
            for index, item in enumerate(instance):
                errors.extend(
                    validate_contract(item, schema["items"], f"{location}[{index}]", root_schema)
                )

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{location}: string is too short")
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            errors.append(f"{location}: string does not match required pattern")
        format_name = schema.get("format")
        if format_name and not _format_matches(instance, format_name):
            errors.append(f"{location}: invalid {format_name}")
    return errors


def resolve_repository_file(root: Path, relative: Any, location: str) -> tuple[Path | None, list[str]]:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return None, [f"{location}: path must be a non-empty repository-relative POSIX path"]
    candidate = (root / relative).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        return None, [f"{location}: path escapes the repository"]
    if not candidate.is_file():
        return None, [f"{location}: referenced file does not resolve: {relative}"]
    return candidate, []


def repository_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__"} for part in relative.parts):
            continue
        paths.append(path)
    return paths


def validate_required_structure(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_TOP_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required top-level file: {relative}")
    for relative in REQUIRED_DIRECTORIES:
        if not (root / relative).is_dir():
            errors.append(f"missing required directory: {relative}/")
    for relative in REQUIRED_SCHEMAS:
        if not (root / relative).is_file():
            errors.append(f"missing required schema: {relative}")
    return errors


def validate_prohibited_paths(root: Path) -> list[str]:
    errors: list[str] = []
    for path in repository_paths(root):
        relative = path.relative_to(root)
        normalized_parts = {normalize_component(part) for part in relative.parts}
        prohibited = sorted(normalized_parts & PROHIBITED_COMPONENTS)
        if prohibited:
            errors.append(
                f"{relative.as_posix()}: prohibited high-risk path component {prohibited[0]!r}"
            )
        if path.is_file() and path.suffix.casefold() in PROHIBITED_MEDIA_EXTENSIONS:
            errors.append(
                f"{relative.as_posix()}: recording/media extension is prohibited in this repository"
            )
        if path.is_file() and path.name.casefold().endswith(SCIENTIFIC_RECORD_SUFFIXES):
            errors.append(
                f"{relative.as_posix()}: completed scientific or participant record is prohibited"
            )
    return errors


def validate_schema_bundle(root: Path) -> list[str]:
    errors: list[str] = []
    readme = root / "schemas/README.md"
    if not readme.is_file():
        return errors
    match = SCHEMA_VERSION_RE.search(readme.read_text(encoding="utf-8"))
    if not match:
        return ["schemas/README.md: missing Schema bundle version"]
    bundle_version = match.group(1)
    for relative in REQUIRED_SCHEMAS:
        path = root / relative
        if not path.is_file():
            continue
        try:
            schema = read_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{relative}: invalid JSON: {exc}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"{relative}: schema must be a JSON object")
            continue
        if schema.get("x-instrument-version") != bundle_version:
            errors.append(f"{relative}: version does not match schema bundle")
    return errors


def validate_readiness(root: Path) -> list[str]:
    relative = "governance/fieldwork-readiness.json"
    path = root / relative
    if not path.is_file():
        return [f"missing fieldwork readiness artifact: {relative}"]
    try:
        record = read_json(path)
    except json.JSONDecodeError as exc:
        return [f"{relative}: invalid JSON: {exc}"]
    if not isinstance(record, dict):
        return [f"{relative}: readiness record must be an object"]

    errors: list[str] = []
    schema_path = root / "schemas/fieldwork-readiness.schema.json"
    determination_schema_path = root / "schemas/governance-determination.schema.json"
    try:
        schema = read_json(schema_path)
        determination_schema = read_json(determination_schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{relative}: cannot load readiness schemas: {exc}"]
    errors.extend(validate_contract(record, schema, relative))
    readiness_version = schema.get("x-instrument-version")
    determination_version = determination_schema.get("x-instrument-version")
    if record.get("readiness_version") != readiness_version:
        errors.append(f"{relative}: readiness_version does not match its schema")
    if readiness_version != determination_version:
        errors.append(f"{relative}: readiness and determination schema versions are incompatible")

    permitted = record.get("execution_permitted")
    status = record.get("status")
    if permitted is False and status != "FIELDWORK_NOT_AUTHORIZED":
        errors.append(
            f"{relative}: execution_permitted=false requires FIELDWORK_NOT_AUTHORIZED"
        )
    if permitted is True and status != "FIELDWORK_AUTHORIZED":
        errors.append(f"{relative}: execution_permitted=true requires FIELDWORK_AUTHORIZED")
    determinations = record.get("determinations")
    if not isinstance(determinations, dict):
        return errors + [f"{relative}: determinations must be an object"]

    for name in REQUIRED_DETERMINATIONS:
        slot = determinations.get(name)
        location = f"{relative}: determination {name!r}"
        if not isinstance(slot, dict):
            errors.append(f"{location} is required")
            continue
        reference = slot.get("record_reference")
        if reference is None:
            if permitted is True:
                errors.append(f"{location} does not resolve to a permitting determination")
            continue
        if not isinstance(reference, dict):
            if permitted is True:
                errors.append(f"{location} does not resolve to a permitting determination")
            continue

        reference_path = reference.get("path")
        determination_path, path_errors = resolve_repository_file(
            root, reference_path, f"{location} record_reference"
        )
        errors.extend(path_errors)
        if isinstance(reference_path, str) and not re.fullmatch(
            r"governance/determinations/[A-Za-z0-9._-]+\.json", reference_path
        ):
            errors.append(f"{location}: record_reference must target governance/determinations/")
        digest = reference.get("sha256")
        if determination_path is not None and isinstance(digest, str) and SHA256_RE.fullmatch(
            digest
        ):
            actual_digest = sha256_file(determination_path)
            if actual_digest != digest:
                errors.append(f"{location}: determination SHA-256 mismatch")
        if determination_path is None:
            if permitted is True:
                errors.append(f"{location} does not resolve to a permitting determination")
            continue
        try:
            determination = read_json(determination_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{location}: invalid determination JSON: {exc}")
            continue
        record_location = determination_path.relative_to(root).as_posix()
        determination_errors = validate_contract(
            determination, determination_schema, record_location
        )
        errors.extend(determination_errors)
        if not isinstance(determination, dict):
            continue
        if determination.get("determination_version") != determination_version:
            errors.append(f"{record_location}: determination_version does not match its schema")
        if determination.get("determination_type") != name:
            errors.append(f"{location}: referenced determination type does not match readiness slot")
        expected_id = determination_path.stem
        if determination.get("determination_id") != expected_id:
            errors.append(f"{record_location}: determination_id does not match its filename")
        if permitted is True and determination.get("outcome") not in PERMITTING_OUTCOMES:
            errors.append(
                f"{location}: outcome {determination.get('outcome')!r} does not permit execution"
            )
    return errors


def validate_methodological_separation(root: Path) -> list[str]:
    paths = {
        "field_note": root / "schemas/field-note.schema.json",
        "life_history": root / "schemas/life-history.schema.json",
    }
    schemas: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for expected_type, path in paths.items():
        if not path.is_file():
            continue
        try:
            schema = read_json(path)
        except json.JSONDecodeError:
            continue
        if not isinstance(schema, dict):
            continue
        schemas[expected_type] = schema
        properties = schema.get("properties", {})
        record_type = properties.get("record_type", {}) if isinstance(properties, dict) else {}
        if record_type.get("const") != expected_type:
            errors.append(f"{path.name}: record_type must be {expected_type!r}")
        for field in (
            "observation",
            "participant_account",
            "researcher_interpretation",
            "analytic_memo",
            "reflexivity",
        ):
            if field not in properties:
                errors.append(f"{path.name}: missing distinct methodological field {field!r}")
        reflexivity = schema.get("$defs", {}).get("reflexivity", {})
        required_reflexivity = set(reflexivity.get("required", []))
        expected_reflexivity = {
            "researcher_role_position",
            "access_conditions",
            "field_relationship_change",
            "interpretive_uncertainty",
            "methodological_change",
        }
        if required_reflexivity != expected_reflexivity:
            errors.append(f"{path.name}: reflexivity contract is incomplete")

    field_schema = schemas.get("field_note")
    life_schema = schemas.get("life_history")
    if field_schema and life_schema and field_schema.get("$id") == life_schema.get("$id"):
        errors.append("field-note and life-history schemas must have distinct identities")
    if life_schema:
        properties = life_schema.get("properties", {})
        if "temporal_design" not in properties or "engagement_dates" not in properties:
            errors.append("life-history schema must make its temporal design explicit")
        serialized = json.dumps(life_schema.get("allOf", []), sort_keys=True)
        if '"longitudinal"' not in serialized or '"minItems": 2' not in serialized:
            errors.append(
                "life-history schema must require repeated engagement for longitudinal status"
            )
    return errors


def validate_release_record(
    record: Any,
    relative: str,
    schema: dict[str, Any],
    expected_id: str | None = None,
) -> list[str]:
    errors = validate_contract(record, schema, relative)
    if not isinstance(record, dict):
        return errors
    schema_version = schema.get("x-instrument-version")
    if record.get("release_record_version") != schema_version:
        errors.append(f"{relative}: release_record_version does not match its schema")
    record_id = record.get("release_record_id")
    if expected_id is not None and record_id != expected_id:
        errors.append(f"{relative}: release_record_id does not match its filename")
    return errors


def validate_public_release(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        metadata_schema = read_json(root / "schemas/public-artifact.schema.json")
        release_schema = read_json(root / "schemas/public-release.schema.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"public-release validation schemas cannot be loaded: {exc}"]
    release_root = root / "governance/public-releases"
    releases: dict[str, dict[str, Any]] = {}
    if release_root.is_dir():
        for path in sorted(release_root.glob("*.json")):
            relative = path.relative_to(root).as_posix()
            try:
                record = read_json(path)
            except json.JSONDecodeError as exc:
                errors.append(f"{relative}: invalid JSON: {exc}")
                continue
            errors.extend(validate_release_record(record, relative, release_schema, path.stem))
            if isinstance(record, dict) and isinstance(record.get("release_record_id"), str):
                releases[record["release_record_id"]] = record

    public_root = root / "public"
    artifacts: set[str] = set()
    metadata_paths: list[Path] = []
    if public_root.is_dir():
        for path in sorted(public_root.rglob("*")):
            if not path.is_file() or path == public_root / "README.md":
                continue
            if path.name.endswith(".metadata.json"):
                metadata_paths.append(path)
            else:
                artifacts.add(path.relative_to(root).as_posix())

    for artifact_relative in sorted(artifacts):
        artifact_path = root / artifact_relative
        metadata_path = Path(str(artifact_path) + ".metadata.json")
        metadata_relative = metadata_path.relative_to(root).as_posix()
        if not metadata_path.is_file():
            errors.append(f"{artifact_relative}: public artifact lacks sidecar metadata")
            continue
        try:
            metadata = read_json(metadata_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{metadata_relative}: invalid JSON: {exc}")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"{metadata_relative}: metadata must be an object")
            continue
        errors.extend(validate_contract(metadata, metadata_schema, metadata_relative))
        if metadata.get("metadata_version") != metadata_schema.get("x-instrument-version"):
            errors.append(f"{metadata_relative}: metadata_version does not match its schema")
        if metadata.get("artifact_path") != artifact_relative:
            errors.append(f"{metadata_relative}: artifact_path does not match its artifact")
        participant_derived = metadata.get("participant_derived")
        release_id = metadata.get("release_record_id")
        if not isinstance(participant_derived, bool):
            errors.append(f"{metadata_relative}: participant_derived must be boolean")
            continue
        if not participant_derived:
            if release_id is not None:
                errors.append(
                    f"{metadata_relative}: non-participant-derived artifact must not claim a release record"
                )
            continue
        if not isinstance(release_id, str) or not RELEASE_ID_RE.fullmatch(release_id):
            errors.append(
                f"{metadata_relative}: participant-derived artifact lacks a valid release_record_id"
            )
            continue
        release = releases.get(release_id)
        if release is None:
            errors.append(
                f"{metadata_relative}: participant-derived artifact lacks public-release record {release_id!r}"
            )
            continue
        if release.get("artifact_path") != artifact_relative:
            errors.append(f"{metadata_relative}: public-release record targets another artifact")
        actual_digest = sha256_file(artifact_path)
        if release.get("artifact_sha256") != actual_digest:
            errors.append(f"{metadata_relative}: public-release artifact SHA-256 mismatch")

    for metadata_path in metadata_paths:
        artifact_path = Path(str(metadata_path)[: -len(".metadata.json")])
        if not artifact_path.is_file():
            errors.append(
                f"{metadata_path.relative_to(root).as_posix()}: orphan public-artifact metadata"
            )
    return errors


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_required_structure(root))
    errors.extend(validate_prohibited_paths(root))
    errors.extend(validate_schema_bundle(root))
    errors.extend(validate_readiness(root))
    errors.extend(validate_methodological_separation(root))
    errors.extend(validate_public_release(root))
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Validation passed: FIELDWORK_NOT_AUTHORIZED; structural safeguards are sound.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
    "governance/public-releases",
)

REQUIRED_SCHEMAS = (
    "schemas/fieldwork-readiness.schema.json",
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
    expected_top_fields = {
        "readiness_version",
        "status",
        "execution_permitted",
        "determinations",
        "external_requirements_notice",
    }
    unexpected_top_fields = set(record) - expected_top_fields
    missing_top_fields = expected_top_fields - set(record)
    if unexpected_top_fields:
        errors.append(f"{relative}: unexpected fields: {sorted(unexpected_top_fields)}")
    if missing_top_fields:
        errors.append(f"{relative}: missing fields: {sorted(missing_top_fields)}")
    schema_path = root / "schemas/fieldwork-readiness.schema.json"
    if schema_path.is_file():
        try:
            schema = read_json(schema_path)
        except json.JSONDecodeError:
            schema = {}
        if isinstance(schema, dict) and record.get("readiness_version") != schema.get(
            "x-instrument-version"
        ):
            errors.append(f"{relative}: readiness_version does not match its schema")
    permitted = record.get("execution_permitted")
    status = record.get("status")
    if not isinstance(permitted, bool):
        errors.append(f"{relative}: execution_permitted must be boolean")
    if permitted is False and status != "FIELDWORK_NOT_AUTHORIZED":
        errors.append(
            f"{relative}: execution_permitted=false requires FIELDWORK_NOT_AUTHORIZED"
        )
    if permitted is True and status != "FIELDWORK_AUTHORIZED":
        errors.append(f"{relative}: execution_permitted=true requires FIELDWORK_AUTHORIZED")
    if not isinstance(record.get("readiness_version"), str) or not record["readiness_version"]:
        errors.append(f"{relative}: readiness_version is required")
    notice = record.get("external_requirements_notice")
    if not isinstance(notice, str) or not notice.strip():
        errors.append(f"{relative}: external requirements notice is required")

    determinations = record.get("determinations")
    if not isinstance(determinations, dict):
        return errors + [f"{relative}: determinations must be an object"]
    unknown = set(determinations) - set(REQUIRED_DETERMINATIONS)
    if unknown:
        errors.append(f"{relative}: unexpected determinations: {sorted(unknown)}")
    for name in REQUIRED_DETERMINATIONS:
        determination = determinations.get(name)
        location = f"{relative}: determination {name!r}"
        if not isinstance(determination, dict):
            errors.append(f"{location} is required")
            continue
        expected_determination_fields = {"status", "record_reference", "note"}
        if set(determination) != expected_determination_fields:
            errors.append(f"{location} fields do not match the versioned contract")
        determination_status = determination.get("status")
        reference = determination.get("record_reference")
        if determination_status not in {"unresolved", "documented"}:
            errors.append(f"{location} has invalid status")
        if determination_status == "unresolved" and reference is not None:
            errors.append(f"{location} unresolved status requires a null record_reference")
        if determination_status == "documented" and (
            not isinstance(reference, str) or not reference.strip()
        ):
            errors.append(f"{location} documented status requires a record_reference")
        if not isinstance(determination.get("note"), str):
            errors.append(f"{location} requires a note string")
        if permitted is True and determination_status != "documented":
            errors.append(
                f"{location} must be documented before execution_permitted can be true"
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
    record: Any, relative: str, expected_id: str | None = None
) -> list[str]:
    if not isinstance(record, dict):
        return [f"{relative}: public-release record must be an object"]
    errors: list[str] = []
    record_id = record.get("release_record_id")
    if not isinstance(record_id, str) or not RELEASE_ID_RE.fullmatch(record_id):
        errors.append(f"{relative}: invalid release_record_id")
    if expected_id is not None and record_id != expected_id:
        errors.append(f"{relative}: release_record_id does not match its filename")
    artifact_path = record.get("artifact_path")
    if not isinstance(artifact_path, str) or not artifact_path.startswith("public/"):
        errors.append(f"{relative}: artifact_path must identify a public/ artifact")
    digest = record.get("artifact_sha256")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        errors.append(f"{relative}: artifact_sha256 must be a lowercase SHA-256 digest")
    if record.get("participant_derived") is not True:
        errors.append(f"{relative}: participant_derived must be true")
    if record.get("disclosure_review") != "passed":
        errors.append(f"{relative}: disclosure review has not passed")
    if record.get("deidentification_review") != "passed":
        errors.append(f"{relative}: de-identification review has not passed")
    if record.get("status") != "cleared_for_public_release":
        errors.append(f"{relative}: release status is not cleared_for_public_release")
    if not isinstance(record.get("release_record_version"), str) or not record[
        "release_record_version"
    ]:
        errors.append(f"{relative}: release_record_version is required")
    if not isinstance(record.get("responsible_research_role"), str) or not record[
        "responsible_research_role"
    ].strip():
        errors.append(f"{relative}: responsible_research_role is required")
    reviewed_at = record.get("reviewed_at")
    try:
        parsed = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
    except (AttributeError, ValueError):
        errors.append(f"{relative}: reviewed_at must be a timezone-aware date-time")
    return errors


def validate_public_release(root: Path) -> list[str]:
    errors: list[str] = []
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
            errors.extend(validate_release_record(record, relative, path.stem))
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
        if metadata.get("artifact_path") != artifact_relative:
            errors.append(f"{metadata_relative}: artifact_path does not match its artifact")
        participant_derived = metadata.get("participant_derived")
        release_id = metadata.get("release_record_id")
        if not isinstance(metadata.get("metadata_version"), str) or not metadata[
            "metadata_version"
        ]:
            errors.append(f"{metadata_relative}: metadata_version is required")
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

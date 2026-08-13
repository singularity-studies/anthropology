from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("anthropology_validate", ROOT / "scripts/validate.py")
assert SPEC and SPEC.loader
VALIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class TemporaryRepository:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "anthropology"
        shutil.copytree(
            ROOT,
            self.root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )

    def close(self) -> None:
        self.temporary_directory.cleanup()


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_passes(self) -> None:
        self.assertEqual([], VALIDATE.validate_repository(ROOT))

    def test_initial_status_is_fieldwork_not_authorized(self) -> None:
        readiness = json.loads(
            (ROOT / "governance/fieldwork-readiness.json").read_text(encoding="utf-8")
        )
        self.assertFalse(readiness["execution_permitted"])
        self.assertEqual("FIELDWORK_NOT_AUTHORIZED", readiness["status"])
        for determination in readiness["determinations"].values():
            self.assertEqual("unresolved", determination["status"])
            self.assertIsNone(determination["record_reference"])

    def test_scaffold_contains_no_scientific_or_participant_records(self) -> None:
        field_site_files = [
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "field-sites").rglob("*")
            if path.is_file()
        ]
        public_files = [
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "public").rglob("*")
            if path.is_file()
        ]
        self.assertEqual(["field-sites/README.md"], field_site_files)
        self.assertEqual(["public/README.md"], public_files)
        for path in ROOT.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                self.assertFalse(path.name.casefold().endswith(VALIDATE.SCIENTIFIC_RECORD_SUFFIXES))

    def test_automation_limits_and_privacy_precedence_are_explicit(self) -> None:
        ethics = (ROOT / "ETHICS_AND_DATA_GOVERNANCE.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("necessary but never sufficient", ethics)
        self.assertIn("rewrite Git history", ethics)
        self.assertIn("take precedence over append-only", agents)


class ProhibitedPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = TemporaryRepository()

    def tearDown(self) -> None:
        self.repository.close()

    def test_high_risk_directories_fail(self) -> None:
        for component in (
            "raw-data",
            "participants",
            "recordings",
            "raw-transcripts",
            "consent-records",
            "private-messages",
            "linkage-keys",
            "interviews",
            "field-notes",
            "consent-forms",
        ):
            with self.subTest(component=component):
                path = self.repository.root / component / "test-only.txt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("structural fixture only", encoding="utf-8")
                errors = VALIDATE.validate_prohibited_paths(self.repository.root)
                self.assertTrue(any("prohibited high-risk path" in error for error in errors))
                path.unlink()
                path.parent.rmdir()

    def test_recording_extension_fails(self) -> None:
        path = self.repository.root / "public/test-only.wav"
        path.write_bytes(b"not media; extension guard fixture")
        errors = VALIDATE.validate_prohibited_paths(self.repository.root)
        self.assertTrue(any("recording/media extension" in error for error in errors))

    def test_completed_methodological_record_suffix_fails(self) -> None:
        path = self.repository.root / "public/test-only.field-note.json"
        path.write_text("{}\n", encoding="utf-8")
        errors = VALIDATE.validate_prohibited_paths(self.repository.root)
        self.assertTrue(any("completed scientific or participant record" in error for error in errors))


class ReadinessGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = TemporaryRepository()

    def tearDown(self) -> None:
        self.repository.close()

    def test_execution_true_with_unresolved_determinations_fails(self) -> None:
        path = self.repository.root / "governance/fieldwork-readiness.json"
        readiness = json.loads(path.read_text(encoding="utf-8"))
        readiness["execution_permitted"] = True
        readiness["status"] = "FIELDWORK_AUTHORIZED"
        write_json(path, readiness)
        errors = VALIDATE.validate_readiness(self.repository.root)
        for determination in VALIDATE.REQUIRED_DETERMINATIONS:
            self.assertTrue(any(determination in error for error in errors))

    def test_documented_determination_requires_record_reference(self) -> None:
        path = self.repository.root / "governance/fieldwork-readiness.json"
        readiness = json.loads(path.read_text(encoding="utf-8"))
        readiness["determinations"]["data_management_plan"]["status"] = "documented"
        write_json(path, readiness)
        errors = VALIDATE.validate_readiness(self.repository.root)
        self.assertTrue(any("documented status requires" in error for error in errors))

    def test_readiness_version_must_match_schema(self) -> None:
        path = self.repository.root / "governance/fieldwork-readiness.json"
        readiness = json.loads(path.read_text(encoding="utf-8"))
        readiness["readiness_version"] = "test-mismatch"
        write_json(path, readiness)
        errors = VALIDATE.validate_readiness(self.repository.root)
        self.assertTrue(any("does not match its schema" in error for error in errors))


class MethodologicalSchemaTests(unittest.TestCase):
    def test_field_note_and_life_history_are_distinct(self) -> None:
        field_note = json.loads(
            (ROOT / "schemas/field-note.schema.json").read_text(encoding="utf-8")
        )
        life_history = json.loads(
            (ROOT / "schemas/life-history.schema.json").read_text(encoding="utf-8")
        )
        self.assertNotEqual(field_note["$id"], life_history["$id"])
        self.assertEqual("field_note", field_note["properties"]["record_type"]["const"])
        self.assertEqual("life_history", life_history["properties"]["record_type"]["const"])
        for schema in (field_note, life_history):
            for field in (
                "observation",
                "participant_account",
                "researcher_interpretation",
                "analytic_memo",
                "reflexivity",
            ):
                self.assertIn(field, schema["properties"])

    def test_longitudinal_claim_requires_repeated_engagement(self) -> None:
        life_history = json.loads(
            (ROOT / "schemas/life-history.schema.json").read_text(encoding="utf-8")
        )
        serialized = json.dumps(life_history["allOf"], sort_keys=True)
        self.assertIn('"longitudinal"', serialized)
        self.assertIn('"minItems": 2', serialized)

    def test_removing_longitudinal_guard_fails_repository_validation(self) -> None:
        repository = TemporaryRepository()
        try:
            path = repository.root / "schemas/life-history.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["allOf"] = []
            write_json(path, schema)
            errors = VALIDATE.validate_repository(repository.root)
            self.assertTrue(any("repeated engagement" in error for error in errors))
        finally:
            repository.close()

    def test_incomplete_reflexivity_contract_fails(self) -> None:
        repository = TemporaryRepository()
        try:
            path = repository.root / "schemas/field-note.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["$defs"]["reflexivity"]["required"].remove("interpretive_uncertainty")
            write_json(path, schema)
            errors = VALIDATE.validate_repository(repository.root)
            self.assertTrue(any("reflexivity contract is incomplete" in error for error in errors))
        finally:
            repository.close()


class PublicReleaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = TemporaryRepository()

    def tearDown(self) -> None:
        self.repository.close()

    def test_public_artifact_without_metadata_fails(self) -> None:
        artifact = self.repository.root / "public/test-only-output.txt"
        artifact.write_text("No participant content; structural fixture only.\n", encoding="utf-8")
        errors = VALIDATE.validate_public_release(self.repository.root)
        self.assertTrue(any("lacks sidecar metadata" in error for error in errors))

    def test_participant_derived_marker_without_release_record_fails(self) -> None:
        artifact = self.repository.root / "public/test-only-output.txt"
        artifact.write_text("No participant content; structural fixture only.\n", encoding="utf-8")
        write_json(
            Path(str(artifact) + ".metadata.json"),
            {
                "metadata_version": "test-only",
                "artifact_path": "public/test-only-output.txt",
                "participant_derived": True,
                "release_record_id": "missing-release",
            },
        )
        errors = VALIDATE.validate_public_release(self.repository.root)
        self.assertTrue(any("lacks public-release record" in error for error in errors))

    def test_pending_reviews_cannot_release_artifact(self) -> None:
        artifact = self.repository.root / "public/test-only-output.txt"
        artifact.write_text("No participant content; structural fixture only.\n", encoding="utf-8")
        write_json(
            Path(str(artifact) + ".metadata.json"),
            {
                "metadata_version": "test-only",
                "artifact_path": "public/test-only-output.txt",
                "participant_derived": True,
                "release_record_id": "test-release",
            },
        )
        write_json(
            self.repository.root / "governance/public-releases/test-release.json",
            {
                "release_record_version": "test-only",
                "release_record_id": "test-release",
                "artifact_path": "public/test-only-output.txt",
                "artifact_sha256": VALIDATE.sha256_file(artifact),
                "participant_derived": True,
                "disclosure_review": "pending",
                "deidentification_review": "pending",
                "responsible_research_role": "test-only role",
                "reviewed_at": "2026-01-01T00:00:00Z",
                "status": "not_cleared",
            },
        )
        errors = VALIDATE.validate_public_release(self.repository.root)
        self.assertTrue(any("review has not passed" in error for error in errors))
        self.assertTrue(any("not cleared" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

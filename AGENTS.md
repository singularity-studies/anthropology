# Agent Instructions

These instructions apply to the entire repository.

## Primary safety rule

- Never commit identifiable or potentially re-identifiable human-subject raw data.
- Never create real, illustrative, or synthetic participant records in scientific data paths.
- Do not create raw-data, participant, recording, raw-transcript, consent-record, recruitment-list, private-message, linkage-key, or equivalent directories.
- Do not invent approvals, reviewers, participants, field sites, encounters, quotations, observations, or findings.

## Research authorization

- The default and current status is `FIELDWORK_NOT_AUTHORIZED` with `execution_permitted = false`.
- Do not represent research involving people as authorized unless the readiness artifact passes validation and all applicable external requirements have actually been met.
- Repository validation checks record completeness, not the substantive validity of an external ethics, legal, consent, or institutional determination.
- A readiness slot is unresolved unless its repository-local public determination record exists, validates, matches the slot identity and schema version, and matches the recorded SHA-256. A non-empty string is never sufficient.
- Only explicit `satisfied` or `not_applicable_with_basis` outcomes may pass the internal execution gate. `blocked` and `unresolved` outcomes fail closed.

## Methodological integrity

- Keep field notes and life histories distinct.
- Do not represent a one-off interview as longitudinal ethnography.
- Separate observation, participant account, researcher interpretation, and analytic memo.
- Preserve researcher position, access conditions, relationship changes, uncertainty, and methodological changes.
- Do not infer AI causation or a “Singularity” from observed change.
- Preserve resistance, non-adoption, reversal, ambivalence, and re-humanization as possible trajectories.

## Privacy incidents and withdrawal

- Participant safety and privacy remediation take precedence over append-only provenance.
- If sensitive material is committed, stop dissemination, restrict access, notify the responsible research role, assess obligations, remove exposed material, and rewrite Git history when required.
- Do not retain unsafe bytes merely to preserve a scientific audit trail. Record a safe incident account only after disclosure review.

## Public release

- Every future public artifact needs metadata. Participant-derived material additionally needs a valid versioned release record with disclosure and de-identification review results and a matching content hash.
- Metadata and release-record versions must match their applicable schemas; arbitrary non-empty versions are invalid.
- Treat automated path, extension, and pattern checks as limited safeguards, never a guarantee of safety.

## Required checks

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

Keep implementations small, auditable, and dependency-light. Do not build participant management, recording ingestion, transcription, surveillance, or AI ethnography systems in this repository.

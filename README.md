# Anthropology of the Singularity

Open research infrastructure for **Anthropology of the Singularity** (シンギュラリティ人類学), the human-side empirical pillar of Singularity Studies.

## Scientific position

- Umbrella field: **Singularity Studies**
- Empirical field: **Empirical Singularity Studies**
- This repository: **Anthropology of the Singularity**
- Perspective: humanity and lived human transition
- Core instruments: field notes and life histories
- Core method: longitudinal ethnography
- Public-facing record concept: **Singularity Field Notes / シンギュラリティ観測記**
- Core question:

  > How do people live through, interpret, negotiate, resist, and normalize changes in human roles within increasingly AI-mediated sociotechnical systems?

“Lived Singularity” is permitted only as an exploratory or sensitizing concept. It is not an assumed fact, participant condition, causal explanation, or finding.

## Independence and complementarity

This repository is scientifically independent from `singularity-studies/observatory`:

- Observatory: technology and system transition
- Anthropology: humanity and lived transition

The repositories may share vocabulary where explicitly governed, but neither supplies evidence or authorization for the other.

## Safety status

> **FIELDWORK_NOT_AUTHORIZED — `execution_permitted = false`**

This scaffold contains no participant data, field-site data, interview data, life-history data, ethnographic claims, or findings. A GitHub change cannot substitute for institutional, legal, community, or other external requirements. See [`ETHICS_AND_DATA_GOVERNANCE.md`](ETHICS_AND_DATA_GOVERNANCE.md).

Never commit identifiable or potentially re-identifiable human-subject raw data here. Public GitHub is limited to protocols, blank methodological instruments, governance, schemas, field-site methodology, and any future derivative output that has passed an explicit versioned disclosure and de-identification review.

## Repository map

- [`PROTOCOL.md`](PROTOCOL.md): longitudinal ethnographic design
- [`FIELDNOTE_GUIDE.md`](FIELDNOTE_GUIDE.md): situated observation and reflexive field-note method
- [`LIFE_HISTORY_PROTOCOL.md`](LIFE_HISTORY_PROTOCOL.md): lived change over time
- [`ETHICS_AND_DATA_GOVERNANCE.md`](ETHICS_AND_DATA_GOVERNANCE.md): privacy, consent, withdrawal, storage, and incident rules
- [`governance/fieldwork-readiness.json`](governance/fieldwork-readiness.json): fail-closed readiness state with byte-bound public determination references
- [`public/`](public/): future cleared derivative outputs only
- [`schemas/`](schemas/): distinct blank methodological and governance contracts
- [`scripts/validate.py`](scripts/validate.py): lightweight fail-closed checks

## Validate

The validator and tests use only the Python standard library.

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

Automated guards are necessary but not sufficient. They do not guarantee de-identification, ethical acceptability, lawful processing, valid consent, or safe public release.

An internal readiness gate can pass only when all eight slots resolve by repository-local path and SHA-256 to version-compatible, non-sensitive determination summaries with permitting outcomes. This still cannot grant, replace, or substantively validate any external approval.

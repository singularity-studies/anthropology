# Schemas

- Schema bundle version: `0.2.0-draft`
- Status: `DRAFT`

The bundle contains separate contracts for field notes and life histories, plus fieldwork readiness, public governance determination summaries, public-artifact metadata, and public-release governance. The methodological schemas define blank structure only and do not authorize collection or public storage of completed records.

Readiness slots bind repository-local records under `governance/determinations/` by path and SHA-256. Those records contain only safe public governance facts and explicit outcomes; external source documents stay outside this repository. All declared record versions must equal the applicable schema's `x-instrument-version`.

`field-note.schema.json` and `life-history.schema.json` must remain distinct. Both separate observation, participant account, researcher interpretation, and analytic memo and preserve reflexive context.

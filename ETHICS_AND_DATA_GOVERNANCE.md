# Ethics and Data Governance

- Instrument version: `0.1.0-draft`
- Status: `DRAFT`
- Fieldwork authorization: none

## Public-repository boundary

Never commit identifiable or potentially re-identifiable human-subject raw data. Prohibited material includes raw interview transcripts, identifiable field notes, recordings, participant-bearing consent forms, contact details, recruitment lists, private messages, unredacted screenshots, private organizational records, identity linkage keys, and sensitive location/time combinations.

Pseudonymization alone is not de-identification. Combinations of indirect identifiers, small groups, rare roles, distinctive narratives, timestamps, locations, and linked public information may permit re-identification.

## Fieldwork readiness

The project is `FIELDWORK_NOT_AUTHORIZED`. Setting `execution_permitted` to `true` is invalid unless the versioned readiness record documents all required determinations:

- ethics or research-review determination, as applicable;
- informed consent or lawful alternative basis, as applicable;
- data-management plan;
- privacy and de-identification plan;
- withdrawal and correction process;
- access-control and storage plan for non-public material;
- public-release and disclosure-review process; and
- responsible research role.

External institutional, legal, community, contractual, or professional requirements remain external. Repository validation cannot grant approval or prove that a determination is substantively adequate.

Each readiness slot may reference only a repository-local, non-sensitive determination summary under `governance/determinations/`, bound by path and SHA-256. The summary records an explicit outcome: `satisfied`, `not_applicable_with_basis`, `blocked`, or `unresolved`. Only the first two can permit the internal gate to proceed. The authoritative external document may remain in its controlled system and must not be copied here merely to satisfy validation.

## Non-public material

Before collection, the project must define authorized systems, encryption, access roles, retention, deletion, backup, transfer, device, breach-response, and linkage-key controls. This repository is not such a system and must not contain connection details or secrets for one.

## Public release

Every future file under `public/` requires a sidecar metadata record validated against its declared schema version. Participant-derived artifacts additionally require a schema-valid, version-matched public-release record under `governance/public-releases/` that binds the artifact path and SHA-256 digest and records passed disclosure and de-identification reviews. A release record cannot guarantee that disclosure is safe; responsible human review remains required.

## Withdrawal, correction, and privacy incidents

Withdrawal requests and corrections must be handled under the approved protocol, consent basis, applicable law, and feasibility commitments made to participants. The process must identify where material is stored, derived, shared, backed up, or published and must avoid promising deletion where it cannot lawfully or technically be delivered.

If sensitive material is accidentally committed or re-identification risk becomes material:

1. stop dissemination and further processing where appropriate;
2. restrict or disable access and preserve only the minimum protected incident evidence;
3. notify the responsible research role and follow applicable escalation and notification duties;
4. assess participant risk, withdrawal/correction commitments, downstream copies, and legal obligations;
5. remove exposed files and rewrite Git history when required;
6. invalidate caches, releases, mirrors, credentials, or links where relevant; and
7. retain only a disclosure-reviewed, non-identifying incident record when safe and required.

Participant privacy and safety take precedence over append-only scientific provenance. Git immutability is not a reason to retain unsafe human data.

## Automation limits

Automated checks can detect prohibited paths, high-risk extensions, missing governance fields, absent release records, or obvious patterns. They cannot establish consent validity, ethical acceptability, lawful processing, contextual integrity, de-identification sufficiency, or absence of re-identification risk. Passing CI is necessary but never sufficient.

# Contributing

Contributions are welcome to protocols, blank instruments, governance, schemas, validation, and documentation.

## Never submit

Do not submit participant data, field-site data, raw notes, transcripts, recordings, consent records bearing participant information, contact or recruitment lists, private messages, identity linkage keys, private organizational material, sensitive screenshots, or combinations that may enable re-identification. Do not submit synthetic or illustrative participant records into scientific paths.

If sensitive content appears in a contribution, stop review and follow the privacy-incident process in `ETHICS_AND_DATA_GOVERNANCE.md`; do not quote or duplicate it in an issue.

## Scientific changes

Explain the construct, method, ethical impact, uncertainty, version boundary, and backward-compatibility implications. Keep field-note and life-history instruments distinct and keep observation, participant account, interpretation, and analytic memo separate.

## Checks

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

Passing automation does not certify a contribution as safe or ethically authorized.

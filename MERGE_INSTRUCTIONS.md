
# Integrating BL-P001-000002 into a TTRP resident GitHub repository

This archive follows the public TTRP resident-workspace template at `edanalytx/ttrp-resident-workspace-template`. It is a **full template-aligned example workspace**, not an automatic patch to an existing resident's repository. No actual user repository was supplied, so the package cannot contain earlier accepted source, decisions, or reflections.

## If creating a new repository from the TTRP template

Create your personal repository using the official template, clone it, then copy the backlog-specific module, tests, fixture, requirements, README and evidence into it. The archive includes template guide/reference files for convenience. Keep original Git history. Review documentation before committing.

## If adding this as the next backlog in an existing project repository

1. Preserve all current accepted source, tests and other files.
2. Add `src/temporal_analysis.py`, `tests/test_temporal_analysis.py`, `tests/fixtures/supplier_receipt_lines.csv`, and the synthetic evidence folder; merge dependency lines into an existing `requirements.txt` instead of discarding earlier packages.
3. **Merge** the new README sections into your current `README.md`. Do not overwrite the existing project overview, setup instructions or earlier backlog handoffs.
4. Create `docs/reflections/BL-P001-000002.md` from the included draft and edit it to reflect what you personally implemented and verified. Keep every earlier reflection.
5. **Append** the three decisions to your current `docs/DECISIONS.md`. Use the next unused stable decision IDs rather than replacing existing D001/D002/D003 entries. Update the reflection links if renumbered.
6. Keep `TTRP_GUIDE.md` and `docs/README_ORIGINAL.md` from your actual workspace; the copies in this archive are references, not replacements for an evolved repository.
7. Run `python -m pytest -q`, then run the CLI on the real cleaned source and inspect `outputs/validation_report.json`; it has not been verified against real source data.
8. Follow **the actual current TTRP submission UI** for branch/commit requirements. The retained historical template guide describes a backlog branch, whereas the inspected T21 board code checks the repository's default-branch commit; reconcile these before submitting rather than relying on the template alone.

Do not commit private data, credentials or large source datasets without authorisation. This archive contains only synthetic receipt data.

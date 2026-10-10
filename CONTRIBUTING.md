# Contributing

Thanks for your interest. This is a small personal project: every change is reviewed and merged by hand by the maintainer, so please be patient.

## How

1. Open an issue first for anything bigger than a typo, so we can agree before you spend time on it.
2. Fork, make your change on a branch, open a pull request against `main`.
3. Workflows from forks don't run until the maintainer approves them.

## Welcome

- Support for another city or another station network (keep Grenoble working).
- New weather models or sources with a public forecast archive.
- Better scoring or validation, with numbers: show the before/after on the same test months.
- Bug fixes, clearer code comments (in English).

## Not accepted

- Changes to the frozen models (`modeles/*.joblib`) without the script and report that produced them.
- Results measured on the training data, or on a different period than the baseline.
- New dependencies without a clear need.

## Checks before a pull request

- `python prevoir.py out/prevision.json` runs without error.
- If you touched training: rerun `figer.py` and include the updated `FIGE.md`.
- No secrets, tokens or personal data in the diff.

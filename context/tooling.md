# Tooling

## Template owns tooling, project owns source

**Id:** 42366680-eee6-4dc4-9dab-3cebe376f13e
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-08-03 (PR #73); `.copier-answers.yml`

`hasansezertasan/copier-pyproject` is the source of truth for tooling, CI,
and project config; olink owns its runtime source and identity. Adoption
ran `copier copy --overwrite` and then restored `src/`, tests, README,
LICENSE, and `AGENTS.md` from git, so future template changes flow in via
`copier update`.

**Reason:** shared tooling maintenance without surrendering the project's
source or identity; the `.copier-answers.yml` anchor makes updates
mechanical.

**Rejected alternative:** cherry-picking template pieces by hand. Rejected
because hand-picks rot — the next template fix would need re-porting instead
of arriving via update.

## Python 3.14 only, no version matrix

**Id:** 4c53b9f1-4f44-4035-be18-a064c5f02759
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-04-29 and 2026-08-03; `pyproject.toml` (`requires-python = ">=3.14"`)

`requires-python = ">=3.14"` and a single-version tox/type-check setup; the
template's `>=3.10` five-version matrix was collapsed.

**Reason:** olink installs once per machine via `uvx`/`pipx`, not pinned
per-project, so a latest-Python floor costs adoption nothing while every
matrix leg costs maintenance on each tooling config.

**Rejected alternative:** keeping the template's broad floor and matrix.
Rejected as maintenance without beneficiaries.

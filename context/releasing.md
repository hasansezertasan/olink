# Releasing

## Release-please drives releases from PR titles

**Id:** a98b3a8d-0ac0-4fb0-b245-1157f7394412
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-06-20 and 2026-07-31; `CHANGELOG.md`, `check-pr-title.yml`

Releases are automated with release-please on Conventional Commits PR
titles: a Release PR bumps `CHANGELOG.md`, merging it creates the `vX.Y.Z`
tag and publishes to PyPI. `check-pr-title.yml` enforces the title format
because the title is what release-please parses for versioning.

**Reason:** no manual version edits, no draft-release publishing step; the
squash-merged title is the single source of release intent.

**Rejected alternative:** release-drafter plus a manual "publish the draft"
step. Rejected as a second manual gate with no compensating benefit once
release-please owned the whole path.

## Git tags are the version source of truth

**Id:** 25478db4-634c-4941-acc9-3d0f95cb7665
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-06-20 and 2026-07-31; `pyproject.toml` (`dynamic = ["version"]`, `hatch-vcs`)

The package version is derived from the git tag via hatch-vcs
(`dynamic = ["version"]`); no version literal is committed to the source.

**Reason:** one source of truth — the tag release-please creates — so the
code can never disagree with the release.

**Rejected alternative:** a committed static version bumped by
release-please's `extra-files` rewriting. This was actually adopted first
(June, matching a sibling project) and then reversed: rewriting a version
literal from automation reintroduces the two-sources problem the tag
derivation removes.

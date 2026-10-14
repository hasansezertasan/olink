# Detection

## CPAN fallback order: Makefile.PL, then lib/, then dist.ini

**Id:** 41648047-04e8-4bd0-838e-4801f73a20fa
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal, 2026-04-29; `core/project.py` (`_get_cpan_name`)

CPAN distribution metadata is read in reliability order: `Makefile.PL`
first (author-specified `NAME`), then the `lib/` directory layout, then
`dist.ini` last.

**Reason:** the `dist.ini` hyphen-to-colon heuristic guesses wrong on
distributions like `Foo-Bar` whose actual module is `FooBar`; the
authoritative and layout-derived sources do not guess.

**Rejected alternative:** `dist.ini` first (the original order). Rejected
once the heuristic's failure mode was found — a preferred source that
misidentifies the package is worse than a fallback that does.

## Maven parent walk with a bounded depth

**Id:** 5dac0094-3a74-4810-af5f-e909d9b219e2
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal, 2026-04-29; `core/project.py` (`_get_maven_name`)

Maven `groupId` resolution walks the full `<parent>` chain via
`<relativePath>` (defaulting to `../pom.xml`), bounded at
`_MAVEN_PARENT_DEPTH` ancestors.

**Reason:** Maven inheritance spans corporate parent to product parent to
service artifact; a one-level lookup misses grandparent `groupId` (a test
caught exactly that). The bound terminates cyclic chains and caps the work.

**Rejected alternative:** one-level parent lookup. Rejected as insufficient
for real corporate hierarchies.

<!--
Thank you for the change. The bar is not "does it work here" but "can a stranger re-run
it and get the same answer". CONTRIBUTING.md says what that means in practice.
-->

## What this changes

<!-- One paragraph. What a user would notice, or why nothing changes for them. -->

## Why

<!-- The problem, and the issue it comes from if there is one. -->

## Checks

- [ ] `make check` passes: format, lint, types, tests, offline smoke.
- [ ] A test fails without this change. For a gate, a test proves it can *fail*.
- [ ] Gates still return a verdict rather than raise, and anything undecided is
      `unknown` rather than a refutation.
- [ ] Documentation under `docs/` is updated when behavior a user sees changed.
- [ ] `CHANGELOG.md` has an entry under `Unreleased` if a user would notice.
- [ ] A new or bumped dependency comes with a regenerated `constraints/` lock file
      (`bash scripts/lock.sh`), and a downloaded tool is pinned by version and SHA-256.

# RELAXED-LEAKAGE ACCEPTANCE: django__django-15252

**Disposition: KEPT under the relaxed-leakage policy.**
`meta.json` records the top-level `relaxed_leakage: true` flag, which (with
this file present) makes the G-LEAK gate record `status = "relaxed"`
(`src/swebench_unified/gates/leak.py`). In this unified repo the policy lives
in the binding spec-construction rules, `prompts/nagini/spec_guide.md`
directive 6 ("**Exception — relaxed-leakage:** ... for a proven
`problem_statement <-> gold` mismatch where the gold's tested discriminator
exists only in `hints_text`/gold internals, so a *faithful* spec MUST name it
... KEEP the instance with the leak allowed"). (The `RELAXED_LEAKAGE.md`
cited by an earlier revision of this file was a source-repo-only doc that does
not exist here.)

This instance is a `problem_statement <-> gold` MISMATCH: the gold's
actually-tested discriminator — gate the bookkeeping-table-ensuring WRITE
effect on whether this connection was determined to have NO migrations to
record, plus the no-table no-touch short-circuit (assemble the result without
issuing the record-reading QUERY effect when, additionally, the table is not
already in place) — appears NOWHERE in the solver-visible `problem_statement`,
which frames the entire defect and fix around `db_router` / `allow_migrate`.
A *faithful* spec (one whose prepatch fails and no wrong impl verifies —
G-DIFF / G-EQ) MUST pin that no-work gate + no-touch discriminator; a
*non-leaking* spec (directive 6, judged against `problem_statement` only)
cannot. Faithful + non-leaking is therefore impossible here — not a lazy
de-narration gap, but a genuine PS<->gold mismatch, confirmed by three
independent adversarial passes (see the analysis below). The
`verify => correct` guarantee is UNAFFECTED; only the secondary no-leakage
property is relaxed.

**Exact extent of the dispositioned facet (spec-view surface — stated
honestly).** The mechanical G-LEAK lexical screen passes: no diff line, no
patched path, and no `plan` / `ensure_schema` / `has_table` /
`_create_project_state` / `with_applied_migrations` / `recorder` /
`MigrationExecutor` token appears in the spec view. What DOES appear — and is
exactly the dispositioned facet, nothing more — is the behavioural
discriminator itself, in the model's own vocabulary: the docstring's
per-connection desired behaviour (no table-ensuring WRITE effect on a
connection determined to have no migrations to record; additionally no
record-reading QUERY effect when the table is not already in place), the
`@Pure no_pending_records(pending)` predicate (argument present AND conveys
no recording work), and the two postconditions keyed on it. The leak is
SEMANTIC (the no-work gate + no-touch concept), not lexical — exactly as the
relaxed-leakage exception in `prompts/nagini/spec_guide.md` directive 6
predicts.

---

## Why faithful + non-leaking is impossible here (adversarial analysis)

Directive 6 judges leakage against the **solver-visible `problem_statement`
ONLY**, never `hints_text`, the gold internals, or the hidden `test_patch`.
Three independent adversarial-panel passes (two prior verdicts + the
2nd-pass re-audit recorded in the source pipeline) each confirmed the
following, and it was re-derived when this disposition was adopted.

### The gold took a narrower angle than the public issue

The gold edit to the migration-execution prologue keys the fix on the
determined-empty work list: when the incoming work list is present and empty,
the table-ensuring write is skipped, and if additionally the bookkeeping
table is absent the routine returns its result without touching the
connection at all; otherwise the prologue ensures the table exactly as
before. The discriminator is the **determined-no-work gate** plus the
**no-table no-touch short-circuit**.

### That discriminator is absent from the solver-visible problem_statement

- The `problem_statement` frames the ENTIRE defect and fix around
  `db_router` / `allow_migrate` (a connection that should not hold the table;
  "Django should only create tables in the first connection"). Token check:
  `allow_migrate`, `router`, `db_router`, `ensure_schema`, `record`,
  `migration`, `table`, `create` all appear in `problem_statement`.
- The gold's actual trigger vocabulary does NOT:
  `no migrations` = absent, `empty` = absent, `does not need` = absent,
  `project state` = absent, `with_applied` = absent, `query` = absent,
  `has_table` = absent. The "doesn't need to record any migrations there"
  concept appears ONLY in `hints_text` (comment 13, Andrew Godwin), and
  `need to record` / `introspection` / `read` are `hints_text`-only.
- The gold does NOT call `allow_migrate` at all. A `problem_statement`-only
  solver would reach for `router.allow_migrate(...)` (as every actual
  proposal in the issue thread did), never a determined-no-work gate.

### Any faithful spec must pin the leaked trigger

To satisfy G-DIFF / G-EQ / faithfulness, `model.py` must pin the gold's
actual behaviour: the write effect occurs iff the connection was not
determined to have no migrations to record
(`schema_ensured == (not no_pending_records(pending))`), and the
record-reading effect is skipped on exactly the no-work + no-table path
(the `records_read` clause). Both are `hints_text`/gold-internal concepts.
There is no PS-derivable (`router`/`allow_migrate`) reformulation that still
models the gold fix, because the gold fix is not the `router`/`allow_migrate`
fix the public issue asked for.

### Why re-grounding clause (2) on the F2P observable does not close the leak

An earlier recovery pass re-grounded clause (2) from a narrated short-circuit
mechanism onto the record-reading QUERY-effect observable (what the F2P
test's zero-query assertion measures). That is a real improvement to the spec
view's surface (no gold-internal mechanism narration remains), but it does
NOT make the trigger `problem_statement`-derivable: the F2P test body is part
of the hidden `test_patch`, which the solver never sees, and directive 6
forbids grounding leakage judgments in it. The behavioural trigger itself
(no-work gate + no-touch path) remains hints/gold-only — hence this
relaxed-leakage disposition rather than a claim of no leak.

## Re-verify snapshot (soundness intact — this is a relaxed leak, not a defect-in-spec)

- G-VERIFY: PASS — `model.py` verifies, no flags, well under the timeout.
- G-DIFF: PASS — `model_prepatch.py` shares the byte-identical spec regions
  (same_spec TRUE) and FAILS on the discriminating postcondition
  `executor.schema_ensured == (not no_pending_records(pending))`
  (the prepatch performs the table-ensuring write unconditionally).
- G-GOLD: PASS — gold-faithful impl verifies; prepatch fails.
- G-AX: `axiom_check.py` RC=0 — model observations == gold-patched
  observations on all 6 (work-list shape x table-existence) combinations,
  plus the F2P witness (gold write-effect count 0 on the no-work path vs
  pre-patch 1).
- G-MUT: 2/2 mutants killed. G-PBT: SOUND. G-RESOLVE: resolved (official
  SWE-bench harness).
- Static gates (G-INTEGRITY / G-HYGIENE / mechanical G-LEAK screen): pass.

The mechanical G-LEAK screen passes (no diff lines/paths/narration), but it
is lexical and blind to this semantic fix-mechanism leak; the adversarial
reconstruction test (G-PANEL attacker 3) is the binding judgment on the
facet's EXTENT, and — per the panel recording convention above — its honest
recording for this properly-dispositioned facet is NO-LEAKAGE (pass) + note,
with LEAKAGE reserved for a NEW leak beyond the facet or a broken
disposition.

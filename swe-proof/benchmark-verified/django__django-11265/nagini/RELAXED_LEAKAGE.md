# Relaxed-leakage disposition — django__django-11265

**Disposition: ACCEPTED under the relaxed-leakage policy.**
`meta.json` records the top-level `relaxed_leakage: true` flag, which (with
this file present) makes the G-LEAK gate record `status = "relaxed"`
(`src/swebench_unified/gates/leak.py`). In this unified repo the policy lives
in the binding spec-construction rules, `prompts/nagini/spec_guide.md`
directive 6 ("**Exception — relaxed-leakage:** ... for a proven
`problem_statement ↔ gold` mismatch where the gold's tested discriminator
exists only in `hints_text`/gold internals, so a *faithful* spec MUST name it
... KEEP the instance with the leak allowed"). (The `RELAXED_LEAKAGE.md`
cited by an earlier revision of this file was a source-repo-only doc that does
not exist here — see `prompts/README.md` on dangling source-repo refs.)

The spec view names the gold's tested discriminator for **site 2** — that **a
leading join of the exclusion subquery retains its filter condition exactly
when the join is left-outer OR carries a relation-specific filter, and an
inner join with a relation-specific filter is therefore never collapsed (its
condition is preserved)** — because this instance is a genuine
`problem_statement` ↔ gold MISMATCH and a *faithful* spec cannot avoid naming
it.

**Exact extent of the dispositioned facet (spec-view surface — stated
honestly).** The mechanical G-LEAK lexical screen passes: no diff line, no
patched path `query.py`, and no `split_exclude` / `trim_start` / `first_join`
/ `alias_map` / `filtered_relation`-the-repo-attribute token appears in the
spec view. What DOES appear in the spec view — and is exactly the
dispositioned facet, nothing more — is the behavioural discriminator itself:
the bundle-local abstract join-kind tokens `LOUTER()` / `INNER()`
(model.py:42–51), the transparent guard `may_trim_leading_join(join_type,
is_filtered_relation) = (join_type != LOUTER() and not is_filtered_relation)`
(model.py:59) whose boolean structure mirrors the post-patch trim guard,
docstring item (2), and the four site-2 postconditions keyed on that guard.
An earlier revision of this file wrongly claimed that no `LOUTER` /
`filtered_relation`-derived identifier appears in the spec view; that claim
was false and is corrected here. The identifiers ARE in the spec view, and
they are WITHIN the dispositioned facet: `LOUTER`/`INNER` are the model's own
mnemonic int tokens for the two join kinds ("left outer" / "inner" — the very
concepts the unavoidable behavioural leak must name; the mnemonic spelling
adds no information beyond them), `is_filtered_relation` is the model's own
boolean parameter for "carries a relation-specific filter" (ditto), and the
guard is the behaviour itself, which requirement 2 below proves cannot be
elided from a faithful spec. The de-narration of the prior batch08 verdict —
D1 the `(repo: constants.LOUTER/INNER)` citations, D2 the "silently drop /
admit rows" causal prose — remains in place: repo bindings live only in
mapping.md / refinement.md, never in the spec view.

## Why faithful + non-leaking is impossible here (adversarial analysis)

Directive 6 judges leakage against the **solver-visible `problem_statement`
ONLY**, never `hints_text`, the gold internals, or the hidden `test_patch`.

**What the `problem_statement` actually says.** The public issue is titled
"Using exclude on annotated FilteredRelation doesn't work". Its entire content is
a **`FieldError` symptom report**: `.exclude(book_alice__isnull=False)` over an
`annotate(book_alice=FilteredRelation(...))` raises
`FieldError: Cannot resolve keyword 'book_alice' into field`, with a traceback
ending in `names_to_path`. The reporter's only diagnosis is: "the function
`split_exclude(...)` seams to be the faulty one. A new query is created without
all extra datas from the original query." That is **site 1 only** — the
registry-propagation fix (the gold's `query._filtered_relations =
self._filtered_relations` hunk). The `problem_statement`:
  - is entirely about the `FieldError` (the alias failing to *resolve* in the
    exclusion subquery),
  - never mentions a left-outer vs inner join, join trimming/collapsing, a
    subquery pushdown, a dropped ON-clause filter, or *wrong rows being
    returned* (a query that runs but returns the wrong result set).

**Where the actually-tested site-2 discriminator lives.** Once site 1 is fixed
the `FieldError` disappears but the generated SQL is still wrong: the inner
query's filtered-relation join is trimmed away, so its `ON`-clause filter is
silently dropped and the exclusion admits rows it was meant to exclude. The gold
patch's second hunk (`trim_start`, `query.py:2145`) adds the
`and not first_join.filtered_relation` conjunct to the trim guard so a
filtered-relation leading join is no longer collapsed. The sole FAIL_TO_PASS
test `filtered_relation.tests.FilteredRelationTests.test_with_exclude` pins this
**wrong-rows** behaviour (it asserts the exclusion returns the *correct* author
set, not merely that no exception is raised). This left-outer-vs-inner /
filtered-relation-keeps-its-filter discriminator, the "missing the join clause",
the "wrong results", the "additional element", the "subquery pushdown", and the
"LEFT OUTER JOIN" reasoning are present ONLY in `hints_text` (the multi-comment
SQL discussion: "ths sql is missing the join clause … the result returned is not
the result we are expecting … This kind of match can only be generated using a
LEFT OUTER JOIN … or a subquery pushdown … split_exclude need to be adjusted to
special case filter_expr that refer to a filtered expression") and the hidden
`test_patch` — never in the `problem_statement`.

Token scan of the `problem_statement` (independently confirmed):
`left outer`=absent, `outer join`=absent, `inner join`=absent, `LOUTER`=absent,
`trim`=absent, `collapse`=absent, `pushdown`=absent, `subquery`=absent,
`wrong result`=absent, `additional element`=absent, `join clause`=absent. Each
of these (except the patched-symbol forms) is **present in `hints_text`**.

**The mismatch — and why hunk 2 is mandatory.** A spec that pins the gold
behaviour (so the prepatch fails — G-DIFF — and no wrong impl verifies — G-EQ)
MUST name the retained-filter / left-outer-or-filtered discriminator: in-container
hunk-isolation shows that with **only** the site-1 registry hunk (the sole
PS-derivable fix) the F2P `test_with_exclude` still FAILS (the now-resolvable
alias is trimmed away, returning the wrong rows), and with **only** the site-2
hunk it FAILS with the original `FieldError`. Both hunks are independently
necessary, and the second hunk's behaviour is not derivable from the public
issue (a PS-only consumer fixes the `FieldError` via site 1 and stops, never
sensing the dropped-filter wrong-rows defect). Hence **faithful + non-leaking is
provably impossible** — the public text (the `FieldError`, a *resolution*
failure) and half the gold fix (a join-trim *result-correctness* fix) are about
different things. This is the spec_guide.md directive-6 relaxed-leakage
condition (a proven PS↔gold mismatch), not lazy de-narration: the docstring is
already de-narrated to an abstract retained-conditions contract; the residual
"leak" is the behaviour itself.

Scope note: **only the site-2 behaviour relaxes.** Site 1 (the registry-must-be-
inherited / alias-must-resolve contract in `propagate_relation_registry`) is
fully PS-derivable — it is exactly the reporter's own `split_exclude`
"new query is created without all extra datas" diagnosis — and does not leak.

## Requirements satisfied (spec_guide.md directive 6)

1. **Core is sound.**
   - G-VERIFY pass: `model.py` verifies in 23.26s (<300s, no flags).
   - G-DIFF fail: both prepatches are spec-byte-identical (same_spec True;
     spec_view hash `195b72188a55f91e…` matches across all three files) and FAIL
     on their discriminating clauses — `model_prepatch_1.py` (site-1 empty inner
     registry, `return []`) fails `ToSeq(Result()) == ToSeq(outer_relations)`;
     `model_prepatch_2.py` (site-2 pre-patch guard `join_type != LOUTER` only)
     fails `Implies(not may_trim_leading_join(...), ToSeq(Result()) ==
     PSeq(leading_filter) + ToSeq(other_filters))`.
   - G-MUT 20/20 impl mutants killed.
   - G-EQ sound/tight: refinement.md is all R / I (no consumed axiom, no
     A-reference, no kind-3); the discriminators are grounded in the actual input
     carrier — `ToSeq(Result()) == ToSeq(outer_relations)` (site 1) and a
     value-exact retained-conditions list keyed on the transparent boolean
     `may_trim_leading_join(join_type, is_filtered_relation)` over the real
     inputs (site 2). There is no `@ContractOnly`/opaque pure oracle; `LOUTER()`
     /`INNER()` are concrete constants and `may_trim_leading_join` is a
     transparent predicate, so a result cannot be echoed from an ungrounded
     answer-key (directive 8) — it must be produced by the modeled branch.
   - G-AX vacuous (legitimate): zero `@ContractOnly` axioms, zero A-references;
     both changed operations are Django-internal data/control flow deep-modeled
     per SPEC_GUIDE §3; no `axiom_check.py` needed or expected.
   - G-RESOLVE: `patch.diff` == gold patch verbatim (1668 B), applies at
     `base_commit`, and the harness reports `resolved` (M0 500/500; in-container
     F2P `test_with_exclude` passes).
2. **The leak is genuinely unavoidable**, established by the adversarial analysis
   above: the gold's site-2 tested discriminator (a left-outer or
   filtered-relation leading join retains its filter; an inner filtered-relation
   join is never trimmed) is demonstrably absent from `problem_statement` (which
   is purely the `FieldError` resolution symptom) and present only in
   `hints_text` / gold / `test_patch`; no PS-derivable reformulation models the
   gold's second hunk (the PS-surface fix is site 1 alone, which is empirically
   insufficient for the F2P test).
3. **Documented in-bundle.** This file; `meta.json` carries the top-level
   `relaxed_leakage: true` flag; the G-LEAK gate reads it (plus this file) and
   records `gates.G-LEAK.status = "relaxed"` pointing at this document.

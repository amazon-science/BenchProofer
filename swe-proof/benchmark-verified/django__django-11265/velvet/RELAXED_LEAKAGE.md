# RELAXED_LEAKAGE — django__django-11265 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). The nagini bundle of THIS
instance carries the same disposition
(`benchmark-verified/django__django-11265/nagini/RELAXED_LEAKAGE.md`), for
the same site-2 facet; velvet precedents: django__django-14155,
django__django-10999, sphinx-doc__sphinx-10466.

## The mismatch

The gold fix (two hunks in `django/db/models/sql/query.py`) makes TWO
independent behavioral changes:

- **(a) Site 1 — registry inheritance in `split_exclude` — fully public.**
  The `problem_statement` is exclusively about this: the `FieldError` on the
  annotation name under `.exclude(...)`, the traceback through
  `split_exclude`, and the reporter's own diagnosis "A new query is created
  without all extra datas from the original query." The spec's
  `inheritedFilteredRelations` (the negated-lookup subquery must recognise
  the SAME named filtered relations as the originating query, so the
  reference resolves instead of failing) is a direct reformulation of that
  public text. This facet does NOT leak.
- **(b) Site 2 — the strengthened leading-join trim guard — hints/gold-only.**
  Once site 1 is fixed the `FieldError` disappears but the generated SQL is
  still wrong: the subquery's filtered-relation join is trimmed away, its
  ON-clause filter silently dropped, and the exclusion returns the wrong
  rows. The gold's second hunk strengthens the `trim_start` guard with
  `and not first_join.filtered_relation`. Token scan of the
  `problem_statement`: left outer / outer join / inner join / LOUTER / trim /
  collapse / pushdown / subquery-pushdown / wrong result / join clause — all
  ABSENT. Every one of these lives ONLY in `hints_text` (the maintainer's
  generated-SQL discussion) and the hidden `test_patch`. Yet the sole
  FAIL_TO_PASS test `test_with_exclude` pins this wrong-rows behaviour.

The velvet spec view discloses facet (b) via the pure def `joinRemovable`
(`(! preservesUnmatchedRows) && (! carriesOwnFilter)`), its `@[grind]`
definitional lemma, the method `canRemoveLeadingJoin` with its
`ensures out = joinRemovable …` clause, the parameter names
`preservesUnmatchedRows` / `carriesOwnFilter`, and the docstrings stating
the retained-filter rationale ("a join introduced by a named filtered
relation carries the relation's filter condition, so dropping it would
silently discard that condition"; "It is safe to drop only when removing it
can neither lose rows nor lose filtering"). That is the entire dispositioned
facet — the behavioural discriminator itself, expressed over the model's own
abstract inputs. The mechanical G-LEAK lexical screen passes: no gold-diff
line, no patched path `query.py`, and no `split_exclude` / `trim_start` /
`first_join` / `alias_map` / `LOUTER` repo token appears in the spec view;
the leak is purely semantic. Repo bindings live only in mapping.md /
refinement.md, never in the spec view.

## Why the leak is unavoidable

Directive 6 judges leakage against the solver-visible `problem_statement`
ONLY, never `hints_text` / gold / `test_patch`.

A faithful spec must pin the gold behaviour the F2P test checks, and BOTH
hunks are independently necessary for `test_with_exclude`: with only the
site-1 registry hunk (the sole PS-derivable fix) the test still FAILS — the
now-resolvable alias's join is trimmed and the wrong rows come back; with
only the site-2 hunk it fails with the original `FieldError`
(hunk-isolation evidence recorded in the nagini sibling's disposition and
refinement.md §C here). `Solution_prepatch_2.lean` is precisely the impl a
PS-only solver would produce (site 1 fixed, pre-patch single-conjunct trim
guard): it fails `prove_correct` against the frozen spec (G-DIFF) exactly on
the `(!preservesUnmatchedRows) = joinRemovable …` clause — and it would fail
the hidden F2P test. A spec weak enough to hide facet (b) would ADMIT
`Solution_prepatch_2.lean`, i.e. admit an implementation that does not
resolve the instance, violating G-EQ/G-DIFF soundness. Faithful +
non-leaking is therefore provably impossible here; this is the defining
shape of the relaxed-leakage exception (spec_guide.md directive 6), NOT
ordinary de-narration: the docstrings are already de-narrated to an abstract
retained-conditions contract over abstract join properties; the residual
"leak" is the behaviour itself.

Scope note: **only the site-2 behaviour relaxes.** Site 1
(`inheritedFilteredRelations`) is fully PS-derivable — it is exactly the
reporter's own `split_exclude` "new query is created without all extra
datas" diagnosis — and does not leak.

## Core soundness is intact

- G-VERIFY: `Solution.lean` verifies (exit 0, ~2s); both `prove_correct`
  goals discharged, postconditions non-vacuous.
- G-DIFF: both prepatches are spec-byte-identical (same_spec True) and FAIL
  on exactly their discriminating clauses — `Solution_prepatch.lean` (site-1
  empty registry) on `[] = outerRelations` / `resolves []`;
  `Solution_prepatch_2.lean` (site-2 single-conjunct guard) on
  `(!preservesUnmatchedRows) = joinRemovable …` (false at
  `preservesUnmatchedRows = false, carriesOwnFilter = true`).
- G-MUT: 3/3 mutants killed.
- G-EQ / G-PANEL-1: pass — 10 same-spec wrong-impl attacks (incl. both
  prepatch bugs and membership-preserving permutations) all rejected;
  positive controls verify (spec non-vacuous, maximally tight
  `out = f(inputs)` shape).
- G-PANEL-2: FAITHFUL — both modeled functions match the two gold edits
  edit-for-edit against the real worktree at base_commit.
- G-AX: skip — genuinely axiom-free (no consumed callee contract; both
  changed ops modeled deeply).
- G-CONF: documented conf_skip (the only discriminating observable is a
  queryset result / `FieldError` on a live ORM + DB; precedent
  django__django-11451, django__django-11179).
- G-RESOLVE: `patch.diff` is the gold patch verbatim; harness `resolved`.

Only the secondary no-leakage property is relaxed, for this one documented
site-2 facet.

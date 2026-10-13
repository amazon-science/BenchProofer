# mapping.md — django__django-13315

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 36bc47069ce071e80c8129500de3b8664d2058a7`, states the type
abstraction (the Lean↔Python bijection), records callee provenance, and explains
why G-CONF is skipped.

Repo file under change: `django/forms/models.py`.
Changed function: `apply_limit_choices_to_to_formfield(formfield)`
(`django/forms/models.py:98`; the touched step is `models.py:102–103` pre-patch
/ `models.py:102–110` post-patch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectEligible (rows : List Candidate)` | the constraint-application step inside `apply_limit_choices_to_to_formfield` — `django/forms/models.py:102–103` | the modeled changed behavior: narrow the formfield's candidate collection to those satisfying the constraint |
| `rows : List Candidate` | the formfield's pre-narrowing candidate collection (`formfield.queryset`), one element per (candidate object × constraint witness) the underlying join would surface | the input collection the constraint is applied to |
| `Candidate.id` | the candidate object's primary key (`pk`) | the stable identity by which the form deduplicates options |
| `Candidate.witnesses` | the number of distinct related rows that make this candidate satisfy `limit_choices_to` (the multiplicity the join would produce for it) | drives eligibility (≥1 ⇒ included) AND the buggy duplication (one row per witness) |
| `out : List Int` | the narrowed candidate collection actually offered as form options (`formfield.queryset` post-narrowing), as the sequence of candidate identities | the observable: which identities appear, and how many times each |

No callee is axiomatized. The collection-narrowing primitive (`complex_filter` /
`filter(Exists(...))`) is modeled DEEPLY as the per-candidate selection
`keepMatching`/`keep`; the underlying DB join/subquery is observed only through
the identities (and their multiplicities) it surfaces, modeled as the returned
`List Int`. There is no consumed axiom (no `axiom` declarations) and no
A-reference deep model of an outside callee.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the formfield candidate collection (a `QuerySet`) | `List Candidate` | the rows the query surfaces ↔ a `List Candidate`; query order ↔ list order; an empty result ↔ `[]`; query concatenation/iteration ↔ `List` traversal |
| a candidate's primary key | `Candidate.id : Int` | `obj.pk` ↔ `c.id`; the form's option identity is the pk |
| how many related rows satisfy the constraint for one candidate | `Candidate.witnesses : Nat` | the join cardinality for that candidate ↔ `c.witnesses`; eligible (the candidate satisfies `limit_choices_to`) ⇔ `witnesses > 0` ⇔ at least one related row matches |
| "candidate is offered as an option, k times" | `c.id` occurring k times in `out` | k = the multiplicity the narrowing produces for that candidate; the fix demands k ∈ {0,1}, the bug allows k = `witnesses` |
| `formfield.queryset = <narrowed>` (the assignment) | `out` (the returned `List Int`) | the narrowed collection's observable content is its sequence of option identities; `assertCountEqual` in the F2P test compares exactly this multiset of pks |

The Python truthiness guard `if limit_choices_to:` (post-patch) vs
`if limit_choices_to is not None:` (pre-patch) is a constraint-presence guard
upstream of the modeled step; both branches reach the narrowing when a real
constraint is present, so the modeled behavior begins at the narrowing itself.
The behavior the F2P test observes — duplicate vs once-each options — is entirely
in HOW the narrowing emits each eligible candidate, which `keepMatching` pins.

## 3. Callee provenance

None axiomatized. The two narrowing primitives are:

* `formfield.queryset.complex_filter(limit_choices_to)` (pre-patch) — an inner
  join against the related table; for a `Q` spanning a join it emits each
  candidate **once per matching related row** (the duplicate-options bug). Its
  per-candidate effect is the deep model `List.replicate c.witnesses c.id`
  (prepatch impl), I/R-tagged, not a consumed contract.
* `formfield.queryset.filter(Exists(... _base_manager.filter(complex_filter)))`
  (post-patch) — a correlated `Exists()` subquery; for each candidate it tests
  *whether any* matching related row exists, emitting the candidate **once iff
  eligible**. Its per-candidate effect is the deep model `keep c`
  (= `[c.id]` if `witnesses > 0` else `[]`), I/R-tagged.

Neither is axiomatized or deep-modeled as an A-reference of a stdlib callee: the
property the fix changes is *the multiplicity with which each eligible candidate
is emitted*, captured exactly by `out = keepMatching rows`. The `&=`/`Q(...)`/
`OuterRef('pk')`/`_base_manager` machinery only assembles the same per-candidate
eligibility predicate the pre-patch join used (same `complex_filter`); it does
not change *which* candidates are eligible, only that each eligible one is now
counted once. mapping.md ties `witnesses > 0` to that shared predicate.

## 4. G-CONF — SKIPPED (conf_skip = true)

There is no pure, DB-free R/I shadow to differential-test. The operation the
control flow performs — narrowing a `QuerySet` by either an inner-join
`complex_filter` (duplicating) or an `Exists()` correlated subquery (deduping) —
only has observable behavior relative to a live relational backend:

* the duplicate-vs-once multiplicity is produced by the SQL the ORM compiles
  (a JOIN vs an `EXISTS (...)` correlated subquery), executed against real
  related rows in real tables;
* reproducing the bug-triggering case (a `Q` spanning *two* joins, so a
  candidate matches via several related-row combinations) requires standing up
  the model graph, the related managers, and a DB connection — i.e. the F2P
  integration test itself (`test_limit_choices_to_no_duplicates`), not a fuzzed
  pure transliteration.

The abstraction the spec pins (`witnesses` ↦ once-or-zero) IS the modeled
content; there is no DB-free oracle that produces `witnesses` to diff against.
Therefore `meta.json conf_skip = true` and `conformance_check.py` is a
`status=skip` stub (exit 0). Soundness of the modeled narrowing is carried by
**G-VERIFY** (the fold provably emits each eligible candidate exactly once) and
**G-DIFF** (the prepatch, which emits `replicate witnesses id`, fails exactly the
`out = keepMatching rows` clause on any candidate with `witnesses ≥ 2` — the
duplicate-options bug the issue reports). This mirrors the django__django-13089
precedent (a live-DB control-flow change with no DB-free shadow).

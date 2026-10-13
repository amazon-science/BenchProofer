# refinement.md — django__django-15022

The operation-by-operation correspondence between `model.py`'s implementation
(`search_retains_object`, with the deep predicates `row_matches_all` /
`some_row_matches_all`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == a real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The search-combination site — `ModelAdmin.get_search_results`

Repo: `django/contrib/admin/options.py`, search body (lines 1029-1046 @
`base_commit`).

Gold hunk (the combination change):
```
  for bit in smart_split(search_term):
      ...
+     term_queries = []   # (declared just before the loop)
      or_queries = models.Q(*((orm_lookup, bit) for orm_lookup in orm_lookups),
                            _connector=models.Q.OR)
-     queryset = queryset.filter(or_queries)
+     term_queries.append(or_queries)
+ queryset = queryset.filter(models.Q(*term_queries))
```

| # | model.py impl op (`search_retains_object`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `terms: PSeq[int]` | the bits produced by `for bit in smart_split(search_term)` | R | each bit ↔ one term id; only the per-row `matches` truth of a term is observable (mapping.md §1,§2). `smart_split` / `unescape_string_literal` are unchanged tokenisers upstream of the combination — not modelled, identical pre/post patch. |
| A2 | `rows: PSeq[int]` | the multi-valued related rows reachable from one candidate | R | each related row ↔ one row id (mapping.md §2). |
| A3 | `matches(row, term)` (uninterpreted relation) | the per-term OR-query `models.Q(*((orm_lookup, bit) …), _connector=OR)` evaluated against one related row | R | the OR over searched fields collapses to one boolean per (row, term); the per-field comparison is UNCHANGED by the patch, so it is left uninterpreted. The proof uses **no property** of `matches` (its contract is the tautology `Implies(R,R)`) — it is neither consumed nor an A-reference, it is a modelling primitive. |
| A4 | the loop accumulating `all_clear = row_matches_all(row, terms)` over each row, then `retained = retained or all_clear`, i.e. `some_row_matches_all(rows, terms)` | `term_queries.append(or_queries)` for every bit, then ONE `queryset.filter(models.Q(*term_queries))` | A-reference | the changed query-combination operation is modelled **deeply**: `row_matches_all` / `some_row_matches_all` (spelled out in the `pure` region) ARE the set semantics of a single `.filter()` of the AND-of-per-term-ORs over a multi-valued relation — a single reused join requires ONE related row to clear the whole conjunction (`∃ row ∀ term`). There is no consumed combination axiom; the deep model is validated **== the real Django semantics** out-of-band by G-AX (axiom_check.py): for every match matrix, `some_row_matches_all == queryset.filter(Q(*term_queries))` (mapping.md §3.1). |
| A5 | `return retained` (a `bool`) | the candidate's membership in the returned `queryset` | R/I | the model's boolean ↔ "this candidate object survives the filter"; `get_search_results` returns `(queryset, may_have_duplicates)` and the F2P tests observe `cl.queryset.count()` — the count is the number of candidates whose `retained` is true. The `may_have_duplicates` half is untouched by the combination change. |

## B. The discriminating content (what G-DIFF senses)

The behavioural delta is a **quantifier swap** over the (row, term) relation:

* fix (single `.filter(Q(*term_queries))`): `∃ row ∀ term: matches(row, term)`
  = `some_row_matches_all` — a SINGLE related row must clear all terms.
* pre-patch (chained `qs = qs.filter(or_queries)` per bit): `∀ term ∃ row:
  matches(row, term)` — each term may be cleared by a DIFFERENT related row.

`model_prepatch.py` reproduces the chained-filter skeleton (loop over terms,
keep iff every term is matched by some row). It keeps the spec byte-identical
(`same_spec` = True) and **fails** verification on
`Invariant(retained == some_row_matches_all(rows, terms))`: the for-all-terms,
exists-row computation cannot establish the exists-row, for-all-terms retention
predicate — exactly the spec sensing the change (G-DIFF). The concrete witness
is the F2P scenario children {Danielle@18, Daniel@19}, search `danielle 19`:
every term is covered (Danielle→"danielle", Daniel→"19") so the pre-patch keeps
the parent (old count 1), but no single child clears both, so the spec / fix
drop it (new count 0). axiom_check.py pins this scenario.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — combining the per-term queries with a single AND-filter instead of
chaining one filter per term — is modelled **deeply** (the spelled-out folds
`row_matches_all` / `some_row_matches_all`, step A4, an **A-reference**), not
hidden behind an axiom about the changed operation. There is **no A-consumed
axiom**: the only `@ContractOnly` symbol, `matches` (the unchanged per-field
comparison), is uninterpreted and the proof depends on no property of it
(hence it is a modelling primitive, not a load-bearing axiom — see meta.json
`axioms: []`).

## D. verify(model) ⇒ resolved

`search_retains_object` verifies only if its result equals
`some_row_matches_all(rows, terms)` (A4) — the exists-row, for-all-terms
retention predicate. By R (terms/rows id abstraction, the OR-collapse to
`matches`, the boolean ↔ membership map) the verified function equals
"candidate survives `queryset.filter(models.Q(*term_queries))`" on the tested
inputs; by G-AX the deep model `some_row_matches_all` equals the real Django
single-filter-AND combination over all small match matrices + fuzz + the F2P
scenarios (A-reference). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited combination
model — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: refinement fidelity (this document, G-EQ) and the
combination-model soundness (axiom_check.py, G-AX); there is no consumed
library axiom.

# refinement.md — django__django-12143

The operation-by-operation correspondence between `model.py`'s implementation
(the `is_edited_pk_key` impl region, its verified helpers `match_literal` /
`run_is_digits`, and the deep `recognises` model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `_get_edited_object_pks` (`options.py:1632-1635`)

Gold hunk:
```
- pk_pattern = re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name))
+ pk_pattern = re.compile(
+     r'{}-\d+-{}$'.format(re.escape(prefix), self.model._meta.pk.name)
+ )
  return [value for key, value in request.POST.items() if pk_pattern.match(key)]
```

The changed expression builds a compiled pattern and the unchanged
comprehension filters the POST items by `pk_pattern.match(key)`. The behaviour
modelled is the per-key acceptance decision under the FIXED pattern.

| # | model.py impl op (`is_edited_pk_key`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| R1 | parameters `prefix, pkname, key : List[int]` | `prefix : str`, `self.model._meta.pk.name : str`, the POST `key : str` | R | `str` ↔ `List[int]` code points (mapping.md §2). `pkname` is the explicit positional stand-in for `self.model._meta.pk.name`. |
| A2 | `Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))`, where `recognises` is the spelled-out literal decomposition `prefix · '-' · \d+ · '-' · pkname` (consumed via the `match_literal` / `run_is_digits` loops) | `re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkname)).match(key) is not None` | A-reference | the changed regex operation is modelled **deeply**: `recognises` (the structural decomposition in the `pure` region) and the verified helper loops ARE the match. There is **no consumed match axiom** — the proof never depends on one. Instead the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `re.escape`-fixed `.match` on boundary+fuzz and asserts `recognises == fixed match` over the scoped POST-key domain (mapping.md §3). `re.escape(prefix)` makes the leading region a LITERAL matcher, which is exactly `prefix_eq(key, prefix)`. |
| R3 | the single boolean `is_edited_pk_key(...)` for one `key` | the comprehension `[value for key, value in request.POST.items() if pk_pattern.match(key)]` | R | the comprehension is an UNCHANGED filter that applies the per-key predicate to each POST item and collects the matching values; it commutes with the change. Modelling the per-key decision pins exactly the behaviour the fix alters (which keys match); the surrounding `.items()` iteration and `value` projection are unchanged structural plumbing. The F2P test observes the resulting `queryset.count()`, which is the number of keys the predicate accepts. |

The discriminating content of the change — `prefix` matched **literally**
(`re.escape`) rather than as a **regex** — lives in `prefix_eq(key, prefix)`
(model) ⇔ `re.escape(prefix)` (real). The pre-patch interpolated `prefix` raw,
so a code point such as `'$'` (U+0024) at the end of `prefix` acted as an
end-anchor; `model_prepatch.py` reproduces that (`label_ends_in_anchor` forces
the leading-region match to fail when `prefix[-1] == '$'`) and **fails** the
postcondition `Result() == recognises(...)`, which is exactly the spec sensing
the change (G-DIFF). On the F2P input `prefix='form$'`, `key='form$-0-uuid'`:
`recognises` is `True` (literal label present), the real fixed match is `True`,
but the raw-prefix pre-fix match is `False` — so the pre-fix code drops the
edited row (the data-loss bug), while the fix recognises it.

## B. The verified helpers (proof scaffolding, not separate change sites)

`match_literal` and `run_is_digits` are verified helper functions whose
postconditions are `Result() == prefix_eq(key.drop(off), lit)` and
`Result() == all_digits(key.take(hi).drop(lo))`. They have **no repo
counterpart** — they are the loop-decomposition of the single per-key decision
that lets Nagini discharge `recognises` with stable function-call facts (the
index-recursive predicates do not auto-unfold across three sequential loops, so
each region is computed by a contracted helper, mapping.md §1). They introduce
no new behaviour: composing them inside `is_edited_pk_key` reconstructs exactly
the `recognises` conjunction (asserted at the tie-up step in the impl). No R/A/I
row is needed for repo correspondence; they are entirely inside the proof.

## C. No kind-3 (unexpressible-changed-op) steps

Every repo-corresponding step above is R, A-reference, or I. The one operation
that genuinely *changed* — the interpretation of `prefix` inside the compiled
pattern — is modelled **deeply** (the spelled-out literal decomposition
`recognises` / `prefix_eq`, step A2, an **A-reference**), not hidden behind an
axiom about the function under change. There is **no consumed `@ContractOnly`
axiom** in this bundle: the only callee touched by the change (the `re` match)
IS the changed operation and is therefore an A-reference validated by G-AX, not
a consumed axiom (per SPEC_GUIDE §3 / directive 7 — never axiomatize the
operation the patch changes).

## D. verify(model) ⇒ resolved

`is_edited_pk_key` verifies only if its result equals the exact literal
structural decomposition `recognises` with the leading label matched
character-for-character (A2). By R (str ↔ List[int]; the unchanged comprehension
filter, R3) the verified per-key decision equals
`re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkname)).match(key) is not
None` on the realistic POST-key domain; by G-AX the deep model `recognises`
equals the real fixed match (A-reference) over that scoped domain, and the F2P
discrimination (`prefix='form$'`) is exhibited. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited A-reference — and the gold patch resolves (G-RESOLVE). The single
trust point is refinement fidelity + the A-reference soundness (this document +
G-AX); there are no consumed axioms.

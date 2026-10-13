# refinement.md — django__django-11555

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`expandOrdering` `do` block and the deep `expandItems`/`itemContribution` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **none** here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (the recursive resolver `resolve` is a FREE input, not
an axiom — mapping.md §3.1). `patch.diff` is the gold patch **verbatim** (applies
at `base_commit`, resolves — G-RESOLVE).

## A. The default-ordering expansion loop — `SQLCompiler.find_ordering_name`

Gold hunk (`django/db/models/sql/compiler.py:724`), the loop that builds the
expanded ordering for a relation's default ordering:
```python
  results = []
  for item in opts.ordering:
+     if isinstance(item, OrderBy):
+         results.append((item, False))
+         continue
      results.extend(self.find_ordering_name(item, opts, alias, order, already_seen))
  return results
```

| # | Solution.lean impl op (`expandOrdering`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `items : List Item`, `resolve : Name → List Pair` | `opts.ordering` (the spec list) and the recursive call `self.find_ordering_name(item, …)` on a name item | R | type bijection (mapping.md §2): `list`↔`List Item` (`OrderBy`↔`expr`, `str`↔`name`); the unchanged recursive resolution of a name item ↔ the free total `resolve`. |
| A2 | `let mut result := []` ; `return result` | `results = []` ; `return results` | I | identical accumulator init + return; `List`↔`list`. |
| A3 | backward `while i>0` over `items` (`i` from `items.length` to 0), prepending each contribution | `for item in opts.ordering:` accumulating left-to-right with `extend`/`append` | I | the backward fold with `++`-prepend computes exactly the in-order concatenation `expandItems` (the loop invariant `result = expandItems resolve (items.drop i)` proves this); `append(x) ≡ extend([x])`. |
| A4 | `match it with \| .expr e => [(e, false)] \| .name n => resolve n` | `if isinstance(item, OrderBy): results.append((item, False)); continue` **else** `results.extend(self.find_ordering_name(item, …))` | I | **the changed op**, modeled deeply: an `OrderBy` item contributes the singleton `[(e, false)]` (≡ `append((item, False))` then `continue`); any other item contributes `resolve n` (≡ `extend(find_ordering_name(item,…))`). This branch is the entire behavioural content of the fix. |
| A5 | `result := contribution ++ result` | `results.append(...)` / `results.extend(...)` | I | per-item accumulation ↔ `++`; identical for both branches. |

Discriminating content of the change — an order *expression* item is taken
as-is (`[(e, false)]`) instead of being routed through the field-name resolution
path — lives in A4: the `.expr e => [(e, false)]` branch (model) ⇔ the inserted
`if isinstance(item, OrderBy): results.append((item, False)); continue` (real).

The pre-patch code had **no** such branch: every item, including an `OrderBy`,
was passed to `self.find_ordering_name(item, …)`, whose first step
`get_order_dir(name, …)` indexes `name[0]` and so raises `TypeError` on a
non-string `OrderBy` (the reported crash). `Solution_prepatch.lean` reproduces
this by contributing `resolve e` for an `.expr e` item (routing the expression
through name resolution) and therefore **fails** the postcondition
`out = expandItems resolve items` exactly on the `.expr` clause (G-DIFF) — the
unsolved goal is `resolve e = [(e, false)]`, which is the precise bug.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — how an
order-expression item is dispatched in the loop — is modeled **deeply** (the
spelled-out `itemContribution` branch and the verified backward fold, step A4),
not hidden behind an axiom about the function under change. There is no consumed
axiom and no A-reference: the only unchanged callee (`resolve`, the recursive
name resolution) is a FREE universally-quantified input (mapping.md §3.1), so it
owes no contract and G-AX has nothing to check.

## C. verify(Solution) ⇒ resolved

`expandOrdering` verifies only if its output equals the in-order concatenation
`expandItems resolve items` in which an order-expression item contributes exactly
`[(e, false)]` (A4) — for EVERY recursive resolver `resolve`. By R
(`opts.ordering ↔ List Item`, the recursive call ↔ `resolve`, the resulting
tuple ↔ `Pair`) the verified loop equals the gold-patched loop body on every
ordering specification; by G-CONF the R/I transliteration of the fold agrees with
`patch.diff`'s behaviour on ≥10⁵ fuzzed specifications (incl. the F2P
`OrderBy(F(...))` scenario). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this doc,
G-EQ + G-CONF); there is no axiom-soundness obligation (no axioms).

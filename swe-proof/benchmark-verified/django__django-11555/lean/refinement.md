# refinement.md — django__django-11555

Maps every operation in `implementation_expandOrdering` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Operation correspondence

| # | Lean impl op | patch.diff / base code op | tag | note |
|---|---|---|---|---|
| 1 | `let mut results : List (OrderExpr × Bool) := []` | `results = []` | I | accumulator init |
| 2 | `for item in items do …` | `for item in opts.ordering:` | R | `opts.ordering` (tuple of `str`/`OrderBy`) ↔ `List OrderingItem`; per mapping.md bijection |
| 3 | `match item with \| .expression e => …` | `if isinstance(item, OrderBy):` | R | the added dispatch; `OrderingItem.expression` ↔ `isinstance(item, OrderBy)` true-branch |
| 4 | `results := results ++ [(e, false)]` | `results.append((item, False)); continue` | R | append the directive directly, flag literal `False`; `++[…]` ↔ `append`; `continue` skips the resolver (modeled by not falling through to op 6) |
| 5 | `\| .fieldRef _ => …` | `else` (item is not `OrderBy`) | R | the string-item path |
| 6 | `results := results ++ resolveFieldRef item` | `results.extend(self.find_ordering_name(item, opts, alias, order, already_seen))` | A-reference | UNCHANGED recursive resolver; deep-modeled as the opaque `resolveFieldRef`, validated == real callee by G-AX. `extend` ↔ `++`. |
| 7 | `return results` | `return results` | I | |

## Notes
- Every step is R, A-reference, or I — no changed-inexpressible op.
- The ONLY behavior the patch changes is the dispatch (ops 3–5): pre-patch,
  every item went to op 6; post-patch, expression items take ops 3–4 and skip
  op 6. The prepatch `Solution_prepatch.lean` removes ops 3–5, sending every
  item to the resolver — exactly the bug, so its `correct_*` is unclosable
  (G-DIFF).
- No A-consumed axiom: the spec `result = items.flatMap expandOrderingItem` is a
  pure structural relation; the loop↔flatMap equality is proved by induction
  (`List.forIn_cons`), consuming no property of `resolveFieldRef`. The callee
  appears identically on both sides (spec helper + impl), so it cancels.
- `resolveFieldRef` is the changed function's own recursive self-call on a
  string item, which is UNCHANGED on that path; it is therefore an A-reference,
  not a consumed axiom (no dead axiom shipped).

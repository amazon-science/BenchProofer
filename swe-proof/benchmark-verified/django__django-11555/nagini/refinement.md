# refinement.md — django__django-11555

The operation-by-operation correspondence between `model.py`'s implementation
(the `expand_default_ordering` impl region, the deep `expanded`/`contribution`
model, and the `resolve_name`/`resolve_name_seq` axiom) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed**, the proof uses the axiom's `Ensures`; **A-reference**,
a deep model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The default-ordering expansion loop — `find_ordering_name` (`django/db/models/sql/compiler.py:723-729`)

Gold hunk (inserted into the `for item in opts.ordering:` loop):
```
              results = []
              for item in opts.ordering:
+                 if isinstance(item, OrderBy):
+                     results.append((item, False))
+                     continue
                  results.extend(self.find_ordering_name(item, opts, alias,
                                                         order, already_seen))
              return results
```

| # | model.py impl op (`expand_default_ordering`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `kinds: List[int]`, `ids: List[int]` (index-aligned) | the items of `opts.ordering` | R | each item ↔ `(kinds[k], ids[k])`: `kinds[k]==1` ↔ `isinstance(item, OrderBy)`, `kinds[k]==0` ↔ textual name; `ids[k]` ↔ the item / produced-expression identity (mapping.md §2). |
| A2 | the loop over `i` accumulating `result` | `results = []` / `for item in opts.ordering: …` / `return results` | I | identical control flow: build a list by iterating the items in order. (The model iterates back-to-front and prepends to keep a front-recursive fold; the produced sequence order is identical — `result` after the loop equals `expanded(items)`, the in-order concatenation.) |
| A3 | `if k == 1: piece = [d]` (the item's own identity as a single target) | `if isinstance(item, OrderBy): results.append((item, False)); continue` | A-reference | the changed operation, modeled **deeply**: `contribution(1, id) == PSeq(id)` and the `k==1` branch ARE the pass-through. The already-formed expression contributes exactly itself, a single target, identity preserved. No consumed axiom stands in for it. G-AX (axiom_check.py) validates the deep model == the real callee: the `Meta.ordering` `OrderBy` appears in the real `find_ordering_name` output as a single `(OrderBy, False)` entry that **is that very object**, in position. The `False` second component matches `(item, False)` and the base case's `…, False` (uniform; mapping.md §2). |
| A4 | `else: piece = resolve_name(state, d)` | `results.extend(self.find_ordering_name(item, opts, alias, order, already_seen))` | A-consumed | the unchanged name-resolution recursion for a textual name. Axiomatized as `resolve_name(state, item_id)` (impl-callable, returns the produced list) pinned to the uninterpreted `resolve_name_seq` (mapping.md §3.2). The proof consumes the structural binding `ToSeq(piece) == resolve_name_seq(d)` ⇒ `ToSeq(piece) == contribution(0, d)`. The value binding is definitionally sound (it over-claims nothing). The axiom additionally carries the two NON-value facts the real callee has: it threads the shared resolution state (the `already_seen` set and the query's accumulated joins, `compiler.py:717-721`) as the RESOURCE `machinery_state(state)`, and it adds the resolved item to that state's account `invocations(state)`. G-AX confirms textual names resolve to ≥1 freshly built `OrderBy` target and that the recursion is never given the `OrderBy` item (`get_order_dir` subscripts it — the pre-patch `TypeError`). |
| A6 | the invocation obligation `invocations(state) == Old(invocations(state)) + name_items(kinds, ids)` | the gold loop applies `self.find_ordering_name` to exactly the non-`OrderBy` items, once each, and to no `OrderBy` item (the `continue` skips it) | A-consumed | the changed operation's OTHER half, and not a value claim. The real recursion is PARTIAL (defined for textual names only) and STATE-CHANGING (each call mutates `already_seen` and grows the query's joins/table references), so WHICH items it is applied to and HOW OFTEN is observable behaviour of the modelled function, not an implementation detail: an extra application to an expression item reproduces the reported crash, and a duplicate application for one name perturbs the join bookkeeping. The account is a MULTISET, so once-per-name is pinned without pinning the walk order (the real function does not guarantee one, and the model in fact walks back-to-front). `machinery_state` is an abstract predicate — a resource with no constructor — because the compiler threads exactly ONE such state per expansion; that is what makes the account complete rather than merely bookkept. Oracle-checked by `conformance_check.py` (G-CONF), which records every depth-1 machinery call the real loop makes and reports a leftover as a disagreement. |
| A5 | `result = piece + result` (and `return result`) | `results.extend(…)` / `results.append((…, False))` then `return results` | I | accumulate each item's contribution into the output list, in order, and return it. `extend` ↔ concatenating the multi-target `resolve_name` piece; `append` ↔ concatenating the singleton pass-through piece; both are list concatenation. |

The discriminating content of the change — an already-formed `OrderBy` item is
**passed through verbatim** as its own single target instead of being fed to the
name-resolution machinery (which subscripts it and crashes) — lives in
`contribution(1, id) == PSeq(id)` (model) ⇔ the
`if isinstance(item, OrderBy): results.append((item, False)); continue` branch
(real). The pre-patch loop routed *every* item through the recursion;
`model_prepatch.py` reproduces that (every item → `resolve_name(d)`) and
**fails** the postcondition `ToSeq(Result()) == expanded(ToSeq(kinds), ToSeq(ids))`
on the `k==1` items (the loop invariant cannot prove
`resolve_name_seq(d) == PSeq(d)`), which is exactly the spec sensing the change
(G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, A-consumed, or I. The one operation that
genuinely *changed* — the `OrderBy` pass-through — is modeled **deeply**
(`contribution(1, ·) == PSeq(·)`, the `k==1` branch, step A3, an
**A-reference**), not hidden behind an axiom about the function under change.
The only consumed axiom, `resolve_name`/`resolve_name_seq` (**A-consumed**, step
A4), covers the **unchanged** recursive name machinery the loop still invokes
for textual names; it makes no content claim (`Ensures(True)` sequence) and is
therefore tautologically sound.

## C. verify(model) ⇒ resolved

`expand_default_ordering` verifies only if BOTH obligations hold.

*The output obligation.* Its output equals the in-order concatenation of each
item's contribution — and for a kind==1 item that contribution is the item's own
single identity `PSeq(id)` (A3), not the opaque `resolve_name_seq(id)`. Because
`resolve_name_seq` is uninterpreted, no implementation can prove
`resolve_name_seq(id) == PSeq(id)`, so routing an already-formed expression
through the name machinery cannot satisfy it. That is the pre-patch bug being
sensed (G-DIFF).

*The invocation obligation.* The applications of the machinery the shared
resolution state has accumulated are exactly the name items, once each (A6). This
is what pins the half of the change that is not a value: the real recursion is
partial and state-changing, so an implementation that produces the right targets
while ALSO applying the machinery to an already-formed expression, or twice to one
name, is not the specified behaviour. Both were measured as real correctness
failures — the first reproduces the reported `TypeError` (F2P fails), the second
regresses `test_related_ordering_duplicate_table_reference` (P2P fails) — so this
obligation is load-bearing for `verify ⇒ resolved`, not decoration. It is not
escapable by resolving against a carrier of the implementation's own making:
`machinery_state` is an abstract predicate (a resource with no body and no
constructor), which mirrors the repository having exactly one resolution state per
expansion, so every application an implementation can reach is in the account.

By R (items ↔ `(kind, id)`; the uniform `False` second component abstracted away)
a verified loop therefore equals the gold loop on the modeled items: each
already-formed `OrderBy` becomes `(item, False)` passed through (A3), each textual
name expands through the unchanged recursion exactly once (A4/A6), in order
(A2/A5), and nothing else is resolved at all. By G-AX the deep pass-through model
equals the real callee (A-reference) and the real name machinery meets the
`resolve_name` binding (A-consumed); by G-CONF the depth-1 invocation account
matches the real loop's calls executably. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE; the F2P
`test_order_by_ptr_field_with_default_ordering_by_expression` passes post-gold,
crashes pre-patch). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).

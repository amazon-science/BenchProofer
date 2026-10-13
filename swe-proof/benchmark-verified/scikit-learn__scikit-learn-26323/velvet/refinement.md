# refinement.md — scikit-learn__scikit-learn-26323

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `collectBroadcastTargets` `do` block and the deep `broadcastTargets`/
`selectReal` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** / **A-reference**
(none in this bundle), or **I** (identical concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are no axioms or deep models of outside callees, so **G-AX is
vacuous** (no `axiom_check.py`). Claim: any impl verifying against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The broadcast site — `ColumnTransformer.set_output` (`_column_transformer.py:275`)

Gold hunk (added lines):
```
         for trans in transformers:
             _safe_set_output(trans, transform=transform)

+        if self.remainder not in {"passthrough", "drop"}:
+            _safe_set_output(self.remainder, transform=transform)
+
         return self
```

| # | Solution.lean impl op (`collectBroadcastTargets`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `listed : List Component` | the `transformers` generator value: `trans for _, trans, _ in chain(self.transformers, transformers_) if trans not in {"passthrough","drop"}` | R | the post-filter list of sub-transformers ↔ `List Component` (mapping.md §2). Sentinel strings ↔ `.marker`, estimators ↔ `.real n`. |
| A2 | parameter `extra : Component` | `self.remainder` | R | the remainder slot ↔ `Component` (mapping.md §2): a sentinel remainder ↔ `.marker`, a remainder estimator ↔ `.real n`. |
| A3 | the backward `while` fold building `selectReal listed`: keep each `c` with `isReal c`, drop markers | the `for trans in transformers: _safe_set_output(trans, ...)` loop over the already-sentinel-filtered generator | I | concrete, transliterated by G-CONF. The per-element action `_safe_set_output(trans,...)` is identical on both sides (R, see A5); the modeled observable is membership — exactly the set the loop iterates. |
| A4 | `result := result ++ (if isReal extra then [extra] else [])` — append `extra` iff it is real | `if self.remainder not in {"passthrough","drop"}: _safe_set_output(self.remainder, ...)` | I | the **added** hunk. `isReal extra` ⇔ `self.remainder not in {"passthrough","drop"}`; appending `extra` to the target list ⇔ the new conditional dispatch. This is the single behavioural change. |
| A5 | (no node — factored out) | `_safe_set_output(c, transform=transform)` per selected component | R | the per-component configuration action is **unchanged** by the patch and applied identically to every selected component; identity on `Component` (mapping.md §2). The F2P observable is *which* components are configured (now including the remainder), which is the ordered `out` list. |
| A6 | `out` returned (`List Component`) | `return self` | R | `set_output` returns `self`; the modeled return is the broadcast target list it built, the carrier of the changed behaviour (mapping.md §2). |

Discriminating content of the change — a real `remainder` estimator now receives
the output-config broadcast — lives in `broadcastTargets listed extra =
selectReal listed ++ (if isReal extra then [extra] else [])` (model) ⇔ the added
`if self.remainder not in {...}: _safe_set_output(self.remainder, ...)` (real).
The pre-patch never reached the remainder; `Solution_prepatch.lean` drops the
A4 append and **fails** the `out = broadcastTargets listed extra` and
`isReal extra = true → out = selectReal listed ++ [extra]` postconditions
exactly when `extra` is a real estimator (G-DIFF) — which is the configuration
the F2P `test_remainder_set_output` exercises (`remainder=VarianceThreshold()`).

## B. No A (axiom / deep-model) steps

There is **no consumed axiom** and **no A-reference deep model of an outside
callee**. The only callee in the changed region, `_safe_set_output`, is
unchanged and applied identically to every selected component (A5, an R
refinement); modeling it deeply would ship a dead model the proof never uses.
The behavioural content lives entirely in the **selection**, modeled deeply by
`broadcastTargets`/`selectReal` (pure region) and verified by the loop.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — extending the
broadcast to the remainder estimator — is modeled **deeply** (the conditional
append A4, an I op over the `broadcastTargets` model), not hidden behind an
axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`collectBroadcastTargets` verifies only if its output equals the exact selection
`selectReal listed ++ (if isReal extra then [extra] else [])` (A3+A4): the real
listed sub-transformers, then the remainder iff it is a real estimator. By R
(`trans/remainder ↔ Component`, sentinel ↔ `.marker`, `_safe_set_output`/`return
self` identities) the verified selection equals the components the patched
`set_output` calls `_safe_set_output` on; by G-CONF the R/I transliteration of
the fold + conditional append agrees with `patch.diff`'s selection behaviour on
≥10⁵ inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms to trust (G-AX vacuous).

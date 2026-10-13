# refinement.md — matplotlib__matplotlib-24627

Operation correspondence between `implementation_clearAxes` (Solution.lean impl
region) and `patch.diff`. Every row is tagged **R** (type refinement), **I**
(identical concrete op), **A-consumed**, or **A-reference**. No A rows here.

| # | Lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `let oldChildren := artists` | `old_children, self._children = self._children, []` (the `old_children` capture) | R | `self._children : list[Artist]` ↔ `artists : List Artist`; snapshot of the prior child list. Order-preserving list ↔ list. |
| 2 | `let mut newChildren : List Artist := []` | `self._children = []` (the new binding) | R | the fresh child list; `[] ↔ []`. Returned as `result.1`. |
| 3 | `for chld in oldChildren do … ` | `for chld in old_children:` | I | iteration over the captured former children, in order. |
| 4 | `let chld := { chld with axes := none, figure := none }` | `chld.axes = chld.figure = None` | R | in-place mutation of two reference fields ↔ functional record update; `None ↔ none` on `Option Nat`. All other fields (`data`) preserved by `with`-update, matching that only `.axes`/`.figure` are assigned. |
| 5 | `formerChildren := formerChildren ++ [chld]` | (the mutated `chld` remains in `old_children`, observed via each artist's now-`None` `.axes`/`.figure`) | R | accumulates the deparented former children in input order; models the post-state of the artists the loop mutates. Returned as `result.2`. |
| 6 | `return (newChildren, formerChildren)` | resulting `self._children` (=`[]`) and the deparented former children | R | pairs the two observable post-states; the spec pins both. |

## Notes
- No changed op is inexpressible: the entire edit is list reset + per-element
  two-field reset, modeled deeply.
- No consumed axiom and no deep-model reference (§3): the operation calls no
  unchanged external callee. `conf_skip = false` (impl region is all R/I).
- The R/I legs are mechanically refuted by G-CONF (`conformance_check.py`):
  oracle = faithful post-patch replica, shadow = op-for-op transliteration of
  the impl region.

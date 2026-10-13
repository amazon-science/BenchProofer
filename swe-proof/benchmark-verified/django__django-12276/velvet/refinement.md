# refinement.md — django__django-12276

Correspondence between `Solution.lean`'s `useRequiredAttribute` impl and
`patch.diff`. The gold patch MOVES `use_required_attribute` from
`ClearableFileInput` up to its parent `FileInput`, body
`return super().use_required_attribute(initial) and not initial`. `patch.diff` is
the gold verbatim (applies at base_commit, resolves — G-RESOLVE).

## A. The moved method — `FileInput.use_required_attribute`

Gold hunks: an addition into `class FileInput` and a deletion of the identical
method from `class ClearableFileInput`:
```
+    def use_required_attribute(self, initial):
+        return super().use_required_attribute(initial) and not initial
...
-    def use_required_attribute(self, initial):
-        return super().use_required_attribute(initial) and not initial
```
Net effect: `FileInput` (and every subclass, incl. `ClearableFileInput`) now
applies the `and not initial` suppression. Before the patch, `FileInput`
inherited only the GRANDPARENT `Widget.use_required_attribute` (no suppression).

| # | Solution.lean impl op (`useRequiredAttribute`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `hasInitial : Bool` | parameter `initial`, used via `not initial` | R | Python truthiness of `initial` ↔ Lean `Bool` (mapping.md §2). |
| A2 | `inheritedRequiredDecision hasInitial` | `super().use_required_attribute(initial)` | **A-consumed** | unchanged inherited callee (`Widget.use_required_attribute`, `widgets.py:275`), modeled as an OPAQUE free function with NO asserted value. The proof/structure consumes it as an opaque term; nothing is claimed about its return, so G-AX has nothing to check (mapping.md §3). |
| A3 | `&& !hasInitial` | `and not initial` | **I** | identical concrete op — the discriminating behavior the fix introduces, modeled deeply (a pure boolean conjunction). |
| A4 | `(… && …)` | `… and …` | I | short-circuit conjunction over two bools ≡ `&&`. |

No kind-3 (changed inexpressible) op. The one A-consumed step is the opaque
inherited callee; the discriminating change (`&& !hasInitial`) is I (deeply
modeled, G-CONF-testable).

## B. verify(Solution) ⇒ resolved

`useRequiredAttribute` verifies only if
`out = inheritedRequiredDecision hasInitial && !hasInitial` (A2-A4). By R (the
truthiness bijection, mapping.md §2) the verified result equals the patched
`super().use_required_attribute(initial) and not initial` on the real widget.

The F2P tests:
  - `test_use_required_attribute`: `use_required_attribute(None)` → `True`
    (no initial: inherited decision `True`, `not None` `True` ⇒ `True`);
    `use_required_attribute('resume.txt')` → `False` (initial present:
    `not 'resume.txt'` `False` ⇒ `False`). The spec pins exactly this: with the
    inherited decision opaque, the result MUST be `False` whenever
    `hasInitial = true`, and equals the inherited decision when `hasInitial =
    false`.
  - `test_filefield_with_fileinput_required`: a `FileInput` field renders
    `required` with no initial, and WITHOUT `required` once `initial` is set —
    the rendered-attribute consequence of the same boolean.

## C. Prepatch fails on the discriminating clause (G-DIFF)

`Solution_prepatch.lean` (byte-identical spec) returns just
`inheritedRequiredDecision hasInitial` — the pre-patch `FileInput` inherited only
`Widget`'s decision, with NO `and not initial`. Against the identical spec this
leaves the unsolved goal

```
inheritedRequiredDecision hasInitial = (inheritedRequiredDecision hasInitial && !hasInitial)
```

which fails whenever `inheritedRequiredDecision hasInitial = true` and
`hasInitial = true` — precisely the missing `&& !hasInitial` conjunct, the bug
the issue describes (a file field with existing initial data wrongly advertising
`required`).

## D. Trust surface

Only the type bijection (mapping.md §2) and the OPAQUE inherited callee (A2).
The opaque callee asserts nothing about its value, so it cannot mask a wrong
impl: the spec still forces the `&& !hasInitial` structure regardless of the
inherited decision. G-CONF differential-tests the I leg (`&& !hasInitial`) with
the inherited decision fuzzed as a free boolean. No axiom_check needed (G-AX
skip — nothing asserted to validate).

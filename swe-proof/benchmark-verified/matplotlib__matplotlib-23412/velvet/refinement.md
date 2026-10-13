# refinement.md — matplotlib__matplotlib-23412

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `renderDashPattern` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (a deep model validated == a real callee
by G-AX), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The draw-time dash-pattern construction — `Patch.draw` (`lib/matplotlib/patches.py:585`)

Gold hunk:
```
-        # Patch has traditionally ignored the dashoffset.
-        with cbook._setattr_cm(
-                 self, _dash_pattern=(0, self._dash_pattern[1])), \
+
+        with cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern)), \
              self._bind_draw_path_function(renderer) as draw_path:
```

The patch changes the `_dash_pattern` value installed for the body of `draw`
from `(0, self._dash_pattern[1])` (offset forced to 0) to `self._dash_pattern`
(offset preserved). This installed value is consumed by
`gc.set_dashes(*self._dash_pattern)` at `patches.py:552`.

| # | Solution.lean impl op (`renderDashPattern`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `phase : Int` | `self._dash_pattern[0]` (the scaled dash offset, a `float`) | R | offset `float` ↔ `Int`; the tested behaviour is offset-preserved-vs-zero, a precision-independent value distinction (mapping.md §2). |
| A2 | parameter `onoff : List Int` | `self._dash_pattern[1]` (the scaled on/off sequence) | R | sequence of `float`/`None` ↔ `List Int`, element-wise (mapping.md §2). |
| A3 | `return phase :: onoff`, yielding `out = phase :: onoff` (`out.head? = some phase`, `out.tail = onoff`) | the post-patch tuple `self._dash_pattern == (self._dash_pattern[0], self._dash_pattern[1])` installed by `cbook._setattr_cm` | R + I | identical construction under the tuple↔(head,tail) refinement: `out.head? = some phase` ↔ component 0 is `self._dash_pattern[0]` (the offset, NOT 0); `out.tail = onoff` ↔ component 1 is `self._dash_pattern[1]` (the on/off sequence, copied verbatim). The model builds exactly the value the patch installs. |

The discriminating content of the change — the offset component is the patch's
**own** offset rather than the literal `0` — lives in `out.head? = some phase`
(equivalently the head of `out = phase :: onoff`) in the model ⇔ the
`_dash_pattern=(self._dash_pattern)` install in the real code. The pre-patch
code installs `(0, self._dash_pattern[1])`; `Solution_prepatch.lean` reproduces
that (`return (0 : Int) :: onoff`) and **fails** the postconditions
`out = phase :: onoff` and `out.head? = some phase` whenever `phase ≠ 0` — which
is exactly the spec sensing the change (G-DIFF; verified: the prepatch leaves the
goals `0 :: onoff = phase :: onoff` and `(0 :: onoff).head? = some phase`
unsolved). The F2P test exercises `phase = 6 ≠ 0`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
offset component of the installed dash pattern (`0` → `self._dash_pattern[0]`) —
is modeled **directly and concretely** (`out.head? = some phase` / the head of
`out = phase :: onoff`), not hidden behind any axiom. There are no axioms in this
bundle: the change is pure tuple construction from values already held on the
object, so there is no unchanged callee to axiomatize and no deep model to
validate against a real callee. Consequently there is **no A-consumed and no
A-reference** row, and no `axiom_check.py` (nothing for G-AX to run).

## C. verify(model) ⇒ resolved

`renderDashPattern` verifies only if its output's head equals the supplied phase
(A3, `out.head? = some phase`) and its tail equals the supplied on/off sequence
verbatim (`out.tail = onoff`, equivalently `out = phase :: onoff`). The on/off
input is read-only — `onoff` is not a `mut` parameter and is reproduced exactly
in the tail (directive 5: a wrong impl cannot satisfy the postcondition while
silently dropping or altering the on/off sequence, because `out.tail = onoff`
pins it). The result is grounded in the inputs (`out = phase :: onoff`), not in
an ungrounded oracle (directive 8): there is no answer-key to echo. By R (offset
`float`↔`Int`, on/off sequence↔`List Int`, tuple↔(head,tail)) the verified
construction equals the post-patch `_dash_pattern=(self._dash_pattern)` installed
for the draw, which `gc.set_dashes` then hands to the renderer with the patch's
own offset. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The sole trust point is refinement fidelity (this document, G-EQ; mechanically
re-checked by G-CONF over 100 050 fuzzed pairs, 0 disagreements); there is no
axiom-soundness trust point because there are no axioms.

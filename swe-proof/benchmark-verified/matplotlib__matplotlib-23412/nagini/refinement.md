# refinement.md — matplotlib__matplotlib-23412

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_dash_pattern` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == a real callee by G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

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

| # | model.py impl op (`render_dash_pattern`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `phase: int` | `self._dash_pattern[0]` (the scaled dash offset, a `float`) | R | offset `float` ↔ `int`; the tested behaviour is offset-preserved-vs-zero, a precision-independent value distinction (mapping.md §2). |
| A2 | parameter `onoff: List[int]` | `self._dash_pattern[1]` (the scaled on/off sequence) | R | sequence of `float`/`None` ↔ `List[int]`, element-wise (mapping.md §2). |
| A3 | `result = [phase]` then append each `onoff[i]` in order, yielding `ToSeq(Result()) == PSeq(phase) + ToSeq(onoff)` | the post-patch tuple `self._dash_pattern == (self._dash_pattern[0], self._dash_pattern[1])` installed by `cbook._setattr_cm` | R + I | identical construction under the tuple↔(head,tail) refinement: `Result()[0] == phase` ↔ component 0 is `self._dash_pattern[0]` (the offset, NOT 0); `Result()[1:]` ↔ component 1 is `self._dash_pattern[1]` (the on/off sequence, copied verbatim). The model builds exactly the value the patch installs. |

The discriminating content of the change — the offset component is the patch's
**own** offset rather than the literal `0` — lives in `Result()[0] == phase`
(equivalently the head of `ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff))`)
in the model ⇔ the `_dash_pattern=(self._dash_pattern)` install in the real
code. The pre-patch code installs `(0, self._dash_pattern[1])`;
`model_prepatch.py` reproduces that (`result = [0]`) and **fails** the
postcondition `ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff))` (and the
companion `Result()[0] == phase`) whenever `phase != 0` — which is exactly the
spec sensing the change (G-DIFF). The F2P test exercises `phase = 6 != 0`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
offset component of the installed dash pattern (`0` → `self._dash_pattern[0]`) —
is modeled **directly and concretely** (`Result()[0] == phase`), not hidden
behind any axiom. There are no `@ContractOnly` axioms in this bundle: the change
is pure tuple construction from values already held on the object, so there is
no unchanged callee to axiomatize and no deep model to validate against a real
callee. Consequently there is **no A-consumed and no A-reference** row, and no
`axiom_check.py` (nothing for G-AX to run).

## C. verify(model) ⇒ resolved

`render_dash_pattern` verifies only if its output's head equals the supplied
phase (A3, `Result()[0] == phase`) and its tail equals the supplied on/off
sequence verbatim (`ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff))`), with
the on/off input held read-only at half permission (directive 5: a wrong impl
cannot overwrite `onoff` to satisfy the postcondition vacuously — it is required
AND ensured at `Acc(list_pred(onoff), 1/2)` and pinned by
`ToSeq(onoff) == Old(ToSeq(onoff))`). By R (offset `float`↔`int`, on/off
sequence↔`List[int]`, tuple↔(head,tail)) the verified construction equals the
post-patch `_dash_pattern=(self._dash_pattern)` installed for the draw, which
`gc.set_dashes` then hands to the renderer with the patch's own offset. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The sole trust point
is refinement fidelity (this document, G-EQ); there is no axiom-soundness trust
point because there are no axioms.

# refinement.md — pytest-dev__pytest-5262

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `textStreamMode` `do` block plus the deep `stripped`/`stripStep` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == the real callee by G-AX), or **I** (identical concrete op). Every
step is R, A, or I — there is no kind-3 (inexpressible changed op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A-reference leg + this narrative are audited by **G-AX** and **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change site — the new `mode` property of `EncodedFile`

Gold hunk (`src/_pytest/capture.py`):
```
+ @property
+ def mode(self):
+     return self.buffer.mode.replace("b", "")
```

| # | Solution.lean impl op (`textStreamMode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `rawMode : List Char` | `self.buffer.mode` — the wrapped stream's mode descriptor (`str`) read inside the property | R | `str ↔ List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. The accessor is read as input data, not a consumed callee (mapping.md §3). |
| 2 | result is `stripped rawMode`: the per-code-point image dropping every `'b'` and preserving the rest in order, computed by the backward `while` fold | `.replace("b", "")` applied to that descriptor | A-reference + I | the changed string op is modeled **deeply**: `stripped`/`stripStep` (pure region) and the verified loop ARE the substitution. The fold ops (`stripStep c`, `++`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `str.replace("b", "")` is the **A-reference** G-AX validates over boundary + fuzz. mapping.md §3. |
| 3 | `result` returned (`List Char`) | the property's `return` value (`str`) | R | identity on character content; the F2P test inspects characters of the returned descriptor (`"b" not in sys.stdout.mode`). |

Discriminating content of the change — the binary marker code point `'b'` is
**removed** rather than passed through — lives in `stripStep 'b' = []` (model) ⇔
the `.replace("b", "")` step (real). The pre-patch property did not exist;
attribute access fell through `__getattr__` to the wrapped stream, returning the
descriptor **unchanged** (marker preserved). `Solution_prepatch.lean` reproduces
that identity delegation and **fails** `out = stripped rawMode` on any descriptor
carrying the marker (G-DIFF) — exactly the discriminator the F2P test
`test_capfd_sys_stdout_mode` (`assert "b" not in sys.stdout.mode`) exercises.

## No consumed axioms, no kind-3 steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the descriptor substitution — is modeled **deeply** (the spelled-out fold
`stripped`, step 2, an A-reference + I), not hidden behind an axiom about the
function under change. There is no consumed `axiom` and no `:|` stub: the
property reads its only callee (`self.buffer.mode`) purely as the modeled input
`rawMode`, so its value is fuzzed by G-CONF rather than pinned by a contract.

## verify(Solution) ⇒ resolved

`textStreamMode` verifies only if its output equals the exact per-code-point
substitution that drops every `'b'` (step 2). By R (`str ↔ List Char`, content
identities of the read and the return) the verified function equals
`self.buffer.mode.replace("b", "")` on the tested descriptors; by G-AX the deep
model `stripped` equals the real `str.replace("b", "")` (A-reference); by G-CONF
the R/I transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and an audited deep model — and the gold patch
resolves (G-RESOLVE). The single trust point is the A-reference fidelity (G-AX)
plus refinement fidelity (this doc, G-EQ + G-CONF).

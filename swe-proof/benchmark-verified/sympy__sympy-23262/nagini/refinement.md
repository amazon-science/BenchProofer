# refinement.md — sympy__sympy-23262

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_container` impl region plus the deep `joined` / `rendered` /
delimiter models in the `pure` region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee semantics by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed function — `_recursive_to_string` (`sympy/utilities/lambdify.py:948`)

The change is confined to the iterable branch of `_recursive_to_string`, where
a container's surface source text is assembled as
`left + ', '.join(_recursive_to_string(doprint, e) for e in arg) + right`.

Gold hunk (lines 959 / 961):
```
-            left, right = "[]"        # list
+            left, right = "[", "]"
-            left, right = "()"        # tuple
+            left, right = "(", ",)"
```
The pre-patch `left, right = "()"` unpacks the 2-character string `"()"` into
`left = "("`, `right = ")"`: the tuple closing delimiter is the lone `)` with no
trailing comma, so a one-element tuple serialises as `"(" + e + ")"` (which
re-parses to the bare element `e`, collapsing the tuple). The fix sets the tuple
delimiter pair to `("(", ",)")`, so a one-element tuple serialises as
`"(" + e + ",)"`, which re-parses to a one-element tuple. (The list hunk
`"[]"` → `"[", "]"` is the analogous explicit-pair rewrite; it is behaviourally
identical to the old `"[]"` unpack — `left = "["`, `right = "]"` either way — and
is included for symmetry.)

| # | model.py impl/pure op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `elems: PSeq[PSeq[int]]` — the elements' already-rendered source fragments | the values `_recursive_to_string(doprint, e) for e in arg` — each element's recursively-rendered source string | R + A-reference | `str` ↔ `PSeq[int]` of code points (mapping.md §2). Producing each fragment is UNCHANGED recursive machinery the patch does not touch, so each is taken as a given input; the deep model is the assembly *over* them. |
| 2 | `is_paren: bool` | the dynamic type test `isinstance(arg, tuple)` vs `isinstance(arg, list)` | R | the boolean selects the container kind; `is_paren == True` ↔ the `tuple` branch, `False` ↔ the `list` branch (mapping.md §2). |
| 3 | `left = PSeq(lparen())` / `PSeq(lbracket())`; `right = PSeq(comma(), rparen())` / `PSeq(rbracket())` | `left, right = "(", ",)"` (tuple) / `left, right = "[", "]"` (list) | I | the literal delimiter pair, character-for-character: `'(' = 40`, `')' = 41`, `'[' = 91`, `']' = 93`, `',' = 44`. The parenthesis kind's `right` is the two code points `[44, 41]` = `",)"`; this is the single behavioural change. |
| 4 | `body = ', '`-join fold over `elems` (the front-recursive `joined`, built back-to-front) | `', '.join(_recursive_to_string(doprint, e) for e in arg)` | I + A-reference | the separator-join is unchanged Python `str.join`; the model spells it out deeply (`joined`) and G-AX validates `joined == ", ".join` (A-reference 1). `', '` = `[44, 32]`. |
| 5 | `result = left + body + right` | `left + ', '.join(...) + right` | I + A-reference | string concatenation ↔ `PSeq` `+`. The full assembly `rendered(elems, is_paren) == left + body + right` is validated == the real fixed serialiser text by G-AX (A-reference 2), including the round-trip arity check that a one-element parenthesis container re-parses to a one-element tuple. |

The discriminating content of the change — the tuple closing delimiter `",)"`
(trailing comma) rather than `")"` — lives in `right_delim(True) == PSeq(44, 41)`
(model) ⇔ `right = ",)"` (gold). The pre-patch closing delimiter `")"`
(`PSeq(41)`) is reproduced in `model_prepatch.py`, which **fails** the
postcondition `Result() == rendered(elems, is_paren)` (and the explicit trailing-
comma / single-element-arity clauses): exactly the spec sensing the change
(G-DIFF).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — the tuple delimiter pair, hence the surface-assembly text — is
modelled **deeply** (the spelled-out delimiter selection + the `joined` fold +
the `rendered` concatenation in the `pure` region, pinned exactly by the spec
and consumed in `render_container`), not hidden behind an axiom about the
function under change: there is **no `@ContractOnly` axiom** at all. The deep
model is validated == the real Python `', '.join` + delimiter concatenation
(both **A-reference**) by axiom_check.py (G-AX). The element-fragment production
(unchanged recursive `_recursive_to_string` machinery) is the only opaque part,
and it is taken as a given input, not modelled.

## Termination obligation (total correctness)

Nagini is a partial-correctness verifier by default: a non-terminating
implementation (bare self-recursion, an endless loop) satisfies every
`Ensures` vacuously while sharing the spec byte-for-byte — a wrong
implementation the spec would otherwise admit. The real serialiser always
answers: assembling a finite container literal from finitely many fragments is
a bounded computation. The spec therefore carries
`Requires(MustTerminate(2))` on `render_container` (consumed in the impl loop
by `Invariant(MustTerminate(i))`, with `i` the strictly decreasing,
bounded-below measure). With termination required and the full functional
postcondition `Result() == rendered(elems, is_paren)`, any verifying same-spec
implementation must terminate and return exactly the pinned text — the spec is
functionally complete on its domain.

## verify(model) ⇒ resolved

`render_container` verifies only if its output equals
`rendered(elems, is_paren)` — i.e. the exact `left + ", "-join + right` assembly
with the tuple closing delimiter `",)"` (steps 3–5) — and only if the explicit
clauses hold: the parenthesis kind ends with `',' ')'` and a one-element
parenthesis container is exactly `'(' + elem + ',)'`. By R (`str` ↔ `PSeq[int]`,
the `isinstance` kind test ↔ `is_paren`) and the A-reference validations (G-AX:
`joined == ", ".join`, `rendered ==` the real fixed serialiser text, and the
one-element parenthesis container re-parses to a 1-tuple), the verified assembly
equals what the gold-patched `_recursive_to_string` emits on the tested inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited Python join — and the gold patch
resolves (G-RESOLVE). The trust point is exactly refinement fidelity (this
document, G-EQ) plus the G-AX-checked equality of the deep model to Python's
own `str.join`/concatenation; there is no axiom-soundness trust point because
there is no consumed axiom.

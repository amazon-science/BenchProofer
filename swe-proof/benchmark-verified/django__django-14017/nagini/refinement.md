# refinement.md — django__django-14017

The operation-by-operation correspondence between `model.py`'s implementation
(the `combine` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`/`Exsures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are NO axioms in this bundle:
every step below is R or I (mapping.md §3).

## A. The combination site — `Q._combine` (`django/db/models/query_utils.py:42`)

Gold hunk (line 43):
```
-        if not isinstance(other, Q):
+        if not(isinstance(other, Q) or getattr(other, 'conditional', False) is True):
             raise TypeError(other)
```

| # | model.py impl op (`combine`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `other_is_container`, `other_is_boolean_operand`, `other_empty` | the operand `other` (arbitrary object) | R | the only observables `_combine` reads off `other` are `isinstance(other, Q)` ↔ `other_is_container`, `getattr(other, 'conditional', False) is True` ↔ `other_is_boolean_operand` (the neutral behavioral name; the repo attribute is named here only for the audit, not in the spec view — D1), and `bool(other)` ↔ `not other_empty` (mapping.md §2); the discriminating behaviour is a function of exactly these. |
| A2 | param `self_empty` | `self` (the calling `Q`), read via `not self` | R | the only observable of `self` the branch logic uses is its emptiness (`tree.Node.__bool__`); `self` is not mutated (mapping.md §2). |
| A3 | `if not (other_is_container or other_is_boolean_operand): raise OperandTypeRejected()` | `if not(isinstance(other, Q) or getattr(other, 'conditional', False) is True): raise TypeError(other)` (lines 43-44) | R + I | **the changed guard.** `or`/`not` and the disjunction structure are identical (I); the two disjuncts are the R-refined predicates of A1; `OperandTypeRejected` ↔ `TypeError` is the user-defined-exception refinement (mapping.md §2, builtin exceptions crash the translator). The post-patch guard accepts an operand that is a same-kind container OR is usable directly as a boolean filter condition (`getattr(other, 'conditional', False) is True`) — modeled exactly by `other_is_container or other_is_boolean_operand`. |
| A4 | `if other_empty: return Combined(0, conn)` | `if not other: _, args, kwargs = self.deconstruct(); return type(self)(*args, **kwargs)` (lines 47-49) | R + I | the empty-operand identity branch, unchanged by the patch; `not other` ↔ `other_empty` (I on the boolean test). The returned `type(self)(*deconstruct())` is a copy of `self`; modeled as `Combined(0, ...)` (branch tag 0 = "container copy"), validated `type(result)==Q and result.children==self.children` by axiom_check.py. |
| A5 | `elif self_empty: return Combined(1, conn)` | `elif not self: _, args, kwargs = other.deconstruct(); return type(other)(*args, **kwargs)` (lines 51-53) | R + I | the empty-container identity branch, unchanged by the patch; `not self` ↔ `self_empty` (I). The returned `type(other)(*other.deconstruct())` is a copy of `other`; modeled as `Combined(1, ...)` (branch tag 1 = "operand copy"), validated `type(result) is type(other)` by axiom_check.py (for an `Exists` operand the copy IS an `Exists`). |
| A6 | `obj = Combined(2, conn); return obj` | `obj = type(self)(); obj.connector = conn; obj.add(self, conn); obj.add(other, conn); return obj` (lines 55-59) | R + I | the merge branch (both non-empty), unchanged by the patch; a fresh container under the requested connector joining both operands. Modeled as `Combined(2, conn)` (branch tag 2 = "merge", connector EXACTLY `conn` ↔ `obj.connector = conn`), validated `isinstance(result, Q) and result.connector == conn` by axiom_check.py. |
| A7 | `Requires(MustTerminate(2))` (totality obligation; `Combined.__init__` carries `MustTerminate(1)` so construction discharges within it) | `_combine` is straight-line bounded work: every path RETURNS or RAISES (lines 43-59; no loops, no recursion) | R + I | **totality.** Nagini is a partial-correctness verifier by default: without this obligation a diverging implementation on any accepted branch (or on the reject path) would satisfy every value postcondition / `Exsures` vacuously while its real analogue hangs the combination and the F2P tests time out. The obligation pins the model to the real callee's always-answers behaviour; an endless loop cannot supply the strictly decreasing measure, so the obligation leak check rejects it. |

The discriminating content of the change — accept an operand that is NOT a
same-kind container but IS usable directly as a boolean filter condition
(`getattr(other, 'conditional', False) is True`; the `Exists` operand of
`Q() & Exists(...)`) — lives in the second disjunct `other_is_boolean_operand`
of the guard (step A3, model) ⇔ the
`getattr(other, 'conditional', False) is True` disjunct (real). The pre-patch
guard had only the first disjunct; `model_prepatch.py` reproduces that
(`if not other_is_container: raise`) and **fails** verification on the
exceptional postcondition
`Exsures(OperandTypeRejected, not other_is_container and not other_is_boolean_operand)`
(model_prepatch.py:121) — because on a boolean-operand-but-non-container operand
(`other_is_container=False, other_is_boolean_operand=True`) it raises
`OperandTypeRejected`, which the frozen spec permits ONLY when BOTH predicates
are false. That is exactly the spec sensing the change (G-DIFF). It is also the
exact F2P observation: `Q() & Exists(...)` / `Q() | Exists(...)` must NOT raise
`TypeError` (tests `test_boolean_expression_combined`,
`test_boolean_expression_combined_with_empty_Q`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — widening
the acceptance guard so a self-declared conditional operand is no longer
rejected — is modeled **directly** by the disjunctive guard in `combine`
(step A3) over the two boolean predicates. There is no axiomatized callee: the
guard reads `isinstance` / `getattr` / truthiness (modeled as the input
predicates), and the unchanged downstream branches (`deconstruct`,
`_new_instance`, `add`) are modeled directly as the three `Combined` branch
outcomes (steps A4-A6). There is therefore no A-consumed axiom and no
A-reference deep model; mapping.md §3 records the empty axiom inventory. The
refinement is the boolean-predicate type abstraction (R) over an otherwise
identical control flow (I), whose fidelity to the real `Q._combine` G-AX
validates exhaustively.

## C. verify(model) ⇒ resolved

`combine` verifies only if it accepts EXACTLY the operands that are a same-kind
container OR usable directly as a boolean filter condition (the
`Ensures(other_is_container or other_is_boolean_operand)` normal-return
postcondition and the matching
`Exsures(OperandTypeRejected, ...)` that fires ONLY when both predicates are
false), only if each acceptance branch produces the right outcome (branch 0
on an empty operand, 1 on an empty container, 2 — carrying exactly `conn` — on a
merge), and only if it actually DELIVERS that outcome on every input
(`Requires(MustTerminate(2))`, step A7): a diverging body cannot discharge the
termination obligation, so the vacuous-satisfaction loophole of partial
correctness is closed. By R (`other` ↔ its three boolean observables; `self` ↔ `self_empty`;
`conn` string ↔ int tag; `OperandTypeRejected` ↔ `TypeError`) the verified
function equals `Q._combine` with the widened guard on the tested inputs; by
G-AX the real post-patch `Q._combine` matches the model's acceptance + branch
behaviour over all 20 concrete operand × connector × self-emptiness
combinations, including the discriminating `Exists` operand and the rejected
non-conditional operands. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: abstraction
soundness (G-AX, here the boolean-predicate refinement rather than a library
axiom) and refinement fidelity (this document, G-EQ).

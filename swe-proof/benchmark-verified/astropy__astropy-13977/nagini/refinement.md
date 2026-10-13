# refinement.md — astropy__astropy-13977

The operation-by-operation correspondence between `model.py`'s implementation
(the `dispatch_ufunc` impl region and the deep `all_recognised` /
`has_custom_handler` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** when
the proof uses an axiom's `Ensures`, **A-reference** when a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The dispatcher — `Quantity.__array_ufunc__` (`astropy/units/quantity.py:620`)

Gold hunk (shape): the entire body is wrapped in `try:`; the previously-unguarded
computation (`converters_and_unit` → `check_output` → input conversion →
`super().__array_ufunc__` → `_result_as_quantity`) becomes the `try` body, and a
new handler is added:

```
+        try:
             <the whole former body>            # may raise TypeError/ValueError
             return self._result_as_quantity(result, unit, out)
+        except (TypeError, ValueError) as e:
+            out_normalized = kwargs.get("out", tuple())
+            inputs_and_outputs = inputs + out_normalized
+            ignored_ufunc = (None, np.ndarray.__array_ufunc__,
+                             type(self).__array_ufunc__)
+            if not all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc
+                       for io in inputs_and_outputs):
+                return NotImplemented
+            else:
+                raise e
```

| # | model.py impl op (`dispatch_ufunc`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `io_kinds: List[int]` (per-operand flags) | the collection `inputs_and_outputs = inputs + out_normalized` | R | each Python operand ↔ its kind flag; `len(io_kinds)` ↔ operand count (mapping.md §2). Read-only (`Acc(..., 1/2)` required AND ensured): the dispatch only *reads* the operand kinds, never mutates them. |
| A2 | param `recoverable_failure: bool` | "the protected body raised `TypeError`/`ValueError`" (the `try`/`except (TypeError, ValueError)` split) | R | the body callees are **unchanged**; the patch only changes whether their raise is caught. The boolean abstracts exactly the caught-error condition (mapping.md §1). |
| A3 | `if not recoverable_failure: return 0` | the `try` body's normal `return self._result_as_quantity(...)` (also the early `return result` for `unit is None`/`None`/`NotImplemented`) | I | a successful protected evaluation yields the ordinary result unchanged. Outcome code `0` = "ordinary computed result returned". The patch does not alter this path. |
| A4 | the loop computing `every_recognised == all_recognised(ToSeq(io_kinds))`, i.e. whether **every** operand flag is `0` | `all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc for io in inputs_and_outputs)` | A-reference | the changed classification is modelled **deeply**: `all_recognised`/`has_custom_handler` (pure region) ARE the per-operand membership-in-`ignored_ufunc` aggregate. There is no consumed axiom. G-AX (`axiom_check.py`) constructs operands of each kind (None, scalar, dict, ndarray, the self type, a plain duck, a custom-handler duck) and asserts the real `getattr(type(io),"__array_ufunc__",None) in ignored_ufunc` test yields the model's flag (`0` ignored / `1` custom), and that the full decision matches gold over boundary + 20000 fuzz collections. |
| A5 | `if every_recognised: return 2` | `else: raise e` | I/R | when **all** operands are recognised built-in kinds the dispatcher surfaces the recoverable error. Outcome code `2` = "the recoverable error is surfaced" ↔ `raise e` (modelled as a result code, not an `Exsures`, since the abstracted error carries no payload the spec observes). |
| A6 | `return 1` (the fall-through: some flag is `1`) | `if not all(...): return NotImplemented` | I/R | when at least one operand supplies its own handler the dispatcher abstains. Outcome code `1` = "not handled here" ↔ `return NotImplemented`. |

### The discriminating behaviour
The single behaviour the F2P tests pin is: a recoverable failure with a
custom-handler operand present must yield `NotImplemented` (code `1`), not the
error. In the model this is the postcondition

```
Ensures(Implies(recoverable_failure and has_custom_handler(ToSeq(io_kinds)),
                Result() == 1))
```

`model_prepatch.py` reproduces the **pre-patch** skeleton — no guard, so a
recoverable failure is surfaced unconditionally (`return 2` in every failing
case) — and **fails** exactly this clause (verifier: "Postcondition … Implies((
recoverable_failure and has_custom_handler(...)), (Result() == 1)) might not
hold"). That is the spec sensing the change (G-DIFF). The F2P
`TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[...]` cases drive
`ufunc(quantity, DuckQuantity3(...))`: the body raises (incompatible units /
non-convertible operand), `DuckQuantity3` carries a custom `__array_ufunc__`, so
post-patch the dispatcher returns `NotImplemented`, the duck's reflected handler
runs, and the result equals the expected value — pre-patch it raised.

## B. No consumed axioms

This bundle ships **no** `@ContractOnly` axiom. The protected body's callees
(`converters_and_unit`, `check_output`, `_to_own_unit`,
`super().__array_ufunc__`, `_result_as_quantity`) are **unchanged** by the patch
and irrelevant to the verified decision beyond *whether they raised* — captured
by the `recoverable_failure` boolean (R). The one genuinely-new operation, the
operand classification + the abstain-vs-surface dispatch, is modelled **deeply**
(A4–A6) and validated against real Python/numpy by G-AX, not axiomatized. Hence
there is no A-consumed row and no dead axiom.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely changed —
trapping the recoverable error and deciding NotImplemented-vs-raise from the
operand kinds — is modelled deeply (the `all_recognised` fold consumed in
`dispatch_ufunc`, an A-reference), never hidden behind an axiom about the
function under change.

## D. verify(model) ⇒ resolved

`dispatch_ufunc` verifies only if (i) success returns the ordinary result (A3),
(ii) a recoverable failure with every operand a recognised built-in kind
surfaces the error (A5), and (iii) a recoverable failure with any custom-handler
operand abstains with the "not handled here" sentinel (A6) — the exact tri-state
the gold `try/except` produces. By R (operand ↔ kind flag; caught-error ↔
boolean; the three control-flow exits ↔ codes 0/1/2) the verified decision
equals the gold patch's decision; by G-AX the deep classification
`all_recognised`/`has_custom_handler` equals the real `ignored_ufunc` membership
aggregate (A-reference). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this document, G-EQ)
plus the G-AX classification check; there is no axiom-soundness trust point
because no axiom is consumed.

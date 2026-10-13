# refinement.md — astropy__astropy-13977

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`dispatchUfunc` `do` block plus the pure deep model `ufuncSpec`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a
deep model validated == the real callee by G-AX), or **I** (identical concrete
op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
plan §4.1); the A legs and this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `Quantity.__array_ufunc__` (`astropy/units/quantity.py:620`)

The patch wraps the existing dispatch body (lines 639-682 @ base_commit) in a
`try:` and appends an `except (TypeError, ValueError):` clause that either returns
`NotImplemented` (when some participating operand advertises its own
`__array_ufunc__`) or re-raises. The wrapped body is otherwise unchanged.

Gold hunk (control flow only; the body lines are re-indented but identical):
```
-        converters, unit = converters_and_unit(function, method, *inputs)
-        out = kwargs.get("out", None)
-        ...
-        return self._result_as_quantity(result, unit, out)
+        try:
+            converters, unit = converters_and_unit(function, method, *inputs)
+            ...
+            return self._result_as_quantity(result, unit, out)
+        except (TypeError, ValueError) as e:
+            out_normalized = kwargs.get("out", tuple())
+            inputs_and_outputs = inputs + out_normalized
+            ignored_ufunc = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)
+            if not all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc
+                       for io in inputs_and_outputs):
+                return NotImplemented
+            else:
+                raise e
```

| # | Solution.lean impl op (`dispatchUfunc`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `call : Int` | the `(self, function, method, *inputs, **kwargs)` ufunc-call descriptor in scope | R | the descriptor ↔ an opaque `Int` handle (mapping.md §2); only the two observations `coreUfunc call` / `canDefer call` are read, never decomposed. G-CONF bridges by replaying each real call and reading both observations. |
| A2 | `match coreUfunc call with …` (branch on the success/recoverable-raise/fatal-raise OUTCOME of the wrapped computation) | `try: <body> … except (TypeError, ValueError) as e:` | A-reference + I | the UNCHANGED body is modeled `opaque` (`coreUfunc`) with NO `ensures`; the `Except`-leg reification of "returns / raises a `(TypeError,ValueError)` / raises something else" is the **A-reference** G-AX validates against the real body (mapping.md §3.1). The `match` dispatching on the outcome — i.e. the `try/except` control flow — is **I** (transliterated 1:1 by G-CONF). |
| A3 | `Except.ok v => Except.ok (Outcome.result v)` (success ⇒ return the value verbatim) | the `try` body's own `return` statements (returns `result`/`NotImplemented`/`None` from `super().__array_ufunc__` or `_result_as_quantity`) | I | when the body completes normally its value escapes the `try` unchanged; modeled as an opaque carried `Int` (`Outcome.result v`). The change never inspects or alters a successful value. |
| A4 | `Except.error UfuncErr.recoverable => if canDefer call then Except.ok Outcome.deferred else Except.error UfuncErr.recoverable` | `except (TypeError, ValueError) as e: if not all(... in ignored_ufunc ...): return NotImplemented else: raise e` | A-reference + I | the discriminating clause. `UfuncErr.recoverable` ↔ the `(TypeError, ValueError)` the clause catches; `canDefer call` ↔ the `not all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc ...)` predicate (per-operand attribute lookup = UNCHANGED machinery, **A-reference**; the `inputs + out` concat, `all(...)`, negation = **I**, replayed verbatim by G-CONF). `Outcome.deferred` ↔ `return NotImplemented`; the else `Except.error UfuncErr.recoverable` ↔ `raise e` (the SAME caught error). mapping.md §3.2. |
| A5 | `Except.error UfuncErr.fatal => Except.error UfuncErr.fatal` (any other failure propagates unchanged) | a raise NOT a `TypeError`/`ValueError` is not caught by the clause and propagates | I | the `except (TypeError, ValueError)` clause is narrow; every other exception leaves `__array_ufunc__` exactly as before the patch. `UfuncErr.fatal` ↔ "not in the caught set". |
| A6 | `return result` (the dispatch yields the `Except UfuncErr Outcome` computed above) | the function returns the body value, returns `NotImplemented`, or re-raises — per A3/A4/A5 | I | totality of the dispatch over the three outcome legs; `Except.ok` ↔ a value escapes, `Except.error` ↔ a failure escapes. |

Discriminating content of the change — a recoverable failure with an available
alternate handler must be turned into a DEFERRAL (`Outcome.deferred`) rather than
PROPAGATED — lives in the `Except.error UfuncErr.recoverable => if canDefer call
then Except.ok Outcome.deferred …` leg (A4) ⇔ the new `except (TypeError,
ValueError): … return NotImplemented`. `Solution_prepatch.lean` reproduces the
unwrapped pre-patch behavior (`Except.error e => Except.error e`, propagating
every failure) and **fails** `out = ufuncSpec call` precisely on that leg
(G-DIFF; confirmed: the prepatch's unsolved goal is the `Except.error
recoverable` case where `canDefer = true` forces `Except.ok deferred` but the
prepatch yields `Except.error recoverable`).

## B. No consumed axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The wrapped body (`coreUfunc`) and the per-operand
handler lookup inside the deferral predicate (`canDefer`) are **unchanged** by the
patch — it wraps the call site in `try/except` and adds the deferral test; it does
not redefine the body or the attribute machinery. Both are modeled `opaque` with
**NO asserted `ensures`**, so there is **no consumed axiom** to over-claim
(directive 7): the desired behavior assumes nothing about WHICH value the body
returns, only how its success vs its recoverable raise is handled. They are tagged
**A-reference** — G-AX validates the modeled facts against the real callees
(mapping.md §3): the body raises exactly a `TypeError`/`ValueError` on the issue's
incompatible operands (so the recover leg is a genuine runtime path), returns
without raising on compatible operands, and `canDefer` matches the real
classification (True for a duck operand with its own `__array_ufunc__`, False for
a plain `dict`).

The operation that genuinely *changed* — intercepting a recoverable failure and
deferring when another handler exists — is the `match`/recover control flow,
modeled **directly** (A2/A4, I legs over A-reference callees), not hidden behind an
axiom about the function under change. There is no axiom about `__array_ufunc__`
itself.

## C. verify(Solution) ⇒ resolved

`dispatchUfunc` verifies only if its output equals `ufuncSpec call` for every
outcome of the opaque `coreUfunc` — including the `Except.error recoverable` leg,
which under `canDefer call = true` forces the deferral `Outcome.deferred` (A4) and
under `canDefer call = false` re-propagates the same recoverable error, and the
`Except.error fatal` leg, which always propagates (A5). By R (the call descriptor
↔ `Int` handle) and the I transliteration of the `try/except` / deferral-test /
re-raise, the verified dispatch equals the gold patch's wrapped block on the
tested calls; by G-AX the real body raises exactly a `(TypeError, ValueError)` on
the issue's incompatible duck operand (so the recover branch is the genuine
runtime path) and `canDefer` classifies the duck (custom handler) as deferrable
and the `dict` (none) as not; by G-CONF the R/I shadow of the dispatch agrees with
`patch.diff`'s behaviour on ≥10⁵ fuzzed calls. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: callee-fact soundness (G-AX) and refinement fidelity
(this doc, G-EQ + G-CONF).

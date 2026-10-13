# refinement.md — sympy__sympy-16450

The operation-by-operation correspondence between `model.py`'s implementation
(the `positive_standin_properties` impl region and the consumed `resolve` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses this axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The replacement site — `posify(eq)` (`sympy/simplify/simplify.py:254`)

Gold hunk:
```
-    reps = {s: Dummy(s.name, positive=True)
+    reps = {s: Dummy(s.name, positive=True, **s.assumptions0)
                  for s in eq.free_symbols if s.is_positive is None}
```

The change is, for each free symbol `s` with `s.is_positive is None`, the
declaration the stand-in `Dummy` is built from: it now carries `**s.assumptions0`
(the original symbol's stated assumptions) in addition to `positive=True`.

| # | model.py impl op (`positive_standin_properties`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `stated: Dict[int, bool]` | `s.assumptions0` — the stated assumptions of the symbol `s` being replaced | R | a symbol's assumption mapping (`dict[str, bool]`) ↔ `Dict[int, bool]` of assumption-name tokens (mapping.md §2); only membership + per-key truth value are observed. |
| A2 | precondition `not (POSITIVE() in stated)` | the comprehension filter `if s.is_positive is None` | R + I | a symbol is replaced exactly when its sign is undecided, i.e. `'positive'` is not a key of its `assumptions0`. The model states this as the precondition (mapping.md §1). |
| A3 | `resolve(stated, True)` — pass the original quantity's stated assumptions (the base) together with the added `positive=True` to the engine, and return the derived assumptions | `Dummy(s.name, positive=True, **s.assumptions0)` (then its `.assumptions0`) | A-consumed | the unchanged assumption-inference engine is the `resolve`/`derived` axiom pair (mapping.md §3.1). The CHANGED dataflow — that `stated` (`**s.assumptions0`) reaches the engine as the base, rather than nothing — is spelled out **deeply** in the impl (the first argument is `stated`, not an empty map). The proof consumes `resolve`'s `Ensures`: **totality** (`Result() is derived(stated, True)` — the whole result is the engine's map), fact preservation (every stated fact survives), and added positivity. |
| A4 | the returned `Dict[int, bool]` is the stand-in's derived assumptions, pinned to be EXACTLY the engine's effective-property map (`Result() is derived(stated, True)`), held read-only (fractional permission) | the `Dummy`'s `.assumptions0` (the value stored in `reps`, used to substitute into `eq`; read, never mutated) | R | the stand-in symbol carries exactly these derived assumptions and NO others; the F2P test observes `posify(...)[0].assumptions0` by **exact whole-dict equality**, so the spec binds the whole result, not just the input-derived subset (mapping.md §2, §3.1). `s.name` is modeled away (does not affect the observed assumptions). |

The discriminating content of the change — every stated assumption (in
particular `finite=True`) is carried into the stand-in rather than discarded —
lives in passing `stated` as `resolve`'s base (model) ⇔ `**s.assumptions0`
(real). The pre-patch built the stand-in from `positive=True` alone;
`model_prepatch.py` reproduces that (`resolve(empty, True)`, an empty base) and
**fails** both the totality postcondition

  `Result() is derived(stated, True)`

and the fact-preservation postcondition

  `Forall k: k in stated ⇒ k in Result() and Result()[k] == stated[k]`

which is exactly the spec sensing the change (G-DIFF): with an empty base the
engine's map `derived(empty, True)` is not `derived(stated, True)` and cannot
derive `finite=True`, so a `stated` carrying `FINITE` is dropped.

**Totality (Defect-1 strengthening).** The result is pinned to the WHOLE engine
map by `Result() is derived(stated, True)` together with `resolve` yielding only
**fractional** permission on its result. The earlier spec constrained only keys
`k in stated`, leaving engine-derived keys (`real`, `nonnegative`, …) free; an
impl could fabricate a spurious derived key (`r[k]=v` for `k ∉ stated`), and the
mapping's licensed "every other name ↔ some other token" makes that a faithful
refinement to a wrong patch (forcing e.g. `real=False`, which both breaks the
F2P's exact-dict equality and raises `InconsistentAssumptions`). The
totality clause rejects every such impl: reference identity to the pure engine
map forbids substituting a different object, and fractional result permission
forbids mutating the engine's output in place. So a verifying impl's result is
byte-for-byte the engine's `assumptions0` — exactly what the F2P pins.

## B. The buggy declaration is modeled deeply, not axiomatized

The operation that genuinely *changed* — WHICH declaration the engine receives
— is modeled deeply (the first argument of `resolve` is `stated`, the original
symbol's full assumptions, vs the empty base in the prepatch). It is NOT hidden
behind an axiom about the function under change. The consumed axiom is the
`resolve`/`derived` pair (**A-consumed**, A3) — `derived` the pure
effective-property map, `resolve` the effectful call whose result IS that map —
covering the **unchanged** assumption-inference engine the new code invokes (the
engine runs identically pre- and post-patch; only its input differs). The same
engine is also the **A-reference** the deep model is validated against:
axiom_check.py confirms the modeled `positive_standin_properties` equals the real
`posify` transformation (`real == derived`, full-dict equality), and that the
engine meets the axiom's `Ensures`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The single changed operation (the base
declaration handed to the engine) is modeled deeply; there is no axiom about
`posify` itself or about the dict-unpacking that changed.

## D. verify(model) ⇒ resolved

`positive_standin_properties` verifies only if its result IS the whole engine
map `derived(stated, True)` (A3/A4, the totality postcondition), which in
particular preserves EVERY fact stated in `stated` (the `Forall` postcondition)
and derives `positive=True`, and carries NO key the engine did not derive. By R
(`assumptions0` ↔ `Dict[int,bool]`, the stand-in carrying its derived
assumptions, `s.name` modeled away) the verified construction equals
`Dummy(s.name, positive=True, **s.assumptions0).assumptions0` — byte-for-byte —
on the symbols `posify` replaces; by G-AX the engine meets the `resolve`/`derived`
axiom (A-consumed: `real == derived` full-dict equality both directions, raise
path lock-step) and the deep model equals the real `posify` transformation
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited engine callee — and the
gold patch resolves (G-RESOLVE). In particular the atk_12 witness (an impl that
adds a derived key the spec never named) no longer verifies: the totality clause
+ fractional result permission reject it (regression case for G-EQ re-audit).
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).

Out-of-domain note: when `stated` together with `positive=True` is an
inconsistent declaration the real engine raises `InconsistentAssumptions`; the
gold patch raises identically and the F2P/P2P tests never exercise it, so the
twin remains equivalent there (the modeled operation simply is not specified on
that input; `resolve`'s `Requires` is satisfied but the engine's own
consistency check, not modeled, is what raises — both sides raise the same way).

# refinement.md — scikit-learn__scikit-learn-14983

The operation-by-operation correspondence between `model.py`'s implementation
(the `reported_param_value` impl region + the deep `resolved_value` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`Ensures`, **A-reference** where a deep model is validated `== the real callee`
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There are **no consumed `@ContractOnly` axioms**: the only operation that
changed — the per-parameter value resolution — is modeled **deeply**, and the
attribute/mapping lookups it stands for are validated as an **A-reference**.

## A. The `__repr__` site — `_RepeatedSplits.__repr__` (`_split.py:1166`)

Gold hunk:
```
+    def __repr__(self):
+        return _build_repr(self)
```

This makes `repr()` of `RepeatedKFold` / `RepeatedStratifiedKFold` route
through `_build_repr` (the parameter-introspecting representation) instead of
`object.__repr__` (the `<... object at 0x...>` string in the issue's "Actual
Results"). The behaviour under spec is therefore *what `_build_repr` reports*,
i.e. the per-parameter value resolution. There is nothing to refine in this
hunk beyond "the representation is the resolved-parameter representation"; its
content lives entirely in site B's resolution, which is the function under
spec.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `reported_param_value` IS the per-parameter resolution that the representation is built from | `def __repr__(self): return _build_repr(self)` | I | dispatching `__repr__` to `_build_repr` makes the reported representation equal the per-parameter resolution; modeling that resolution (site B) models the representation. No type distance. |

## B. The `_build_repr` cvargs-fallback site (`_split.py:2162-2164`)

Gold hunk:
```
                 value = getattr(self, key, None)
+                if value is None and hasattr(self, 'cvargs'):
+                    value = self.cvargs.get(key, None)
```

This is the discriminating change. It is modeled directly by `reported_param_value`
(impl) and `resolved_value` (deep model).

| # | model.py impl op (`reported_param_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `value = attr` | `value = getattr(self, key, None)` | A-reference | `attr` IS the result of `getattr(self, key, None)` under the §2 bijection (`None` ↔ the `none` sentinel). The attribute lookup is not changed by the patch; its semantics are validated `== model` by axiom_check.py (`real_resolution`, G-AX). |
| B2 | `if value == none and has_store:` | `if value is None and hasattr(self, 'cvargs'):` | R + A-reference | `value == none` ↔ `value is None` (sentinel bijection); `has_store` ↔ `hasattr(self, 'cvargs')` (mapping.md §2). The two-condition guard is identical control flow. |
| B3 | `if key in store: value = store[key]` else `value = none` | `value = self.cvargs.get(key, None)` | R + A-reference | `self.cvargs.get(key, None)` is exactly "store[key] if key present, else None"; modeled by the `key in store` test + `store[key]` / `none`. `key in store` ↔ `key in self.cvargs`, `store[key]` ↔ `self.cvargs[key]` (mapping.md §2). Validated `== model` by G-AX. |
| B4 | `return value` | `params[key] = value` (the value placed in the reported params dict) | I | the resolved value is what is reported for `key`; the model returns it. The surrounding loop / `_pprint` formatting is unchanged framing, not part of the modeled delta. |

The discriminating content — a parameter with no direct attribute but recorded
in the secondary store resolves to the store's concrete value, NOT to absent —
lives in the postcondition
`Implies(attr == none and has_store and (key in store), Result() != none)` and
`... Result() == store[key]`. The pre-patch `_build_repr` omitted the fallback;
`model_prepatch.py` reproduces that (`value = attr; return value`, no store
fallback) and **fails** the postcondition
`Result() == resolved_value(attr, none, has_store, store, key)` exactly on the
`attr == none and has_store and key in store` case (e.g. `n_splits` in
`cvargs`) — the spec sensing the change (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the value resolution gaining the `cvargs` fallback — is modeled
**deeply** (`resolved_value` in the `pure` region, consumed by `reported_param_value`),
not hidden behind an axiom about the function under change. There is **no
consumed `@ContractOnly` axiom**: the unchanged stdlib-style lookups it stands
for (`getattr(...)`, `dict.get`, `in`, `hasattr`) are the **A-reference** that
G-AX validates the deep model against (axiom_check.py asserts the deep model ==
the real `_build_repr` resolution on boundary + fuzz, and the real
`RepeatedKFold` / `RepeatedStratifiedKFold` `repr()` == the F2P string).

## C2. Termination (totality obligation)

The spec carries `Requires(MustTerminate(2))`. The real per-key resolution is
loop-free straight-line code — `getattr(self, key, None)`, one guarded
`self.cvargs.get(key, None)`, and the value is recorded — so every execution
of the modeled operation returns; the obligation adds no behaviour beyond what
the real code already has and cannot exclude a correct implementation. It is
load-bearing because Nagini checks partial correctness by default: without it,
a same-spec implementation that diverges (an infinite loop inserted into the
per-key body) satisfies every `Ensures` vacuously while its faithful real
patch makes `repr()` hang forever, so the F2P `test_repeated_cv_repr` never
completes and the patch does not resolve (the audit's recorded
verify⇏resolve witness class). The surrounding `for key in args:` loop of
`_build_repr` is unchanged framing (refinement.md §B4) and is bounded by the
constructor's parameter list in the real code.

## D. verify(model) ⇒ resolved

`reported_param_value` verifies only if its output equals the exact resolution with
the `cvargs` fallback (`Result() == resolved_value(...)`) and, on the
discriminating case, is the store value rather than absent (B3 postconditions).
By R (name↔int, `None`↔`none`, `cvargs`↔`store`, `hasattr`↔`has_store`) the
verified resolver equals the gold `_build_repr` body; by A (the `__repr__`
dispatch, A) the reported representation is that resolution; by G-AX the deep
model equals the real lookups and the real classes' `repr()` equals the
FAIL_TO_PASS string. The `test_build_repr` PASS_TO_PASS case (a MockSplitter
with no `cvargs`, `c=None`) is preserved: with `has_store` false a `none`
attribute stays `none`
(`Ensures(Implies(attr == none and not has_store, Result() == none))`).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited reference — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: the
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).

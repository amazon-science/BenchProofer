# mapping.md — astropy__astropy-7336

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 732d89c2940156bdc0e200bb36dc38b5e424bcba`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one deep-model reference.

Repo file under change: `astropy/units/decorators.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `processReturn (annot : Annot) (ret : RetVal)` | the result post-processing tail of `QuantityInput.__call__.wrapper` — `astropy/units/decorators.py:223-226` (the `if wrapped_signature.return_annotation …: return return_.to(...) else: return return_` block) | the modeled changed function (the changed guard + its two branches) |
| `Annot` | `wrapped_signature.return_annotation` (`inspect.Signature.return_annotation`) | the declared result annotation: `absent ↔ inspect.Signature.empty`, `nullAnnot ↔ None`, `target u ↔` a genuine unit object |
| `RetVal` | `return_` — the value the wrapped callable produced | `quantity u ↔` an `astropy.units.Quantity` carrying unit `u`; `null ↔ None` (a callable, e.g. a constructor `__init__`, that returns no value) |
| `coerceUnit` *(deep model — A-reference)* | `return_.to(target)` — `astropy.units.Quantity.to` (`astropy/units/quantity.py`), the unchanged unit re-expression callee | pure spec: re-express a quantity in the target unit, **partial on dimensional compatibility** — succeeds (unit becomes target) only when source and target share a measurement kind, else rejected; **undefined on `None`** (`None` has no `.to` → `AttributeError`), validated == real `.to` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `unitKind` / `compatible` *(part of the A-reference model)* | the physical dimension of a unit / `Unit.is_equivalent` outcome | `unitKind` tags each unit id with its measurement kind; `compatible s t` (same kind) holds iff real `q.to(t)` succeeds rather than raising `UnitConversionError`. Pinned to the real dimension by axiom_check.py |
| `processReturnSpec` | the intended behavior of the post-processing tail | pure spec the method's `ensures` pins |

The pre-patch repo guard the change replaces (refinement audit only, not named
in the consumer spec view): `return_annotation is not inspect.Signature.empty`
(`decorators.py:223`), which fires the `.to(...)` branch for **every**
non-empty annotation, including `None`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `wrapped_signature.return_annotation` | `Annot` | `inspect.Signature.empty ↔ .absent`; `None ↔ .nullAnnot`; a unit object `u ↔ .target (id u)` where `id` is any injective tag (only equality/branch-selection is observed) |
| `return_` (the wrapped result) | `RetVal` | `None ↔ .null`; a `Quantity` of unit `u ↔ .quantity (id u)` (only the resulting **unit** is observed by the F2P/P2P tests — `solarx.unit == u.deg`, `solarx is None`) |
| `return_.to(target)` | `coerceUnit ret t` | For a same-kind target, `Quantity(...).to(target_unit)` is a `Quantity` whose `.unit == target_unit` ↔ `coerceUnit (.quantity s) t = .ok (.quantity t)` when `compatible s t`; for a different-kind target, `.to` raises `UnitConversionError` ↔ `coerceUnit (.quantity s) t = .error .notCompatible` when `¬ compatible s t`; `None.to(...)` raises `AttributeError` ↔ `coerceUnit .null _ = .error .noConvertOp` |
| the value/magnitude carried by a `Quantity` | dropped (not in `RetVal`) | the tests observe only `.unit` and `is None`; the magnitude is observationally irrelevant to this change, so it is not modeled (avoids over-claiming) |

Unit identity is modeled as `Nat` tags: the post-processing tail only ever
selects a branch on the annotation shape and, on `.target`, asks `.to` to stamp
that unit onto the result — it never inspects unit internals. A `Nat` tag is a
faithful, total carrier for "which unit".

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `coerceUnit` deep model ↔ `Quantity.to` / `None.to` (A-reference)
**Callee:** `astropy.units.Quantity.to(unit)`, unchanged by this patch. The
post-processing tail invokes it **only** when the annotation names a genuine
unit target. Its three observable behaviors:

* on a `Quantity` whose source unit is the **same kind** as `target`,
  `q.to(target)` returns a `Quantity` whose `.unit` is `target` (re-expression
  in the new unit) — `coerceUnit (.quantity s) t = .ok (.quantity t)` when
  `compatible s t`;
* on a `Quantity` whose source unit is a **different kind** from `target`,
  `q.to(target)` raises `UnitConversionError` (the units are not convertible,
  e.g. `Quantity(3.0, u.hour).to(u.kg)`) — `coerceUnit (.quantity s) t =
  .error .notCompatible` when `¬ compatible s t`;
* on `None` (a callable that returned nothing), `None.to(target)` raises
  `AttributeError: 'NoneType' object has no attribute 'to'` — the crash the
  issue reports — `coerceUnit .null _ = .error .noConvertOp`.

This is an **A-reference**, not a consumed axiom: the re-expression operation is
modeled deeply (`coerceUnit`) and validated against the real callee by G-AX,
which constructs real `astropy` quantities and asserts (a) for a same-kind
target `q.to(target).unit == target`, (b) for a different-kind target
`q.to(target)` raises `UnitConversionError`, and (c) `None.to(target)` raises
`AttributeError`. `unitKind`/`compatible` are pinned to the real physical
dimension by the same check (same group ⇒ convertible ⇒ `.to` succeeds;
different group ⇒ `.to` raises). There is **no** consumed `axiom` in this
bundle.

The patched function under spec (`processReturn` ↔ the guard) is **never**
axiomatized — only the unchanged `.to` callee is modeled (SPEC_GUIDE §0.7).

### 3.2 Flag/branch dependency
`coerceUnit` is invoked by `processReturn` exactly when the impl's `annotated`
guard is true, i.e. only for `.target`. G-AX therefore exercises `.to` on the
configuration the impl actually reaches (a genuine unit target), and separately
confirms the `None.to` crash that motivates routing `.nullAnnot` to the
pass-through branch.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7336`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`processReturnSpec` / the impl's branch selection to Python and bridges I/O via
the §2 bijection, leaving the A-tagged callee behavior (`.to` / `None.to`) as
the real observable outcome (unit-stamp on a quantity, crash on null). It diffs
the shadow against `patch.diff`'s patched-wrapper behavior over ≥10⁵ fuzzed
`(annotation, return value)` pairs.

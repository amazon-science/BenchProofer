# refinement.md — django__django-13297

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`deferMapping` `do` block, plus the `deferOne`/`deferredOf`/`coerce` pure model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none in this bundle), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4);
the type-dispatch facts the model depends on are audited by **G-AX**
(`axiom_check.py`) against the real Django objects; the narrative is audited by
**G-EQ**. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The wrapper-constructor swap — `_wrap_url_kwargs_with_deprecation_warning`

Gold hunk (`django/views/generic/base.py`):
```
-from django.utils.functional import SimpleLazyObject
+from django.utils.functional import lazy
 ...
-        @SimpleLazyObject
         def access_value(key=key, value=value):
             ...
             return value
-        context_kwargs[key] = access_value
+        context_kwargs[key] = lazy(access_value, type(value))()
```

| # | Solution.lean impl op (`deferMapping`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `entries : List (Nat × Value)` | `url_kwargs` arg (an ordered `dict`) | R | `dict` items in insertion order ↔ `List (Nat × Value)`; key ↔ `Nat` id, value ↔ `Value` (mapping.md §2). G-CONF bridges the dict↔list and the per-value type tag. |
| A2 | the backward `while` loop building `result` by prepending `(p.fst, deferOne p.snd)` | `for key, value in url_kwargs.items(): context_kwargs[key] = <deferred>` (the loop that fills `context_kwargs`) | I | the loop is a concrete structural per-entry map preserving key and order; the backward fold computes exactly the left-to-right `deferredOf` (transliterated by G-CONF). |
| A3 | `deferOne p.snd = { forced := p.snd, reported := none }` | `context_kwargs[key] = lazy(access_value, type(value))()` | R + I | the deferred-value construction. **R:** `lazy(f, type(value))()` ↔ a `Wrapper` whose `forced` is the value `access_value` returns and whose `reported` is `none` — because the resulting `__proxy__` is NOT a subclass of the wrapped value's type, so `isinstance(w, type(value))` is `False` (mapping.md §3.1). **I:** the construction is a concrete, transliterated op (G-CONF). |
| A4 | the genuineness clause `coerce (deferOne v) v.tag = genuine v`, modeled by `coerce` | the consumer the fix unblocks: `Field.to_python`'s `isinstance(value, <type>)` guard, reached when the deferred value is used to filter (`Account.objects.get(slug=…)`) | R + I | `coerce` is the abstract shape of the type-dispatching consumer (mapping.md §2); under the post-patch wrapper it returns `genuine` (the value is coerced to a real value of its type, so the filter/DB-bind works). G-AX confirms `to_python(post)` is genuine and `to_python(pre)` is not. |

Discriminating content of the change — the deferred value MUST report a type
distinct from the wrapped value's own type (so a type-dispatching consumer
coerces it rather than passing it through) — lives in `deferOne`'s
`reported := none` (model) ⇔ `lazy(access_value, type(value))()` returning a
`__proxy__` (real). The pre-patch `@SimpleLazyObject` made the wrapper masquerade
as the wrapped value's type (`reported := some v.tag`); `Solution_prepatch.lean`
reproduces that and **fails** the invariant `result = deferredOf (entries.drop i)`
(G-DIFF), because the masquerading wrapper is not `deferOne`.

## B. No second site

The gold patch touches a single function (and its import line). There is one
independently-observable fixed behaviour (the deferred value is no longer a
type-masquerading wrapper), exercised by the single F2P test
`test_template_params_filtering`. One failing prepatch suffices.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the wrapper
constructor and the runtime type its product advertises — is modeled
**directly** (`Wrapper.reported` + `coerce`, steps A3/A4), not hidden behind an
axiom about the function under change or any unchanged callee. There is **no
consumed axiom and no deep-model reference** (`axioms` region empty). The
type-dispatch facts the direct model relies on (pre masquerades, post does not;
`to_python` genuineness) are executable-checked against real Django by G-AX.

## D. verify(Solution) ⇒ resolved

`deferMapping` verifies only if (i) its output equals `deferredOf entries` — the
per-entry deferral with `reported = none` (A3), and (ii) the genuineness clause
`coerce (deferOne v) v.tag = genuine v` holds for every value (A4). By R
(`dict ↔ List (Nat × Value)`, key↔`Nat`, value↔`Value`, `type(value)`↔tag) the
verified function equals the patched
`_wrap_url_kwargs_with_deprecation_warning` on the tested mappings; by G-AX the
real post-patch wrapper is genuine under `Field.to_python` while the pre-patch
one is not (so the discriminator is the real one); by G-CONF the R/I
transliteration of the fold + the genuineness property agrees with `patch.diff`'s
behaviour on ≥10⁵ fuzzed inputs. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). Trust points: refinement fidelity (this doc, G-EQ +
G-CONF) and the executable type-dispatch audit (G-AX); there are no axioms to
trust.

# mapping.md — pydata__xarray-2905

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7c4e2ac83f7b4306296ff9b7b51aaf016e5ad614`, states the type
abstraction (the bijection G-CONF / G-AX would use to bridge Lean↔Python), and
gives the provenance of each modeled observable.

Repo file under change: `xarray/core/variable.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepareData (w : Incoming)` | `as_compatible_data(data, fastpath=False)` — `xarray/core/variable.py:189`; the modeled slice is the "we don't want nested self-described arrays" step at **line 220–221** | the modeled changed function (the self-described-array unwrap step) |
| `Incoming.obj` | the incoming `data` object's own identity (what `as_compatible_data` carries forward when it does NOT unwrap) | input observable |
| `Incoming.valuesPayload` | `getattr(data, "values", <absent>)` — the object's stored `.values` attribute, `some` when present else `none` | input observable |
| `Incoming.isRecognized` | `isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` (post-patch type predicate) | input observable (the dispatch key the fix introduces) |
| `forwarded (w : Incoming)` *(pure spec)* | the value bound to `data` after line 220–221 executes | pure spec: the object handed downstream to `_maybe_wrap_data` |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): `data = getattr(data, "values", data)`
(`variable.py:221` @ base_commit) — unwrap on the mere *presence* of a `.values`
attribute, irrespective of the object's type.

## 2. Type abstraction (R-refinements) — the Lean↔Python correspondence

The modeled slice neither inspects nor transforms the *content* of any array; it
only chooses WHICH object to forward. So the carrier is a single opaque identity
(`Obj := Nat`), and the three observables the dispatch reads are lifted into the
`Incoming` structure. This is exactly the astropy__astropy-14096 modeling shape
(opaque identities + the observables the branch consults).

| repo reality | Lean carrier | correspondence |
|---|---|---|
| a data object's identity (`data`, or its `.values`) | `Obj` (`= Nat`, opaque) | distinct objects ↔ distinct `Obj`; only equality / identity is observed, never content |
| `getattr(data, "values", <absent>)` | `valuesPayload : Option Obj` | attribute present ↔ `some v` (v = the payload's identity); attribute absent ↔ `none` |
| `isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` | `isRecognized : Bool` | the (post-patch) recognized self-describing container types ↔ `true`; anything else ↔ `false` |
| `data = data.values` (taken arm) | `w.valuesPayload.getD w.obj` | forward the stored payload |
| `data` unchanged (not-taken arm) | `w.obj` | forward the object itself |

**`require` justification.** `isRecognized = true → valuesPayload.isSome = true`:
every recognized container type (`pd.Series`, `pd.Index`, `pd.DataFrame`) always
exposes a `.values` attribute, so when the post-patch branch is taken the
attribute access `data.values` always succeeds. This is a property of those
unchanged pandas types, not of the function under change; it makes
`valuesPayload.getD w.obj` denote the genuine payload (never the `getD`
fallback) on the recognized arm. It does NOT weaken the discriminating clause:
on the **unrecognized** arm (`isRecognized = false`) the payload may still be
`some` (the bug's trigger), and there the spec forces `w.obj`.

## 3. Callee provenance — none consumed (no G-AX)

No callee contract is consumed and no callee is deep-modeled-as-an-external-
reference. The two operations the dispatch performs —
`isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` and `getattr(data,
"values", …)` / `data.values` — are unchanged Python/pandas reflection
primitives whose *outcomes* are carried as the free input observables
`isRecognized` and `valuesPayload`. The spec makes no behavioural claim about
either primitive and holds for every value the observables could take, so there
is nothing to validate against a real callee. Hence `axioms` is empty, there is
no `axiom_check.py`, and **G-AX is not applicable** (auto-skips). This mirrors
astropy__astropy-14096 (`axioms: []`, no G-AX).

## 4. G-CONF — conf_skip=true (no interpreter-free R/I shadow)

`conf_skip=true`; `conformance_check.py` is a `status=skip` stub. The modeled
op's only discriminating observable is the **identity** of the forwarded object:
an arbitrary user object exposing a `.values` attribute must be returned *as
itself* (so it lands in an object-dtype array as `array([<obj>])`), not replaced
by its `.values` payload. That distinction materializes only against the live
CPython type system and numpy's object-array machinery — i.e. the F2P test
`TestAsCompatibleData::test_unsupported_type`, which builds a bespoke
`CustomWithValuesAttr` class and asserts `orig._data.item()` is that very
instance — not a pure, interpreter-free transliteration fuzzable over ≥10⁵
inputs. Both dispatch arms merely *select* among free inputs with no
input-dependent content computation. Soundness is instead carried by G-VERIFY
(the frozen `forwarded` postcondition provably forces the unrecognized-with-
payload object to be forwarded unchanged) and G-DIFF (the prepatch, which
unwraps on the mere presence of a payload, fails exactly that clause). Precedent
for the skip: astropy__astropy-14096, django__django-11451.

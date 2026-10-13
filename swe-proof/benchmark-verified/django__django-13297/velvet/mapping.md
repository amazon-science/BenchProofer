# mapping.md — django__django-13297

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8954f255bbf5f4ee997fd6de62cb50fc9b5dd697`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled construct.

Repo file under change: `django/views/generic/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deferMapping (entries : List (Nat × Value))` | `_wrap_url_kwargs_with_deprecation_warning(url_kwargs)` — `django/views/generic/base.py:168` (loop body lines 170–181) | the modeled changed function: repackages every key→value entry of a mapping as a deferred value, keys/order preserved |
| `deferOne (v : Value)` | the per-entry construction `context_kwargs[key] = <deferred value>` (`base.py:181` post-patch) | pure spec: build the deferred value for one entry |
| `deferredOf` | the whole-mapping result `context_kwargs` (`base.py:169–182`) | pure spec: defer every entry (front-recursive) |
| `coerce (w : Wrapper) (t : Nat)` | a downstream type-dispatching consumer — `Field.to_python`'s `isinstance(value, <type>)` guard (`django/db/models/fields/__init__.py:1023`, the path the issue's `Account.objects.get(slug=…)`/`Artist.objects.get(name=…)` filter reaches) | pure spec: how a consumer that branches on the value's runtime type treats a deferred value |

The pre-patch construct the change removes (refinement audit only, not in the
consumer spec view): the `@SimpleLazyObject`-decorated `access_value` closure
(`base.py:172–181`, the wrapper whose `__class__` masquerades as the wrapped
value's type).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `url_kwargs` / `context_kwargs` — an ordered `dict` of `key → value` | `List (Nat × Value)` / `List (Nat × Wrapper)` | the dict's items in insertion order ↔ the list; a key (the URL-capture name) ↔ `Nat` (an interned key id, identity-only — keys are never inspected, only carried through); membership/order/length preserved exactly |
| a runtime Python value `value` (the deferred URL kwarg) | `Value` | `Value.tag` ↔ the value's runtime type `type(value)` (interned to a **positive** `Nat`; distinct Python types ↔ distinct positive tags); `Value.content` ↔ the value's payload (`str` body, modeled `List Char`) |
| `type(value)` passed to `lazy(access_value, type(value))` | the target `Nat` argument of `coerce` and the `v.tag` in the genuineness clause | the resultclass the deferred value is told to delegate to; in the spec it is the value's OWN runtime type — which is why the genuineness clause quantifies `coerce (deferOne v) v.tag` |
| the deferred wrapper object (`base.py:181`) | `Wrapper` | `Wrapper.forced` ↔ the value obtained when the wrapper is finally evaluated (`func()` returns `value`); `Wrapper.reported` ↔ the runtime type the wrapper advertises to a type-dispatching consumer: `none` ⇔ a **distinct proxy type** (post-patch `__proxy__` whose `type(...)` is neither `str` nor any wrapped type, so `isinstance(w, str)` is `False`); `some t` ⇔ the wrapper **masquerades** as runtime type `t` (pre-patch `SimpleLazyObject`, whose `__class__` property returns the wrapped value's class, so `isinstance(w, str)` is `True`) |
| `Field.to_python(value)` outcome | `Coerced` | `Coerced.genuine v` ⇔ the guard `isinstance(value, str)` is `False`, so `to_python` runs `str(value)` and returns a **genuine** value of the target type (`type(...) is str`); `Coerced.passthrough w` ⇔ the guard is `True`, so `to_python` returns the wrapper **unchanged** (a non-genuine value — the object whose later DB bind raises `Error binding parameter … probably unsupported type`) |

The list carrier (not `HashMap`) is used because the operation is a structural
per-entry map preserving key and order; no key is ever looked up.

## 3. Construct provenance (no kind-A callee)

There is **no axiomatized callee and no deep-model reference** in this bundle.
The change is a *callee-swap of the wrapper constructor* — `SimpleLazyObject(f)`
→ `lazy(f, type(value))()` — and the only behaviour that distinguishes them is
**how the resulting object answers a type-dispatching consumer**. That behaviour
is modeled **directly** by `Wrapper.reported` + `coerce`, not behind an axiom
about an unchanged callee. So `axioms` region is empty; `meta.json axioms = []`,
`deep_model_references = []`.

### 3.1 Why `reported = none` (post-patch) vs `some tag` (pre-patch) is faithful
**Pre-patch** `SimpleLazyObject(access_value)`: `LazyObject.__class__` is a
property delegating to the wrapped value's `__class__`
(`django/utils/functional.py:331`), so for a wrapped `str`, `isinstance(w, str)`
is `True`. A consumer guarding `if isinstance(value, str): return value`
(`CharField.to_python`, `fields/__init__.py:1023-1025`) returns the wrapper
itself — a non-`str` object — which later fails the SQLite parameter bind
(`probably unsupported type`, the issue's crash). ⇔ `coerce (deferOne v) v.tag
= passthrough` had we set `reported := some v.tag`.

**Post-patch** `lazy(access_value, type(value))()`: returns a `__proxy__`
instance (`functional.py:85`). `type(w)` is `__proxy__`, which is **not** a
subclass of `str` even when `str ∈ resultclasses` (the resultclass only adds
delegating magic methods; `isinstance(w, str)` is `False`). So the consumer
guard is `False` and `to_python` runs `str(w)` → a genuine `str`. ⇔
`coerce (deferOne v) t = genuine v` for every target `t` (`reported = none`).

**G-AX:** there is no axiom over an unchanged callee to validate, so
`axiom_check.py` instead pins the *type-dispatch facts the model depends on* by
executing the REAL Django objects in-container: it builds the pre-patch
`SimpleLazyObject` wrapper and the post-patch `lazy(...,type(value))()` wrapper
over the same closure and asserts (a) `isinstance(pre, type(value))` is `True`
while `isinstance(post, type(value))` is `False`; (b) `CharField.to_python(pre)`
returns a non-genuine value (`type(...) is not str`) while
`CharField.to_python(post)` returns a genuine `str` equal to the value. This
confirms the `coerce`/`Wrapper.reported` model matches real behaviour. Imports
only `django` (the module under change) + stdlib. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13297`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`deferOne`/`deferredOf`/`coerce` (R/I-tagged ops) to Python over the real repo
types and compares against `patch.diff`'s behaviour: for each fuzzed mapping it
runs the patched `_wrap_url_kwargs_with_deprecation_warning` and checks that
every produced wrapper, fed to `CharField.to_python`, yields a **genuine** value
equal to the original — the property `deferredOf` + the genuineness clause
encode. No A-tagged callee is left un-shadowed (there are none).

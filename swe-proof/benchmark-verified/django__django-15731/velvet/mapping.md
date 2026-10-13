# mapping.md — django__django-15731

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 93cedc82f29076c824d476354527af1150888e4f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `django/db/models/manager.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildForwarderMeta (forwarder : CallableMeta) (target : CallableMeta)` | `create_method(name, method)` — `django/db/models/manager.py:83`; specifically the metadata it confers on the inner `manager_method` (`manager.py:84`) before returning it (`manager.py:89`) | the modeled changed function: the proxy-builder whose returned wrapper must be introspection-faithful to `method` |
| `CallableMeta` | the introspectable surface of a Python callable — the result of `obj.__name__`, `obj.__doc__`, and `str(inspect.signature(obj))` | the only-touched-fields structure (mapping.md §2) |
| `propagate (forwarder target : CallableMeta)` *(deep model — A-reference)* | `functools.wraps(method)(manager_method)` (post-patch `@wraps(method)`, `manager.py:84`); i.e. `functools.WRAPPER_ASSIGNMENTS` copy + the `__wrapped__ = method` assignment that `inspect.signature` follows | pure spec: the full metadata-propagation effect of the standard wrapper-decorator facility on the three observed fields; validated `propagate == real functools.wraps effect` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo construct the change removes (refinement audit only, not in the
consumer spec view): the manual two-attribute copy
`manager_method.__name__ = method.__name__` / `manager_method.__doc__ = method.__doc__`
(`manager.py:87-88` @ base_commit), which leaves the wrapper's own
`(*args, **kwargs)` call signature in place — so `inspect.signature` reports the
wrong signature.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a Python callable's introspectable identity, restricted to the three observed fields | `CallableMeta` | `c` (a callable) ↔ `{ name := c.__name__, doc := c.__doc__ ?? "", sig := str(inspect.signature(c)) }`. Only these three fields are modeled; every other attribute a callable carries is orthogonal to the desired behaviour and is omitted from the structure (SPEC_GUIDE §2 "rich object → structure with only the touched fields"). |
| `c.__name__` (a `str`) | `CallableMeta.name : String` | identity on the string |
| `c.__doc__` (a `str` or `None`) | `CallableMeta.doc : String` | identity on the string; a `None` docstring ↔ `""` (the F2P/P2P observables compare a docstring that is a real `str`, see §3) |
| `str(inspect.signature(c))` (a `str`, e.g. `"(objs, batch_size=None, ...)"` or `"(*args, **kwargs)"`) | `CallableMeta.sig : String` | identity on the rendered-signature string. The KEY observation: `inspect.signature` follows `__wrapped__`, so the rendered signature of a `functools.wraps`-decorated wrapper is the target's, whereas a manually-name/doc-copied wrapper renders its own `(*args, **kwargs)`. |
| `target` (the bound argument `method` of `create_method`) | the `target : CallableMeta` parameter | the queryset method being proxied (e.g. `QuerySet.bulk_create`); its metadata is what the wrapper must present |
| `forwarder` (the inner `manager_method` BEFORE metadata is conferred) | the `forwarder : CallableMeta` parameter | the raw proxy: `forwarder.name` is `"manager_method"`, `forwarder.sig` is `"(*args, **kwargs)"` (the generic forwarding signature), `forwarder.doc` is `None ↔ ""`. Read-only: `buildForwarderMeta` never returns any field of `forwarder` (directive 5 frame — see §2.1). |

### 2.1 `mut`-frame discipline (directive 5)
Both `forwarder` and `target` are read-only inputs; NEITHER is declared `mut`.
`buildForwarderMeta` returns a freshly-built `CallableMeta` and copies no field of
`forwarder` into the result — under correct propagation the forwarder's own
generic signature must NOT survive. The post-state is pinned by three `ensures`
that equate every observed field of the result to the corresponding field of
`target`; there is no unconstrained output field (no full-permission analogue).

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `propagate` deep model ↔ `functools.wraps(method)` effect
**Facility:** CPython `functools.wraps` (a partial of `functools.update_wrapper`),
the standard wrapper-decorator. Applied as `@wraps(method)` to `manager_method`,
it (a) copies `WRAPPER_ASSIGNMENTS = ('__module__','__name__','__qualname__',
'__annotations__','__doc__')` from `method` onto `manager_method`, (b) updates
`__dict__`, and (c) sets `manager_method.__wrapped__ = method`. Effect (c) is the
load-bearing one for this issue: `inspect.signature(obj)` follows `__wrapped__`
(unless `follow_wrapped=False`), so the rendered signature of the decorated
`manager_method` resolves to `method`'s real parameter list rather than the
wrapper's `(*args, **kwargs)`.

The changed metadata-propagation operation is modeled **deeply** by `propagate`
in the `pure` region: it maps `(forwarder, target) ↦ { name := target.name,
doc := target.doc, sig := target.sig }` — every one of the three observed fields
is taken from `target`. There is **no consumed `wraps` axiom**; the proof
discharges the postconditions by unfolding `propagate` (`simp [propagate]`).

Restricted to the three observed fields, the real facility's effect is exactly
`propagate`:
- `name`: `WRAPPER_ASSIGNMENTS` copies `__name__` ⇒ wrapper's `__name__ == method.__name__` = `target.name`. ✓
- `doc`: `WRAPPER_ASSIGNMENTS` copies `__doc__` ⇒ wrapper's `__doc__ == method.__doc__` = `target.doc`. ✓
- `sig`: `__wrapped__ = method` ⇒ `str(inspect.signature(wrapper)) == str(inspect.signature(method))` = `target.sig`. ✓

**Soundness check (G-AX):** `axiom_check.py` builds a real forwarding wrapper
with `@functools.wraps(target)` over a battery of real callables — including the
exact F2P target `QuerySet.bulk_create` plus boundary callables (no-arg,
*args/**kwargs, defaults, keyword-only, positional-only, annotated, `None`
docstring) and randomized fuzz signatures — and asserts that for every one, the
real `(__name__, __doc__, str(inspect.signature(·)))` of the decorated wrapper
equals `propagate(forwarder, target)` computed from the target's own observables.
Imports only stdlib `functools` / `inspect`. Exit 0 iff sound.

### 3.2 No A-consumed axioms
There is no unchanged imperative/pure callee whose `ensures` the proof consumes.
`get_queryset()` and `getattr(...)(*args, **kwargs)` (the body of `manager_method`,
`manager.py:84-85`) are UNCHANGED by the patch and the call-time behaviour they
implement is not observed by the F2P/P2P tests this bundle pins (those tests
introspect the wrapper's metadata, they do not invoke it against a DB). They are
therefore not modeled at all — modeling them would be a dead axiom (SPEC_GUIDE §3
/ directive 7). The single trust point is the A-reference of §3.1.

### 3.3 Flag dependency
`inspect.signature(obj, follow_wrapped=True)` is the default; the F2P test calls
`inspect.signature(Article.objects.bulk_create)` with no kwargs, so the
`__wrapped__`-following path (the one the fix relies on) is the one exercised.
axiom_check.py uses the same default, matching the test configuration.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15731`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `propagate` (the I-tagged op: take all three observed fields from
`target`) to Python and diffs it against `patch.diff`'s behaviour — the real
`create_method`-produced wrapper's `(__name__, __doc__, str(inspect.signature))`
at base_commit with the gold patch applied — over the F2P target and ≥10⁵ fuzzed
callables. The deep-model reference `propagate` (A-reference) is the only callee
and it is the op under differential test, not substituted by a model.

# mapping.md — django__django-13297

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8954f255bbf5f4ee997fd6de62cb50fc9b5dd697`, states the type
abstraction, and gives the provenance of the deep-model references (validated by
axiom_check.py / G-AX).

Repo file under change: `django/views/generic/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `wrap_kwarg_value(value)` | the per-entry wrapping inside `_wrap_url_kwargs_with_deprecation_warning(url_kwargs)` — `django/views/generic/base.py:168` (changed body lines 172, 181) | the modeled changed operation: build the deferred entry for one URL kwarg value |
| `Wrapped` (class; NO readable field) | the deferred entry object stored in `context_kwargs[key]` — post-patch `lazy(access_value, type(value))()`, pre-patch `SimpleLazyObject(access_value)` | minimal model of the entry. It deliberately carries NO readable field: the value the entry resolves to is reachable only by RUNNING its deferred computation, which is an effect (see `run_deferral`) |
| `resolves_to(w, value)` *(abstract capability — A-reference)* | the fact that the entry, when its deferred computation is run, yields `value` — i.e. that `access_value()` returns the original `value` | facet (1b): resolution ROUND-TRIP (shared by both constructions, NOT the discriminator). Granted UNCONDITIONALLY by `wrap_opaque`, which declares no result class and so never post-processes what it resolves to, and only OFF the `own_type_unpreparable` family by `wrap_resolvable`, because that is exactly where the real `__cast` hands the value back unchanged; the WHOLE-DOMAIN half of facet (1) is `deferral_of` below. Modeled as an unforgeable `@ContractOnly @Predicate` with NO body, so it is *inert*: an implementation can hold it and hand it on, but can never evaluate it to obtain the value. The value itself is therefore reachable only by RUNNING the deferral (`run_deferral`), which is an effect. See the note on inertness below |
| `deferral_of(w, value)` *(abstract capability — A-reference)* | the fact that the entry was built around THIS value's deferred computation: both images close the entry over the `access_value` closure made for this iteration's `value` (`django/views/generic/base.py:169-178`), so whatever running it hands back is determined by `value` and by nothing else | facet (1a): resolution PROVENANCE, the WHOLE-DOMAIN half of facet (1). An unforgeable `@ContractOnly @Predicate` with NO body on the same terms as `resolves_to` (inert — holdable and passable, never evaluable), naming the SPECIFIC entry AND value, so a capability obtained for a different value does not discharge it. Granted unconditionally by BOTH constructions, so it is shared and never a discriminator. It is what stops the guarded round-trip clause from becoming a licence to substitute an entry built for something else on the `own_type_unpreparable` family: measured on the patched reference, the bytes-arm entry for a value reporting width *n* resolves to *n* bytes and a same-shape value reporting *n+2* resolves to *n+2* bytes, so provenance stays observable exactly where the round-trip is not (axiom_check.py) |
| `own_type_unpreparable(value)` *(deep model — A-reference)* | the value family on which `__proxy__.__prepare_class__` (`django/utils/functional.py:109-127`) cannot prepare a resolution arm that yields `value`. TWO independent routes, both exercised on every build: **(i) ancestor enumeration**, `for type_ in resultclass.mro()` (`functional.py:111`) — with `resultclass = type(value)`, this raises when that type offers no usable zero-argument `mro()` (a type-valued `value`, whose `type(value)` is a metaclass, so `type.mro()` is unbound: `TypeError: unbound method type.mro() needs an argument`; and equally an ordinary non-type `value` whose own class shadows `mro` with a data attribute / one-arg method / property); **(ii) the delegate overlay**, `cls._delegate_bytes = bytes in resultclasses` / `cls._delegate_text = str in resultclasses` / the `assert not (both)` (`functional.py:120-123`) — the `in` tests invoke the METACLASS's `__eq__` on a well-formed `resultclass`, so they can raise (propagating out of the build), can report both arms (firing the `AssertionError`), or can select the **bytes** arm, in which case the build SUCCEEDS and `__cast` takes `__bytes_cast` (`functional.py:142-143`), returning `bytes(func(...))` — a post-processed value, not `value` | the domain marker of the construction's PARTIALITY. Abstract `@ContractOnly @Pure` (uninterpreted, no body): the spec never says which values satisfy it beyond the abstract fact, and an implementation cannot decide it. It does NOT coincide with `isinstance(value, type)` (route (i) contains non-type `mro`-shadowing values; route (ii) contains non-type values whose metaclass misreports the delegate comparisons) and it does NOT coincide with "the build aborts" (route (ii)'s bytes arm returns an entry that a binder accepts and then fails to resolve). Validated against real Python by axiom_check.py §PARTIALITY BOUNDARY over BOTH routes |
| `type_of(value)` *(deep model — A-reference)* | the value's OWN real runtime type — the type the binder's cast resolves to, `type(value._proxy____cast())` (post-patch) | the real runtime type of the value; modeled deeply, validated `type(resolved) is type(value)` by axiom_check.py |
| `binder_accepts(w)` *(abstract capability — A-reference, granted by `wrap_resolvable`)* | the type-directed binder's RECOGNITION test `isinstance(value, Promise)` in `Field.get_prep_value` (`django/db/models/fields/__init__.py:825-828`): `lazy(...)()` returns a `__proxy__`, which subclasses `Promise` (`functional.py:84`), so the binder takes the resolution branch for EVERY value the build returns an entry for — including a route-(ii) bytes-arm entry, where recognition succeeds and the subsequent `_proxy____cast()` then raises. `SimpleLazyObject` is NOT a `Promise`, so the binder never recognises it, at any value | facet (2a), the WHOLE-DOMAIN half of usability: unforgeable `@ContractOnly @Predicate`, granted unconditionally by `wrap_resolvable` and never by `wrap_opaque`. This is what keeps the contract non-silent on the unpreparable family — an entry there is still `Promise`-recognised, so returning a non-`Promise` stand-in is never equivalent |
| `binder_castable(w, cast_to, cast_t)` *(abstract capability — A-reference, granted by `wrap_resolvable`)* | the type-directed parameter binder `Field.get_prep_value` casting the entry (`isinstance(value, Promise)` → `value._proxy____cast()`) to a concrete value at its real type — `django/db/models/fields/__init__.py:825-828` | facet (2b), the PER-VALUE half of usability: the entry is binder-resolvable to `cast_to` at real type `cast_t`. Granted by `wrap_resolvable` only off the `own_type_unpreparable` family, because that is exactly where the real `__cast` hands the value back unchanged. Unforgeable `@ContractOnly @Predicate` (directive-8) |
| `deferrals_run(n)` *(abstract effect ledger — A-reference)* | the number of advisory notices raised so far, i.e. the number of times some entry's deferred computation has actually been run: each run executes `warnings.warn(..., RemovedInDjango40Warning, stacklevel=2)` inside `access_value` (`base.py:173-177`) | facet (3), the preservation carrier: `n` deferred computations have been run. Unforgeable `@ContractOnly @Predicate` with NO body, so the count cannot be reset, walked back, or fabricated |
| `run_deferral(w, value, n)` *(A-consumed axiom)* | running the entry's deferred computation — any access that resolves the deferred stand-in, e.g. `w == value` / `str(w)` / the binder's `_proxy____cast()`; each such run calls `access_value`, which raises exactly one advisory notice and returns the value | the ONLY route from an entry to its value, and it is never free: it advances the ledger `deferrals_run(n)` → `deferrals_run(n + 1)`. It models one RUN, not one access: every run raises its own notice, and the two constructions differ in how many runs a sequence of accesses performs — the binder-resolvable proxy re-runs its closure on EVERY access (`functional.py:76-82`, "Results are not memoized; the function is evaluated on every access"), whereas the non-resolvable stand-in keeps the object it produced in `_wrapped` and re-runs nothing after the first access (`functional.py:375-376` with the `_wrapped is empty` guards at `functional.py:269/276/301`), so only its first access performs a run. The axiom claims one notice per run, which holds of both. It consumes `resolves_to(w, value)` to learn *which* value comes back, and hands that capability on unchanged |
| `wrap_resolvable(value)` *(A-consumed axiom)* | `lazy(access_value, type(value))()` (post-patch `base.py:180`) — `django/utils/functional.py:76` | the post-change construction: a `Promise` the binder resolves; SOLE producer of `binder_castable`. Building it does NOT run the deferred computation, so it touches no ledger. It is PARTIAL, not total, and its partiality has two shapes: on the `own_type_unpreparable` family the real callee either raises instead of returning an entry (routes (i) and (ii)-raise/(ii)-both) or returns an entry the binder accepts and then cannot resolve to the value ((ii)-bytes-arm). The axiom therefore grants `resolves_to` + `binder_accepts` unconditionally and `binder_castable` only off that family, and states the abort as a permitted exceptional exit guarded by `own_type_unpreparable(value)` (measured in axiom_check.py; also diffed in conformance_check.py's partiality lane). The exit is *permitted*, not required, so a construction that succeeded and resolved faithfully on those values as well still refines the spec |
| `wrap_opaque(value)` *(A-consumed axiom)* | `SimpleLazyObject(access_value)` (pre-patch `base.py:172`) — `django/utils/functional.py:356` | the pre-change construction: a non-`Promise` the binder cannot resolve; does NOT grant `binder_castable`. Building it does NOT run the deferred computation either |

The pre-patch repo symbols the change removes (for the refinement audit, not
referenced from the consumer spec view): the import
`from django.utils.functional import SimpleLazyObject` (`base.py:14`) and the
`@SimpleLazyObject` decoration of `access_value` (`base.py:172`). The post-patch
adds `from django.utils.functional import lazy` (`base.py:14`) and
`context_kwargs[key] = lazy(access_value, type(value))()` (`base.py:180`).

Note on inertness (why facet 1 is a predicate and not a projection): reading the
resolution value must cost what it costs in the repo. Two earlier revisions of
this model got that wrong in the same way at two different strengths.

The first bound a *readable field* `Wrapped.forced` to "the result of
`access_value()`". Reading a field is free and silent, whereas running the real
deferred computation raises a user-visible advisory notice at the moment of the
access — so an implementation that resolved the entry while assembling the
mapping was indistinguishable from one that left it deferred.

The second replaced the field with a `@ContractOnly @Pure` *projection*
`resolution_of(w)`. That is no better: a `@Pure` function is callable from an
implementation, so the projection was a second, free, silent route from an entry
to its value, running *around* the ledger instead of through it. The ledger then
constrained only implementations that happened to choose the `run_deferral`
route, which is no constraint at all.

Facet 1 is therefore an *inert* abstract predicate `resolves_to(w, value)`: it
can be held, required, and handed on, but there is no expression that evaluates
it, so `run_deferral` — which charges the ledger — is the only route from an
entry to its value. This is the property the spec needs, because the behaviour
under change is precisely *when* the deferred computation runs.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a URL kwarg value (any object — in the F2P test a `str`) | `int` value-tag | each distinct value is a distinct integer tag; only its real runtime type, its identity through resolution, and whether resolution has happened are observed, so an integer tag is a faithful carrier |
| the value's real runtime type `type(value)` (the type the binder's cast resolves to) | `int` type-tag, produced by `type_of(value)` | each runtime type is a distinct type-tag; equal types ↦ equal tags, distinct types ↦ distinct tags |
| the deferred entry object (`lazy(...)()` / `SimpleLazyObject(...)`) | `Wrapped` (no field) plus the inert capability `resolves_to(w, value)` and the capability `binder_castable(w, …)` | an entry is characterised, for the tested behaviour, by the value it resolves to (an inert capability; the value is obtainable only by running the deferral), and by whether a type-directed binder can resolve it to the value at its real type (the capability) |
| the number of advisory notices raised so far while the mapping is being assembled — one per actual run of some entry's deferred computation (`warnings.warn(...)` in `access_value`) | `int` count carried by the abstract predicate `deferrals_run(n)` | each real run of a deferred computation ↦ exactly one increment of `n`, so the count tracks runs and not accesses: repeated resolutions of the binder-resolvable entry each perform a run and so each increment, while an entry that keeps the object it already produced performs a run only on its first access. A run cannot be un-done, matching the fact that a notice, once raised, has already been delivered (and, under an escalating configuration, has already aborted the caller) |
| the dict rebuild `for key, value in url_kwargs.items(): context_kwargs[key] = <entry>` | the surrounding loop is NOT modeled (unchanged control flow); the single per-value construction operation is modeled. The ledger the modeled operation must hand back unchanged is the mapping-wide count of deferred computations run while the rebuild is in progress | the loop, the key passthrough, the `access_value` closure and the advisory notice it raises are byte-identical pre- and post-patch — only the entry construction on the value changed (refinement.md) |

`str`/object indexing is banned in Nagini and is unnecessary here: the tested
behaviour observes only (a) the resolution value's identity, (b) whether the
entry is binder-resolvable to the value at its real type, and (c) whether any
deferred computation was run — all faithfully carried by integer tags plus the
abstract capability and the abstract ledger.

## 3. Deep-model references (kind-A — checked by G-AX / axiom_check.py)

The resolution capability `resolves_to`, the usability capability
`binder_castable` and the effect ledger `deferrals_run` are abstract
`@ContractOnly @Predicate`s (no body); `own_type_unpreparable` is an abstract,
uninterpreted `@ContractOnly @Pure` domain marker; the three callees
`run_deferral` / `wrap_resolvable` / `wrap_opaque` are A-consumed axioms whose
`Ensures` (and, for `wrap_resolvable`, whose `Exsures`) the proof uses. Their
faithfulness to the real Django callees is validated against real Python
out-of-band:

### 3.1 `type_of` deep model ↔ the value's real runtime type (A-reference)
**Callee:** the binder's cast result `type(value._proxy____cast())`. The post-patch
proxy, when resolved by `Field.get_prep_value`, yields the original value, whose
`type()` is the value's OWN real runtime type — NOT the entry's surface type
(the proxy's own `type()` is `__proxy__`) and NOT the declared result class.
axiom_check.py asserts, on real values, that the binder resolves the post-patch
entry to a value with `type(resolved) is type(value)` for
CharField/IntegerField/FloatField (so `type_of` faithfully models the value's
real type the binder binds at).

### 3.2 `binder_castable` / `wrap_resolvable` / `wrap_opaque` ↔ Django's two constructions + the binder (A-reference)
**Callees:** `django.utils.functional.lazy(func, *resultclasses)`
(`functional.py:76`), `django.utils.functional.SimpleLazyObject`
(`functional.py:356`), and the type-directed parameter binder
`django.db.models.fields.Field.get_prep_value`
(`django/db/models/fields/__init__.py:825-828`):
```
def get_prep_value(self, value):
    if isinstance(value, Promise):
        value = value._proxy____cast()
    return value
```

  * **`lazy(access_value, type(value))()`** builds a `__proxy__(Promise)`
    (`functional.py:85`). Because it IS a `Promise`, `get_prep_value` casts it via
    `_proxy____cast()` (`functional.py:148-154`, returns `func()` == the original
    `value`) and binds it at the value's own real runtime type. Model:
    `wrap_resolvable` grants `binder_castable(w, value, type_of(value))`. This is
    the post-patch behaviour. NOTE the surface type of the proxy is `__proxy__`,
    not `type(value)`; and the SAME binder-resolution succeeds for ANY result
    class (`object`, `int`, `str` — verified in-container), so the discriminator
    is binder-resolvability, NOT `type(entry) == type(value)`.

  * **`SimpleLazyObject(access_value)`** is a `LazyObject`, NOT a `Promise`
    (`functional.py:356`, base `LazyObject` at `functional.py:251`). Because
    `isinstance(value, Promise)` is False, `get_prep_value` leaves it an
    unresolved deferred stand-in; the DB layer then rejects it ("Error binding
    parameter 0 - probably unsupported type" for text, `TypeError ... expected a
    number but got <SimpleLazyObject>` for numeric fields). Model: `wrap_opaque`
    grants only `resolves_to(w, value)`, NOT `binder_castable`. This is the
    pre-patch behaviour and the bug.

  * **the post-change construction is PARTIAL where the pre-change one is
    total.** `lazy(f, resultclass)` prepares its proxy class from the declared
    result class, which for a value that is itself a type object means preparing
    from a metaclass; that preparation exercises a bound-method path that raises
    (`unbound method type.mro() needs an argument`) before any entry exists.
    `SimpleLazyObject(access_value)` takes no result class and so never does
    this. Model: `wrap_resolvable` carries `Exsures(Exception,
    own_type_unpreparable(value))`; `wrap_opaque` carries no exceptional exit. The
    aborting path raises ZERO advisory notices — the failure happens during class
    preparation, before the deferred closure could be run — which is why the
    model preserves the ledger on the exceptional exit too. Measured
    bidirectionally in axiom_check.py (13 type-valued inputs raise with 0
    notices; 17 non-type inputs succeed; the pre-change construction is total on
    the same type-valued family) and diffed against the real patched function in
    conformance_check.py's partiality lane.

  * **the family has TWO shapes, and the SILENT one is why facet (1) is
    split.** Route (ii)'s bytes arm does not abort: `__prepare_class__`
    completes, the entry IS a `Promise` the binder recognises, and `__cast`
    becomes `__bytes_cast` (`functional.py:142-143`), which returns
    `bytes(func(...))`. Where `bytes(value)` itself raises, resolution raises
    (`EqBytesOnly()` → TypeError). Where it does NOT — a value whose class also
    offers `__index__` — resolution SUCCEEDS and hands back a well-formed
    object of another type, with no exception and no extra advisory notice.
    That silent shape is the witness that an UNCONDITIONAL round-trip clause
    predicts an outcome the real callee does not produce, and it is what
    licenses the guard on `resolves_to` (facet 1b) and on `binder_castable`
    (facet 2b). Measured on the patched reference in axiom_check.py: build OK
    with 0 notices, `isinstance(entry, Promise)`, `_delegate_bytes and not
    _delegate_text`, resolution OK with exactly 1 notice, the resolved object
    neither `==` the value nor of the value's type, and `get_prep_value` hands
    that same non-round-tripped object on to the consumer — while what comes
    back IS derived from this value (see `deferral_of`), which is why facet
    (1a) stays unconditional. conformance_check.py diffs both sub-shapes
    against the real patched function in its non-aborting lane, and
    properties.py fences the relaxation from the other side with three
    on-family rivals (`weak-family-substituted-entry`,
    `weak-family-binder-refused`, `weak-family-deferral-run`), each rejected
    by the clause that stayed unconditional there (P2a, P3a, P1).

### 3.3 `deferrals_run` / `run_deferral` ↔ the real advisory-notice effect (A-reference)
**Callee:** the deferred closure the operation stores, `access_value`
(`base.py:171-177`), whose body is
```
def access_value(key=key, value=value):
    warnings.warn(
        'TemplateView passing URL kwargs to the context is deprecated. '
        'Reference %s in your template through view.kwargs instead.' % key,
        RemovedInDjango40Warning, stacklevel=2,
    )
    return value
```
Running the entry's deferred computation calls this closure, so it raises exactly
one `RemovedInDjango40Warning` and returns the value. Two facts make the ledger a
faithful model:

  * **the run is the only route to the value, and it is never free.** Every way of
    obtaining a deferred entry's value — ordinary access (`w == value`,
    `str(w)`), or the binder's `_proxy____cast()` — goes through `access_value`
    and therefore raises the notice. There is no side channel that reads the
    value without the effect, which is why the model records facet 1 only as the
    INERT capability `resolves_to(w, value)` — holdable but not evaluable — so
    that `run_deferral`, which advances the count, is the sole route from an
    entry to its value.
  * **the count is monotone and un-restorable.** Each run raises its own notice,
    and a notice once raised has already been delivered to the caller, so the
    count only ever goes up. The predicate has no body, so a proof cannot `Fold`
    a count back from `n + 1` to `n`. Note the ledger counts RUNS and not
    accesses, because the two constructions differ on exactly that: `lazy`'s
    `__proxy__.__cast` / `__wrapper__` call `func()` on EVERY access
    (`functional.py:76-82`, "Results are not memoized; the function is evaluated
    on every access"), so each repeated access of that entry is a fresh run and
    raises its own notice — which is what axiom_check.py measures over three
    repeats; `SimpleLazyObject` instead keeps the object its setup produced in
    `_wrapped` (`functional.py:375-376`, reached only while `_wrapped is empty`,
    `functional.py:269/276/301`), so its FIRST access performs the run and
    raises the notice and later accesses of that same entry perform none.
    `run_deferral` models one run, which costs exactly one notice on either
    construction; it does not claim that every access is a run.

The consequence the model relies on: because the caller's configuration may
escalate this notice into an error (a project may configure the advisory category
as an error, which is exactly what the test configuration for this area does),
running a deferred computation while the mapping is being assembled is observably
wrong in two ways — the notice is attributed to the assembly instead of to the
consumer's access, and under an escalating configuration the assembly raises
before any entry exists. Hence `wrap_kwarg_value` must hand the ledger back at
its entry count.

**Soundness check (G-AX):** `axiom_check.py` constructs, for representative
values across CharField/IntegerField/FloatField (incl. the F2P `str` case
`'Rene Magritte'`), both the real `SimpleLazyObject(access_value)` (pre-patch)
and the real `lazy(access_value, type(value))()` (post-patch), with the real
notice-raising closure and the real `Field.get_prep_value` binder, and checks:

  1. both constructions RESOLVE to the original value when their deferred
     computation is run through ordinary access (`facet 1`, shared);
  2. the post-patch entry is a `Promise` AND the binder resolves it to the
     original value with `type(resolved) is type(value)` (`facet 2`, post-patch
     == `wrap_resolvable` grants `binder_castable(w, value, type_of(value))`);
  3. the pre-patch entry is NOT a `Promise` AND the binder does NOT resolve it
     to a concrete bindable value (`facet 2`, pre-patch == `wrap_opaque` grants
     no capability), reproducing the "unsupported type" binding failure on the
     real callee;
  4. **the effect ledger (`facet 3`):** CONSTRUCTING either entry raises ZERO
     advisory notices (so `wrap_resolvable` / `wrap_opaque` touch no ledger and
     the preservation obligation is satisfiable), while EACH resolution that
     RUNS the deferred computation raises EXACTLY ONE — including the repeated
     resolutions of the binder-resolvable entry, each of which is a fresh run,
     and including resolution through the binder (no side channel).
     Under a configuration that escalates the notice to an error, CONSTRUCTION
     still succeeds while RESOLUTION raises. Both constructions agree on all of
     this, so deferral-preservation is a property the pre-change code ALSO had:
     it is a preservation claim, not the patch's delta.
  5. **alternative-fix admission (the verdict's external-resolver probe):**
     `lazy(..., object)()`, `lazy(..., int)()`, `lazy(..., str)()` are each a
     binder-resolvable `Promise` that the binder resolves to the value at its
     real type, and each raises no notice at construction — so BOTH
     discriminators ADMIT them (they are `wrap_resolvable` and they preserve the
     ledger), confirming the spec pins binder-resolvability + deferral
     preservation, not the entry's surface type and not the gold's exact result
     class.

It imports only Django's own `django.utils.functional`,
`django.db.models.fields`, `django.utils.deprecation`, and the stdlib; nothing
test-specific. Exit 0 iff every obligation holds.

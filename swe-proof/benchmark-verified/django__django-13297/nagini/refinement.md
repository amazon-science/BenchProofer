# refinement.md — django__django-13297

The operation-by-operation correspondence between `model.py`'s implementation
(the `wrap_kwarg_value` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == a real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested input, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `_wrap_url_kwargs_with_deprecation_warning`

Gold hunks (`django/views/generic/base.py`):
```
-from django.utils.functional import SimpleLazyObject
+from django.utils.functional import lazy
 ...
     for key, value in url_kwargs.items():
         # Bind into function closure.
-        @SimpleLazyObject
         def access_value(key=key, value=value):
             warnings.warn( ... RemovedInDjango40Warning, stacklevel=2, )
             return value
-        context_kwargs[key] = access_value
+        context_kwargs[key] = lazy(access_value, type(value))()
     return context_kwargs
```

The change is one operation: how each entry's `value` is wrapped for deferred
consumption. Pre-patch wraps with `SimpleLazyObject`, which is NOT a `Promise`;
post-patch wraps with `lazy(access_value, type(value))()`, which IS a `Promise`.
Everything else in the function (the loop, the key passthrough, the
`access_value` closure that returns `value`, the deprecation warning it raises)
is unchanged.

### The real F2P-observable mechanism (why one discriminator is binder-resolvability)

The F2P test (`test_template_params_filtering`) passes the wrapped value into an
ORM lookup, whose type-directed parameter binder is
`django.db.models.fields.Field.get_prep_value`
(`django/db/models/fields/__init__.py:825-828`):
```
def get_prep_value(self, value):
    if isinstance(value, Promise):
        value = value._proxy____cast()
    return value
```
- **Post-patch** `lazy(access_value, type(value))()` is a `Promise`, so
  `get_prep_value` casts it via `_proxy____cast()` (== `func()` == the original
  `value`) and binds it **at the value's own real runtime type** — verified
  in-container: `get_prep_value(post)` returns `value` with
  `type(resolved) is type(value)` for str/int/float.
- **Pre-patch** `SimpleLazyObject(access_value)` is NOT a `Promise`, so
  `get_prep_value` leaves it an unresolved deferred stand-in; the DB layer then
  rejects it ("Error binding parameter 0 - probably unsupported type" for
  CharField; `TypeError ... expected a number but got <SimpleLazyObject>` for
  numeric fields) — the bug.

Crucially, the discriminator is NOT the wrapper's surface `type()`: the real
`__proxy__`'s own `type()` is `__proxy__` (NOT `str`/`int`), and the SAME
binder-resolution succeeds for ANY declared result class (`object`, `int`,
`str` — all verified in-container). So the property the F2P test observes is
**"the binder can resolve this Promise to the value at its real type"**, modeled
as the unforgeable capability `binder_castable(w, value, type_of(value))`, NOT
`type(wrapper) == type(value)`.

### The real P2P-observable mechanism (why deferral preservation is also a discriminator)

Binder-resolvability alone does not characterise the changed operation. The
function's whole point is that the value is produced **later**, by a deferred
computation that also raises a user-visible advisory notice
(`warnings.warn(..., RemovedInDjango40Warning, stacklevel=2)` inside
`access_value`, `base.py:173-177`). Two properties of the real code make the
TIMING of that notice observable, and both hold in the pre-patch and the
post-patch images alike:

  * **Building the entry runs no deferred computation.** Neither
    `SimpleLazyObject(access_value)` nor `lazy(access_value, type(value))()`
    calls `access_value`; the notice is raised only when something actually
    reaches for the value. Verified in-container on both images: building 9
    entries raises 0 notices.
  * **The notice may be escalated to an error by the caller's configuration.**
    A project (and the test configuration for this area) may configure the
    advisory category as an error, so a run performed while the mapping is being
    assembled does not merely mis-attribute the notice — it raises, aborting the
    assembly before any entry exists.

Consequently the surrounding rebuild is observed not only through the entries it
produces but through **how many deferred computations were run while producing
them**, which must be zero. The P2P tests in
`tests/generic_views/test_base.py` observe exactly this: one asserts that the
notice is raised at the point of template access and attributed to it, and one
renders a view twice and requires the second render to behave like the first —
both fail if the assembly resolves the entries on the spot. This is a
**preservation** obligation: it is a property the pre-patch code already had, and
the gold patch keeps. It is modeled as the abstract effect ledger
`deferrals_run(n)`: the operation is given the ledger at a count and must hand it
back at the same count.

| # | model.py impl op (`wrap_kwarg_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: int` | the loop variable `value` (one URL kwarg value) | R | an arbitrary value ↔ an integer value-tag; only its identity-through-resolution and its real runtime type (`type_of`) are observed (mapping.md §2). |
| A2 | the surrounding rebuild (loop over entries, key passthrough, `access_value` closure, the advisory notice it raises) | `for key, value in url_kwargs.items(): … context_kwargs[key] = …` | I | byte-identical before and after the gold patch — not part of the change. The model factors it out and contracts only the one changed per-value construction operation; the loop is the same concrete control flow in both images (NOT a "changed inexpressible op"). The ledger `deferrals_run` the contracted operation must preserve is the count of deferred computations run while this unchanged rebuild is in progress. |
| A3 | `wrap_resolvable(value)` — produces an entry that carries THIS value's deferred computation (grants `deferral_of(Result(), value)`) and is binder-RECOGNISED (grants `binder_accepts(Result())`) at every value, resolves to `value` and is binder-resolvable (grants `binder_castable(Result(), value, type_of(value))`) off the `own_type_unpreparable` family, and does NOT run its deferred computation | `lazy(access_value, type(value))()` | A-consumed | the changed construction is the post-patch `lazy(...)()`. The proof consumes `wrap_resolvable`'s `Ensures`. Its faithfulness to the real callee is the A-reference below (A5/A6/A8), validated by axiom_check.py against the real `lazy(...)()` + `get_prep_value` + the real notice. WEAKEST sufficient: it claims only provenance + binder-recognition on the whole domain, resolves-to-value + binder-resolvable off the `own_type_unpreparable` family, and no-ledger-effect; never no-raise/exact-surface-type/exact result class. |
| A4 | `Implies(not own_type_unpreparable(value), resolves_to(Result(), value))` (facet 1b, shared) | `access_value` returns `value`; the `lazy` proxy resolves to `func()` (`functional.py:135,148,154`); the pre-patch `SimpleLazyObject` also resolves to `value` | A-reference + I | running either entry's deferred computation yields the original value. Shared with the pre-patch — this is the faithfulness clause, NOT a discriminator (axiom_check.py asserts both `post == value` and `pre == value`). It is modeled as an INERT abstract capability rather than a readable field or a `@Pure` projection precisely so that obtaining the value at runtime costs a `run_deferral` (see A8): a field can be read and a `@Pure` projection can be *called*, both for free and silently, and under either one resolving early and not resolving would be indistinguishable. A predicate with no body can be held and handed on but never evaluated, so no free route to the value exists. The clause is GUARDED because route (ii)'s bytes arm resolves to `bytes(func(...))` rather than to `value` (see A9); `wrap_opaque` grants it unconditionally because it declares no result class and so never post-processes. |
| A4b | `deferral_of(Result(), value)` (facet 1a, shared, UNCONDITIONAL) | both images close the entry over the `access_value` closure built for this iteration's `value` (`django/views/generic/base.py:169-178`), so what running the entry hands back is determined by that value and by nothing else | A-reference + I | the WHOLE-DOMAIN half of facet (1), and what keeps the guard on A4 from being a licence to substitute someone else's entry: on the guarded family an implementation still may not hand back an entry built around another value. Modeled as a second INERT abstract capability on the same terms as `resolves_to`, naming entry AND value so it cannot be laundered across values. Measured where it matters — on the family, where the round-trip is gone: the bytes-arm entry for a value reporting width *n* resolves to *n* bytes and a same-shape value reporting *n+2* resolves to *n+2* bytes, so the entry demonstrably carries THIS value's computation (axiom_check.py). properties.py's `weak-family-substituted-entry` is the rival this clause alone rejects. |
| A5 | `binder_castable(Result(), value, type_of(value))` (facet 2, the usability discriminator) granted by `wrap_resolvable` | `lazy(access_value, type(value))()` is a `Promise`; `Field.get_prep_value` casts it (`_proxy____cast()` == `value`) and binds at the value's real type | A-reference | the **usability** capability: the post-patch proxy is binder-resolvable to the value at its own real type. axiom_check.py builds the real `lazy(...)()` and the real `Field.get_prep_value`, asserts the binder resolves it to `value` with `type(resolved) is type(value)`, for CharField/IntegerField/FloatField (mapping.md §3.2). Validated, NOT consumed-as-oracle: `binder_castable` is an abstract `@ContractOnly @Predicate` (no body) granted ONLY by `wrap_resolvable` (directive-8 capability grounding). Since the clause is guarded, this is the PER-VALUE half of usability; the whole-domain half is A5b. |
| A5b | `binder_accepts(Result())` (facet 2a, the WHOLE-DOMAIN usability discriminator) granted unconditionally by `wrap_resolvable` | the binder's RECOGNITION test `isinstance(value, Promise)` in `Field.get_prep_value` (`django/db/models/fields/__init__.py:825-828`): `lazy(...)()` returns a `__proxy__`, which subclasses `Promise` (`functional.py:84`), so the binder takes the resolution branch for EVERY value the build returns an entry for — including a route-(ii) bytes-arm entry, where recognition succeeds and resolution then diverges. `SimpleLazyObject` is not a `Promise`, so the binder never recognises it, at any value | A-reference | recognition is what the pre-patch entry fails at EVERY value, so with `binder_castable` guarded this is the clause that carries the discrimination: `model_prepatch.py` fails on it (see below). Unforgeable `@ContractOnly @Predicate` (no body), granted only by `wrap_resolvable`. Kept UNGUARDED deliberately — there is no value family on which handing back a stand-in the binder refuses is acceptable, which is what keeps the guards on A4/A5 from going silent on that family. axiom_check.py asserts the post-change entry is a `Promise` at every probed value including the two bytes-arm members, and that the pre-change entry is a `Promise` at none of them (mapping.md §3.2); properties.py's `weak-family-binder-refused` is the rival this clause alone rejects. |
| A6 | absence of `binder_castable` from `wrap_opaque` (pre-patch facet 2) | `SimpleLazyObject(access_value)` is NOT a `Promise`; `Field.get_prep_value` does not cast it; the DB binder rejects it | A-reference | the pre-patch entry is NOT binder-resolvable. axiom_check.py asserts `not isinstance(pre, Promise)` and that `get_prep_value(pre)` does not yield a concrete bindable value (mapping.md §3.2), reproducing the "unsupported type" failure on the real callee. `wrap_opaque`'s `Ensures` grants only `resolves_to(w, value)`, never `binder_castable`. |
| A7 | `type_of(value)` (the value's real runtime type) | the type the binder's cast resolves to (`type(value._proxy____cast())`) | A-reference | `type_of` is the deep model of the value's OWN real runtime type. axiom_check.py asserts `type(resolved) is type(value)` for the value the binder casts to (mapping.md §3.1). NOT pinned to the entry's surface type (which is `__proxy__`). |
| A8 | `Ensures(deferrals_run(0))` against `Requires(deferrals_run(0))` (facet 3, the preservation discriminator); `run_deferral` as the only route to a value | building either entry does not call `access_value`, so no advisory notice is raised while the mapping is assembled; every access that RUNS an entry's deferred computation (ordinary access or the binder's `_proxy____cast()`) calls `access_value` and raises exactly one notice; the post-change proxy re-runs the closure on every access, while the pre-change stand-in keeps what it produced and so runs it only on the first access — the ledger counts runs, not accesses | A-reference + I | the **preservation** obligation, unchanged by the gold patch and therefore a P2P property. axiom_check.py asserts on the real callees: 0 notices while CONSTRUCTING (both images), exactly 1 per run — including each of three repeated resolutions of the binder-resolvable entry, and including binder resolution — and that under an escalating configuration construction survives while resolution raises (mapping.md §3.3). Modeled as the abstract ledger `deferrals_run(n)` (`@ContractOnly @Predicate`, no body): `run_deferral` advances it `n → n + 1` and nothing restores it, so "the ledger comes back at its entry count" is a genuine ran-no-deferral obligation on every path. It does NOT pin WHICH construction is used, HOW MANY entries are built, or any iteration order — only that no deferred computation was run (the `pos-extra-entry-unrun` positive in properties.py is the anti-over-fit control: building extra entries still verifies). |

| A9 | `Exsures(Exception, own_type_unpreparable(value))` and `Exsures(Exception, deferrals_run(0))` on the contracted operation (and on `wrap_resolvable`), together with `binder_castable` being granted only under `not own_type_unpreparable(value)` while `binder_accepts` is granted unconditionally | `__proxy__.__prepare_class__` (`django/utils/functional.py:109-127`) prepares the entry from `resultclass = type(value)` in two steps, and BOTH can come out unusable. (i) `for type_ in resultclass.mro()` (`:111`) raises when that type has no usable zero-arg `mro()` — a type-valued `value` (`type.mro()` unbound) and equally an ordinary non-type `value` whose class shadows `mro`. (ii) `bytes in resultclasses` / `str in resultclasses` / `assert not (both)` (`:120-123`) run the metaclass's `__eq__`, which may raise, may report both arms (AssertionError), or may select the **bytes** arm — and in that last case the build SUCCEEDS while `__cast` becomes `__bytes_cast` (`:142-143`), returning `bytes(func(...))`, so the entry is `Promise`-recognised by the binder and then fails to resolve to `value`. Measured on the patched reference: `EqBoom()` -> RuntimeError, `EqAll()` -> AssertionError, `EqBytesOnly()` -> build OK + `_proxy____cast()` raises TypeError, and `IntBytesArm(5)` -> build OK with 0 notices, the entry IS a `Promise`, `_delegate_bytes and not _delegate_text`, and resolution SUCCEEDS with exactly one notice while handing back five bytes instead of the value — the SILENT shape, in which nothing raises anywhere and `get_prep_value` passes that object on; all with 0 notices on the aborting exits; `SimpleLazyObject` is total and faithful on all of them. | A-reference | the operation is **partial in two ways**, and the spec states both rather than pretending totality or shrinking its input domain. The domain stays every value (`Requires` unchanged); the exceptional exit is *permitted*, not required, and is guarded — it may be taken only on the family the real callee actually fails on, and it may not launder an effect, because the ledger must come back at its entry count on the aborting path too. The round-trip clause (A4) is guarded by the SAME family, because on it the real `__cast` may post-process the value instead of returning it — silently, on the `IntBytesArm` witness. Two clauses are NOT guarded, and they are what stop the guard from becoming a licence: recognition (A5b/`binder_accepts`), because the real entry is a `Promise` at every value, so a binder-refused stand-in is never equivalent; and provenance (A4b/`deferral_of`), because the real construction always closes over THIS value's computation, so an entry built around another value is never equivalent either. Not an over-fit: no exception type or message is pinned, `pos-never-aborts` verifies, and the alternative-fix admissions (`lazy(..., object/int/str)`) are unaffected. Not an under-fit either: three properties.py rivals live INSIDE the guarded branch and are each rejected there — `weak-family-substituted-entry` by `deferral_of(Result(), value)`, `weak-family-binder-refused` by `binder_accepts(Result())`, and `weak-family-deferral-run` by `deferrals_run(0)` — so the guard relaxes two clauses rather than the contract. |

The changed content of the operation — the entry must be **usable by a
type-directed parameter binder**, rather than an opaque stand-in the binder
refuses outright — lives in the two binder clauses: `binder_accepts(Result())`
on the whole domain, and `binder_castable(Result(), value, type_of(value))` off
the `own_type_unpreparable` family. The pre-patch wraps with the non-`Promise`
`SimpleLazyObject`; `model_prepatch.py` reproduces that (`wrap_opaque(value)`,
which grants neither capability) and **fails** the postcondition
`binder_accepts(Result())` — measured on the twin as `Postcondition of
wrap_kwarg_value might not hold. There might be insufficient permission to
access binder_accepts(Result())` — which is exactly the spec sensing the change
(G-DIFF). The refuting clause is deliberately the UNGUARDED one: a twin can
never discharge it anywhere, whereas the guarded `binder_castable` clause is
vacuous on part of the domain and so is no longer what refutes the twin. The preserved content — the entry
must still be **deferred**, i.e. built without running any deferred computation —
lives in `Ensures(deferrals_run(0))`; it is satisfied by both images of the real
code and rules out "fixes" that obtain binder-resolvability at the cost of
resolving the entry during assembly.

## B. Capability grounding (directive 8) and no kind-3 steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — which deferred construction the value is given, and crucially
whether a type-directed binder can resolve it — is the difference between two
A-consumed construction callees (`wrap_resolvable` vs `wrap_opaque`). The
discriminating fact is a **control-flow / capability effect** (resolvable-vs-not)
with no plain value-level discriminator (both entries resolve to the same value),
so per directive 8 it is grounded as an **unforgeable capability predicate**
`binder_castable(w, cast_to, cast_t)`: an abstract `@ContractOnly @Predicate`
(no body) that an implementation cannot `Fold` into existence and that names the
specific entry / value / real-type so it cannot be laundered across
value-equal copies. Its SOLE producer is `wrap_resolvable`'s `Ensures`. This is
NOT an answer-key oracle on a result value (directive-8 anti-echo): a wrong impl
cannot `return materialize(oracle(x))` — there is no value to echo; the capability
can only be obtained by actually performing the binder-resolvable construction.

The second obligation is likewise an effect with no value-level discriminator:
whether the deferred computation has been RUN is not visible in the value the
entry resolves to (it is the same value either way), only in whether the advisory
notice has already been delivered. It is therefore grounded the same way, as the
abstract monotone ledger `deferrals_run(n)` (`@ContractOnly @Predicate`, no body):
`run_deferral` consumes `deferrals_run(n)` and produces `deferrals_run(n + 1)`,
and because there is no body there is no `Fold` that walks the count back, so a
proof cannot restore a ledger it has advanced. Two model choices make this
obligation bite rather than being decorative:

  * `Wrapped` carries **no readable field and no evaluable projection**: the
    resolution fact is recorded only as the INERT abstract capability
    `resolves_to(w, value)`, which an implementation can hold and pass on but has
    no way to evaluate. Two earlier revisions of this model failed this the same
    way at different strengths. The first stored the resolution in a plain field:
    reading a field is free and silent, so running the deferral early was
    indistinguishable from not running it. The second replaced the field with a
    `@ContractOnly @Pure` projection `resolution_of(w)` — but a `@Pure` function
    is *callable from an implementation*, so it was simply a second free, silent
    route to the value that went AROUND the ledger, leaving the ledger a
    constraint only on implementations that chose to use `run_deferral` at all.
    An abstract predicate has no such route: no expression evaluates it, so
    `run_deferral` — which moves the ledger — is the only way to get from an
    entry to its value. This is what makes obligation (3) bite on every
    implementation rather than on a cooperative one.
  * the ledger is counted, not boolean, so running SOME OTHER entry's deferral
    is equally forbidden: the obligation is "this operation ran no deferred
    computation", not "it did not resolve the entry it returns".

The pre-patch repo symbols `lazy` / `SimpleLazyObject`, the binder
`Field.get_prep_value`, and the notice-raising closure `access_value` appear only
as **A-references** that G-AX validates the A-consumed axioms against
(mapping.md §3). The loop and the closure are unchanged (A2, tag I).

## C. verify(model) ⇒ resolved

`wrap_kwarg_value` verifies only if, on every value, it either aborts on the
guarded partial family without having run a deferred computation (A9) or returns
an output that (1) resolves to the original value (A4) AND (2) holds
`binder_castable(Result(), value, type_of(value))` (A5) AND (3) was produced while
running NO deferred computation, i.e. handing the ledger back at its entry count
(A8). By R (value ↔ int tag, entry ↔
`Wrapped`) and I (the unchanged loop/closure/notice, A2) the verified
construction equals `lazy(access_value, type(value))()` on the tested input; by
G-AX (A5/A6/A7) the real `lazy(...)()` proxy IS binder-resolvable to the value at
its real type while the real `SimpleLazyObject` is NOT, and (A8) constructing
either real entry runs no deferred computation while every resolution runs one,
so the A-consumed axioms faithfully model the real callees. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE,
`test_template_params_filtering`: filtering by the wrapped URL kwarg succeeds;
and the deprecation/caching tests in the same module continue to pass, which is
what (3) preserves).

The spec ADMITS the alternative correct fixes (`lazy(..., object)()`,
`lazy(..., int)()`, `lazy(..., str)()`): each is a binder-resolvable `Promise`
that resolves to the value at its real type and raises no notice when built,
hence `wrap_resolvable` granting the same capability and preserving the ledger —
confirming the discriminators pin the observable properties, not incidental
correlates (the verdict's alternative-fix admission test; axiom_check.py probes
it directly). Neither obligation constrains how many entries an implementation
builds, in what order, or with which exception messages: the
`pos-extra-entry-unrun` positive in properties.py verifies while building a
spare entry, so (3) forbids RUNNING a deferral, not allocating; and the
`pos-never-aborts` positive verifies, so A9 permits an exceptional exit without
demanding one. Obligation (3) is what rejects the family of wrong "fixes" that
build the binder-resolvable entry and then read its value out during assembly —
whether they discard the reading, branch on it, or return a re-wrapping of it:
each is exactly a fix that restores `test_template_params_filtering` while
breaking `test_template_params_warning` and `test_cached_views`, because the
notice is delivered at assembly time instead of at template access. The reject
lane in properties.py carries one such case per route (hand-on, control-flow,
data-flow). The trust points
are exactly the two of PLAN §1.1: callee soundness (G-AX) and refinement
fidelity (this document, G-EQ).

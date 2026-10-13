# refinement.md — django__django-14787

Operation correspondence between `implementation_attachIdentity` (Solution.lean)
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: the wrapper-construction step inside `_multi_decorate._wrapper`

The gold patch changes one line in `_multi_decorate`'s inner `_wrapper`:

```python
- bound_method = partial(method.__get__(self, type(self)))
+ bound_method = wraps(method)(partial(method.__get__(self, type(self))))
```

`partial(...)` produces a freshly synthesised callable that carries **none** of a
function's identity attributes (`__name__`, `__qualname__`, …). User decorators
applied to `bound_method` (the `for dec in decorators` loop on the next line, and
the eventual `dec`-supplied wrapper) inspect those attributes — e.g. `func.__name__`.
The fix transfers `method`'s identity onto the synthesised callable via
`wraps(method)(…)` (i.e. `functools.update_wrapper`), so the synthesised callable
exposes `method`'s identity.

The modeled domain is the **identity metadata of the synthesised callable, plus
its call shape**: the three standard wrapper-assignment attributes that are
genuinely absent on a bare `partial` and present on a real function/method
(`__name__`, `__module__`, `__qualname__`) — each carried at BOTH of the layers a
Python attribute lives at, what a reader is answered with (`observed`) and what
the object's own attribute table holds (`ownEntry`) — a flag recording whether the
callable transparently delegates to another (`__wrapped__`), and a flag recording
whether the callable is invokable with the decorated call's own arguments alone
(`selfSufficient`).

Both layers are in the domain because `wraps` reads and writes both, in two
separate passes, and because the `source` this construction is handed is often a
callable whose two layers DISAGREE: `_multi_decorate` itself produces such
callables (`django/utils/decorators.py:13-19,45-49` — `_update_method_wrapper`
followed by `update_wrapper(_wrapper, method)` leaves the inner wrapper answering
with the original method's name while its own table holds the decorator's), and
stacking two decorators feeds one straight back in as `method`. A single-layer
model of the identity surface agrees with the real construction on every source
whose layers coincide and mispredicts every source where they differ — including
that one — so the second layer is not a refinement of the domain but part of it.
See mapping.md §2 (`IdentityAttr`, `WRAPPER_UPDATES`). The call-shape flag is part of the domain
because the construction has two jobs at once, not one: the object handed to the
decorators must carry `method`'s identity AND still be the instance-bound object
they can call as `bound_method(*args, **kwargs)`. Modeling only the metadata
conflates the synthesised callable with the original `method` — they are
metadata-indistinguishable after the transfer — even though calling the latter
without the instance raises
`TypeError: … missing 1 required positional argument: 'self'` and breaks both the
FAIL_TO_PASS observable and the pre-existing decorator tests. (`__doc__` is excluded
for a different reason: it is not exercised by the FAIL_TO_PASS test, and a `partial`
carries a non-`None` `__doc__` natively, so the destination is never attribute-bare
on that facet. It is NOT excluded for holding a `None` value — the three-state
`AttrSlot` carrier models that state directly on each attribute it does cover, so
"the source holds the attribute but its value is `None`" is expressible rather than
a reason to drop a facet; see mapping.md §2.) `method.__get__(self,
type(self))` (the bound descriptor) and `partial(...)` itself produce the
*synthesised callable*; the identity-bearing object whose attributes the fix
copies FROM is `method` (modeled as `source`).

| # | `implementation_attachIdentity` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `source : CallableAttrs` (input) | `method` — the original callable whose identity must be preserved | R | a Python callable's identity surface ↔ the `CallableAttrs` record of its standard wrapper-assignment attributes, each at both of its layers (`IdentityAttr`; see mapping.md §2). |
| 2 | `let mut bound := bareCallable` | `partial(method.__get__(self, type(self)))` — a freshly synthesised callable | R | a `partial` object answers for NONE of the three attributes — reading `__name__`, `__module__` or `__qualname__` on a fresh `partial` raises `AttributeError` — and its own attribute table is EMPTY; modeled as `bareCallable` (all three vacant at both layers, `wrapped := false`). Measured, not assumed: axiom_check.py's `check_destination_transparency` reads all three at both layers on a fresh `partial` in the instance's own interpreter and fails the gate if any is answered. Its call shape IS modeled: the descriptor bind has already absorbed the instance, so the object takes the decorated call's own arguments (`selfSufficient := true`). This op also fixes WHICH KIND of destination the next op writes to, and that is load-bearing rather than incidental: a `partial` has no slot for these attributes, so once its table holds one it answers from that table — the destination is table-transparent, both of op 3's passes land in the same storage, and the second decides the answer. A function destination would not behave that way. |
| 3 | `bound := copyIdentity source bound` | `wraps(method)( … )` applied to the partial (i.e. `functools.update_wrapper(partial, method)`) | A-reference | `wraps`/`update_wrapper` is FOUR steps in order, and `copyIdentity`/`IdentityAttr.transfer` has a leg for each. (i) the `assigned` loop over `WRAPPER_ASSIGNMENTS`: per attribute, `getattr` guarded by `except AttributeError`, then `setattr` — held-ness ALONE and never the value, so an attribute the source is observed to hold is copied even when its value is `None`, overwriting the destination's ⇒ `src.observed.overlay dst.ownEntry` (a two-state present/absent encoding would wrongly predict the destination's value at a held-but-`None` source; mapping.md §2). (ii) the `updated` loop over `WRAPPER_UPDATES == ('__dict__',)`: `getattr(wrapper,'__dict__').update(getattr(wrapped,'__dict__',{}))`, one whole-table merge of the source's OWN table onto the wrapper's ⇒ the outer `src.ownEntry.overlay …`. Since op 2's destination is a `partial`, step (i)'s `setattr` wrote that very table, so step (ii) is the LATER write to the same storage and its entry survives — which is why the model composes the two in that order and not the reverse. What the result is then observed to hold is its new table entry laid over what the destination already answered (`entry.overlay dst.observed`), and since the destination answers for none of the three on its own account, what a reader observes on the result is exactly the transferred entry — held where the source supplied one at either layer, and absent where it supplied neither. (iii) `wrapper.__wrapped__ = wrapped`, after both loops ⇒ `wrapped := true`, faithful even when the source's table holds a `__wrapped__` key that step (ii) copied, because step (iii) writes last. (iv) `return wrapper` — it RETURNS the wrapper it was handed and never alters which arguments that wrapper needs, so the result's call shape is the destination's, never the source's ⇒ `selfSufficient := dst.selfSufficient`. Modeled DEEPLY as `copyIdentity` — NOT axiomatized. G-AX validates `copyIdentity` == the real `functools.update_wrapper` over fuzzed inputs, comparing BOTH layers of all three attributes plus the delegation flag and the call-shape leg, and failing if its own sweep never reached a source whose layers disagree — the state at which a model carrying only step (i) is wrong. |
| 4 | `return bound` | the value assigned to `bound_method` | I | identical concrete op — returns the constructed callable, i.e. the synthesised one that was dressed, not the original that dressed it. |

No op is changed-inexpressible. There is **no consumed axiom** and **no opaque
callee**: the identity transfer is modeled deeply (`copyIdentity`), making the
library routine an **A-reference** (G-AX-checked), and the proof discharges by
case analysis on the three attribute slots of `source`.

## Note on spec strength

The postcondition pins EIGHT components: for each of the three attributes, both
the entry the result holds in its own table and what a reader observes on it, plus
the delegation flag and the call shape. Nothing is left free, so the spec is as
strong as the construction is determined.

Per attribute, the value pinned is `transferredEntry source.attr`, i.e. the
source's own table entry where its table holds one and what a reader observes on
it otherwise. That is what the real construction produces, and the ORDER is the
whole content of the clause: the routine's second pass (the `__dict__` merge)
writes the same storage as its first (the per-attribute `setattr`) and writes it
later, so where the source's two layers disagree it is the table entry that ends
up on the result. Pinning what a reader observes on the source instead would be
faithful only on sources whose layers coincide, and `_multi_decorate` produces
sources whose layers differ (op 3, step (ii)). This is verified against the repo
rather than argued: conformance_check.py evaluates this postcondition on both
layers of each fuzzed source and compares it to what the reconstructed post-patch
line actually exposes, over 120134 inputs of which 42916 have a source whose
layers disagree, with 0 disagreements — and the same run with `transferredEntry`
replaced by the source's observed layer alone disagrees on all 42916.

The clauses are strong enough that the pre-patch impl (which returns the bare
callable, whose name is absent at both layers) cannot satisfy the name clauses.
Those are the real bug: pre-patch, `bound_method.__name__` does not exist
(`AttributeError`), so a decorator reading `func.__name__` fails — exactly the F2P
test `test_wrapper_assignments`. Pinning the table layer as well as the observed
one is not over-fitting: the table entry is what the NEXT decorator in the stack
copies on, so a construction that got the observed value right and the table entry
wrong would be observably wrong one decorator later, and the G-PBT reject case
`weak-result-table-disagrees` is that construction.

The last clause, `result.selfSufficient = true`, pins the other half of what the
post-patch line produces, and it is the half the metadata clauses cannot see. `wraps(method)(x)` returns `x` with metadata assigned onto it; it does not
change what `x` needs to be called with. So the post-patch `bound_method` is the
instance-bound partial — callable as `bound_method(*args, **kwargs)` — and that is
exactly what the next two lines of `_wrapper` go on to do with it. The clause is
TRUE of the real patched function for that reason, and it is not a restatement of
the gold expression: any construction that hands the decorators an
instance-bound, identity-carrying callable satisfies it, whatever route it takes
(the G-PBT `pos-record-literal` control is one such alternative and verifies).

It is FALSE of the constructions that dress the wrong object. `wraps(partial(…))(method)`
(the transfer run in reverse) and `wraps(method)(method)` both end up handing back
`method` itself, whose metadata after the transfer is indistinguishable from
gold's while `method(*args)` raises
`TypeError: method() missing 1 required positional argument: 'self'`. Those are
the wrong implementations a metadata-only postcondition admitted; the usability
clause is what rejects them, on the ground that they are genuinely wrong rather
than because they were excluded from the domain.

The precondition is `True`: the construction is defined for every callable
`method_decorator` can be handed, whatever entries that callable holds at either
layer and however it itself has to be called. Nothing is excluded — a source
holding only some of the three attributes, one holding an entry whose content is
`None`, one whose table disagrees with what a reader observes on it, and one that
is not callable without its instance are all admissible, and all four are inputs
`_multi_decorate` really produces. The last of them is the input the usability
clause discriminates at, and the third is the input the table clauses discriminate
at, so the claim is made over the whole domain rather than over a part of it
chosen to make the claim easy.

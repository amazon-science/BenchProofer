# mapping.md — django__django-14787

## Modeled function

| Lean | Python | file:line @ base_commit `004b4620f6` |
|---|---|---|
| `implementation_attachIdentity` / `problem_spec_attachIdentity` / `correct_attachIdentity` | the wrapper-construction step in `_multi_decorate._wrapper`: build `bound_method` so it carries the original `method`'s identity attributes | `django/utils/decorators.py:35-43` (changed line 40; post-patch: `bound_method = wraps(method)(partial(method.__get__(self, type(self))))`) |

The gold patch edits a single line inside `_multi_decorate`'s inner closure
`_wrapper`. The behaviorally relevant change is that the callable bound to
`bound_method` — previously a bare `partial` lacking identity attributes — is now
wrapped with `wraps(method)` so it exposes `method`'s identity. The subsequent
`for dec in decorators` loop and `bound_method(*args, **kwargs)` call are
unchanged and identity-transparent w.r.t. the fix; the observable defect is solely
the missing identity on `bound_method`.

`method` (the SOURCE of the identity) is whatever callable `method_decorator` was
handed, and in `_multi_decorate`'s own recursive use it is frequently a callable
that has ALREADY been through this file's `_update_method_wrapper` +
`update_wrapper(_wrapper, method)` pair
(`django/utils/decorators.py:13-19` and `:45-49` at base_commit `004b4620f6`).
Such a callable carries identity at TWO layers that DISAGREE: its slots answer
with the original method's `__name__` while its own `__dict__` holds the
decorator-side one. That is not a corner case — it is what stacking two decorators
produces — so the modeled `source` domain must cover it, and §2 does (see the
`IdentityAttr` row).

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| a callable's identity surface (the `functools.WRAPPER_ASSIGNMENTS` attributes it carries, at each of the two layers they live at) plus its call shape | `CallableAttrs` (record of `name, module, qualname : IdentityAttr`, `wrapped : Bool`, `selfSufficient : Bool`) | `wrapped` ↔ whether `__wrapped__` is set. `selfSufficient` ↔ whether the object can be called with the decorated call's own arguments alone (see the row below). Each identity attribute is an `IdentityAttr`, i.e. a PAIR of `AttrSlot`s, one per layer (next two rows). |
| for one attribute: `getattr(obj, attr)` (or `AttributeError`) **and** `obj.__dict__.get(attr)` (or absence) | `IdentityAttr` (`observed`, `ownEntry` : `AttrSlot`) | **Two layers, because `update_wrapper` reads and writes two.** `observed` ↔ what `getattr(obj, attr)` answers, `vacant` when it raises `AttributeError`. `ownEntry` ↔ what `obj.__dict__` holds for `attr`, `vacant` when the key is absent (or the object has no `__dict__`, e.g. `object().__str__`). The two layers can DISAGREE, and modeling only `observed` is what makes a spec of this construction unfaithful: a plain `def f` answers from type-level slots while `f.__dict__` is empty (`observed` filled, `ownEntry` vacant); a function that has been through `update_wrapper` answers from the SLOT — a function's `__name__` is a data descriptor, which outranks the instance dict — while its `__dict__` still holds the entry it was given, so the two differ; an object whose type answers by raising has nothing observable while its `__dict__` may hold an entry. All three shapes are built out of real objects by both generators (`src_plain_function`, `src_table_shadowed_function` / `src_stacked_method`, `_ReadRefused`), and each script COUNTS the disagreeing inputs and fails if the count is zero, so a passing run cannot be one that never exercised the second layer. |
| for one attribute at ONE layer: held-or-not, and if held its value | `AttrSlot` (`vacant` / `filled (content : Option String)`) | a **three-state** carrier, because Python's attribute space is three-state at each layer and both of `update_wrapper`'s passes dispatch on presence alone (`except AttributeError` for the `assigned` pass, a `dict.update` for the `updated` one): `vacant` = not held; `filled none` = held, value `None`; `filled (some s)` = held, value the `str` `s`. `AttrSlot.overlay a b` ↔ "`a`'s entry if `a` holds one, else `b`'s", the primitive both passes are built out of. |
| **why three states and not two** | `AttrSlot` vs `Option String` | A two-state present/absent `Option String` would be UNFAITHFUL. `update_wrapper` copies an attribute iff `getattr` does not raise — it never inspects the value — so a source holding `__module__ = None` has that `None` copied VERBATIM onto the wrapper, leaving an entry there whose content is `None`. A two-state encoding maps present-but-`None` onto absent and so predicts that nothing is written and the destination's state stands instead — on the destination this construction builds, no entry and nothing observable at all — which is not what the real routine does. Verified against the real patched `_multi_decorate` at `004b4620f6`+gold, run in the interpreter *Environment of record* names: with the decorated method's `__module__` set to `None`, the user decorator observes `__module__ = None` — an entry holding `None`, not the absence a two-state model predicts — while `__name__`/`__qualname__` still arrive as the original's. All three states are REAL and separately constructible: absence on all three by a bare `partial`, and on `__module__` also by a bound method-wrapper (`object().__str__`), which additionally has no `__dict__` at all; held-but-`None` by `setattr(partial(...), attr, None)`. Both generators draw the three states as separate pool entries (`ABSENT` vs `None`), so the module leg is exercised at the state that distinguishes them. |
| whether a callable is invokable as `obj(*args, **kwargs)` without a leading instance argument | `.selfSufficient : Bool` | `true` for the bound-and-partial'd callable (`partial(method.__get__(self, type(self)))`) and for anything `update_wrapper` hands back, since it returns its WRAPPER argument unchanged in call shape; `false` for the unbound `method`, which raises `TypeError: … missing 1 required positional argument: 'self'` when called without the instance. Observed operationally (a real call) by conformance_check.py and axiom_check.py, not by attribute inspection. |
| `__name__` / `__module__` / `__qualname__` | `.name` / `.module` / `.qualname` | the three standard wrapper-assignment attributes modeled (a representative, fixed-arity subset of `WRAPPER_ASSIGNMENTS` — the ones genuinely absent on a bare `partial` and present on a real function; `__doc__` and `__annotations__` are excluded because a `partial` carries both natively, so the destination is never attribute-bare there and the F2P observable does not turn on them). The three-state `AttrSlot` applies at each of the two layers of each, so a held-but-`None` value is carried rather than collapsed, and a `__dict__` entry that differs from the slot is carried rather than ignored. **The projection onto three attributes is exact, not approximate:** the `assigned` pass treats each attribute independently and the `updated` pass is a key-wise `dict.update`, so what the routine does to these three keys does not depend on the other keys, and dropping the others changes nothing about what is claimed of these. |
| `WRAPPER_UPDATES == ('__dict__',)` — the container the `updated` pass merges | the `ownEntry` layer of each `IdentityAttr`, plus `IdentityAttr.transfer`'s second overlay | `__dict__` is **NOT** an unmodeled attribute: it is the CONTAINER whose merge the second pass performs, and its effect on the three modeled keys is exactly what the `ownEntry` layer records. `getattr(wrapper,'__dict__').update(getattr(wrapped,'__dict__',{}))` is, restricted to one key, `wrapper_entry := overlay(src_entry, wrapper_entry)` — which is the `src.ownEntry.overlay …` leg of `IdentityAttr.transfer`. The keys of `__dict__` OTHER than the three modeled ones are outside the modeled surface (the merge is key-wise, so they do not interact), and the delegation key `__wrapped__` is handled by the row below. Both scripts compare this layer explicitly. |
| `__wrapped__` attribute set by `update_wrapper` | `.wrapped : Bool` | `update_wrapper` sets `wrapper.__wrapped__ = wrapped` as its LAST statement, after both passes, so the constant `wrapped := true` is faithful even when the source's own `__dict__` holds a `__wrapped__` key that the `updated` pass copied over: verified — with `f.__dict__['__wrapped__'] = 'bogus'`, `update_wrapper(p, f).__wrapped__ is f` is `True`. Both generators include such a source. |
| `partial(method.__get__(self, type(self)))` | `bareCallable` | a fresh `partial` answers for NONE of the three attributes — `getattr` raises `AttributeError` for `__name__`, `__module__` and `__qualname__` alike — and its own `__dict__` is EMPTY. Modeled at both layers: all three `:= {observed := .vacant, ownEntry := .vacant}`, `wrapped := false`. MEASURED rather than assumed, and measured where it counts: axiom_check.py's `check_destination_transparency` reads all three at both layers on a real fresh `partial` in the interpreter the gate runs in, and fails G-AX if any of them is answered. The fact is interpreter-dependent and the section *Environment of record* below pins which interpreter it is claimed of; on a newer host interpreter that same check fails BY DESIGN, and such a failure is about the interpreter rather than about this model. `selfSufficient := true`: the instance is already bound in, so it is callable with the decorated call's own arguments — which is why the decorators can invoke it at all. |
| **the destination is TABLE-TRANSPARENT** | the `observed := entry.overlay dst.observed` leg of `IdentityAttr.transfer` | a `partial` has no slot for these three attributes, so once its `__dict__` holds one the `getattr` answers from that entry: `p.__dict__['__name__']='x'` ⇒ `p.__name__ == 'x'`, and likewise for the other two. That is why `observed` is the new table entry laid over what the destination already answered, and why the two passes both land in the SAME storage. The modeled construction always builds this destination (`partial(...)`), so the leg is a claim about the real destination and not a general one — a *function* destination would behave differently, its slot winning over the merged entry. axiom_check.py CHECKS the transparency on a real `partial` at startup rather than assuming it, and every destination it fuzzes is a `partial`. |
| `wraps(method)(callable)` ≡ `functools.update_wrapper(callable, method)` | `copyIdentity source dst` (per attribute: `IdentityAttr.transfer`) | **The routine is two passes over the same storage, and the model has a leg for each.** (i) `assigned` pass: `for attr in WRAPPER_ASSIGNMENTS: try: value = getattr(wrapped, attr) except AttributeError: pass else: setattr(wrapper, attr, value)` ↔ `src.observed.overlay dst.ownEntry` — held-on-source overwrites, content and all including `None`, else the destination's entry stands; dispatch on held-ness only, never on content. (ii) `updated` pass: `for attr in WRAPPER_UPDATES: getattr(wrapper, attr).update(getattr(wrapped, attr, {}))` ↔ the outer `src.ownEntry.overlay …` — the source's own table laid over the result of (i). Since the destination is a `partial`, pass (i)'s `setattr` lands in `wrapper.__dict__`, so pass (ii) writes the SAME storage LATER and its entry is the one that survives; hence `entry := src.ownEntry.overlay (src.observed.overlay dst.ownEntry)` and NOT the other order. (iii) `wrapper.__wrapped__ = wrapped`, last ↔ `wrapped := true`. (iv) `return wrapper` ↔ `selfSufficient := dst.selfSufficient`: the call shape is `dst`'s and is never taken from the source. That last leg is what distinguishes handing back the synthesised callable from handing back `method`; G-AX checks both halves (`update_wrapper(dst, src) is dst`, and the usability probe unchanged across the call), and checks the pass ORDER by construction — it fuzzes sources whose two layers differ, on which pass order is observable. |

`source` ↔ `method` (the original callable being decorated); the synthesised
`partial` ↔ `bareCallable`; the result ↔ post-fix `bound_method`'s identity.

## Environment of record — which interpreter "the real callee" means

The reference interpreter for this instance is the one inside the instance image
(the conda `testbed` env at `/testbed`, **CPython 3.9.20**): that is where the
FAIL_TO_PASS / PASS_TO_PASS tests run, and it is where G-AX and G-CONF execute
axiom_check.py and conformance_check.py. A probe run against a `/tmp` worktree
under the HOST interpreter is not that environment, and for one carrier fact —
the one the `bareCallable` row above records — the two differ. Measured, with
`patch.diff` applied:

| interpreter | `getattr(functools.partial(f), '__module__')` | `'__module__' in functools.partial.__dict__` |
|---|---|---|
| image `testbed` python, CPython 3.9.20 | `AttributeError` | `False` |
| host CPython 3.10.20 (also 3.12) | `'functools'` | `True` |

From CPython 3.10 on, a static C type's `__module__` is recorded in the type's own
dict, which puts it on the instance lookup path; through 3.9 it is only a getset
descriptor on `type`, which an instance lookup never consults. So on a 3.10+
interpreter a fresh `partial` answers `'functools'` for `__module__`, and
`bareCallable`'s `module := {observed := .vacant, ownEntry := .vacant}` reads as
over-strong. In the reference interpreter it is exact. End to end through the
public API there, with the gold patch applied and a source that supplies no
module at either layer (`meth = object.__init__`), the user decorator observes
`__name__ = '__init__'`, `__qualname__ = 'object.__init__'`, and `__module__`
raises `AttributeError` — which is what the postcondition predicts, since
`transferredEntry` of an attribute vacant at both of the source's layers is
`vacant`. Both oracles confirm it over their whole sweeps in that interpreter:
axiom_check.py exits 0 (120018 inputs, both layers) and conformance_check.py
exits 0 (120134 inputs, 0 disagreements).

Nothing here is tolerant of the difference. `check_destination_transparency`
re-measures the carrier on a real `partial` at every G-AX run, so on an
interpreter where the fact does not hold the gate FAILS loudly instead of
certifying a model the carrier does not match — a `G-AX FAIL: … a fresh partial
answers for __module__` is that guard firing on the wrong interpreter, not a
finding about the model.

## Callee provenance / flag deps

- The unchanged callee whose behavior the fix relies on is
  `functools.wraps` / `functools.update_wrapper` (stdlib). It is **modeled deeply**
  as `copyIdentity` (no opaque callee, no consumed `_prop` axiom). Its contract is
  not one operation but FOUR STEPS in order, and each has its own model leg:
  1. the `assigned` loop over `WRAPPER_ASSIGNMENTS` — per attribute, copy what the
     source is OBSERVED to hold (`getattr`, guarded by `except AttributeError`),
     whatever the value, `None` included ⇒ `src.observed.overlay dst.ownEntry`;
  2. the `updated` loop over `WRAPPER_UPDATES == ('__dict__',)` — one whole-table
     merge of the source's OWN attribute table onto the wrapper's
     ⇒ the outer `src.ownEntry.overlay …`. Because the wrapper is a `partial`,
     step 1 wrote that same table, so step 2 is the LATER write and wins;
  3. `wrapper.__wrapped__ = wrapped`, after both loops ⇒ `wrapped := true`;
  4. `return wrapper` — the object handed back is the wrapper
     ⇒ `selfSufficient := dst.selfSufficient`.
  All four are pinned directly in `copyIdentity` / `IdentityAttr.transfer` and
  validated against the real `functools.update_wrapper` by `axiom_check.py`
  (G-AX, A-reference), which compares BOTH layers of all three attributes and
  fails if its own sweep never reached a source whose layers disagree — the state
  at which a model carrying only step 1 is wrong.
- No flag dependency: `update_wrapper`'s `assigned`/`updated` arguments are left at
  their defaults (`WRAPPER_ASSIGNMENTS` / `WRAPPER_UPDATES`); BOTH defaults are
  modeled (step 1 and step 2 above). G-AX fuzzes the default configuration.
- `method.__get__(self, type(self))` and `partial(...)` only synthesise the
  callable that receives the identity; they contribute no identity attributes of
  their own (the partial is attribute-bare), so they are subsumed by `bareCallable`
  and need no separate axiom.

## G-CONF fuzz seed

`conf_seed = 14787` (pinned; see conformance_check.py and meta.json).

conformance_check.py asserts three legs over the same inputs: the impl shadow
against the reconstructed post-patch line; the POSTCONDITION's own predicted
values (`transferredEntry` at each of the result's two layers) against that same
real construction, so the postcondition is checked against the
repo rather than against itself; and a coverage leg that fails the run if no
source had an own-table entry differing from what a reader observes. Its source
pool includes `src_stacked_method`, which runs this file's real
`_update_method_wrapper` + `update_wrapper` pair to produce the two-layer source
the repo itself produces.

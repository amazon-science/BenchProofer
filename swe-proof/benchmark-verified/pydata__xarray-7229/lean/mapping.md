# mapping.md — pydata__xarray-7229

## Symbol binding (file:line, `patch.diff` APPLIED)

Line numbers for the changed body are POST-patch (the reference worktree an
auditor builds); `def where` itself is at the same line on both legs.

| Lean symbol | Python | location |
|---|---|---|
| `implementation_where` / `problem_spec_where` / `correct_where` | `where(cond, x, y, keep_attrs)` | `xarray/core/computation.py:1775` (changed body `1858-1894`) |
| `select_combine cond a b keep_attrs` | `apply_ufunc(duck_array_ops.where, cond, x, y, join="exact", dataset_join="exact", dask="allowed", keep_attrs=keep_attrs)` | `xarray/core/computation.py:1864-1873` |
| `XObj` | a labelled array object: `Variable` / `DataArray` (`name`) / `Dataset` (container, `data_vars`) | `xarray/core/{variable,dataarray,dataset}.py` |
| `XObj.topAttrs` | `obj.attrs` | — |
| `XObj.dataVars` | `getattr(obj, "data_vars", [])` (named variables of a Dataset; empty for non-container) — this is the very expression the rebuild's iteration source is, see "Modeled domain" | `computation.py:1888` |
| `XObj.coords` | `getattr(obj, "coords", [])` (named coordinates) — likewise the rebuild's other iteration source | `computation.py:1890` |
| `XObj.name` | the object's OWN name: `obj.name` for the non-container kinds (`Variable.name` / `DataArray.name` are genuine class properties, so no like-named component can shadow them — unlike the `getattr(x, v, …)` of ops 7-8, this read needs no resolution table). `expectedResult` reads the field only in the promotion branch, whose guard `b.isContainer && !a.isContainer` already forces the second argument to be a non-container, so a container's field is never consulted (G-CONF still fuzzes it, identically on both legs) | — |
| `XObj.isContainer` | `isinstance(obj, Dataset)` | — |
| `Component {name, attrs}` | a data-variable / coordinate, with its `.attrs` | — |
| `XObj.reserved` | the object CLASS's own attribute table: `[(nm, getattr(getattr(type(obj), nm) resolved on obj, "attrs", {})) for nm in dir(type(obj)) if nm is a class attr]` — the names normal attribute lookup answers, so `Common.__getattr__` is never reached | `xarray/core/common.py:271` |
| `lookupAttrs a nm` | `getattr(getattr(x, nm, None), "attrs", {})` | `computation.py:1889,1892` |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

- `XObj` ↔ a JSON record `{topAttrs, name, isContainer, dataVars, coords, reserved}`
  where `topAttrs` is a list of `[key,val]` string pairs, `name` is `null | str`,
  `isContainer` a bool, `dataVars`/`coords` lists of `{name, attrs}`, and
  `reserved` a list of `[name, attrs]` pairs — the object class's own attribute
  table (see the resolution-order section below).
- `Attrs` (`List (String × String)`) ↔ an ordered list of `[key, value]` pairs.
- The Python shadow models each object as exactly this record; `select_combine`
  is modeled as a deterministic pure structural combine (see below) so the R/I
  legs can be differential-tested without the real xarray stack.

## Callee provenance + flag dependency

- **`select_combine` — A-reference (deep-model reference, NOT a consumed axiom).**
  The real callee is the unchanged
  `apply_ufunc(duck_array_ops.where, cond, x, y, …, keep_attrs=keep_attrs)`. It is
  byte-identical on both the pre- and post-patch legs (the patch renames
  `return apply_ufunc(...)` to `result = apply_ufunc(...)`; the call arguments are
  unchanged). **The retention flag is one of those arguments, so it is part of the
  callee's signature in the model too** (`XObj → XObj → XObj → Bool → XObj`):
  inside `apply_ufunc` (`computation.py:1157-1158`) `isinstance(keep_attrs, bool)`
  turns the flag into `combine_attrs="override"` (True) or `"drop"` (False), so the
  combined object's own attribute bags genuinely differ between the two flag
  values. That difference is observable, not masked: in the promotion branch the
  post-combine rebuild touches only `result[x.name]`, so every OTHER data variable
  keeps the carrier's flag-dependent bag, and with `keep_attrs` False nothing is
  rebuilt at all. Dropping the flag from the carrier would make the model assert a
  keep_attrs-invariance of those bags that the real function does not have. The
  impl reads the result's component *names*, and rewrites only the `.attrs` the
  gold code rewrites. G-CONF uses the same flag-taking structural stand-in on both
  legs, so the choice of stand-in cancels. No `_prop` axiom is consumed by the
  proof; `axiom_check.py` is a skip stub.
- **Flag dependency:** the attribute rebuild fires only under `keep_attrs is True`
  (after `keep_attrs = _get_keep_attrs(default=False)` resolves `None`). G-CONF
  fuzzes `keep_attrs ∈ {True, False}` (and the resolved-from-None case folds to
  `False` in the test default), and the container-promotion branch
  (`isinstance(y, Dataset) and not isinstance(x, Dataset)`) is fuzzed by varying
  `a.isContainer` / `b.isContainer`. The name pool mixes unreserved names
  (`time`/`lat`/`lon`) with both reserved outcomes — view-valued (`T`, `real`,
  carrying the object's own top-level bag) and bag-less (`dims`, `values`,
  `mean`, carrying `[]`) — so all three resolution stages are exercised.

## Attribute-name resolution order (faithfulness of `lookupAttrs`)

`lookupAttrs a nm` models `getattr(getattr(x, nm, None), "attrs", {})`
(`computation.py:1889,1892`) as the REAL two-stage Python resolution, not as a
variable-namespace lookup:

1. **The class table first.** `getattr(obj, nm)` consults `type(obj)` and
   `obj.__dict__` before ever calling `__getattr__`. xarray reaches the
   variable namespace ONLY through `Common.__getattr__`
   (`xarray/core/common.py:271`), which Python invokes only when normal
   attribute lookup RAISES `AttributeError`. So every class
   attribute/property/method of `DataArray`/`Dataset` answers first and
   SHADOWS a like-named data variable or coordinate. `XObj.reserved` is that
   per-class table, each reserved name paired with the `.attrs` of whatever the
   class-level answer is. Measured on the patched repo at base_commit
   (`dir(xr.DataArray)` sweep, 187 public names, every one used as a legal
   coordinate name):
   - names whose answer is a **view of the whole object** carry the object's
     OWN top-level bag: `T`, `real`, `imag`, `variable`, `_variable` (5 names);
   - all other reserved names answer with a method or a non-`attrs` object, so
     `getattr(..., "attrs", {})` returns `{}`: 180 names, e.g. `dims`, `values`,
     `attrs`, `loc`, `name`, `mean`, `where`, `plot`, `shape`, `size`.
   The table is **per class**: `T` is a `DataArray` property but NOT a `Dataset`
   attribute, so a Dataset data variable named `T` resolves through the variable
   namespace and keeps its own bag, while a DataArray coordinate named `T` does
   not. `Dataset`'s own view-valued names are `real`/`imag`. This is why
   `reserved` is a field OF the object rather than a global constant.
   The 187 non-dunder `DataArray` class names account exactly: 5 view-valued +
   180 bag-less + `_cache` + `dt`. The last two are the BOUNDARY cases, and both
   were measured rather than assumed:
   - `_cache` is a declared slot that is unset on a fresh object, so normal
     lookup raises `AttributeError` — which is precisely the trigger for
     `Common.__getattr__`. A coordinate named `_cache` therefore reaches stage 2
     and keeps its OWN bag, exactly as the model's fall-through says. Measured on
     the patched worktree: coord `_cache` → `{'units': 'kelvin'}` (its own),
     against coord `T` → `{'src': 'X_TOP'}` (`x`'s top-level, the reserved
     answer) and the unreserved control coord `k` → `{'units': 'kelvin'}`.
     Stage 1 is therefore keyed on "normal lookup SUCCEEDS", not on "the name is
     a class attribute" — which is what `reserved` records.
   - `dt` is the one NON-DUNDER name on either class whose class-level answer
     cannot be produced at all (`__dask_optimize__` / `__dask_scheduler__` behave
     the same way, and `__class__` answers with a non-bag); see "Modeled domain"
     below, which enumerates those cases by the code line that fails rather than
     by a name sweep — a name sweep cannot see them all, because one of the
     failing reads is of a name that is NOT in `dir()` of the class it is read
     off.
2. **The variable namespace second.** For a name the class does not reserve,
   `Common.__getattr__` walks `_attr_sources`, which for `Dataset` yields
   `data_vars` then `coords` (`dataset.py:1357-1366`) and for `DataArray` yields
   `coords` (`dataarray.py:842-850`) — modelled as the `dataVars ++ coords`
   search, whose order is unambiguous because component names are unique within
   each collection and the two namespaces are disjoint.
3. **The empty bag last.** A name that is neither reserved nor a component
   yields `{}` — either because `_attr_sources`' final `self.attrs` leg answers
   with a plain attribute value that has no `.attrs`, or because
   `Common.__getattr__` raises and `getattr`'s default fires.

The `self.attrs` leg of `_attr_sources` is deliberately NOT modelled as a
separate stage: it can only answer for a name that is a KEY of `x.attrs`, and
the bag it yields is `getattr(that value, "attrs", {})`, which is `{}` for every
attribute value that is not itself a labelled object. Both outcomes are already
in range of the modelled `[]` leg, and no `attrs` value is a bag-carrying object
in the F2P domain. (Verified in-container: an `x.attrs` key whose value is a
plain string yields `{}`; a component of the same name always wins over an
`x.attrs` key, so the leg is unreachable whenever a component exists.)

## Modeled domain: the model is exact wherever `where` RETURNS

`problem_spec_where` is universally quantified over every `XObj` triple and both
flag values, with no hypothesis of any kind — so no Python input is excluded from
its scope. Its outcome is an `Option XObj`, and it takes a fifth binder
`produces`, which denotes the observation OF THE SAME CALL that the call yields
an object. The claim being made is:

> On every Python input, the patched `where` either RETURNS or RAISES. `produces`
> denotes which of the two that call does. When it RETURNS, the record image of
> what it returns is exactly `retainedResult`, and `problem_spec_where` pins the
> outcome to `some` of it. When it RAISES, `problem_spec_where` pins the outcome
> to `none`. So no value the patched function actually produces is left
> unconstrained or mispredicted, and no input on which it produces no value is
> predicted to produce one.

`produces` is a BINDER rather than a predicate computed from the record, and it
has to be: **whether the call raises is not a function of the record image.**
Measured on the patched worktree, two input triples whose record images for
`cond`, `x` AND `y` are equal disagree on raise-vs-return:

| triple | x record image | outcome |
|---|---|---|
| `x` a `DataArray` with `dims=['data_vars']`, no coords | `{"topAttrs": [["src","X_TOP"]], "name": "v", "isContainer": false, "dataVars": [], "coords": []}` | RAISES at `1889` |
| the same with `dims=['d']` | *byte-identical* | RETURNS |
| `x` with a coordinate named `data_vars`, dim length 2 | *(image equal to its length-0 sibling)* | RAISES at `1889` |
| the same at dim length 0 | *byte-identical* | RETURNS |

The obstruction lives in structure the bag record deliberately does not carry
(dimension names, and lengths), so no predicate over `XObj` can carve the raising
inputs out exactly and a definedness side-condition on the abstraction function
cannot be discharged. Taking the outcome as an observation of the call sidesteps
that: it is exactly the information "did this call yield an object", which is
what the two-arm postcondition needs and all it needs.

The rebuild reads its inputs through `getattr`, at four places, and exactly two
kinds of read can produce something no attribute-bag record can carry.

**(a) x-side value reads — `1889`, `1892`:**
`getattr(getattr(x, nm, None), "attrs", {})`, where `nm` ranges over the
result's component names. `XObj.reserved` pairs a name with the bag its
class-level answer carries, so a name is representable iff the class-level answer
is absent (→ stage 2), raises `AttributeError` (→ `Common.__getattr__` runs, also
stage 2, e.g. the `_cache` slot above), or carries an attribute bag. If the answer
cannot be produced at all, or is an object whose `.attrs` is not a mapping, the
line raises instead of assigning.

**(b) result-side iteration sources — `1888`, `1890`:**
`getattr(result, "data_vars", [])` and `getattr(result, "coords", [])`. These two
expressions are literally what `XObj.dataVars` and `XObj.coords` denote (rows
above): collections of NAMED components. A literal read `getattr(o, LIT, default)`
can be diverted into the variable namespace only when `LIT` is absent from
`type(o)`'s MRO **and** `type(o)` defines `__getattr__`. That is a decidable
question about the two classes, so the failure set here is exhaustively
enumerable rather than sampled. Measured on the patched worktree over every
literal attribute name the changed region reads:

| literal read | `DataArray` | `Dataset` | `Variable` |
|---|---|---|---|
| `attrs` (`1882`, `1884`, `1887`, `1889`, `1892`) | class attr | class attr | class attr |
| `coords` (`1890`) | class attr | class attr | absent, no `__getattr__` → default `[]` |
| `name` (`1883`) | class attr | absent — but unread: `1880`'s guard makes `x` a non-`Dataset` | absent, no `__getattr__` → `None` |
| `data_vars` (`1883`, `1888`) | **absent, and `__getattr__` present → SHADOWABLE** | class attr | absent, no `__getattr__` → default `[]` |

`__getattr__` is defined on `DataArray`/`Dataset` (inherited from
`Common.__getattr__`, `common.py:271`) and NOT on `Variable`. A coordinate named
`attrs` therefore does not shadow the bag (measured: `.attrs` is still the `dict`),
and the changed region contains **exactly one** shadowable read: line `1888`'s
iteration source, and only when the result is a `DataArray` carrying a component
literally named `data_vars`. (Line `1883`'s `result.data_vars` sits under the
promotion guard, where `y` is a `Dataset` and hence so is the result, so it reads
the genuine property.) When `1888` is diverted it yields a `DataArray`, the loop
iterates 0-d `DataArray`s, and `1889` calls `getattr(x, <0-d DataArray>, None)`.

Measured raise families — every input the record model does not map, and nothing
else:

| # | mechanism | line | witness component name | what the patched call does |
|---|---|---|---|---|
| 1 | (b) iteration source shadowed | `1888` → raises at `1889` | `data_vars`, as a component of a non-container result | `TypeError: getattr(): attribute name must be string` |
| 2 | (a) class-level answer cannot be produced | `1889` / `1892` | `dt`, on a `DataArray` `x` whose data is not datetime-like | `TypeError` from `CombinedDatetimelikeAccessor(obj)` via `CachedAccessor.__get__`; `getattr`'s default swallows only `AttributeError` |
| 3 | (a) class-level answer cannot be produced | `1889` / `1892` | `__dask_optimize__`, `__dask_scheduler__` | `ModuleNotFoundError` — the class attribute imports dask on access |
| 4 | (a) answer's `.attrs` is not a bag | `1889` / `1892` | `__class__` | `TypeError: 'property' object is not iterable` at `dataarray.py:871` (`self.variable.attrs = dict(value)`, i.e. `dict(<property>)`) |

Two notes a reader checking family 1 will want. It is `DataArray`-vs-`Dataset`
asymmetric in the opposite direction from family 2: `data_vars` is a `Dataset`
class attribute, so a Dataset result is immune and it is the DataArray result
that raises, while `dt` is a `DataArray` accessor, so a Dataset `x` with a
component named `dt` resolves normally. And a raise at line `1889` can come from
either mechanism — from the x-side value read (a) or from the result-side
iteration source (b); the two are distinguished by whether the offending name is
a component of `x` or of the result.

The table above is not exhaustive of the raise MECHANISMS, and does not need to
be: further ones measured on the patched worktree include a DIMENSION named
`data_vars` with no coordinate at all (raises at `1889`), an `x.attrs` key of
that name (`KeyError` at `1888` for a non-empty `str` value, `TypeError` for an
`int`), a 0-d coordinate of that name (`iteration over a 0-d array` at `1888`),
a `Dataset` result with a non-`str` Hashable data-var name (at `1889`, so a
Dataset result is NOT immune), and a non-`str` coordinate name (at `1892`).
Because `produces` is a binder, the postcondition covers every one of these
without enumerating them, and a mechanism discovered later does not invalidate
it.

**Why the two-arm form is the right encoding.** It does not narrow the property:
every `XObj` triple and both flag values remain in scope, and the reviewer's
witness — a `DataArray` `x` with a coordinate named `data_vars` — is still an
admissible input, now predicted correctly (`none`, matching the real `TypeError`)
instead of predicted to return an object. Nor does it weaken the obligation: on
`produces = true` the outcome is pinned to the single value `retainedResult`, the
unchanged clause that carries all the discriminating content, and
`spec_where_deterministic` makes the whole postcondition single-valued in both
arms. Both arms are attacked by their own G-PBT reject rivals
(`weak-no-object-arm-ignored`, `weak-no-object-arm-overreach`), so neither can be
collapsed to a constant. And the spec view names no identifier of the gold hunk:
`produces` is a neutral name for "this call yields an object", and no raising
mechanism, line number, or attribute name appears in it. The behaviour the patch
exists to change — a coordinate keeping its OWN bag rather than being overwritten
by `x`'s top-level bag — sits entirely on the `produces = true` arm and is what
the prepatch twin fails on.

### Differential measurement against the real patched repo

Beyond G-CONF (shadow-vs-shadow), the model was run against the real patched
worktree: `apply_ufunc(duck_array_ops.where, cond, x, y, join="exact",
dataset_join="exact", dask="allowed", keep_attrs=keep_attrs)` supplies the
opaque carrier (so `select_combine` cancels), `x`/`y` are abstracted through the
table above — `reserved` built from `type(x)`'s own descriptors, NOT from the
patched code path, so the oracle is not echoed — the Lean impl region is applied
to the carrier record, and the result is compared against `xr.where(...)` at
every level (own name, container flag, top-level bag, every data-variable bag,
every coordinate bag).

**(1) Exhaustive name sweep.** Component-name pool = `dir(xr.DataArray)` ∪
`dir(xr.Dataset)` ∪ the literal names the changed region reads
(`attrs`, `data_vars`, `coords`, `name`) ∪ ordinary names
(`time`, `lat`, `lon`, `q`, `k`) = **347 names**, each used as a coordinate of
`x`/`y` (and, where both sides are containers, also as a data variable), over 11
kind pairs — `DataArray`/`Dataset`/`Variable`/plain scalar in either position —
and both flag values. For each input the domain predicate of the previous section
is evaluated from `type(x)`'s descriptors and the two classes' MROs alone, then
`xr.where` is called:

- **3488 in-domain inputs: every one RETURNED, and the model matched the returned
  object exactly** at every level. By kind pair: `da_da` 687, `ds_ds` 1382,
  `da_ds` 690, `ds_da` 691, `var_var` 6, `da_var` 5, `var_da` 5, `scalar_da` 5,
  `scalar_ds` 6, `da_scalar` 5, `scalar_scalar` 6. By branch: 1755 with
  `keep_attrs` false, 1387 normal retention, 346 container promotion.
- **22 out-of-domain inputs: every one RAISED**, distributed over the 8
  (mechanism, line) families of the table above — `data_vars` 5 (line 1888→1889),
  `__class__` 5, `__dask_optimize__` 5, `__dask_scheduler__` 5, `dt` 2.
- **0 in-domain raises, 0 out-of-domain returns, 0 value mismatches.**

**(2) Randomised differential.**

- 9893 inputs over 4 seeds, drawn from all four shape pairs
  (DataArray/Dataset × DataArray/Dataset) with component names sampled from a
  pool mixing unreserved names (`time`, `lat`, `lon`, `q`, `v`) with view-valued
  (`T`, `real`, `imag`, `variable`, `_variable`) and bag-less (`dims`, `values`,
  `attrs`, `name`, `loc`, `mean`, `shape`, `str`, `plot`, `coords`, `data`,
  `encoding`, `sizes`, `chunks`, `ndim`, `size`, `count`, `round`, `copy`,
  `where`, `min`, `max`) reserved names, plus `dt`.
- **0 disagreements.** Branch coverage: 4738 `keep_attrs=False`, 3737 normal
  retention, 1146 container promotion.
- Of those 9893, 272 had a component literally named `dt` with `x` a
  `DataArray`. Each was run twice with two DIFFERENT bags for `dt` and gave the
  same answer both times — the bag is never read on those paths — so they agree
  wherever the real call returned a value; in the 107 where it returned nothing
  it raised `TypeError`, per the table above.
**(3) The two recorded objection witnesses, re-run one by one.**

- The **`data_vars` witness** (family 1 above), verbatim: `x` a `DataArray` named
  `v` with `attrs={'src':'X_TOP'}` and a coordinate named `data_vars` whose own
  attrs are `{'units':'kelvin'}`; `y` a `DataArray`; `cond` a boolean
  `DataArray`. `xr.where(cond, x, y, keep_attrs=True)` raises
  `TypeError: getattr(): attribute name must be string`, and the traceback's last
  `computation.py` frame is line `1889`,
  `result[v].attrs = getattr(getattr(x, v, None), "attrs", {})` — reached because
  line `1888`'s iteration source resolved to the coordinate. Three controls, all
  measured on the same worktree: with `keep_attrs=False` the same input returns
  normally (`top={}`, coord bags `{}`) and the model agrees; the opaque carrier
  alone (`apply_ufunc(...)`) returns on that input, so it is the rebuild's
  iteration source and not the combine that fails; and renaming the coordinate to
  `zz` returns `top={'src':'X_TOP'}`, `zz={'units':'kelvin'}`, which the model
  reproduces exactly. `'data_vars' in dir(xr.DataArray)` is `False` and
  `'data_vars' in dir(xr.Dataset)` is `True` — the asymmetry the family-1 row
  records.
- The **`T` witness** is included in (2) and now agrees:
  `x` a `DataArray` with `attrs={'src':'X_TOP'}` and a coordinate `T` whose own
  attrs are `{'units':'kelvin'}` → real `{'src': 'X_TOP'}`, model
  `lookupAttrs a "T"` = the reserved answer's bag = `a.topAttrs` =
  `{'src':'X_TOP'}`. Re-sweeping the same 146 non-underscore `dir(xr.DataArray)`
  names one at a time as a coordinate name, with two different (top-level, own)
  attr pairs so the classification cannot be a coincidence: the 145 a
  variable-namespace-only `lookupAttrs` got wrong (4 view-valued + 141 bag-less)
  now match; the 146th is `dt`, which raises. The unreserved control (`k`,
  `time`, `lat`) still takes the like-named coordinate's own bag — the patch
  delta the spec exists to pin.

## G-CONF fuzz seed

`conf_seed = 7229` (pinned in meta.json and conformance_check.py).

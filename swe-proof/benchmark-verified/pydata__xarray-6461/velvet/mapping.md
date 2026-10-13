# mapping.md — pydata__xarray-6461

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 851dadeb0338403e5021c3fbe80cbc9127ee672d`, states the type
abstraction, and gives the provenance of every modeled fact.

Repo file under change: `xarray/core/computation.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `attrsToKeep (present, xAttrs, xPos)` | the attribute-selection callback constructed inside `where(cond, x, y, keep_attrs=None)` when `keep_attrs is True` — `xarray/core/computation.py:1832` (`keep_attrs = lambda attrs, context: attrs[1]`) | the modeled changed operation: which attribute mapping the callback returns |
| parameter `present` | the callback's first parameter `attrs` — built by the caller `apply_dataarray_vfunc` as `[x.attrs for x in objs]`, `objs = _all_of_type(args, DataArray)` (`computation.py:281, 311`) — i.e. the attribute mappings of exactly the inputs that are `DataArray`s, in argument order | the list the buggy code indexes at the constant offset 1 |
| parameter `xAttrs` | `getattr(x, "attrs", {})` — `x` is `where`'s second positional argument, captured by the lambda's closure (post-patch `computation.py:1832`) | the second argument's OWN attribute mapping (`{}` when `x` is a scalar) |
| parameter `xPos` | the position of `x`'s attribute mapping within `objs`/`attrs` (i.e. the number of `DataArray` inputs at argument positions before `x`); `-1` when `x` is not a `DataArray` (a scalar, so it never appears in `objs`) | locates `x` inside `present`; the discriminator between the happy path and the bug |

The `context` parameter of the real lambda is unused by both the old and the new
body, so it is not modeled.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an attribute mapping (`dict`, e.g. `{"attr": "x"}`) | an opaque `Int` identity | distinct dicts ↔ distinct ints; the empty dict `{}` (also what `getattr(scalar, "attrs", {})` returns) ↔ the identity `0`. Equality of identities ↔ identity of the selected dict object that `apply_ufunc` then assigns to the output via `merge_attrs([...], combine_attrs=<callback>)`. The F2P test observes only WHICH mapping is kept (`actual.attrs == {"attr": "x"}` and `actual.attrs == {}`), i.e. mapping identity — exactly what the `Int` carrier preserves. |
| `attrs = [x.attrs for x in objs]` (the list passed to the callback) | `present : List Int` | element `present[k]` = the identity of `objs[k].attrs`; `present.length` = number of `DataArray` inputs. |
| `getattr(x, "attrs", {})` | `xAttrs : Int` | the identity of `x`'s own mapping, `0` if `x` is a scalar. The structural link "if `x` is a `DataArray` it appears in `objs` and its attrs is the entry there" is the precondition `∀ k, (xPos = k ∧ k < present.length) → present[k]! = xAttrs`; "a scalar carries `{}`" is `xPos = -1 → xAttrs = 0`. |
| `attrs[1]` (old body) / `getattr(x, "attrs", {})` (new body) | `present[1]!` (prepatch) / `xAttrs` (Solution) | the single changed expression. |

The `where` → `apply_ufunc` → `apply_dataarray_vfunc` plumbing
(`computation.py:1835-1844, 311-316`) only forwards the callback and applies it
to `[x.attrs for x in objs]`; it does not change the character of the selection,
so it is abstracted away (the model is exactly the callback's input→output map).

`xPos` is typed `Int` (not `Nat`) because the sentinel value `-1` (scalar second
argument) must be representable; the in-bounds precondition `0 ≤ xPos ∧ xPos <
present.length` and the cast `xPos = (k : Int)` bridge to `Nat` indexing.

## 3. Callee provenance

None. There is **no axiomatized callee** (A-consumed) and **no deep-model
A-reference**: the changed operation is a pure positional/identity selection that
Velvet expresses directly, so it is modeled deeply in `attrsToKeep` itself.
`getattr(x, "attrs", {})` is not an opaque library callee whose behavior must be
axiomatized — it is the elementary fact "an object's own attribute mapping, or
`{}` if it has none", captured by the `xAttrs` parameter and its `xPos`
preconditions. Hence `axiom_check.py` is not shipped for this instance (no
consumed axiom, no A-reference to validate against a real callee).

## 4. Why the abstraction is faithful (the tested inputs)

The F2P test `test_where_attrs` exercises two configurations of `where(cond, x,
y, keep_attrs=True)`:

1. `cond, x, y` all `DataArray`s with attrs `{"attr": "cond"/"x"/"y"}`. Then
   `objs = [cond, x, y]`, `attrs = [cond.attrs, x.attrs, y.attrs]`, and `x` sits
   at offset 1: `xPos = 1`, `present = [c, X, y]`, `xAttrs = X`. Both old
   (`present[1] = X`) and new (`xAttrs = X`) select `x.attrs`. Expected
   `{"attr": "x"}`. (Modeled: `present[1] = present[xPos] = xAttrs`.)
2. `where(cond, 1, 0, keep_attrs=True)`: `x = 1` is a scalar, so `objs = [cond]`,
   `attrs = [cond.attrs]`. Here `xPos = -1`, `xAttrs = 0` (the empty mapping).
   Old `attrs[1]` is out of range → `IndexError` (the reported bug); new
   `getattr(1, "attrs", {}) = {}` → expected `{}`. (Modeled: `present` has length
   1, `present[1]` is out of bounds; `xAttrs = 0`.)

The model's three parameters range over both configurations; the postcondition
`out = xAttrs` is satisfied by the new body in both and violated/blocked by the
old body in configuration 2 — exactly the observable the F2P test adds.

## 5. G-CONF fuzz seed

`conformance_check.py` is pinned to `SEED = 6461`, `N_FUZZ = 100_000`. It builds
the R/I shadow (`shadow_keep(x_own) = getattr(x, "attrs", {})`) and diffs it
against the patched `xr.where(cond, x, y, keep_attrs=True).attrs` over both
boundary configs (all-DataArray, scalar-second-argument) and the fuzz, with `x`
and `y` independently scalar or DataArray-with-attrs.

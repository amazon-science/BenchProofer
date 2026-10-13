# mapping.md — pydata__xarray-6461

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 851dadeb0338403e5021c3fbe80cbc9127ee672d`, states the type
abstraction, and gives the provenance of every modelled fact.

Repo file under change: `xarray/core/computation.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `attrs_to_keep(present, x_attrs, x_pos)` | the attribute-selection callback constructed inside `where(cond, x, y, keep_attrs=None)` when `keep_attrs is True` — `xarray/core/computation.py:1832` (`keep_attrs = lambda attrs, context: attrs[1]`) | the modelled changed operation: which attribute mapping the callback returns |
| parameter `present` | the callback's first parameter `attrs` — built by the caller `apply_dataarray_vfunc` as `[x.attrs for x in objs]`, `objs = _all_of_type(args, DataArray)` (`computation.py:281, 311`) — i.e. the attribute mappings of exactly the inputs that are `DataArray`s, in argument order | the list the buggy code indexes at offset 1 |
| parameter `x_attrs` | `getattr(x, "attrs", {})` — `x` is `where`'s second positional argument, captured by the lambda's closure (post-patch `computation.py:1832`) | the second argument's OWN attribute mapping (`{}` when `x` is a scalar) |
| parameter `x_pos` | the position of `x`'s attribute mapping within `objs`/`attrs` (i.e. the number of `DataArray` inputs at argument positions before `x`); `-1` when `x` is not a `DataArray` (a scalar, so it never appears in `objs`) | locates `x` inside `present`; the discriminator between the happy path and the bug |

The `context` parameter of the real lambda is unused by both the old and the
new body, so it is not modelled.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an attribute mapping (`dict`, e.g. `{"attr": "x"}`) | an opaque `int` identity | distinct dicts ↔ distinct ints; the empty dict `{}` (also what `getattr(scalar, "attrs", {})` returns) ↔ the identity `0`. Equality of identities ↔ identity of the selected dict object that `apply_ufunc` then assigns to the output via `merge_attrs([...], combine_attrs=<callback>)`. The F2P test observes only WHICH mapping is kept (`actual.attrs == {"attr": "x"}` and `actual.attrs == {}`), i.e. mapping identity — exactly what the `int` carrier preserves. |
| `attrs = [x.attrs for x in objs]` (the list passed to the callback) | `present: List[int]` | element `present[k]` = the identity of `objs[k].attrs`; `len(present)` = number of `DataArray` inputs. |
| `getattr(x, "attrs", {})` | `x_attrs: int` | the identity of `x`'s own mapping, `0` if `x` is a scalar. The structural link "if `x` is a `DataArray` it appears in `objs` and its attrs is the entry there" is the precondition `Implies(0 <= x_pos < len(present), present[x_pos] == x_attrs)`; "a scalar carries `{}`" is `Implies(x_pos == -1, x_attrs == 0)`. |
| `attrs[1]` (old body) / `getattr(x, "attrs", {})` (new body) | `present[1]` (prepatch) / `x_attrs` (model) | the single changed expression. |

The `where` → `apply_ufunc` → `apply_dataarray_vfunc` plumbing
(`computation.py:1835-1844, 311-316`) only forwards the callback and applies it
to `[x.attrs for x in objs]`; it does not change the character of the selection,
so it is abstracted away (the model is exactly the callback's input→output map).

## 3. Callee provenance

None. There is **no axiomatized callee** and **no deep-model A-reference**: the
changed operation is a pure positional/identity selection that Nagini expresses
directly, so it is modelled deeply in `attrs_to_keep` itself. `getattr(x,
"attrs", {})` is not an opaque library callee whose behaviour must be
axiomatized — it is the elementary fact "an object's own attribute mapping, or
`{}` if it has none", captured by the `x_attrs` parameter and its `x_pos`
preconditions. Hence `axiom_check.py` is not required for this instance (no
`@ContractOnly`, no A-reference to validate against a real callee).

## 4. Why the abstraction is faithful (the tested inputs)

The F2P test `test_where_attrs` exercises two configurations of `where(cond, x,
y, keep_attrs=True)`:

1. `cond, x, y` all `DataArray`s with attrs `{"attr": "cond"/"x"/"y"}`. Then
   `objs = [cond, x, y]`, `attrs = [cond.attrs, x.attrs, y.attrs]`, and `x` sits
   at offset 1: `x_pos == 1`, `present == [c, X, y]`, `x_attrs == X`. Both old
   (`present[1] == X`) and new (`x_attrs == X`) select `x.attrs`. Expected
   `{"attr": "x"}`. (Modelled: `present[1] == present[x_pos] == x_attrs`.)
2. `where(cond, 1, 0, keep_attrs=True)`: `x = 1` is a scalar, so `objs = [cond]`,
   `attrs = [cond.attrs]`. Here `x_pos == -1`, `x_attrs == 0` (the empty
   mapping). Old `attrs[1]` is out of range → `IndexError` (the reported bug);
   new `getattr(1, "attrs", {}) == {}` → expected `{}`. (Modelled: `present` has
   length 1, `present[1]` is out of bounds; `x_attrs == 0`.)

The model's three parameters range over both configurations; the postcondition
`Result() == x_attrs` is satisfied by the new body in both and violated/blocked
by the old body in configuration 2 — exactly the observable the F2P test adds.

# mapping.md — pydata__xarray-4629

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a41edc7bf5302f2ea327943c0c48c532b12009bc`, states the type
abstraction, and gives the provenance of the one deep-model reference.

Repo file under change: `xarray/core/merge.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combine_attrs(variable_attrs, mode)` | `merge_attrs(variable_attrs, combine_attrs)` — `xarray/core/merge.py:495` | the modeled changed function (attribute-mapping combiner) |
| `mode == DROP` branch | `if combine_attrs == "drop": return {}` — `merge.py:501-502` | unchanged sibling branch, modeled to situate the change |
| `mode == OVERRIDE` branch | `elif combine_attrs == "override":` — `merge.py:503-504` | the CHANGED branch (`return variable_attrs[0]` → `return dict(variable_attrs[0])`) |
| `variable_attrs[0]` | `variable_attrs[0]` (the leading source mapping) — `merge.py:504` | the leading source attribute mapping |

The unmodeled branches (not in the differential domain): the empty short-circuit
`if not variable_attrs: return None` (`merge.py:497-499`) and the
conflict-resolving modes `no_conflicts` (`merge.py:505-515`) and `identical`
(`merge.py:516-524`). Both conflict-resolving modes ALREADY open with
`result = dict(variable_attrs[0])` (`merge.py:506,517`) — i.e. they already make
an independent copy of the leading source; the change brings `override` into
line with them. These branches are unchanged by the patch and orthogonal to the
tested behaviour, so they are excluded by the `len(variable_attrs) > 0` /
`mode ∈ {DROP, OVERRIDE}` preconditions.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an attribute mapping `dict` (e.g. `{"x": 0}`) | `List[int]` of its per-entry value tokens | a mapping and its content list correspond 1:1 for the tested behaviour: the operation reads/copies the whole mapping and never indexes a specific key, so a mapping is faithfully carried by its content sequence. Two mappings are model-equal (`ToSeq(a) == ToSeq(b)`) iff content-equal (`dict` `==`). |
| the collection `variable_attrs` (a `list` of mappings) | `List[List[int]]` | `variable_attrs[k]` ↔ the k-th mapping's content list; `len` ↔ `len`; only index `0` is consulted by the modeled branches |
| `combine_attrs` (a `str` mode: `"drop"`, `"override"`, …) | `int` token (`DROP=0`, `OVERRIDE=1`) | the mode is an opaque tag compared for equality; `str` ↔ `int` token is a faithful enumeration of the two modeled modes (no string indexing, which Nagini bans) |
| **object identity** of the returned mapping vs. `variable_attrs[0]` | Nagini reference identity + separation-logic permission | `dict` aliasing ↔ Python/Nagini object identity (`is`); "an independent fresh mapping" ↔ FULL `Acc(list_pred(Result()))` on a DISTINCT object while the source keeps its `1/2` read permission |
| `{}` (a fresh empty dict, drop) | a fresh empty `List[int]` (`len == 0`, full permission) | empty-mapping ↔ empty-list; freshness ↔ full permission on a new object |
| `dict(variable_attrs[0])` (a fresh shallow copy, override post-patch) | the verified per-entry copy loop producing a fresh `List[int]` with `ToSeq(Result()) == ToSeq(src)` and `Result() is not src` | a shallow `dict(...)` copy is content-equal to and object-distinct from its argument; the loop reproduces exactly that under the content/identity refinement |

`str` indexing/iteration is banned in Nagini, so mode is an `int` token and a
mapping is carried by `List[int]`; identity is the decisive observable and is
carried by Nagini's reference identity + the fractional-permission discipline
(directive 5).

## 3. Callee / deep-model provenance (kind A — checked by G-AX / axiom_check.py)

### 3.1 `combine_attrs` deep model ↔ patched `merge_attrs` (A-reference)
There is **no consumed `@ContractOnly` axiom**. The combination is the operation
under change and is modelled **deeply**: the model's `impl` region spells out the
empty drop mapping and the per-entry copy of the leading source, and the
postconditions pin both the content (`ToSeq(Result()) == ToSeq(variable_attrs[0])`)
and the decisive identity (`Result() is not variable_attrs[0]`, plus full
permission on the fresh result while the source keeps its read permission).

The real operation the deep model mirrors, post-patch (`merge.py:501-504`):

```python
if combine_attrs == "drop":
    return {}
elif combine_attrs == "override":
    return dict(variable_attrs[0])   # gold patch: was `return variable_attrs[0]`
```

`dict(variable_attrs[0])` constructs a NEW dict with the same items as
`variable_attrs[0]` — a distinct object (`dict(d) is not d`) that is equal in
content (`dict(d) == d`). Mutating it therefore cannot reach back into
`variable_attrs[0]`. This is the property `combine_attrs`'s override
postconditions encode. `axiom_check.py` (G-AX) executes the real patched branch
over boundary + 20000 fuzz inputs and asserts: override returns a distinct,
content-equal object whose mutation never mutates the leading source (including
the exact F2P `test_merge_attrs_override_copy` scenario), and drop returns a
fresh empty mapping. Exit 0 iff sound. It imports only the standard library
(`dict(...)` is a builtin; nothing repo-specific).

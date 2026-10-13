# mapping.md — pydata__xarray-4629

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a41edc7bf5302f2ea327943c0c48c532b12009bc`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `xarray/core/merge.py`.

## 0. The behaviour under change

The modeled function combines the attribute mappings of several source objects
under the "take the first" policy and returns the combined mapping. The
correctness property the issue + F2P test demand is an **object-identity /
freshness** property: the returned mapping must be *its own object*, so that a
later in-place update of the result is **not** observed through any source
object. The pre-patch implementation returned the first source's mapping object
directly (a shared reference); the gold implementation returns a fresh shallow
copy of it.

Because Lean is purely functional and has no aliasing, a naive value-level model
(`result = sources.head` contents) cannot see this property at all — buggy and
fixed would denote the same value. We therefore model **object identity
explicitly**, following the Velvet heap/allocator pattern
(`Velvet/Examples/MemAlloc.lean`): a `store : Handle → Entries` giving each live
object's current contents, and a bump counter `fresh : Handle` of the next
never-yet-allocated handle. Allocating a fresh object copies contents into a new
handle; returning an existing handle shares (aliases) that object.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineFirst (store) (fresh) (sources)` | `merge_attrs(variable_attrs, combine_attrs)` — `xarray/core/merge.py:495`, the branch taken when `combine_attrs == "override"` (body line 504) | the modeled changed function, restricted to the policy branch the issue is about |
| `sources : List Handle` | `variable_attrs` — the list of source attribute mappings (each element is one object identity) | input |
| `sources.head!` | `variable_attrs[0]` — the first source mapping | the object whose contents are taken |
| `store : Handle → Entries` | the heap of live mapping objects: `store h` = the dict carried by the object with identity `h` | identity → contents map |
| `fresh : Handle` | the allocator's next-fresh object identity (Python `id()` of a newly-constructed `dict`, abstracted to a monotone counter) | bump allocator |
| `result : Handle` | the value `merge_attrs` returns under this branch | output object identity |

The two other policy branches of `merge_attrs` (`no_conflicts`, `identical`)
already copied (`dict(variable_attrs[0])`); `drop` returns `{}`; the empty-input
guard returns `None`. They are outside the modeled branch and unchanged by the
patch, so they are not modeled (the F2P test exercises only `override`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an attribute mapping *object* (a `dict`) | a `Handle` (`Int`) into `store` | a live Python object ↔ a live handle; `id(obj)` ↔ the handle value; **distinct objects ↔ distinct handles** (this is the identity the bug turns on) |
| the *contents* of one mapping object | `Entries := List (String × String)` | `dict(d.items())` ↔ the association list `d`; key/value order preserved (Python 3.7+ dict order); `store h` ↔ the contents currently reachable through that object |
| `list[dict]` `variable_attrs` | `List Handle` (`sources`) | the i-th source dict object ↔ `sources[i]`; `len` ↔ `.length`; non-empty ↔ `≠ []` |
| `variable_attrs[0]` | `sources.head!` | first element (the input is required non-empty — `require sources ≠ []`) |
| constructing a fresh `dict(...)` | `fresh` handle + `Function.update store fresh (...)` + `fresh := fresh + 1` | `dict(d)` allocates a new object (a new `id`) holding a shallow copy of `d`'s contents; modeled as a fresh handle bound to the copied `Entries` |
| `obj is other` / `obj is not other` | handle equality / disequality | object identity comparison ↔ `Handle` `=` / `∉` |

The precondition `∀ h ∈ sources, h < fresh` states the obvious well-formedness
invariant of a bump allocator: every already-live object has a handle below the
next-fresh counter. This is what makes `result = fresh` provably distinct from
every source (`result ∉ sources`) — the freshness the fix establishes.

## 3. Callee provenance

### 3.1 Object copy / allocation (deep model — A-reference)
**Callee:** the `dict(...)` constructor (CPython built-in). The changed
operation `dict(variable_attrs[0])` is modeled **deeply** in the impl region by
the allocate-fresh-handle + copy-contents sequence; there is **no consumed
axiom** about `dict`. The deep model's claim — *constructing a copy yields an
object distinct from every pre-existing object, carrying equal contents, and
leaving the source object's contents untouched* — is validated against the real
CPython `dict` by `axiom_check.py` (G-AX):

```python
src = {"a": "b"}
sources = [src, {"a": "c"}]
result = dict(sources[0])          # the gold operation
assert result is not sources[0]    # fresh identity            (result ∉ sources)
assert result is not sources[1]
assert dict(result) == dict(src)   # equal contents            (store result = storeOld head)
result["a"] = "d"                  # mutate the combined object
assert src == {"a": "b"}           # source untouched           (store h = storeOld h)
```

and dually, that the **pre-patch** operation `variable_attrs[0]` (return the
object directly) *fails* the freshness obligation — `result is sources[0]`, so a
later `result[k]=v` is visible through the source — which is the bug the F2P
test `test_merge_attrs_override_copy` observes.

### 3.2 No consumed axioms
`Solution.lean`'s `axioms` region is empty. The only "callee" involved is the
built-in object copy, modeled deeply (§3.1), so it is an **A-reference**
validated by G-AX, not an A-consumed axiom. The proof uses only
`Function.update` algebra (`Function.update_self`, `Function.update_of_ne`),
which is Lean/Mathlib core, not a repo claim.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`4629`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the impl region's allocate-copy ops to Python `dict(...)` over real `dict`
objects (the carrier bijection above), and diffs the three observable
consequences — returned contents, source-after-result-mutation, and
result-is-not-any-source — against `patch.diff`'s patched `merge_attrs(...,
combine_attrs="override")` over ≥10⁵ fuzzed inputs.

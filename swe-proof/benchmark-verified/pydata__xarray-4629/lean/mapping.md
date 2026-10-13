# mapping.md — pydata__xarray-4629

## Symbol binding (file:line @ base_commit `a41edc7b`)

| Lean | Python | location |
|---|---|---|
| `implementation_mergeAttrsOverride` / `problem_spec_mergeAttrsOverride` / `correct_mergeAttrsOverride` | `merge_attrs(variable_attrs, combine_attrs)` restricted to the `combine_attrs == "override"` path (and its leading empty-input guard) | `xarray/core/merge.py:495–504` (def at 495; empty guard 497–499; `override` branch 502–504) |

The modeled slice is `merge_attrs` under `combine_attrs == "override"` — the only
behavior the patch changes (`return variable_attrs[0]` → `return dict(variable_attrs[0])`)
and the only behavior exercised by the FAIL_TO_PASS test
`test_merge_attrs_override_copy`. The other `combine_attrs` branches
(`"drop"`, `"no_conflicts"`, `"identical"`, the `else` raise) are byte-identical
pre- and post-patch and are outside the modeled slice; they are not observed by
the bug or the F2P test.

## Type bijection (used by G-CONF and G-AX)

| Python reality | Lean model | notes |
|---|---|---|
| an attribute `dict` object | `Nat × AttrDict` — a `(identity, contents)` pair | only two things about a dict object are observable here: its **identity** (Python `id()`; whether two handles are the *same object*) and its **contents** (its key→value mapping). The `Nat` is the object identity; `AttrDict` is the contents. |
| object identity (`id(d)`, `a is b`) | the `Nat` first component | distinct objects ⇒ distinct `Nat`s; `a is b` ⇔ `a.1 = b.1`. The actual integer value is irrelevant — only distinctness/equality is observed. |
| dict contents (`dict(d)`, `==`) | `AttrDict := List (Int × Int)` (key→value assoc pairs; string keys/values abstracted to `Int` by an injective encoding — only equality of contents is observed) | |
| `variable_attrs` (a list of dict objects) | `List (Nat × AttrDict)` | each element is one source dict object: `(id, contents)`. |
| `not variable_attrs` (empty list guard) | `match attrs with \| [] => ...` | the leading early return. |
| `return None` | `none : Option (Nat × AttrDict)` | |
| `return dict(variable_attrs[0])` (post-patch) | `some (freshId, first.2)` where `freshId ∉ attrs.map Prod.fst` | `dict(d)` allocates a **brand-new object** (fresh identity) whose contents equal `d`'s. Modeled: fresh identity `(ids.foldl max 0) + 1` (an id strictly greater than every input id ⇒ distinct from all of them), contents copied verbatim (`first.2`). |
| `return variable_attrs[0]` (pre-patch BUG) | `some first` — i.e. `some (first.1, first.2)` | returns the *same object* (aliases `variable_attrs[0]`): identity component equals an input id ⇒ NOT fresh. |

### Freshness abstraction (the heart of the model)
Real `dict(d)` returns an object distinct from **every** live object. The only
objects whose aliasing is observable to the caller (and the only thing the F2P
test checks) are the elements of `variable_attrs` — the sources. So the faithful
minimal property is **distinct from every input identity**:
`freshId ∉ attrs.map Prod.fst`. Modeling the fresh id as `max(ids)+1` makes it
provably distinct from all input ids without any precondition. This freshness is
exactly what guarantees the F2P property "mutating the merged result's attrs does
not affect the source": a write to a fresh object cannot alias a source object.

## Callee provenance / flag deps
- The `"override"` path calls NO repo callee: `dict(...)` is a Python builtin
  (shallow copy → fresh object + copied contents), reproduced concretely as an
  R/I op (fresh id + content copy), not abstracted. ⇒ **no `opaque`/`axiom`**.
- Flag dependency: behavior is modeled only under `combine_attrs == "override"`
  (recorded above); G-CONF fuzzes the real `merge_attrs(..., combine_attrs="override")`.

## Pinned G-CONF fuzz seed
`SEED = 4629` (also in `conformance_check.py`, `meta.json verifier_pins.conf_seed`).

# refinement.md — pydata__xarray-4629

Modeled function: `merge_attrs(variable_attrs, combine_attrs)` under
`combine_attrs == "override"` (incl. the leading empty-input guard).
`implementation_mergeAttrsOverride (attrs : List AttrObj) : Option AttrObj`.

Type refinement (R), per mapping.md:
- a Python attribute dict object  ⇔  `AttrObj = Nat × AttrDict` (identity ×
  contents). `id(obj)` ⇔ the `Nat`; `dict(obj)`/contents ⇔ the `AttrDict`.
- `variable_attrs`               ⇔  `attrs : List AttrObj`.
- `return None`                  ⇔  `none`.
- a returned dict object         ⇔  `some (id, contents)`.

| # | `implementation_mergeAttrsOverride` op | `patch.diff` / source counterpart | tag |
|---|---|---|---|
| 1 | `if attrs.isEmpty then return none` | `if not variable_attrs: return None` (merge.py:497–499, unchanged guard) | I (identity op under R: empty list ↔ falsy list; `None` ↔ `none`) |
| 2 | `let mut maxId := 0; for p in attrs do if p.1 > maxId then maxId := p.1; let freshId := maxId + 1` | the *allocation* half of `dict(variable_attrs[0])`: it returns a brand-new object whose identity is distinct from every live object | R (object identity ⇔ `Nat`; "fresh, distinct from every source id" is realized as `max(input ids)+1`, an id provably ∉ the input ids — the minimal faithful property of a freshly-allocated object w.r.t. the only observable objects, the sources) |
| 3 | `let first := attrs.head!` | `variable_attrs[0]` (merge.py:503) | I (first element of a non-empty list; reached only when `¬ attrs.isEmpty`) |
| 4 | `return some (freshId, first.2)` | `return dict(variable_attrs[0])` (post-patch, merge.py:504): the *copy* half — new object's contents equal the first source's | R (contents ⇔ `AttrDict`; shallow-copy of contents ⇔ `first.2` carried verbatim) paired with op 2's fresh identity |

Every op is R or I — **no A-consumed, no A-reference, no `opaque`/`axiom`**.
`dict(...)` is a Python builtin reproduced concretely (fresh id + content copy),
not abstracted behind a callee model. ⇒ G-AX is a skip stub; `conf_skip = false`
(the impl region is all R/I, so G-CONF runs a real fuzz).

## The bug the spec sees (G-DIFF)
Pre-patch op 4 is `return variable_attrs[0]` ⇔ `return some first` (= `some
(first.1, first.2)`): the result REUSES the first source's identity, dropping
op 2 (no allocation). The spec's discriminating clause `id ∉ attrs.map Prod.fst`
then forces `first.1 ∉ attrs.map Prod.fst`, which is false (`first.1` is the head
id, trivially a member). So the prepatch `correct_*` is unclosable. Post-patch
`freshId = max(ids)+1 > every input id`, hence `∉` the input ids — provable.

This freshness clause is exactly the F2P observable: a fresh result object cannot
alias any source, so mutating the merged attrs leaves the sources unchanged
(`test_merge_attrs_override_copy`).

# mapping.md — django__django-12754

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 18759b2209ff556aed7f20d83cbf23e3d234e41c`, states the type
abstraction, and gives the provenance of the modeled operation.

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `removed_base_field_prereqs(candidates, parent_after, child)` | the added block inside `MigrationAutodetector.generate_created_models`, `django/db/migrations/autodetector.py:562-565` (the per-base loop body), specifically the new lines 566-575 of the post-patch file | the modeled changed behavior: for one string base, compute the set of removed-and-clashing base field names and append a "removed field" dependency for each |
| `selected(candidates, parent_after, child)` *(deep model — A-reference)* | `set(old_base_model_state.fields).difference(new_base_model_state.fields).intersection(model_state.fields)` (post-patch lines 569-571) | pure spec: the qualifying-name subsequence; the deep model of the real Python set difference-then-intersection, validated `selected == real-set-expr` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `qualifies(name, parent_after, child)` | the membership conditions implicit in `difference(new).intersection(model)` applied to a name already in `old` | pure spec: a prior parent name qualifies iff withdrawn-from-parent (`name not in new`) AND re-declared-by-child (`name in model`) |
| `candidates: PSeq[int]` | `old_base_model_state.fields` (a `dict`; iterated as its key set `set(old_base_model_state.fields)`) — `self.from_state.models.get((base_app_label, base_name)).fields` | parent's prior field names (the iteration domain of the set difference) |
| `parent_after: PSet[int]` | `new_base_model_state.fields` keys — `self.to_state.models.get(...).fields` | parent's target field names |
| `child: PSet[int]` | `model_state.fields` keys — `self.to_state.models[app_label, model_name].fields` | child (inheriting) model's field names |
| emitted `List[int]` element `f` | one appended dependency `(base_app_label, base_name, removed_base_field, False)` (post-patch line 575) | a "removed field" ordering prerequisite: the child's `CreateModel` must follow the `RemoveField` of `f` on the parent (see `check_dependency`, autodetector.py:399-405) |

The pre-patch repo state the change adds to (for the refinement audit, not the
consumer view): the per-base loop body at `autodetector.py:562-565` appended
only `(base_app_label, base_name, None, True)` — an existence dependency on the
parent — and nothing about withdrawn fields, so a child re-declaring a withdrawn
parent field was ordered BEFORE the removal, producing an unappliable migration.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| field name (`str`, a dict key in `ModelState.fields`) | `int` identifier | a fixed injective naming of field names to integers; the change performs ONLY set membership / equality / hashing on these keys (`set(...)`, `.difference(...)`, `.intersection(...)`, `in`) — never any character-level operation — so an integer carrier is observationally exact (mapping.md §3). |
| `set(old_base_model_state.fields)` (key set of the prior parent dict) | `candidates: PSeq[int]` (the same names, listed) + the fact that iteration domain == the parent's prior names | a `dict`'s key set is finite with distinct keys; `set(d)` enumerates the keys. The fold `selected` walks `candidates` once, so order/repetition of `candidates` does not change the *membership* of the result (each element is gated by `qualifies`); the produced dependency tuples are deduplicated by `dependencies` being consumed as a set downstream. |
| `new_base_model_state.fields` (keys) | `parent_after: PSet[int]` | `name in new_base_model_state.fields` ↔ `name in parent_after`. |
| `model_state.fields` (keys) | `child: PSet[int]` | `name in model_state.fields` ↔ `name in child`. |
| `.difference(new).intersection(model)` of the key sets | the per-element predicate `qualifies` applied to candidates | `n ∈ set(old).difference(new).intersection(model)` ⇔ `n ∈ old ∧ n ∉ new ∧ n ∈ model`. Since `candidates` enumerates exactly `old`, every result element is a candidate gated by `n ∉ parent_after ∧ n ∈ child`. |
| the appended dependency tuple `(base, base, removed_base_field, False)` | one element of the returned `List[int]` (the `removed_base_field` slot) | the base app-label / base name are loop-fixed; the only varying content of the appended tuple is `removed_base_field`, so the list of emitted field ids captures the dependency set exactly. |

`set`/`dict` key iteration with `str` keys is replaced by integer field
identifiers because Nagini bans `str` indexing/iteration; the membership and
difference/intersection semantics are preserved verbatim under the integer
relabeling.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `selected` deep model ↔ Python set difference-then-intersection (A-reference)
**Callee:** the CPython built-in set algebra
`set(old).difference(new).intersection(model)` (lines 569-571 post-patch). The
changed selection operation is modeled **deeply** by the `@Pure` front-recursive
fold `selected` (with `qualifies`) in the `pure` region; there is **no
`@ContractOnly` axiom** the proof consumes. The deep model is validated equal to
the real built-in set algebra out-of-band by axiom_check.py (G-AX):

For a name `n` that is a key of the prior parent dict (`n ∈ old`):
```
n ∈ set(old).difference(new).intersection(model)
  ⇔ (n ∈ old) and (n ∉ new) and (n ∈ model)
  ⇔ qualifies(n, parent_after=new, child=model)     # since n ∈ old by construction
```
`selected(candidates, parent_after, child)` keeps exactly the candidates (= the
keys of `old`) for which `qualifies` holds, which is exactly the membership of
the real set expression. The order/duplication of the candidate enumeration does
not affect the *set* of emitted field names, and the downstream `dependencies`
list is consumed via `check_dependency` membership (autodetector.py:374-411), so
the order is immaterial to the resolved behavior. `axiom_check.py` asserts the
deep model's emitted set equals the real `set(...).difference(...).intersection(...)`
on boundary + randomized fuzz inputs. Imports only the standard library; nothing
repo-specific.

### 3.2 No consumed axioms
There are no `@ContractOnly` axioms in this bundle. The set primitives
(`in`, `set()`, `.difference()`, `.intersection()`) are language built-ins
refined to `PSet[int]` membership, modeled deeply, and checked as the
A-reference §3.1 — not contracts the proof depends on.

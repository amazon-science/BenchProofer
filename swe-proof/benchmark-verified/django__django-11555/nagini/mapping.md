# mapping.md — django__django-11555

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8dd5877f58f84f2b11126afbd0813e24545919ed`, states the type
abstraction, and gives the provenance of the axiomatized / referenced callees.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `expand_default_ordering(kinds, ids, state)` | the related-model default-ordering expansion block of `SQLCompiler.find_ordering_name` — `django/db/models/sql/compiler.py:723-727` (the `results = []` loop over `opts.ordering`) | the modeled changed function: builds the list of ordering targets from a related model's `Meta.ordering` |
| `resolve_name(state, item_id)` *(axiom — A-consumed, impl-callable)* | the recursive call `self.find_ordering_name(item, opts, alias, order, already_seen)` for a textual-name item — `django/db/models/sql/compiler.py:725` | unchanged name-resolution machinery: resolves one textual field-name item to its concrete ordering targets, advancing the shared resolution state it is threaded |
| `machinery_state(state)` *(axiom — ABSTRACT PREDICATE, i.e. an opaque RESOURCE)* | the shared resolution state the recursion threads: the `already_seen` join-tuple set (`compiler.py:717-721`) plus the compiler's accumulated joins/alias state | bodyless `@Predicate @ContractOnly`, so it is a resource rather than a boolean fact: there is no constructor and `Fold` is rejected (`abstract.predicate.fold`). `resolve_name` consumes and returns it, so an expansion can invoke the machinery only on the single state it was handed. Counterpart: the compiler threads ONE query/`already_seen` state through the whole recursion — there is no second resolution state to resolve a name against privately |
| `invocations(state)` *(axiom — pure observation of the state, requires the resource)* | the items the recursion has been applied to against that shared state — observable in the real tree as the join tuples accumulated in `already_seen` and the joins/table references grown on the query | `@Pure @ContractOnly` multiset of item identities, readable only while holding `machinery_state(state)`; the only thing that changes it is `resolve_name`, which adds exactly the item it was applied to. Multiset, not sequence: WHICH items and HOW MANY TIMES is real behaviour, the walk ORDER is not |
| `name_items(kinds, ids)` | the multiset of `opts.ordering` items the loop recurses on | pure spec: every textual-name item exactly once, and no already-formed `OrderBy` item |
| `resolve_name_seq(item_id)` *(axiom — pure sequence the impl callee is pinned to)* | the pure target-identity sequence the recursive `find_ordering_name(textual_name, …)` produces | uninterpreted (`Ensures(True)`) spec sequence; defined to BE whatever the real machinery returns |
| `contribution(kind, item_id)` | the per-item branch of the loop body | pure spec: the targets one `Meta.ordering` item contributes |
| `expanded(kinds, ids)` *(deep model — A-reference for the kind==1 branch)* | the whole `results` list the loop accumulates over `opts.ordering` | pure spec: the front-to-back concatenation of each item's contribution |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): the loop at
`compiler.py:723-727` handed EVERY `opts.ordering` item — including items that
are already `OrderBy` expression objects — to `self.find_ordering_name(item, …)`,
whose first statement is `name, order = get_order_dir(name, default_order)`
(`compiler.py:707`). `get_order_dir` (`django/db/models/sql/query.py:2212`,
body `if field[0] == '-':` at line 2221) **subscripts** its argument, so an
`OrderBy` item raised `TypeError: 'OrderBy' object is not subscriptable`. The
patch adds, before the recursion, a guard that an already-formed `OrderBy` item
is appended directly to `results` as `(item, False)` and the loop `continue`s.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `opts.ordering`, a tuple of items, each either a `str` field-name or an `OrderBy` expression object | two index-aligned `List[int]`: `kinds[k]` ∈ {0,1} and `ids[k]` (an identity tag) | `kinds[k] == 1` ↔ `isinstance(opts.ordering[k], OrderBy)`; `kinds[k] == 0` ↔ `opts.ordering[k]` is a textual name; `ids[k]` ↔ a stable identity for the item / its produced expression |
| `results`, a list of `(OrderBy_expr, is_ref_bool)` pairs | `List[int]` of target-identity tags | `results[j][0]` ↔ `ids`-tagged produced expression; `results[j][1]` is uniformly `False` for every entry `find_ordering_name` returns (both the base case `compiler.py:729` and the new pass-through emit `…, False`), so it carries no discriminating content and is abstracted away |
| an already-formed `OrderBy` item appended verbatim as `(item, False)` | `contribution(1, id) == PSeq(id)` (a single target carrying the item's own identity) | identity preservation: the SAME object flows to the output; modeled by the singleton of its identity tag |
| a textual name expanded by the recursive machinery | `contribution(0, id) == resolve_name_seq(id)` (the opaque produced sequence) | the unchanged recursion; its content is irrelevant to the fix and is left opaque |
| the shared resolution state the recursion threads — `already_seen` (the join-tuple set guarding cyclic ordering, `compiler.py:717-721`) and the compiler's accumulated joins | a `state` carrier held as the abstract-predicate RESOURCE `machinery_state(state)`, whose invocation account `invocations(state)` is the MULTISET of items the machinery was applied to | each real invocation mutates that state (adds a join tuple to `already_seen`, accumulates joins), so an invocation is observable and cannot be undone; modeled by adding the invoked item's identity to `invocations`. The resource has no constructor because the real compiler has exactly one such state per expansion: an implementation cannot conjure a private `already_seen`/join carrier that the shared account does not see — a "private" recursion is still the real recursion applied to the real item |

`opts.ordering` items and the `OrderBy`/`str` discriminant are not directly
expressible in Nagini's fragment; they are abstracted to the kind tag. The
identity-preservation property — the heart of the fix — is carried by
`PSeq(id)` (the item's own identity) vs the opaque `resolve_name_seq(id)`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `contribution(1, ·)` deep model ↔ the `OrderBy` pass-through (A-reference)
**Changed operation.** The patch's new branch
```python
if isinstance(item, OrderBy):
    results.append((item, False))
    continue
```
makes an already-formed ordering-expression item contribute **exactly itself**,
as a single `(OrderBy, False)` target, passed through verbatim (identity
preserved), in its original position. This changed behaviour is modeled
**deeply** as `contribution(1, item_id) == PSeq(item_id)` (the `pure` region) and
the `k == 1` branch of the impl (`piece = [d]`). There is **no `@ContractOnly`
axiom for the pass-through** — it is spelled out.

`axiom_check.py` (G-AX) validates this deep model against the REAL callee: it
drives Django's post-patch `SQLCompiler.find_ordering_name` for a related model
whose `Meta.ordering` contains an `OrderBy` expression and asserts the
expression appears in the output as a single `(OrderBy, False)` entry that **is
that very object** (`e[0] is meta_orderby`), at its original position, never
expanded by the name machinery. It also confirms, against the same real source,
that `get_order_dir` subscripts its argument (so an `OrderBy` argument raises
`TypeError: 'OrderBy' object is not subscriptable` — the exact pre-patch crash),
i.e. the `isinstance` guard is load-bearing. Provenance:
`django/db/models/sql/compiler.py:723-729`,
`django/db/models/sql/query.py:2212-2223`.

### 3.2 `resolve_name` / `resolve_name_seq` ↔ the recursive name machinery (A-consumed)
**Unchanged callee.** For a textual-name item the loop recurses through
`self.find_ordering_name(item, …)` — unchanged by the patch. The model
axiomatizes it with the weakest contract the proof needs about its RETURNED
VALUE, plus the two facts about it that are not value facts at all:
- `resolve_name_seq(item_id)` is `@Pure @ContractOnly` with `Ensures(True)` — an
  uninterpreted sequence, *defined* to be whatever the real machinery produces;
- `resolve_name(state, item_id)` is `@ContractOnly`, returns a freshly produced
  owned `List[int]`, and is pinned `ToSeq(Result()) == resolve_name_seq(item_id)`;
- it CONSUMES AND RETURNS the resource `machinery_state(state)`, and it adds
  exactly `item_id` to `invocations(state)`.

The value binding is a **definitional tautology** — `resolve_name_seq` makes no
claim about content, so it over-claims nothing about the real callee.

The other two facts are NOT tautologies, and are the substance of the model.
The real callee is **partial** and **stateful**, and the axiom says only what is
true of it on both counts:

* *Stateful, and every invocation lands in one account.* The recursion threads a
  single `already_seen` set and grows the query's joins/table references
  (`compiler.py:717-721, 725`). So an invocation is observable and cannot be
  undone — hence `invocations(state)` grows by the invoked item and never
  shrinks. It also means the ACCOUNT IS SHARED: the compiler has exactly one such
  state per expansion, so there is no private carrier to resolve a name against
  on the side. That is why `machinery_state` is an **abstract predicate** (a
  resource with no body and no constructor) rather than an uninterpreted boolean
  well-formedness test. An uninterpreted boolean `Ensures(True)` is unrefutable,
  so an implementation could invent a carrier, satisfy the guard, and obtain an
  invocation that the shared account never recorded — a modelling artifact with
  no repository counterpart, since a "private" recursion is still the real
  recursion applied to the real item. As a resource, the state cannot be
  fabricated (`Fold` on a bodyless predicate is rejected outright), so every
  invocation an implementation can reach is recorded.
* *Partial.* `find_ordering_name`'s first statement is
  `name, order = get_order_dir(name, default_order)` (`compiler.py:707`), whose
  body subscripts its argument (`query.py:2221`), so it is defined for textual
  names only. The model does not encode that as a guard on the callee's kind
  argument; it is enforced through the account instead — the modelled function's
  invocation obligation admits exactly the name items, so an implementation that
  applies the machinery to an already-formed expression records an item the
  obligation does not allow.

`axiom_check.py` confirms the operative consequences against the real source —
the name machinery is applied to textual names only, yielding ≥1 freshly built
`OrderBy` target per name, and never to the already-formed `OrderBy` item (which
raises the exact pre-patch `TypeError`). `conformance_check.py` (G-CONF)
additionally checks the invocation account executably: it records every depth-1
machinery call the real loop makes, the shadow consumes one recorded call per
invocation, and a leftover recorded call is reported as a disagreement — so the
"exactly once per name item, never for an expression item" claim is oracle-checked,
not merely asserted. The account abstracts **depth-1** invocations (deeper
recursion is the callee's own business) and is a MULTISET, so it pins which items
and how many times without pinning the walk order, which the real function does
not guarantee.

**Soundness check (G-AX):** `axiom_check.py` runs inside the official SWE-bench
container for this instance (Django importable, sqlite available). It builds a
multi-table-inheritance parent/child whose parent `Meta.ordering` mixes an
`OrderBy` expression and a textual name, drives the real
`find_ordering_name`/`get_order_dir`, and asserts every obligation above. It
imports only Django (the very framework the patch lives in) and stdlib; nothing
test-specific. Exit 0 iff sound. (Verified locally against the base_commit
source at Django 3.0 / Python 3.8: passes on the patched tree, raises the exact
`TypeError` on the unpatched tree.)

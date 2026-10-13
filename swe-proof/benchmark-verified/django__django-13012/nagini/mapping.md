# mapping.md — django__django-13012

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 22a59c01c00cf9fbefaee0e8e67fab82bbaf1fd2`, states the type
abstraction, and gives the provenance of the deep-model reference (the wrapped
node's own grouping-column rule) checked by axiom_check.py / G-AX.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `wrapper_group_by_cols(node, request)` | `ExpressionWrapper.get_group_by_cols(self, alias=None)` — *added* by the patch at `django/db/models/expressions.py:865` (the class is at line 850) | the modeled changed function (the composite's grouping-column rule) |
| `WrappingNode` | `ExpressionWrapper` — `django/db/models/expressions.py:850` | minimal carrier: the composite query node, with only the touched data |
| `WrappingNode.inner_id` | identity of `ExpressionWrapper.expression` (the wrapped node, `expressions.py:858`) | the node the composite wraps |
| `WrappingNode.node_id` | identity of the `ExpressionWrapper` instance itself | the composite's own identity (what the pre-patch default contributes) |
| `WrappingNode.inner_is_constant` | whether the wrapped node's own `get_group_by_cols()` returns `[]` (constant, `Value`-like) vs `[self]` (column-like) | the discriminating property of the wrapped node |
| `base_group_by_cols(node_id, is_constant, request)` *(deep model — A-reference)* | the WRAPPED node's own `get_group_by_cols`: `Value.get_group_by_cols` (`expressions.py:706`, returns `[]`) for a constant, and `BaseExpression.get_group_by_cols` (`expressions.py:350`, non-aggregate branch returns `[self]`) for a column-like node | unchanged callee the patch forwards to; modeled deeply, validated == the real callees by axiom_check.py (G-AX), NOT consumed as an axiom |
| `base_group_cols_seq(node_id, is_constant)` | the pure sequence value of the same rule | `@Pure` spec helper carrying the dichotomy |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): `ExpressionWrapper` has no own
`get_group_by_cols`, so it inherits `BaseExpression.get_group_by_cols`
(`expressions.py:350-356`), whose non-aggregate branch (`if not
self.contains_aggregate: return [self]`, line 351-352) contributes the
**wrapper itself** — the bug.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an expression *node* (a `BaseExpression` instance) | an `int` identity | each node ↔ a distinct int; equality of nodes ↔ equality of identities. The wrapper and the node it wraps are distinct objects, so `node_id != inner_id` (a class invariant `WrappingNode`, required of the constructor and re-Required by `wrapper_group_by_cols`). |
| `get_group_by_cols`'s return — a `list` of expression nodes | `List[int]` of node identities; specification carried by `PSeq[int]` via `ToSeq` | `[]` ↔ empty `List[int]`; `[node]` ↔ `[node_id]`; `[a, b]` ↔ `[a_id, b_id]`. For the node kinds in question the list has length 0 or 1. |
| the `alias` keyword argument (`alias=None`) | `request: Optional[int]` | the grouping request is threaded to the wrapped node unchanged (`get_group_by_cols(alias=alias)`); for the **modelled family** — a constant (`Value`) and a non-aggregate column-like node — the answer does not depend on it, so the model's result is independent of `request`. The parameter is carried for skeleton fidelity (the patch forwards `alias=alias`). |

`Value.get_group_by_cols` ignores `alias` entirely (`expressions.py:706-707`);
`BaseExpression.get_group_by_cols`'s non-aggregate branch returns `[self]`
without consulting `alias` (`expressions.py:350-352`). Hence the `request`
parameter is observationally inert **for the modelled family of node kinds**,
which the `base_group_cols_seq` value (a function of `(node_id, is_constant)`
only) faithfully reflects. This alias-inertness is **not** universal over all
query nodes — e.g. `Subquery.get_group_by_cols` is alias-DEPENDENT (`alias=None`
→ `[]`, but a non-trivial alias → `[Ref(self)]`, `expressions.py:1069`). Such
nodes lie **outside** the modelled family; the composite's *forwarding* contract
still holds for them (G-AX checks this, §3.1), but they are not in the domain
`base_group_cols_seq` describes, and the model never wraps them. The two
FAIL_TO_PASS inputs (`Value(3)`, `Lower(Value('f'))`) lie strictly inside the
modelled family.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `base_group_by_cols` / `base_group_cols_seq` ↔ the wrapped node's own `get_group_by_cols`

The wrapped node's grouping-column rule is **not** changed by the patch — the
patch only makes `ExpressionWrapper` *forward to it*. It is therefore a callee,
modeled **deeply** (the constant/column-like dichotomy spelled out) rather than
hidden behind a consumed axiom; G-AX validates the deep model equal to the real
callees.

The two real callees the deep model abstracts:

```python
# django/db/models/expressions.py:350  (BaseExpression — the default, inherited
#                                        by Func/Transform/Lower/Col/RawSQL/...)
def get_group_by_cols(self, alias=None):
    if not self.contains_aggregate:
        return [self]
    cols = []
    for source in self.get_source_expressions():
        cols.extend(source.get_group_by_cols())
    return cols

# django/db/models/expressions.py:706  (Value — overrides to contribute nothing)
def get_group_by_cols(self, alias=None):
    return []
```

For the **modelled family** — non-aggregate, constant-or-column-like wrapped
nodes (the case the issue and both F2P tests exercise) — this is exactly the
dichotomy `base_group_cols_seq` encodes:

  * a bare constant (`Value`, `Value`-subclasses) → `[]` (`is_constant=True`);
  * an ordinary column-like node (`Lower`, `Upper`, `Length`, `Coalesce`,
    `RawSQL`, `Col`, resolved `F`, …) → `[self]` (`is_constant=False`).

The dichotomy is a **sound instantiation for this family, not a universal
property** of every query node. Two demonstrated escaping kinds:

  * `Subquery` is **alias-DEPENDENT** (`alias=None` → `[]`, a non-trivial alias
    → `[Ref(self)]`) — violates the alias-inertness the deep model assumes;
  * `OrderBy(<column-like>)` returns its *wrapped expression's* cols (e.g.
    `[Col(id)]`), which is neither `[]` nor `[the OrderBy itself]` — outside the
    `[]`/`[self]` dichotomy.

These nodes are deliberately outside the modelled family; the model never wraps
them. The composite's **forwarding** contract (the actual soundness obligation)
still holds for them, which G-AX confirms.

**Soundness check (G-AX):** `axiom_check.py` runs **two tiers**:

  1. *Universal (the soundness obligation the proof relies on)* — for EVERY
     wrapped node (modelled-family AND the escaping kinds above), it constructs
     the real `ExpressionWrapper` and asserts the **delegation**: the
     composite's `get_group_by_cols(alias=a)` equals the wrapped node's
     `get_group_by_cols(alias=a)` for several `alias` requests (including a
     non-trivial alias), and the composite never contributes itself. It detects
     the mounted tree (post-patch: equality holds; pre-patch: the composite
     returns `[itself]`).
  2. *Scoped (the deep-model instantiation)* — for the modelled-family nodes
     ONLY, it observes each node's real `get_group_by_cols`, asserts the
     observation is `[]` or `[self]` (dichotomy), asserts the deep model
     `base_group_cols_seq` agrees, and asserts **alias-inertness** (the answer
     is independent of the alias request). For the escaping kinds it SKIPS these
     scoped assertions and instead asserts each node actually escapes (≥1
     alias-dependent, ≥1 non-dichotomy) — so the domain boundary is
     demonstrated, not assumed, and a universally-phrased dichotomy /
     alias-inertness claim is shown to be false rather than relied upon.

Both FAIL_TO_PASS witnesses (`Value(3)`→`[]`,
`Lower(Value('f'))`→`[self.expression]`) are asserted explicitly. Imports only
`django` (the repo under test) + stdlib; resolving an `F` into a `Col` and
constructing a `Subquery` over an in-memory sqlite queryset run only Python and
open no real database connection. Exit 0 iff sound.

## 4. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl regions (the shadow)
differentially against the real patched
`ExpressionWrapper.get_group_by_cols` in-container, over the type bridge of
§2 (per-probe node↔identity bijection; the optional grouping request raises
to the `alias` keyword). Boundary grid + 100000 randomized fuzz tuples;
pinned fuzz seed: **13012** (the instance number).

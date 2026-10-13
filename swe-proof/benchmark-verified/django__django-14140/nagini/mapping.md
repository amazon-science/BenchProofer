# mapping.md — django__django-14140

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 45814af6197cfd8f4dc72ee43b90ecde305a1d5a`, states the type
abstraction, and records the provenance of the one A-reference (the changed
operation is modelled deeply; there is no consumed axiom).

Repo file under change: `django/db/models/query_utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deconstruct_arguments(node)` | `Q.deconstruct(self)` — `django/db/models/query_utils.py:83` (the `args`/`kwargs` computation, lines 87-96) | the modeled changed function (the `args`/`kwargs` halves of the reconstruction triple) |
| `Node` (class) | `django.db.models.Q` (a `django.utils.tree.Node` subclass) — `query_utils.py:28`, base `django/utils/tree.py:11` | the node being deconstructed; minimal class carrying only the touched state |
| `Node.children` | `Q.children` (a `list`; `tree.Node.__init__`, `tree.py:23`) | ordered sub-conditions |
| `Node.connector` | `Q.connector` (`tree.py:24`; `Q.AND`/`Q.OR`, `query_utils.py:34-35`) | combining connector |
| `Node.default` | `Q.default == Q.AND` (`query_utils.py:36`) | class default connector |
| `Node.negated` | `Q.negated` (`tree.py:25`) | negation flag |
| `Deconstruction.args` | the `args` tuple returned by `deconstruct` (`query_utils.py:97`) | positional reconstruction arguments |
| `Deconstruction.connector_kwarg` | presence of the `'_connector'` key in the returned `kwargs` | keyword-arg marker for a non-default connector |
| `Deconstruction.negated_kwarg` | presence of the `'_negated'` key in the returned `kwargs` | keyword-arg marker for negation |

The `path` element of the triple is unchanged by the patch (lines 84-86 are
untouched) and is not modeled — the behavioural delta is entirely in the
`args`/`kwargs` computation.

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the single-child special case
`if len(self.children) == 1 and not isinstance(self.children[0], Q): child =
self.children[0]; kwargs = {child[0]: child[1]}` (`query_utils.py:88-90`), which
emptied `args` and relocated the lone child into `kwargs` — crashing on a
non-subscriptable child (e.g. `Exists`) and mis-filing length-2-tuple children.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Q.children` — a `list` of heterogeneous sub-conditions (kwarg `(key, value)` tuples, positional objects such as `Exists`, nested `Q`s) | `List[int]` of opaque child identifiers | each child object ↔ a distinct `int`; list order/length preserved; `tuple(children)` ↔ the `List[int]` copied element-wise; an empty children list ↔ `[]` |
| `args` tuple returned by `deconstruct` | `List[int]` (`Deconstruction.args`) | `args[k]` ↔ identifier of the k-th positional argument; `tuple(...)` is the identity on element content (order/membership), the only property the F2P tests observe (`assertEqual(args, (...))`) |
| `kwargs` dict returned by `deconstruct` | two booleans (`connector_kwarg`, `negated_kwarg`) | the patched `kwargs` can only contain `'_connector'` and/or `'_negated'` (no child key) — `'_connector' in kwargs` ↔ `connector_kwarg`, `'_negated' in kwargs` ↔ `negated_kwarg`. The associated values are fixed by the keys: `kwargs['_connector'] == self.connector`, `kwargs['_negated'] is True`. axiom_check.py checks the keys-subset and value bindings against the real method. |
| `self.connector` / `self.default` (string codes `'AND'`/`'OR'`) | `int` codes | the only operation the spec performs is the equality `connector != default`; modelled as integer inequality (an order-isomorphic relabelling of the string codes) |
| `isinstance(self.children[0], Q)` guard (pre-patch only) | absorbed into the modelled domain | the modelled `children` are opaque non-`Q` sub-conditions — exactly the `not isinstance(..., Q)` arm of the removed guard, which is the case the F2P tests exercise (a `(key,value)` tuple and an `Exists`). The post-patch code drops the guard entirely, so it is absent from `model.py`; the prepatch skeleton reproduces the guard's effect (single child ⇒ empty args) on this domain. |

`str` indexing is banned in Nagini; no string content is needed here (the
behaviour is about which children land in `args`, not their internal bytes), so
opaque `int` identifiers suffice and the specification is carried over
`PSeq[int]` via `ToSeq`.

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

### 3.1 `deconstruct_arguments` deep model ↔ real `Q.deconstruct` (A-reference)

**Callee:** the changed method `django.db.models.Q.deconstruct`
(`query_utils.py:83`). The changed operation is modelled **deeply** (the args
loop + the two boolean kwargs flags in `deconstruct_arguments`); there is **no
consumed `@ContractOnly` axiom**. The deep model is validated **== the real
(patched) method** out-of-band by `axiom_check.py` (G-AX).

Post-patch source (the equivalent of the deep model):

```python
def deconstruct(self):
    path = ...
    args = tuple(self.children)          # clause (1): every child, positionally
    kwargs = {}
    if self.connector != self.default:   # clause (2): connector marker
        kwargs['_connector'] = self.connector
    if self.negated:                     # clause (2): negation marker
        kwargs['_negated'] = True
    return path, args, kwargs
```

The model's three postcondition clauses are exactly this method's behaviour:
`ToSeq(args) == ToSeq(children)` is `args = tuple(self.children)`;
`connector_kwarg == (connector != default)` is the `_connector` guard;
`negated_kwarg == negated` is the `_negated` guard. No child key can appear in
`kwargs` (the special case is gone), which axiom_check asserts via
`set(kwargs).issubset({'_connector', '_negated'})`.

**Soundness check (G-AX):** `axiom_check.py` constructs `Q` nodes covering the
boundary (no children; a single kwarg child; a single positional tuple child;
single non-subscriptable `Exists` child — the crash case; multi-child;
non-default `OR` connector; negated; the three exact F2P fixtures
`Q(price__gt=F(...))`, `~Q(price__gt=F(...))`, `Q(Exists(...))`; and the empty-Q
combinations from the expressions F2P) plus 5000 randomized node shapes (random
kwargs, positional tuples, injected `Exists` children, random connector/negation
flags). For each it asserts the real `deconstruct()`'s `args` equals
`tuple(self.children)` and its `kwargs` keys/values match the two markers
exactly, and that `Q(*args, **kwargs) == self` (the reconstruction round trip
the method exists to serve). It imports only the repo's public
`django.db.models` symbols (the module under change). Exit 0 iff sound.

Confirmed locally (Django 4.0 from the base_commit worktree, Python 3.10):
patched method ⇒ axiom_check exits 0; pre-patch method ⇒ axiom_check raises the
exact `TypeError: 'Exists' object is not subscriptable` from the problem
statement on the `Q(Exists(...)) & Q()` boundary input — so the A-reference
discriminates the fix and is not a dead/over-broad check.

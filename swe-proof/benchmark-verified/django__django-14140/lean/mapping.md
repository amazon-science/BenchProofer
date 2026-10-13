# mapping.md — django__django-14140

## Modeled function

| Lean | Python | file:line @ base_commit `45814af619` |
|---|---|---|
| `implementation_deconstruct` / `problem_spec_deconstruct` / `correct_deconstruct` | `Q.deconstruct(self)` — return `(path, args, kwargs)` such that `type(self)(*args, **kwargs)` rebuilds the node | `django/db/models/query_utils.py:83-97` (post-patch body computes `args = tuple(self.children)` and `kwargs` from the combinator/negation flags only) |

The modeled behavior is the derivation of the `(args, kwargs)` pair (and the
pass-through of the already-computed dotted `path`) from a filter node's stored
components:
- `self.children` — the node's ordered child sequence;
- `self.connector` — the node's logical combinator (`AND` / `OR`); `self.default = AND`;
- `self.negated` — the node's negation flag.

The `path` string is computed by an unchanged prefix of the method
(`'%s.%s' % (module, name)`, then a `startswith`/`replace` normalization). That
computation is identical pre- and post-patch and does not depend on the modeled
inputs, so it is taken as an already-computed `path : String` input and pinned
unchanged in the postcondition (frame discipline, SPEC_GUIDE §0.5).

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| a `Q` node's `children` list | `children : List Child` | order-preserving; `tuple(self.children)` ↔ the same list |
| a child that is a `(key, value)` lookup pair (from `sorted(kwargs.items())`; an index-addressable length-2 tuple, not a `Q`) | `Child.cond key val` | `child[0]`/`child[1]` ↔ `key`/`val`; the pre-patch single-child path subscripts these |
| a child that is a standalone conditional expression (e.g. `Exists(...)`; NOT index-addressable, not a `Q`) | `Child.expr e` | `child[0]` raises `TypeError` in the pre-patch path (`'Exists' object is not subscriptable`); `e` is an opaque label (deconstruct never inspects its content post-patch) |
| a child that is itself a `Q` node (`isinstance(child, Q)` is `True`) | `Child.nested s` | `Child.isNode` ↔ `isinstance(_, Q)`; `s` is an opaque label |
| `self.connector` / `self.default` (`'AND'` / `'OR'`) | `Connector` (`cAnd` / `cOr`); default `cAnd` | `self.connector != self.default` ↔ `connector ≠ Connector.cAnd` |
| `self.negated` | `negated : Bool` | verbatim |
| the returned `args` tuple | `Deconstructed.args : List Child` | `tuple(self.children)` ↔ the child list |
| the returned `kwargs` dict | `Deconstructed.kwargs : Kwargs` | `Kwargs.pair` ↔ the `{child[0]: child[1]}` inlined entry (only ever set on the pre-patch single-child path); `Kwargs.connector` ↔ presence of `'_connector'`; `Kwargs.negated` ↔ presence of `'_negated': True` |
| the returned `path` | `Deconstructed.path : String` | unchanged pass-through |

`Child.asPair` models Python subscription `child[0], child[1]`: it yields
`some (k, v)` for an index-addressable `cond` child and `none` otherwise. The
pre-patch impl reaches it via `Option.getD ("", "")`, modeling the fact that the
real code blindly subscripts a child it has not checked is a pair (the source of
the `TypeError` crash on `Exists` children).

## Callee provenance / flag deps

- The modeled function invokes **no UNCHANGED repository callee**: post-patch it
  uses only `tuple(...)` (a language primitive, modeled as the identity list
  refinement) and dict construction. Hence the `axioms` region declares no
  `opaque` callee and the proof consumes no `_prop` axiom. **G-AX = skip.**
- No flag-dependent callee.

## G-CONF fuzz seed

`conf_seed = 14140` (pinned; see conformance_check.py and meta.json).

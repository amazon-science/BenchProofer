# refinement.md — django__django-14140

Operation correspondence between `implementation_deconstruct` (Solution.lean) and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: `deconstruct`

The post-patch Python body (after the unchanged `path` computation) is:

```python
args = tuple(self.children)
kwargs = {}
if self.connector != self.default:
    kwargs['_connector'] = self.connector
if self.negated:
    kwargs['_negated'] = True
return path, args, kwargs
```

The behaviorally relevant part is the derivation of `(args, kwargs)` from the
node's stored components. `path` is computed by an unchanged method prefix that
does not depend on the modeled inputs; it is taken as an already-computed input
and pinned unchanged in the postcondition (frame discipline).

| # | `implementation_deconstruct` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `path : String` input, returned unchanged in `result.path` | the pre-computed `path` local, returned as the first tuple element | R / I | the `'%s.%s'` + `startswith`/`replace` prefix is unchanged by the patch and input-independent of the modeled components; modeled as a pass-through `String`. Frame: pinned `result.path = path`. |
| 2 | `let args := children` | `args = tuple(self.children)` | R | `tuple(self.children)` ↔ the identity on the child list. Python `tuple`/list ↔ Lean `List Child` (mapping.md). Order-preserving, no element transform. |
| 3 | `let mut kw := { pair := none, connector := none, negated := false }` | `kwargs = {}` | R | the empty keyword mapping. The `pair` slot models the (now removed) inlined `{child[0]: child[1]}` entry; post-patch it is never populated, so it stays `none`. |
| 4 | `if connector ≠ Connector.cAnd then kw := { kw with connector := some connector }` | `if self.connector != self.default: kwargs['_connector'] = self.connector` | R / I | `self.connector != self.default` ↔ `connector ≠ Connector.cAnd` (`default = AND` ↔ `cAnd`, mapping.md). Records the combinator iff non-default. |
| 5 | `if negated then kw := { kw with negated := true }` | `if self.negated: kwargs['_negated'] = True` | I | sets the negation flag iff the node is negated. |
| 6 | `return { path, args, kwargs := kw }` | `return path, args, kwargs` | I | the assembled decomposition triple. |

No op in `implementation_deconstruct` is changed-inexpressible. The whole
behavior is modeled directly from the node's stored components; there is **no
consumed axiom**, **no opaque callee** (the `axioms` region is empty), and **no
A-reference** deep model of an unchanged callee. The impl is all R/I content, so
G-CONF runs a real differential fuzz against the post-patch behavior, and **G-AX
is a skip** (`conf_skip = false`, no axioms to validate).

## The discriminating clause (G-DIFF / verify⟹correct)

The pre-patch body had a single-child special case:

```python
args, kwargs = (), {}
if len(self.children) == 1 and not isinstance(self.children[0], Q):
    child = self.children[0]
    kwargs = {child[0]: child[1]}
else:
    args = tuple(self.children)
    if self.connector != self.default:
        kwargs = {'_connector': self.connector}
```

For a node with exactly one non-`Q` child, the pre-patch path emptied `args`
and inlined `{child[0]: child[1]}` into `kwargs`. Two observable defects:
- a single key/value child landed in `kwargs` instead of `args` (the inconsistency
  the F2P `test_deconstruct` / `test_deconstruct_negated` pin), so `result.args`
  is `[]` instead of `children` and `result.kwargs.pair` is `some …` instead of
  `none`;
- a single standalone conditional child (`Child.expr`, e.g. `Exists(...)`) is not
  index-addressable; `child[0]` raised `TypeError` in Python. The model captures
  this by `Child.asPair` returning `none` for `expr`, which the pre-patch impl
  blindly coerces via `Option.getD ("", "")` — producing a `pair` entry the spec
  forbids (`result.kwargs.pair = none`), so the prepatch is unprovable.

`Solution_prepatch.lean` carries exactly this buggy skeleton; its
`correct_deconstruct` is unclosable on the `args = children` / `pair = none`
clauses of `problem_spec_deconstruct` (G-DIFF). The `Child.nested` case is
behavior-preserving across the patch (the pre-patch `else` branch handled it
identically), which is why the `test_deconstruct_nested` PASS_TO_PASS test
continues to hold under both.

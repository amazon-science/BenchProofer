# refinement.md — django__django-14140

The operation-by-operation correspondence between `model.py`'s implementation
(the `deconstruct_arguments` impl region — the deep model of the changed
behaviour) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses a `@ContractOnly` axiom's Ensures),
**A-reference** (a deep model validated `==` the real callee by
axiom_check.py / G-AX, NOT consumed as an axiom), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The deconstruct site — `Q.deconstruct` (`django/db/models/query_utils.py:83`)

Gold hunk (the `args`/`kwargs` computation):
```
- args, kwargs = (), {}
- if len(self.children) == 1 and not isinstance(self.children[0], Q):
-     child = self.children[0]
-     kwargs = {child[0]: child[1]}
- else:
-     args = tuple(self.children)
-     if self.connector != self.default:
-         kwargs = {'_connector': self.connector}
+ args = tuple(self.children)
+ kwargs = {}
+ if self.connector != self.default:
+     kwargs['_connector'] = self.connector
  if self.negated:
      kwargs['_negated'] = True
  return path, args, kwargs
```

| # | model.py impl op (`deconstruct_arguments`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `node: Node` with fields `children: List[int]`, `connector/default: int`, `negated: bool` | `self` (a `Q`/`tree.Node`) with `self.children`/`self.connector`/`self.default`/`self.negated` | R | object ↔ minimal class; `list` of children ↔ `List[int]` of opaque ids; string connector codes ↔ `int` (mapping.md §2). Read-only ⇒ all fields at `Acc(..., 1/2)` (directive 5). |
| A2 | `args = []` then the loop appending `node.children[i]` for `i` in `0..n`, establishing `ToSeq(args) == ToSeq(node.children)` | `args = tuple(self.children)` | R + I | `tuple(self.children)` is the children verbatim (order/membership preserved); the model spells the same copy out as a verified loop because Nagini has no `tuple`. The carrier refinement is R (list↔tuple identity on content); the per-element copy is I. This is clause (1): **every** child is positional, with no single-child special case. |
| A3 | `connector_kwarg = node.connector != node.default` | `kwargs = {}` then `if self.connector != self.default: kwargs['_connector'] = self.connector` | R | the presence of the `'_connector'` key ↔ the boolean `connector_kwarg`; the guard `self.connector != self.default` is the identical comparison (string-code ↔ int relabelling, mapping.md §2). Clause (2), connector half. |
| A4 | `negated_kwarg = node.negated` | `if self.negated: kwargs['_negated'] = True` | R + I | presence of the `'_negated'` key ↔ the boolean `negated_kwarg`; `self.negated` carried through identically. Clause (2), negation half. |
| A5 | `return Deconstruction(args, connector_kwarg, negated_kwarg)` | `return path, args, kwargs` | R | the model packages the two computed halves into a result object; the unchanged `path` element (lines 84-86) is outside the modelled behaviour (mapping.md §1). |

The whole `Q.deconstruct` method is the function **under change**, modelled
**deeply** (A2-A4 spell out its post-patch body), so it is an **A-reference**,
not a consumed axiom: G-AX (axiom_check.py) asserts the deep model equals the
real `Q.deconstruct` on boundary + fuzz nodes. There is **no `@ContractOnly`
axiom** in this bundle.

## B. The discriminating behaviour (G-DIFF)

The change removes the single-child special case that emptied `args` and
relocated the lone child into `kwargs`. The discriminating clause is

  `ToSeq(Result().args) == ToSeq(node.children)`  (clause 1),

which demands **every** child be positional. `model_prepatch.py` reproduces the
pre-patch skeleton: on a single-child node (the `not isinstance(child, Q)` arm
of the removed guard, which is the modelled domain — see mapping.md §2) it
leaves `args` empty. It therefore **fails** exactly this postcondition (`args`
is empty while `children` has one element) — the spec sensing the change. The
F2P tests observe the same delta:

- `test_deconstruct`: `Q(price__gt=F(...))` ⇒ post-patch `args == (('price__gt',
  F(...)),)`, `kwargs == {}` (pre-patch put it in `kwargs`).
- `test_deconstruct_negated`: `~Q(price__gt=F(...))` ⇒ `args == (child,)`,
  `kwargs == {'_negated': True}`.
- `test_deconstruct_boolean_expression`: `Q(Exists(...))` ⇒ `args ==
  (Exists(...),)`, `kwargs == {}` (pre-patch **crashed** here — `child[0]` on a
  non-subscriptable `Exists`).
- `test_boolean_expression_combined_with_empty_Q`: `Q(Exists(...)) & Q()` etc.
  ⇒ no crash, since `_combine` calls `deconstruct()` (pre-patch crashed).

A single `model_prepatch.py` suffices: the connector/negation kwargs markers are
unchanged by the patch (the `_connector`/`_negated` guards are identical
pre/post), so the only independently-fixed behaviour is the single-child→args
relocation, which one failing skeleton exhibits.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— how children/connector/negation map to `args`/`kwargs` — is modelled
**deeply** (the spelled-out loop + boolean flags in `deconstruct_arguments`),
not hidden behind an axiom about the function under change. There is no consumed
`@ContractOnly` axiom; the changed method appears only as the **A-reference**
that G-AX validates the deep model against (mapping.md §3.1).

## D. verify(model) ⇒ resolved

`deconstruct_arguments` verifies only if its `args` equals the full children
sequence (A2, clause 1) and its two kwargs flags are the exact connector/negation
markers (A3/A4, clause 2). By R (list↔tuple content identity, string-code↔int,
key-presence↔boolean — mapping.md §2) the verified result equals the gold
method's `(args, kwargs)` on the tested inputs; by G-AX the deep model equals the
real `Q.deconstruct` (A-reference) over the boundary + 5000 fuzz nodes, including
the exact F2P fixtures and the `Exists` crash case. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited A-reference — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).

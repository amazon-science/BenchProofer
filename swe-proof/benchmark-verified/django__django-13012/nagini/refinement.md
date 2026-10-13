# refinement.md — django__django-13012

The operation-by-operation correspondence between `model.py`'s implementation
(the `wrapper_group_by_cols` impl region, plus the deep model `base_group_by_cols`
/ `base_group_cols_seq`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The added method — `ExpressionWrapper.get_group_by_cols` (`django/db/models/expressions.py`, added at line 865)

Gold hunk (the entire patch):
```
+    def get_group_by_cols(self, alias=None):
+        return self.expression.get_group_by_cols(alias=alias)
```

| # | model.py impl op (`wrapper_group_by_cols`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `node: WrappingNode` | the `self` of `ExpressionWrapper.get_group_by_cols` | R | each expression node ↔ an int identity; the wrapper ↔ a `WrappingNode` carrying only the touched data (`inner_id`, `inner_is_constant`, `node_id`) — mapping.md §1, §2. |
| A2 | parameter `request: Optional[int]` | the `alias=None` keyword argument | R | the grouping request; `None` ↔ `None`, any alias ↔ an int. mapping.md §2. |
| A3 | `cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)` | `self.expression.get_group_by_cols(alias=alias)` | R + A-reference | `self.expression` ↔ the wrapped node identified by `node.inner_id`; `.get_group_by_cols(alias=alias)` ↔ the deep model `base_group_by_cols(node.inner_id, node.inner_is_constant, request)` of the wrapped node's own (unchanged) grouping-column rule. The request `alias` is forwarded **unchanged** in both (R on the parameter). The wrapped node's rule is modeled **deeply** (the constant/column-like dichotomy spelled out in `base_group_by_cols` / `base_group_cols_seq`), validated == the real callees by G-AX (mapping.md §3.1) — an **A-reference**, not a consumed axiom. There is no `@ContractOnly` axiom in this bundle. |
| A4 | `return cols` | `return ...` | I | return the wrapped node's answer verbatim. |

## B. The deep model — `base_group_by_cols` / `base_group_cols_seq`

The wrapped node's own `get_group_by_cols` is the callee the new method
forwards to; the patch does **not** change it. It is modeled deeply:

| # | model.py construct | real counterpart | tag | justification |
|---|---|---|---|---|
| B1 | `base_group_cols_seq(id, is_constant) == PSeq()` when `is_constant` | `Value.get_group_by_cols` returns `[]` (`expressions.py:706`) | A-reference | a bare constant contributes no grouping columns. G-AX asserts every real constant wrapped node observes `[]`. |
| B2 | `base_group_cols_seq(id, is_constant) == PSeq(id)` otherwise | `BaseExpression.get_group_by_cols` non-aggregate branch returns `[self]` (`expressions.py:350-352`) | A-reference | a column-like non-aggregate node contributes itself. G-AX asserts every real column-like wrapped node observes `[self]`. |

The deep model is the A-reference; G-AX validates `base_group_cols_seq` equal to
these real callees and validates the A3 delegation against the real
`ExpressionWrapper.get_group_by_cols` (mapping.md §3.1).

## C. The discriminator (G-DIFF)

The decisive content of the change: the composite must return the WRAPPED
node's answer, **never** `[self]` (the composite). The pre-patch
`ExpressionWrapper` had no own `get_group_by_cols` and inherited
`BaseExpression`'s default, which returns `[self]` for a non-aggregate node.
`model_prepatch.py` reproduces exactly that (`return [node.node_id]`) and
**fails** the postcondition

  `ToSeq(Result()) == base_group_cols_seq(node.inner_id, node.inner_is_constant)`

for BOTH tested arms simultaneously:
  * wrapped constant — required `[]`, prepatch yields `[node_id]` (non-empty);
  * wrapped column-like — required `[inner_id]`, prepatch yields `[node_id]`,
    and `inner_id != node_id` (the wrapper and the node it wraps are distinct
    objects, a class invariant of `WrappingNode`).

Both FAIL_TO_PASS tests (`test_empty_group_by`: `Value(3)`→`[]`;
`test_non_empty_group_by`: `Lower(Value('f'))`→`[self.expression]`) are the two
arms; a single pre-patch skeleton witnesses both, since the inherited default
returns the wrapper in either case. No separate `model_prepatch_<k>` is needed:
there is one fixed behaviour (the missing override / inherited `[self]`) whose
two observable arms are both sensed by the one symbolic postcondition.

## C'. Termination (total correctness)

Both modelled routines carry a `MustTerminate` obligation in their
preconditions (`base_group_by_cols` at measure 2, `wrapper_group_by_cols` at
measure 3, strictly above its callee). Nagini verifies partial correctness by
default, so without the obligation a non-terminating implementation (e.g. bare
self-recursion before returning) would satisfy the value postcondition
vacuously; the real operations always answer. The decreasing measures let the
composite invoke the wrapped node's rule while forbidding self-reinvocation of
either routine.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding the composite's forwarding rule — is the verified
`wrapper_group_by_cols` itself (step A3/A4), modeled directly. The callee it
forwards to (the wrapped node's own rule) is **unchanged** and modeled deeply
(B1/B2, an A-reference G-AX validates); there is no consumed `@ContractOnly`
axiom about the function under change or anything else.

## E. verify(model) ⇒ resolved

`wrapper_group_by_cols` verifies only if its result equals the wrapped node's
own grouping-column answer `base_group_cols_seq(inner_id, inner_is_constant)`
(the A3 postcondition), i.e. `[]` for a constant and `[inner_id]` for a
column-like node — never the composite `[node_id]`. By R (node ↔ identity,
list ↔ `List[int]`/`PSeq`, `alias` forwarded unchanged) the verified method
equals `self.expression.get_group_by_cols(alias=alias)` on the tested inputs;
by G-AX the deep model `base_group_cols_seq` equals the real wrapped-node
callees (A-reference) and the real `ExpressionWrapper.get_group_by_cols`
forwards identically. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited deep-model
reference — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ).

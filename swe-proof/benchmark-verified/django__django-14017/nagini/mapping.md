# mapping.md — django__django-14017

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 466920f6d726eee90d5566e0a9948e92b33a122e`, states the type
abstraction, and records the (absence of) axiom provenance.

Repo file under change: `django/db/models/query_utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combine(other_is_container, other_is_boolean_operand, other_empty, self_empty, conn)` | `Q._combine(self, other, conn)` — `django/db/models/query_utils.py:42` (changed guard at line 43) | the modeled changed function (boolean combination of a filter container with another operand) |
| `other_is_container` (bool param) | `isinstance(other, Q)` — `query_utils.py:43` | observable: the operand is another same-kind container |
| `other_is_boolean_operand` (bool param) | `getattr(other, 'conditional', False) is True` — post-patch guard at `query_utils.py:43` | observable: the operand is usable directly as a boolean filter condition (a boolean-valued operand). NB: the model param is the NEUTRAL behavioral name `other_is_boolean_operand`; the repo attribute it abstracts (`conditional`) is named here only for the refinement audit and is NOT in the consumer spec view (D1: that fix-keying term, absent from the public problem_statement, was scrubbed from model.py). |
| `other_empty` (bool param) | `not other` — `query_utils.py:47` (`tree.Node.__bool__`, `django/utils/tree.py:60`) | observable: the operand is empty (its identity form) |
| `self_empty` (bool param) | `not self` — `query_utils.py:51` (`tree.Node.__bool__`) | observable: the calling container is empty |
| `conn` (int param) | `conn` argument of `_combine` (`Q.AND` / `Q.OR`) — `query_utils.py:42`, set at line 56 | the requested boolean connector (opaque tag) |
| `Combined` (result class) | the value `_combine` returns: a `Q` (`type(self)(*args, **kwargs)` line 49, `type(other)(...)` line 53, or the fresh `obj` lines 55-59) | observable outcome: which branch produced the result + the merged connector |
| `OperandTypeRejected` (exception) | `raise TypeError(other)` — `query_utils.py:44` | user-defined stand-in for the rejection `TypeError` |

The pre-patch guard the change widens (referenced for the refinement audit, not
from the consumer spec view): `if not isinstance(other, Q):` at
`query_utils.py:43`.

`Q.conditional = True` is a class attribute at `query_utils.py:37`; the operand
the bug rejected, `Exists`, gets `conditional == True` from
`BaseExpression.conditional` (`django/db/models/expressions.py:255-257`,
`return isinstance(self.output_field, fields.BooleanField)`) because
`Exists.output_field = fields.BooleanField()` (`expressions.py:1152`). These are
unchanged by the patch and are exercised concretely by axiom_check.py.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `other` (an arbitrary object) | three booleans `other_is_container`, `other_is_boolean_operand`, `other_empty` | the only observables `_combine` reads off `other` are `isinstance(other, Q)`, `getattr(other, 'conditional', False) is True` (modeled by the neutral `other_is_boolean_operand`), and `bool(other)`. The discriminating behaviour (reject vs. accept, and which acceptance branch) is a function of exactly these three predicates plus `self`'s emptiness — proven exhaustively (20 combos) in axiom_check.py against the real callee. |
| `self` (the calling `Q`) | boolean `self_empty` | the only observable of `self` the branch logic reads is `bool(self)` (`not self`); `self` is not mutated by `_combine`. |
| `conn` (`'AND'` / `'OR'` string) | `int` tag | `_combine` only stores `conn` into the merged node's `connector` and never inspects its value; the connector is observationally opaque. The model pins the merge to carry EXACTLY the passed `conn`, mirroring `obj.connector = conn` (line 56). |
| return value (a `Q`, or a copy of `other`) | `Combined(branch, connector)` | `branch` tags which of the three real return statements fired (line 49 self-copy / line 53 other-copy / lines 55-59 merge); `connector` is the merged node's connector. The F2P tests observe only that no `TypeError` is raised and that the combination is the intended conjunction/disjunction; the branch + connector tags over-determine that. |
| `raise TypeError(other)` (line 44) | `raise OperandTypeRejected()` | a builtin exception in an `Exsures` crashes the Nagini translator (SPEC_GUIDE §2), so the rejection is a user-defined class; the executable equivalence `TypeError` ↔ `OperandTypeRejected` is checked by axiom_check.py / G-AX. |

No `str` content is observed; nothing is indexed; no heap permission beyond the
freshly-constructed `Combined` result is needed.

**Totality.** `combine` carries `Requires(MustTerminate(2))` (and
`Combined.__init__` carries `MustTerminate(1)` so result construction
discharges within it): the real `Q._combine` is straight-line bounded work
that always returns or raises, and Nagini's default partial-correctness
reading would otherwise let a diverging implementation satisfy every
postcondition vacuously (refinement.md step A7).

## 3. Callee provenance (kind-A)

**None.** This bundle consumes NO `@ContractOnly` axiom and has NO A-reference
deep model. The changed function `_combine` invokes no unchanged library callee
inside the changed logic: it reads `isinstance`, `getattr`, and object
truthiness (all modelled abstractly as the input predicates), and its downstream
identity/merge branches (`deconstruct` / `_new_instance` / `add`) are modelled
directly as the three branch outcomes. The `axioms` and `pure` regions of
model.py are therefore empty.

The single soundness obligation — that the boolean-predicate abstraction is
faithful to the real `Q._combine` — is discharged by axiom_check.py (G-AX),
which runs the REAL post-patch `Q._combine` on concrete Django operands
(`Q()`, `Q(...)`, `Exists(...)`, `Value(...)`, a plain int) across both
connectors and both self-emptiness states (20 combinations) and asserts every
acceptance decision and branch outcome equals the model's pinned behaviour. In
particular it exercises the discriminating operand `Exists(...)` (a non-`Q`
usable directly as a boolean filter condition — `conditional is True`), which the
model and the real callee both ACCEPT, and the non-boolean operands (`Value(1)`,
a plain int), which both REJECT with `TypeError`.

**Patch state (reproducibility).** The model abstracts the POST-patch
`Q._combine`, but the eval image is checked out at `base_commit` (PRE-patch),
where `Q._combine` still rejects a boolean-valued non-container operand.
axiom_check.py therefore self-applies the bundle's `patch.diff` to the writable
`/testbed` checkout BEFORE importing Django (idempotent: it detects the
post-patch guard `getattr(other, 'conditional', False) is True` and skips
re-applying if the harness already applied the patch via `apply_gold=True`). It
thus returns RC 0 under the STANDARD default recipe (`apply_gold=False`, bundle
mounted read-only at `/work`) and under `apply_gold=True`; both were confirmed
in-container (RC 0, 20/20 combos, 0 violations). A `git apply` failure surfaces
explicitly as RC 3 rather than being swallowed as a generic mismatch.

**Conformance (G-CONF).** conformance_check.py runs the contract-stripped impl
region (the shadow) against the REAL patched `Q._combine` (the gate applies
patch.diff and sets PYTHONPATH=/testbed) over an exhaustive boundary grid of
concrete container states x operand categories x both connectors plus 100000
randomized fuzz probes. Pinned fuzz seed: 14017.

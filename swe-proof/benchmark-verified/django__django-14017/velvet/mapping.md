# mapping.md — django__django-14017

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 466920f6d726eee90d5566e0a9948e92b33a122e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/models/query_utils.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineConditions (other : Operand) (combined : CombinedNode)` | `Q._combine(self, other, conn)` — `django/db/models/query_utils.py:42` | the modeled changed function, restricted to its admissibility guard |
| `other : Operand` | the `other` argument of `_combine` (`query_utils.py:42`) — the right-hand operand of `&`/`\|` | the operand whose admissibility the guard decides |
| `other.isFilterNode : Bool` | `isinstance(other, Q)` (`query_utils.py:43`) — whether `other` is itself a filter-condition container (`Q`) | first admissibility observable |
| `other.isCondition : Bool` | `getattr(other, 'conditional', False) is True` (post-patch `query_utils.py:43`) — whether `other` advertises it denotes a boolean condition usable as a filter | second admissibility observable (the one the fix adds) |
| `combined : CombinedNode` | the node `_combine` builds from the two operands when they ARE admissible (`query_utils.py:45-58`: the empty-operand short-circuits and the `obj.add(self,conn); obj.add(other,conn)` construction) | the UNCHANGED combination result; modeled as a free input (see §3) |
| `combineResult` *(deep model)* | the post-patch guard `if not(isinstance(other,Q) or getattr(other,'conditional',False) is True): raise TypeError(other)` followed by the unchanged combination | pure spec: admit ⟹ return the combination, else reject; modeled deeply, NOT an axiom |
| `Except.error CombineErr.notCombinable` | `raise TypeError(other)` (`query_utils.py:44`) | the observable rejection of an inadmissible operand |

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): `if not isinstance(other, Q): raise TypeError(other)`
(`query_utils.py:43`), which rejects EVERY non-`Q` operand — including a
condition-bearing expression — so `Q() & <condition>` raises `TypeError` while
`<condition> & Q()` (handled by the operand's own `_combine`, unchanged) does
not. The change makes the two directions agree.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `other`, the right-hand operand, reduced to the two observables the guard reads | `Operand` (`isFilterNode`, `isCondition`) | an operand is modeled by (a) `isinstance(other, Q)` ↔ `isFilterNode` and (b) `getattr(other, 'conditional', False) is True` ↔ `isCondition`. These are the ONLY two observables the changed guard consults. |
| the node `_combine` constructs from two admissible operands (`query_utils.py:45-58`) | `CombinedNode` (opaque `payload : List Int`) | the construction (empty short-circuits, `obj.add(self,conn)`, `obj.add(other,conn)`) is UNCHANGED by the patch; its content is not inspected by the guard. Modeled as an opaque carrier supplied to the operation (a free input). |
| `raise TypeError(other)` (`query_utils.py:44`) | `Except.error CombineErr.notCombinable` | the observable rejection: the operand cannot participate in the combination. |
| a successful combination (`_combine` returns the built node) | `Except.ok combined` | the operation yields the unchanged combination result. |

The truthiness short-circuits (`if not other: …` / `elif not self: …`,
`query_utils.py:46-51`) and the `obj.add` construction are UNCHANGED by the patch
and live ENTIRELY after the guard; the change touches only the admissibility
test on line 43. They are therefore folded into the opaque `combined` carrier and
are outside the modeled behaviour.

## 3. Callee provenance

No consumed axioms; no deep-model reference to a concrete external callee.

- **The combination result (`combined`).** When the operands are admissible,
  `_combine` builds the combined node by machinery the patch does NOT change (the
  empty-operand short-circuits and `obj.add(self,conn); obj.add(other,conn)`). We
  do NOT axiomatize it: it is supplied to the operation as a free input
  `combined : CombinedNode`, and the postcondition (`Except.ok combined` on
  admission) holds for EVERY value of `combined`. This is strictly weaker than
  any concrete behaviour of the real construction, so there is no over-claim to
  check (directive 7). The change is parametric in this construction — pre- and
  post-patch build the combination identically; only the admissibility guard
  differs.

- **The admissibility guard (`isinstance(other, Q) or getattr(other,
  'conditional', False) is True`).** This is the CHANGED operation; it is
  modeled DEEPLY (`combineResult` + the branch on `isFilterNode || isCondition`),
  NOT behind an axiom about the function under change (directive 7). The two
  Python predicates `isinstance(other, Q)` and `getattr(other, 'conditional',
  False) is True` are pure attribute/type reads with no hidden behaviour; their
  fidelity to the gold patch is audited mechanically by G-CONF
  (`conformance_check.py`).

There is therefore no `axiom_check.py` for this bundle (`meta.json gates.G-AX =
skip`, like django__django-13590 / django__django-11149).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14017`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `combineResult` (the deep guard model) to Python and runs it
against the gold-patched `Q._combine` admissibility behaviour over the four
operand classes the change distinguishes: a filter-condition container (`Q`,
empty and non-empty), an operand advertising a boolean condition
(`conditional=True`), an operand advertising `conditional=False`, and an operand
with no `conditional` attribute at all. The whole impl region is R/I (no A-tagged
callee in the computed `out`), so `conf_skip = false`.

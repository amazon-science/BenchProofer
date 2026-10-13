# mapping.md — django__django-13028

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 78ad4b4b0201003792bfdbf1a7781cbc9ee03539`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of every modeled operation.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `checkFilterable (nodes : List Node)` | `Query.check_filterable(self, expression)` — `django/db/models/sql/query.py:1125` | the modeled changed function (the filterability guard over the operand tree) |
| `Node.filterable` | `getattr(node, 'filterable', True)` — `query.py:1127` post-patch | per-node filterability flag (absent ⇒ `True`) |
| `Node.isOperand` | `hasattr(node, 'resolve_expression')` — `query.py:1128` post-patch (the **added** conjunct) | whether the node is a query operand (the kind of object whose filterability flag is meaningful), vs a plain comparison value |
| `nodeBad (n : Node)` | the post-patch guard `hasattr(node,'resolve_expression') and not getattr(node,'filterable',True)` — `query.py:1128-1129` | per-node "offending" predicate (I — identical concrete op) |
| `anyBad (ns : List Node)` | the recursive DFS over `get_source_expressions()` (`query.py:1132-1134`) reduced to "does any visited node offend" | deep, identical model of the unchanged traversal (R + I) |

The recursion structure (`get_source_expressions`, `query.py:1132-1134`) is
**unchanged** by the patch; only the per-node guard at `query.py:1127-1131`
changed. The traversal is therefore a type refinement (R), not an axiom.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the operand tree rooted at `expression`, walked DFS via `get_source_expressions()` | `List Node` | the multiset of all nodes `check_filterable` visits (root + every recursive descendant) ↔ the `List Node`; visit order is irrelevant because the observable (raise-or-not) is an order-independent OR over per-node guards |
| `getattr(node, 'filterable', True)` | `Node.filterable : Bool` | `True`/absent ↔ `filterable = true`; `False` ↔ `filterable = false` |
| `hasattr(node, 'resolve_expression')` | `Node.isOperand : Bool` | present ↔ `isOperand = true`; absent ↔ `isOperand = false` |
| `check_filterable` raises `NotSupportedError` | `raised : Bool` | raised ↔ `raised = true`; returns normally ↔ `raised = false`. `check_filterable` returns `None`; its only observable is the raise. |

`check_filterable`'s recursion visits the root and every node returned by
`get_source_expressions()` transitively. Because the per-node guards are
combined by a short-circuit-free disjunction (any single offending node forces
the raise, regardless of traversal order), the tree flattens losslessly to the
unordered `List Node` carrier.

## 3. Callee provenance

**No axioms; no deep-model references (A-reference); no consumed axioms
(A-consumed).** The single operation the patch changes — the per-node guard —
is modeled **identically** (`nodeBad`), and the surrounding traversal is a
structural refinement (`anyBad` over the flattened node list). Every step is
therefore R or I (see refinement.md), all mechanically checked by G-CONF
against the real patched `check_filterable`. There is no unchanged opaque
callee whose contract the proof must assume, so `axiom_check.py` (G-AX) has no
axiom to validate and exits 0 after confirming the bundle declares none.

The two attribute accesses the guard performs (`getattr(...,'filterable',True)`,
`hasattr(...,'resolve_expression')`) are Python builtins with fixed semantics,
refined to the `Node` fields per §2; G-CONF exercises both real builtins on
fuzzed node objects (with/without each attribute) so the §2 bijection is
falsifiable, not merely asserted.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13028`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `nodeBad`/`anyBad` (R/I-tagged ops) to Python and compares the
resulting boolean against the real patched `Query.check_filterable`'s
raise-or-not observable over fuzzed operand trees. There are no A-tagged
callees to leave as real-callee calls (§3).

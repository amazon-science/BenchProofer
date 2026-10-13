# mapping.md — django__django-13128

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2d67222472f80f251607ae1b720527afceba06ad`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the modeled function and its (un-axiomatized) collaborators.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveCombined (selfKind conn lt rt)` | `CombinedExpression.resolve_expression(self, query, allow_joins, reuse, summarize, for_save)` — `django/db/models/expressions.py:476` | the modeled changed function: the resolve-time node-kind **selection** the patch introduces |
| `dispatchKind` (pure) | the new `if not isinstance(self, (DurationExpression, TemporalSubtraction)): …` selection body added to `resolve_expression` (`expressions.py:476` post-patch, hunk 2) | deep model of the changed selection — the function under change, NOT an axiom |
| `NodeKind.combined / durationNode / temporalNode` | the three node classes `CombinedExpression` / `DurationExpression` / `TemporalSubtraction` (`expressions.py:425 / 484 / 512`) | the result-node identity the selection returns |
| `Connector.plus / minus` | the `connector` string; `minus` is `CombinedExpression.SUB = '-'` (`Combinable.SUB`, `expressions.py:39`) | the binary connector |
| `FieldTag` ∪ `none` | the operand `output_field.get_internal_type()` string, or the `None` produced when reading it raises `AttributeError`/`FieldError` | the resolved operand's output-type tag |

The pre-patch repo symbols the change *moves* (refinement audit only — NOT in the
consumer spec view): the identical type-driven dispatch block that lived in
`CombinedExpression.as_sql` (`expressions.py:445`, the gold-removed hunk) gated by
`not connection.features.has_native_duration_field`, and `DurationExpression.as_sql`'s
new native-duration short-circuit (`expressions.py:496`). Neither is modeled: the
sole behavioral observable the F2P tests exercise is **which node kind the resolve
step selects** (which fixes `output_field` resolution so the mixed-type `FieldError`
is no longer raised).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the receiver node's class | `NodeKind` | `CombinedExpression ↔ combined`, `DurationExpression ↔ durationNode`, `TemporalSubtraction ↔ temporalNode` (G-CONF `name_to_kind`) |
| `self.connector` string | `Connector` | `'-' ↔ minus`; every other connector (`'+' '*' '/' …`) ↔ `plus` — only `SUB` participates in the temporal branch, so all non-`SUB` connectors are observationally one class (`'+'` is the representative G-CONF fuzzes) |
| operand `output_field.get_internal_type()` | `Option FieldTag` | `'DateField' ↔ some dateTag`, `'DateTimeField' ↔ some dateTimeTag`, `'TimeField' ↔ some timeTag`, `'DurationField' ↔ some durationTag`, any other internal type ↔ `some otherType`, and **`AttributeError`/`FieldError` when reading `output_field` ↔ `none`** |
| the `try/except (AttributeError, FieldError): … = None` guards | the `Option` being `none` | reading a missing/unresolvable output field yields `none`; the model supplies the tag as an abstracted **input**, so the exception handling is collapsed into the carrier (LESSON: abstracted-input-not-axiom — `lt`/`rt` are R-refined inputs, not callee axioms) |

`lt`/`rt` are **inputs** to `resolveCombined`, abstracting the two
`{lhs,rhs}.output_field.get_internal_type()` reads (with their exception→`None`
collapse). They are NOT axiomatized callees: the selection's behavior is a pure
function of these tags + the connector + the receiver kind, and that pure function
(`dispatchKind`) is exactly what the patch adds. There is therefore **no `axiom`**
in this bundle and **no `axiom_check.py`** — G-AX skips (gates.py: "no axiom_check.py").

## 3. Callee provenance (kind-A) — none

There are **no consumed axioms and no deep-model references** in this bundle. The
changed operation is the node-kind selection itself, modeled deeply by
`dispatchKind` and proven equal to the `do`-block skeleton by `prove_correct`. The
recursive `lhs/rhs.resolve_expression(...)` calls the patch also performs are
**unobservable** at the granularity the F2P tests check (they recurse structurally
and do not alter which top-level node class is selected for the tested operands,
which are leaf `F()`/`Value`/subquery operands); they are abstracted away by taking
`lt`/`rt` as already-resolved output-type tags (R, mapping.md §2). No callee is
pinned by a contract, so nothing is G-AX-checked.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13128`** so the
consumer-side verdict is reproducible. It enumerates the full abstract product
(3 node kinds × 2 connectors × 6 operand tags × 6 operand tags = 216 boundary
configs) and then 100 000 fuzzed configs, transliterating `dispatchKind` (the
R/I impl) to Python (`shadow_dispatch`) and comparing it to the patched real
`CombinedExpression.resolve_expression` observed as the selected node class
(`make_oracle`). Exit 0 iff zero disagreements.

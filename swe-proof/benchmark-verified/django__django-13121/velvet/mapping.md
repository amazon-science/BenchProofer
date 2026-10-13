# mapping.md — django__django-13121

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ec5aa2161d8015a3fe57dcbbfe14200cd18f0a16`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

Repo file under change (behaviourally): `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectRenderer (native, conn, lt, rt)` | `CombinedExpression.as_sql` — `django/db/models/expressions.py:443` (the renderer-selection head, lines 444–459) | the modeled changed function: chooses which renderer produces a generic binary node's SQL |
| `dispatchNode` *(pure deep model — R/I)* | the two leading `if` guards of `CombinedExpression.as_sql` (post-patch, lines 452–460) | pure spec: the renderer chosen from native flag, connector, and the two operand type tags |
| `isIntervalMix lt rt` *(pure — R/I)* | `'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type` (post-patch interval guard) | pure spec: operands mix an interval-typed operand with a differently-typed one |
| `isTemporalTag t` *(pure — R/I)* | `lhs_type in {'DateField','DateTimeField','TimeField'}` (the point-in-time-difference guard) | pure spec: tag denotes a point-in-time type |
| `FieldTag` / `Connector` / `NodeKind` *(inductive carriers — R)* | a resolved operand's `get_internal_type()` string / `self.connector` / the renderer class chosen (`CombinedExpression` vs `DurationExpression` vs `TemporalSubtraction`) | abstracted inputs/output of the selection |

There are **no axioms** and **no deep-model references** in this bundle: the only
behaviour the fix changes — which renderer a generic node selects — is modeled
directly over abstracted inputs. The renderers themselves
(`DurationExpression.as_sql`, `TemporalSubtraction.as_sql`, the generic combine)
are an UNCHANGED shared continuation reached identically before and after the
fix; nothing about them is consumed as a contract (refinement.md §C).

### 1.1 Supporting refactors folded away (audit only — not in the spec view)

The gold patch is multi-site, but every other hunk is a mechanical refactor that
preserves the F2P-observable dispatch decision modeled here:

- `Combinable._combine` (`expressions.py:56`): a `timedelta` literal is wrapped as
  `Value(other, output_field=DurationField())` instead of the bespoke
  `DurationValue`. Observationally this just makes the literal's resolved tag
  `durationTag` — captured by the `rt`/`lt` input to `selectRenderer`.
- `DurationExpression.compile` (`expressions.py:482`): drops the
  `isinstance(side, DurationValue)` short-circuit; with `DurationValue` removed,
  the duration-typed operand path is unchanged for the F2P inputs.
- `DurationValue` class deleted (`expressions.py:712`); `date_interval_sql`
  removed from base/mysql/sqlite operations, and the now-dead
  `duration_microseconds` import dropped. These are the broken interval renderer
  the buggy dispatch used to reach; once two-duration sums route through the
  generic combine, they are unreachable for the F2P case and removed.

These are R-refinements of the same selection (mapping.md §2) — they change *how*
a duration literal acquires its tag and *what* the now-unused interval path
contained, not *which renderer a generic node selects*, which is the sole
F2P-observable behaviour `test_duration_expressions` checks.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `operand.output_field.get_internal_type()` ∈ {`'DateField'`,`'DateTimeField'`,`'TimeField'`,`'DurationField'`, other} | `FieldTag` (`dateTag`/`dateTimeTag`/`timeTag`/`durationTag`/`otherType`) | string ↔ constructor; any other concrete internal type ↔ `otherType` (never participates in a branch) |
| `output_field` raises `FieldError` (no resolvable type) | `none : Option FieldTag` | the `except FieldError: lhs_type = None` arm |
| `self.connector` (`self.ADD='+'` / `self.SUB='-'` / any other) | `Connector` (`plus`/`minus`) | `'-'` ↔ `minus`; every other connector ↔ `plus` (only `SUB` participates in the temporal branch) |
| `connection.features.has_native_duration_field` (`bool`) | `native : Bool` | identity; `True` for postgres/oracle, `False` for sqlite/mysql (base default) |
| the renderer chosen (`CombinedExpression` self / `DurationExpression` / `TemporalSubtraction`) | `NodeKind` (`combined`/`durationNode`/`temporalNode`) | class ↔ constructor; this is the observable output |

The two operand tags are abstracted **inputs** (R-tagged), supplied directly to
`selectRenderer` — they are NOT axiomatized callees (the
LESSON-abstracted-input-not-axiom pattern; cf. sibling instance 13128).

## 3. Callee provenance and flag dependency

- **No consumed axioms; no A-reference deep models.** G-AX has nothing to check
  for this bundle (no `axiom_check.py`; gates.py skips G-AX when absent).
- **Flag dependency (G-CONF must cover both settings):** the interval branch is
  gated on `not connection.features.has_native_duration_field`. G-CONF therefore
  fuzzes `native ∈ {False, True}` so both the SQLite/MySQL (the issue's failing
  backends, `native=False`) and the postgres/oracle (`native=True`) configurations
  are exercised. The bug from the problem statement is the `native=False`,
  both-`durationTag` case.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13121`**. It enumerates
the full abstract product (2·2·6·6 = 144 boundary configs) then fuzzes 100 000
more, building the oracle from the patched `CombinedExpression.as_sql` driven by
a recording stub compiler/connection that reports which renderer branch fires.
The shadow transliterates `dispatchNode`/`isIntervalMix`/`isTemporalTag` (all
R/I ops); there is no A-tagged callee to leave as a real call.

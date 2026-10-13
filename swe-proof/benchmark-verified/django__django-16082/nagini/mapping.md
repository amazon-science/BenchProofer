# mapping.md — django__django-16082

Binds every `model.py` symbol to its repository counterpart at
`base_commit = bf47c719719d0e190a99fa2e7f959d5bbb7caf8a`, states the type
abstraction, and gives the provenance of each deep-model reference (the
unchanged primitive the deep model is validated against by G-AX).

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_combined_type(connector, lhs_type, rhs_type)` | `_resolve_combined_type(connector, lhs_type, rhs_type)` — `django/db/models/expressions.py:621-628` | the modeled function: combined-type resolution for a binary combination, consulting the per-connector registry and returning the first matching result type or `None` |
| `is_subtype(a, b)` *(deep model — A-reference)* | the `issubclass(lhs_type, combinator_lhs_type)` / `issubclass(rhs_type, combinator_rhs_type)` tests inside the scan (`expressions.py:625-627`) | pure spec: the subtype test the scan uses; validated `is_subtype == issubclass` against the real hierarchy by axiom_check.py (G-AX) |
| `is_int_kind(t)` *(deep model — A-reference)* | `issubclass(t, fields.IntegerField)` — the integer-operand arm of the same two tests | pure spec: the OPEN family of field types below `IntegerField`. Validated by G-AX against every real subclass of `IntegerField` discovered by walking `Field.__subclasses__()` in the repo's own field modules |
| `is_date_kind(t)` *(deep model — A-reference)* | `issubclass(t, fields.DateField)` — the date-operand arm | pure spec: `DateTimeField` lies below `DateField` (`fields/__init__.py:1453`); validated by G-AX |
| `row(clhs, crhs, lhs, rhs)` | one iteration of the scan's `if issubclass(...) and issubclass(...)` test (`expressions.py:625-627`) | pure spec: does a recorded row match the query |
| `records_same_type_numeric(c)` | the connector tuple of the **same-type numeric** dict (`expressions.py:512-521`) — ADD/SUB/MUL/DIV/MOD/POW | pure spec: which connectors record the same-type numeric rows (and, per `expressions.py:557-565`, the numeric-with-NULL rows) |
| `records_mixed_numeric(c)` | the connector tuple of the **different-type numeric** dict (`expressions.py:531-536` post-patch) — ADD/SUB/MUL/DIV/MOD | pure spec: which connectors record the MIXED-type numeric rows |
| `records_bitwise_integer(c)` | the connector tuple of the **bitwise** dict (`expressions.py:541-547`) | pure spec: the five bitwise connectors, each recording one `(Integer, Integer) -> Integer` row |
| `has_permitted_combination(c, lhs, rhs)` | "the `for` loop over `combinators` finds SOME matching row" (`expressions.py:623-628`) | pure spec: the registry permits this combination, i.e. the scan returns a type rather than falling through to `None` |
| `resolve_combined_type` impl cascade *(deep model — A-reference)* | the data `_connector_combinators[connector]` built from `_connector_combinations` + `register_combinable_fields` (`expressions.py:503-618`), scanned by the `for ... in combinators` loop (`expressions.py:623-628`) | the whole registry, recorded per connector; validated == the real `_connector_combinators` (via `_resolve_combined_type`) for every registered connector by axiom_check.py (G-AX) |

The pre-patch repo state the change fixes (for the refinement audit, not
referenced from the consumer spec view): the **"Numeric operations - operands of
different type"** dict (`expressions.py:523-537`) registers its four mixed rows
only `for connector in (Combinable.ADD, Combinable.SUB, Combinable.MUL,
Combinable.DIV)` — `Combinable.MOD` is absent. The gold patch adds
`Combinable.MOD` to that connector tuple, so the four mixed rows are recorded
for the remainder connector too. (The same-type numeric dict at
`expressions.py:505-522` already includes `Combinable.MOD`, and the
numeric-with-NULL dict at `expressions.py:550-566` already includes it; only the
mixed-type dict was missing it — which is why same-type and with-NULL MOD
already resolved, but MIXED MOD did not.)

## 2. Type abstraction (R-refinements)

The carrier must be as OPEN as the real domain, because the real
`_resolve_combined_type` is driven with every `Field` subclass and every
connector string, and the scan matches by `issubclass` rather than by identity.
A closed 4×4 operand grid would make the subtype test extensionally
indistinguishable from exact matching plus one hard-coded alias, so the
integer-kind axis is modelled as an unbounded BAND of codes rather than as a
finite list.

| repo reality | model carrier | bijection |
|---|---|---|
| field class `IntegerField` (`fields/__init__.py:1953`) | `T_INT = 8` | type identity |
| every field class strictly BELOW `IntegerField` — `BigIntegerField` (:2049), `SmallIntegerField` (:2066), `PositiveBigIntegerField` (:2252), `PositiveIntegerField` (:2267), `PositiveSmallIntegerField` (:2282), `AutoField` (:2753), `BigAutoField` (:2761), `SmallAutoField` (:2769), `OrderWrt` (`fields/proxy.py:9`), and any further integer-derived class | the OPEN band `t >= T_INT_SUB` (`T_INT_SUB = 8+1 = 9`); `T_AUTO = 9` names one member | `is_int_kind(code(x)) ⇔ issubclass(x, IntegerField)`. The band is unbounded on purpose: the model must not claim the family is any particular finite set |
| field class `DecimalField` (:1591) | `T_DEC = 2` | type identity; no db-model class lies below it (the only `class X(DecimalField)` at this commit is `django/forms/fields.py:384`, a form field the registry never sees) |
| field class `FloatField` (:1911) | `T_FLT = 3` | type identity; likewise nothing db-model below it |
| field class `DurationField` (:1744) | `T_DUR = 4` | type identity |
| field class `TimeField` (:2406) | `T_TIME = 5` | type identity |
| field class `DateField` (:1318) | `T_DATE = 6` | type identity |
| field class `DateTimeField` (:1453), which extends `DateField` | `T_DTM = 7` | type identity; `is_date_kind(T_DTM)` ⇔ `issubclass(DateTimeField, DateField)` |
| `type(None)` — the type of a `Value(None)` operand, the registry's `NoneType` row type (`expressions.py:501`) | `T_NULL = 1` | type identity |
| every other field class (character, boolean, uuid, binary, …), i.e. every class below NO recorded operand type | the OPEN band `t <= T_UNREL_TOP` (`T_UNREL_TOP = -1`) | matches no recorded row, so resolution yields the sentinel. Also unbounded on purpose |
| `None` (no combination found) | `T_NONE = 0` | the unresolved sentinel `_resolve_combined_type` returns; not an operand type |
| connector strings `Combinable.ADD/SUB/MUL/DIV/MOD/POW` (`"+","-","*","/","%%","^"`, `expressions.py:43-51`) | `C_ADD=1 … C_MOD=5, C_POW=6` | connector identity (the string value is observationally just a dict key) |
| connector strings `Combinable.BITAND/BITOR/BITLEFTSHIFT/BITRIGHTSHIFT/BITXOR` (`expressions.py:56-60`) | `C_BITAND=7 … C_BITXOR=11` | connector identity |
| any connector string with no entry in `_connector_combinators` (`.get(connector, ())`, `expressions.py:622`) | every other connector code | resolution yields the sentinel |
| `issubclass(x, y)` for a recorded `y` | `is_subtype(code(x), code(y))` | the whole family below `IntegerField` matches a recorded `IntegerField`; `DateTimeField` matches a recorded `DateField`; otherwise identity (validated by G-AX) |
| `_connector_combinators[connector]` (a `list` of `(lhs, rhs, result)` tuples, fixed length) | the straight-line cascade of `row(...)` tests in registration order | the fixed-length iteration over the recorded rows is modeled as the same row tests in the same order; returning the first match ⇔ the loop's first `return combined_type` |

The precondition admits EVERY connector code and EVERY operand field-type code,
so no in-repo call site of `_resolve_combined_type` is modelled away: the
bitwise, exponentiation, numeric-with-NULL and date/duration row families are
all inside the modeled domain and all pinned by postconditions. (Note the
numeric-with-NULL dict is a comprehension with an inner `for field_type in
(IntegerField, DecimalField, FloatField)` at `expressions.py:566`, so the later
field types OVERWRITE the earlier ones per connector and only the `FloatField`
NULL rows survive — the model records exactly those two rows, as G-AX confirms
against the real registry.)

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

No `@ContractOnly` axiom is consumed by the proof. Two UNCHANGED primitives
underpin the deep model and are validated == the real callee out-of-band:

### 3.1 `is_subtype` deep model ↔ `issubclass` (A-reference)
**Callee:** Python builtin `issubclass`, applied to the Django field classes.
The scan in `_resolve_combined_type` (`expressions.py:625-627`) matches a query
operand type against a recorded type with `issubclass(query_type,
recorded_type)`. `is_subtype` encodes: the open family below `IntegerField`
matches a recorded `IntegerField`; `DateTimeField` matches a recorded
`DateField`; every other recorded operand type matches only itself.

**G-AX** does not assume that hierarchy — it DISCOVERS it. axiom_check.py walks
`Field.__subclasses__()` transitively (after importing the repo's own field
modules) and asserts that the set of classes below each recorded operand type is
exactly what the carrier claims: the integer family for `IntegerField` (at least
three members, all proper subclasses), `{DateTimeField}` for `DateField`, and
empty for `DecimalField`, `FloatField`, `DurationField` and `TimeField`. It then
asserts `is_subtype == issubclass` over every (discovered class, recorded class)
pair — 200 pairs at this commit, spanning all 9 members of the integer family.

### 3.2 registry cascade deep model ↔ `_connector_combinators` (A-reference)
**Callee:** Django's module-level registry `_connector_combinators`, populated at
import by flattening `_connector_combinations` via `register_combinable_fields`
(`expressions.py:503-618`), and the scan over it in `_resolve_combined_type`
(`expressions.py:621-628`). POST-PATCH the recorded rows the cascade spells out
are, per family:

```
numeric same-type (ADD/SUB/MUL/DIV/MOD/POW):
    (Integer, Integer)->Integer  (Float, Float)->Float  (Decimal, Decimal)->Decimal
numeric mixed-type (ADD/SUB/MUL/DIV/MOD — the remainder connector included):
    (Integer, Decimal)->Decimal  (Decimal, Integer)->Decimal
    (Integer, Float)->Float      (Float, Integer)->Float
numeric with NULL (ADD/SUB/MUL/DIV/MOD/POW):
    (Float, NoneType)->Float     (NoneType, Float)->Float
bitwise (BITAND/BITOR/BITLEFTSHIFT/BITRIGHTSHIFT/BITXOR):
    (Integer, Integer)->Integer
date/time under ADD:
    (Date, Duration)->DateTime   (DateTime, Duration)->DateTime
    (Duration, Date)->DateTime   (Duration, DateTime)->DateTime
    (Duration, Duration)->Duration
    (Time, Duration)->Time       (Duration, Time)->Time
date/time under SUB:
    (Date, Duration)->DateTime   (DateTime, Duration)->DateTime
    (Date, Date)->Duration       (Date, DateTime)->Duration
    (DateTime, Date)->Duration   (DateTime, DateTime)->Duration
    (Duration, Duration)->Duration
    (Time, Duration)->Time       (Time, Time)->Duration
```

(The mixed-type rows come from the dict at `expressions.py:523-537`, whose
connector tuple the gold patch extends with `Combinable.MOD`.) Because
resolution returns the first matching row, and the same-type rows precede the
mixed rows, an integer/integer query resolves to `Integer` before reaching the
mixed rows; a narrower integer operand matches the `Integer` rows via
`issubclass`, and a `DateTime` operand matches the `Date` rows likewise — which
is why the model's `(Date, Date)->Duration` row under SUB covers all four
date/date-time combinations.

**G-AX** asserts the deep cascade equals the real `_resolve_combined_type` over
every registered connector plus four unregistered connector codes × the whole
discovered field-class domain squared — 9375 observations at this commit — and
(boundary) that the remainder connector resolves mixed numeric operands to the
wider type for EVERY member of the integer family, and that a bitwise
combination of two narrower integer operands resolves to `Integer`. It also
checks containment: the real callee never returns a type outside the modeled
result set anywhere in that domain. axiom_check.py imports only the standard
library and the repo's own `django`; nothing external.

**Flag dependency:** none (no float-precision behavior; no `quote=`-style callee
flag). The resolution is over field *types*, class objects and string keys only.

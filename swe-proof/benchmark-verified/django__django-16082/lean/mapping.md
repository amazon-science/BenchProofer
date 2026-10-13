# mapping.md — symbol binding & type bijection (django__django-16082)

## Modeled function
- **Lean** `implementation_resolveCombinedType : ArithOp → FieldKind → FieldKind → Option FieldKind`
- **Python** `_resolve_combined_type(connector, lhs_type, rhs_type)` —
  `django/db/models/expressions.py:622-628 @ base_commit`.

```python
def _resolve_combined_type(connector, lhs_type, rhs_type):
    combinators = _connector_combinators.get(connector, ())
    for combinator_lhs_type, combinator_rhs_type, combined_type in combinators:
        if issubclass(lhs_type, combinator_lhs_type) and issubclass(
            rhs_type, combinator_rhs_type
        ):
            return combined_type
```

`_connector_combinators` is a `defaultdict(list)` populated at import time
(`expressions.py:600-619`) by iterating the `_connector_combinations` table
(`expressions.py:504-590`) and calling `register_combinable_fields`. For a given
connector it holds, **in registration order**, the `(lhs_type, rhs_type,
combined_type)` rows from every dict in `_connector_combinations` that mentions
that connector. `_resolve_combined_type` returns the `combined_type` of the first
row whose two slots both accept the operand types under `issubclass`, else
`None`.

### Where the fix lands
`_connector_combinations` has two relevant numeric dicts:
- **same-type** (`expressions.py:505-523`): rows `(Int,Int,Int)`,
  `(Float,Float,Float)`, `(Decimal,Decimal,Decimal)` for connectors
  `ADD, SUB, MUL, DIV, MOD, POW`. MOD is already present here at base_commit.
- **different-type** (`expressions.py:524-540`): rows `(Int,Decimal,Decimal)`,
  `(Decimal,Int,Decimal)`, `(Int,Float,Float)`, `(Float,Int,Float)` for
  connectors `ADD, SUB, MUL, DIV`. **The gold patch adds `MOD` to this tuple**
  (the `+ Combinable.MOD,` line at `expressions.py:537`).

Effect (verified empirically against the real repo, base vs patched):
| connector | (Int,Decimal) | (Decimal,Int) | (Int,Float) | (Float,Int) | (Int,Int) |
|---|---|---|---|---|---|
| MOD base    | None | None | None | None | Integer |
| MOD patched | Decimal | Decimal | Float | Float | Integer |

The same-type `(Int,Int)→Int` row already existed, so same-kind MOD was never
broken; the fix is purely about **mixed** numeric kinds promoting to the wider
kind. `POW` is NOT in the different-type tuple, so mixed-kind POW stays `None`
both before and after — modeled faithfully (`mixedKindOps` excludes `powOp`).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `connector` string (`Combinable.ADD='+'`, `SUB='-'`, `MUL='*'`, `DIV='/'`, `MOD='%%'`, `POW='^'`) | `op : ArithOp` (`add/sub/mul/div/modOp/powOp`) | the six core arithmetic connectors |
| operand field class `IntegerField` | `FieldKind.integerKind` | numeric integer kind |
| operand field class `FloatField` | `FieldKind.floatKind` | numeric float kind |
| operand field class `DecimalField` | `FieldKind.decimalKind` | numeric decimal kind |
| operand field class `AutoField` | `FieldKind.autoKind` | a subclass of `IntegerField` (`issubclass(AutoField, IntegerField) == True`); the only proper-subclass relation in the modeled numeric set |
| `_resolve_combined_type(...)` return: a field **class** or `None` | `Option FieldKind` | `some k` ↔ the class, `none` ↔ `None` (→ `FieldError` raised by the caller `_resolve_output_field`) |

### `issubclass` ↔ `kindMatches`
`_resolve_combined_type` accepts an operand of class `C` for a slot of class `S`
when `issubclass(C, S)`. Over the modeled numeric kinds the subclass lattice is
flat except `AutoField ⊂ IntegerField`. So:
- `issubclass(Auto, Integer) == True`, `issubclass(Auto, Auto) == True`,
  every other `issubclass(X, X) == True`;
- `issubclass(Float, Integer)`, `issubclass(Integer, Float)`,
  `issubclass(Decimal, Integer)`, etc. are all `False` (verified empirically).

`kindMatches operand slot` reproduces exactly this: `autoKind` matches `integerKind`
slot, and otherwise match iff equal. No slot in the registered numeric rows is of
`autoKind`, so the only place the subclass relation bites is an `AutoField`
operand against an `IntegerField` slot — which the number F2P test exercises
(`(AutoField, IntegerField, IntegerField)` rows).

## Callee provenance
- `_connector_combinators.get(connector, ())` — the registered rows. The data
  structure is unchanged; the gold patch only APPENDS the mixed-kind rows to the
  remainder operator's entry. Reproduced concretely as `combosFor op` (same-kind
  rows then mixed-kind rows, the registration order). G-AX validates this row
  model against the base repo **only for the parts the patch does not change**:
  the full row set for the unchanged operators, and the same-kind portion for the
  changed remainder operator — plus a check that the remainder operator has NO
  mixed-kind row yet at base (the bug is real). The added post-patch mixed-kind
  MOD rows are validated by **G-CONF** against the patched repo, never by G-AX
  against base (SPEC_GUIDE §0.7 — the changed op is not validated against the
  pre-change callee). I-tagged, not axiomatized.
- `issubclass` — Python builtin, UNCHANGED. Reproduced as the total decidable
  `kindMatches` over the finite numeric-kind lattice. Its agreement with the real
  `issubclass` over all modeled (operand, slot) pairs is validated executably by
  G-AX, so it is an A-reference (deep model), NOT a consumed axiom — and the proof
  needs no `_prop` axiom for it (`kindMatches` is concrete).
- The changed op (adding MOD to the mixed-kind operators) is modeled deeply via
  `mixedKindOps` / `combosFor`, NOT axiomatized.

## Scope note
`_connector_combinations` also contains bitwise rows and date/time rows. Those
connectors are not arithmetic-numeric and are untouched by the fix; they are out
of model scope (the modeled `ArithOp` is the six numeric operators). The
date/time and NULL rows do not change for any MOD case the F2P tests exercise.

### NULL F2P note
`test_resolve_output_field_with_null` is listed FAIL_TO_PASS but is behaviorally
UNCHANGED by the gold patch (verified: it passes at base_commit and post-patch —
none of its cases involve mixed-type MOD). It is effectively a pass-to-pass guard
that the harness happens to list as F2P. The single discriminating behavior is
`test_resolve_output_field_number` over MOD with mixed numeric kinds, which the
spec pins. No prepatch variant is needed for the NULL test (no independent fixed
behavior).

## G-CONF fuzz seed
Pinned seed: **16082**. ≥10^5 fuzzed inputs over the six operators × the four
numeric field kinds (Integer/Float/Decimal/Auto) for both operand slots.

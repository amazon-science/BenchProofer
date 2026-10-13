# refinement.md — django__django-16560

Maps every operation in the three `implementation_*` skeletons to its
`patch.diff` counterpart in the constraint classes
(`django/db/models/constraints.py`, with the identical threading mirrored in
`django/contrib/postgres/constraints.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** op left as the real repo
callee in G-CONF (not axiomatized), **I** identical concrete op.

## What the patch does
The patch adds one optional field, the violation error *code*, to the constraint
classes and threads it through construction (`__init__` of `BaseConstraint`,
`CheckConstraint`, `UniqueConstraint`, `ExclusionConstraint`) and then into three
observable behaviors. Construction itself is pure plumbing (store the value); the
observable contract is what the three triples pin:

1. the raised validation error now carries the code (`validate`);
2. equality now also compares the code (`__eq__`);
3. the reconstruction data (`deconstruct`) now surfaces the code when set.

The `__repr__` change (a presentation-only conditional segment appending
`violation_error_code=%r` when set) is the same conditional-inclusion logic as the
reconstruction-data leg, observed through a string format; it is NOT modeled
separately to avoid binding to Python's `%r` formatting. Its underlying decision
("surface the code iff set") is exactly `implementation_serializedCode`.

## Carrier refinement (applies to all three)
- `self.violation_error_code : str | None` ↔ `code : Option String`
  (`none ↔ None`, `some s ↔ s`). (R)
- The pre-existing comparison payload of a constraint (its name, defining
  data/check, and message — all compared unchanged before the patch) ↔
  `Constr.rest : String`, a single comparison key. Sound because the fix adds the
  code conjunct and changes nothing about how the prior parts compare. (R)
- Whether the constraint's own (unchanged) detection found a violation ↔
  `violated : Bool`. Abstracts `Q(self.check).check(...)` / `queryset.exists()`,
  which the fix does not touch. (R)

## `validate`  →  `implementation_validateError`
Post-patch (CheckConstraint.validate, and analogously in the other classes):
```python
if not Q(self.check).check(against, using=using):
    raise ValidationError(
        self.get_violation_error_message(), code=self.violation_error_code
    )
```
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if violated then return some code` | the detection fired ⇒ `raise ValidationError(msg, code=self.violation_error_code)` | R | `violated ↔` detection found a violation; raising ↔ `some _`; the carried code ↔ `code` (the FIXED token `code=...`) |
| 2 | `return none` | detection did not fire ⇒ no raise | I | no violation ⇒ nothing raised |

The message argument (`get_violation_error_message()`) is unchanged by the fix and
orthogonal to the code, so it is not modeled.

## `__eq__`  →  `implementation_constraintEq`
Post-patch (CheckConstraint.__eq__):
```python
return (self.name == other.name
        and self.check == other.check
        and self.violation_error_code == other.violation_error_code
        and self.violation_error_message == other.violation_error_message)
```
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `a.rest == b.rest` | the pre-existing conjuncts (name, check, message) | R | unchanged comparison payload collapsed to one key |
| 2 | `&& (a.code == b.code)` | `and self.violation_error_code == other.violation_error_code` | R | the FIXED token: `Option String` equality ↔ code equality (incl. `None==None`) |

## `deconstruct`  →  `implementation_serializedCode`
Post-patch (BaseConstraint.deconstruct):
```python
if self.violation_error_code is not None:
    kwargs["violation_error_code"] = self.violation_error_code
```
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `match code with \| some c => return some c \| none => return none` | `if self.violation_error_code is not None: kwargs[...] = self.violation_error_code` | R | the FIXED token: key present with the code value iff a code is configured; `some c ↔` key present (value `c`), `none ↔` key absent. Mirrors the existing message handling. |

## R/I legs ⇒ G-CONF
Every modeled op is **R** (carrier/type refinement) or trivially **I**. The three
FIXED tokens (the `code=` argument, the code conjunct, the conditional inclusion)
are the modeled change. `conf_skip = false`: the impl region is genuine R/I
content. `conformance_check.py` builds the three Python shadows and
differential-tests each against the REAL patched `CheckConstraint.validate` /
`__eq__` / `deconstruct` over ≥10^5 fuzzed inputs total, drawing codes from
`{None} ∪ {code strings}`, names/messages from small pools (so equal/unequal both
occur), and `violated ∈ {True, False}`.

## No A-consumed / A-reference row
No unchanged callee needs a property: each behavior is pure boolean/optional logic
plus the threaded code. The unchanged detection (`Q.check`, `queryset.exists()`)
and message handling are abstracted, not axiomatized. So `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## F2P alignment
- `test_validate_custom_error` (CheckConstraint): a violation must raise an error
  whose `.code` equals the configured code (`"fake_discount"`). Pre-patch the raised
  error carries no code → modeled prepatch `validateError` returns `some none`,
  violating the spec's `some code` clause. Fixed impl returns `some code`. ✓
- `test_eq` (CheckConstraint / UniqueConstraint): two constraints differing only in
  code must be unequal, and equal-code constraints equal. Pre-patch equality ignores
  the code → prepatch `constraintEq` returns `a.rest==b.rest`, satisfiable when codes
  differ, violating the `&& a.code==b.code` clause. ✓
- `test_deconstruction` (BaseConstraint): the reconstruction kwargs must contain the
  configured code. Pre-patch never includes it → prepatch `serializedCode` returns
  `none`, violating `result = code` for a configured code. ✓
- `test_custom_violation_code_message`, `test_repr_with_violation_error_code`: the
  code round-trips through construction and presentation — the same
  "surface the code iff set" decision as the reconstruction leg.

`patch.diff` is the gold patch verbatim; it resolves the harness (G-RESOLVE).

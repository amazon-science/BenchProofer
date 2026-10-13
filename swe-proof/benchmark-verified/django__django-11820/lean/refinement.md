# refinement.md — django__django-11820

Maps every op in `implementation_lookupPathValid` (Lean) to its `patch.diff`
counterpart in `Model._check_ordering`'s related-field traversal
(`django/db/models/base.py`). Tags: **R** (type refinement), **A-consumed**
(proof uses an axiom property), **A-reference** (deep model == real callee,
G-AX-checked), **I** (identical concrete op).

The modeled unit is the traversal of ONE lookup path
(`field.split(LOOKUP_SEP)`); the surrounding `for field in related_fields` loop
and the `errors.append(... E015 ...)` bookkeeping are I structure (one path
=> accept/reject = no-E015/E015-for-this-path).

| # | Lean impl op | patch.diff / base.py op | tag | note |
|---|---|---|---|---|
| 1 | `cur := some startModel` | `_cls = cls` | R | current model ↔ `Option Nat` index (mapping.md) |
| 2 | `fld := none` | `fld = None` | I | last-resolved-field accumulator |
| 3 | `invalid := false` | (no E015 appended yet) | I | per-path validity flag ↔ presence of an E015 for this path |
| 4 | `for part in parts` | `for part in field.split(LOOKUP_SEP)` | R | `parts:List String` ↔ split path (mapping.md) |
| 5 | `match cur with some c / none` | implicit: `_cls` is a model vs `None` | R | a `None` `_cls` makes `_cls._meta.get_field` raise `AttributeError` ⇒ except branch |
| 6 | `if part == "pk" then some (models c).primaryKey` | **gold**: `if part == 'pk': fld = _cls._meta.pk` | I | the pk-alias branch — the FIRST fixed behavior |
| 7 | `else (models c).getField part` | `else: fld = _cls._meta.get_field(part)` | A-reference | by-name field resolution; `none` ↔ `FieldDoesNotExist` (G-CONF binds to real `opts.get_field`) |
| 8 | `some f => fld := some f` | `fld = <resolved>` (assigned before the relation test) | I | record the resolved field |
| 9 | `if f.isRelation then cur := some f.target` | `if fld.is_relation: _cls = fld.get_path_info()[-1].to_opts.model` | A-reference | relation target ↔ `FieldInfo.target` (G-CONF binds to real `get_path_info`) |
| 10 | `else cur := none` | **gold**: `else: _cls = None` | I | non-relation ends the walk — the SECOND fixed behavior |
| 11 | `none =>` (resolution failed) → except branch | `except (FieldDoesNotExist, AttributeError):` | R | `getField`/pk returning `none` ↔ the caught exception |
| 12 | `match fld with some pf => if !(pf.acceptsTransform part) then invalid := true` | `if fld is None or fld.get_transform(part) is None: errors.append(E015)` | A-reference | `get_transform(part) is None` ↔ `!acceptsTransform part` (G-CONF binds to real `get_transform`/`register_lookup`) |
| 13 | `\| none => invalid := true` | `if fld is None ...: errors.append(E015)` | I | no field resolved yet ⇒ invalid |
| 14 | `return !invalid` | path acceptable ⇔ no E015 appended for it | R | `result:Bool` ↔ no-E015 |

## Axioms
No **A-consumed** axiom: the changed control flow (ops 6, 10 — the two fixed
behaviors) is modeled concretely (I), and graph operations (ops 7, 9, 12) are
**A-reference** data validated against the real callees by G-CONF, not consumed
as proof axioms. `axiom_check.py` is therefore a skip stub.

## conf_skip
`false` — the impl region has genuine R/I content (the per-segment resolution
control flow, the pk-alias branch, the non-relation termination). G-CONF
differential-tests the Python shadow of the walk against the REAL patched
`Model.check()`/`_check_ordering` E015 decision over ≥10⁵ fuzzed model graphs +
paths.

## No changed-inexpressible op
Every op above is R, A-reference, or I. The two gold-added behaviors (pk alias,
non-relation termination) are both modeled concretely.

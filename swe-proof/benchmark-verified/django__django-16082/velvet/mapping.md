# mapping.md — django__django-16082

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = bf47c719719d0e190a99fa2e7f959d5bbb7caf8a`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveModType (lhs rhs : NumKind)` | `_resolve_combined_type(connector, lhs_type, rhs_type)` — `django/db/models/expressions.py:622` — **specialized to `connector = Combinable.MOD`** | the modeled changed behaviour: the combined output type of a remainder expression over two numeric operand kinds |
| `combinedNumeric` / `lookup` / `modCombinators` (pure) | the registered combinator list for `Combinable.MOD` produced by `register_combinable_fields` from `_connector_combinations` (`expressions.py:504-588`), scanned first-match by `_resolve_combined_type` (`expressions.py:622-666`) | pure spec: the result-kind relation and its first-match search |
| `NumKind` (pure) | the numeric operand field classes `IntegerField` / `FloatField` / `DecimalField` (and their subclasses), `django/db/models/fields/__init__.py` | abstract numeric operand kind |

The change site itself: the `Combinable.MOD` entry added to the connector tuple
of the **"Numeric operations - operands of different type"** group
(`expressions.py:531-536`, gold hunk at `@@ -533`). Pre-patch that group lists
only `ADD, SUB, MUL, DIV`; the patch adds `MOD`, registering the mixed-kind rows
`(IntegerField, DecimalField → DecimalField)`, `(DecimalField, IntegerField →
DecimalField)`, `(IntegerField, FloatField → FloatField)`, `(FloatField,
IntegerField → FloatField)` for `MOD`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| operand `output_field` class | `NumKind` | any subclass of `IntegerField` (incl. `AutoField`, `BigIntegerField`, `SmallIntegerField`, `PositiveIntegerField`) ↔ `NumKind.int`; `FloatField` ↔ `NumKind.float`; `DecimalField` ↔ `NumKind.dec`. The resolver's `issubclass` test means every integer-family operand matches the canonical `IntegerField` combinator rows, so they collapse to one kind. |
| `_resolve_combined_type(...)` return | `Option NumKind` | a result field **class** `C` ↔ `some k` where `k` is the kind of `C` (`IntegerField↔int`, `FloatField↔float`, `DecimalField↔dec`); Python `None` (no rule matched → caller raises `FieldError`) ↔ Lean `none`. |
| the connector argument fixed to `Combinable.MOD` | (implicit) | `resolveModType` models the `MOD` slice only; the modeled operation is the per-connector combinator scan, instantiated at `MOD`. |

The modeled domain is the numeric slice (Integer/Float/Decimal families). The
date/duration/bitwise groups are outside the changed behaviour (the gold hunk
touches only the different-type **numeric** group) and outside the spec; G-CONF
fuzzes the numeric operand classes exhaustively (49 class pairs) plus randomized
draws to the budget.

## 3. Callee provenance

**None.** `resolveModType` calls no unchanged repository callee whose contract the
proof needs: the result-kind relation it computes is the operation under change
itself, modeled **deeply** as the pure `combinedNumeric` / `lookup` over
`modCombinators` (the first-match scan that `_resolve_combined_type` performs).
There is therefore **no `axiom`** and **no `axiom_check.py`** in this bundle
(G-AX skips). Crucially, the resolver under change is *not* axiomatized or
A-referenced — doing so would be unsound (directive 7: never axiomatize the
function under change), and would also fail an executable G-AX because the
real resolver only exhibits the widened mixed-kind behaviour *after* the patch.
Its agreement with the modeled relation is validated by **G-CONF**, which runs
the real resolver in its actual (gold-applied) configuration.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16082`** so the
consumer-side verdict is reproducible. The shadow transliterates
`combinedNumeric` (the R/I scan) to Python and bridges operand/result classes to
kinds via §2; the oracle is the real `_resolve_combined_type(Combinable.MOD, …)`
with the gold patch applied (`apply_gold=True`).

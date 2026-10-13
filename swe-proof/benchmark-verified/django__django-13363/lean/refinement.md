# refinement.md — operation correspondence (django__django-13363)

Maps every op in `implementation_truncDateCast` / `implementation_truncTimeCast`
to its `patch.diff` counterpart. Tags: **R** type refinement · **A-consumed**
proof uses axiom property · **A-reference** deep model validated == real callee
(G-AX) · **I** identical op.

The patch edits two methods identically: each replaces the inline expression
`timezone.get_current_timezone_name() if settings.USE_TZ else None` with
`self.get_tzname()` (the shared `TimezoneMixin.get_tzname`, UNCHANGED), then feeds
the resulting zone name into the per-flavour cast. We model the inner-fragment
compilation as the passthrough input `lhs`, the cast as the unchanged `opaque`
callee, and the changed zone selection deeply as `conversionZoneName`.

## `implementation_truncDateCast` ↔ `TruncDate.as_sql`

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `lhs : String` | `lhs, lhs_params = compiler.compile(self.lhs)` | R | str ↔ String bijection (mapping.md); compiled inner fragment passed through unchanged; `lhs_params` unaffected by the fix, out of scope |
| 2 | `let mut tzname := none; if useTz then (match requestedZone with none => some currentZone | some z => some z)` | `tzname = self.get_tzname()` = the `get_tzname` body: `None` unless `USE_TZ`, then requested zone if present else ambient | R | the **changed op** modeled deeply as `conversionZoneName`: requested zone takes precedence over ambient; only used under `USE_TZ`. NOT axiomatized. `requestedZone : Option String` models `self.tzinfo` by the name `_get_timezone_name` extracts (A-reference, below). `currentZone` models the ambient `get_current_timezone_name()` as a free input. |
| 3 | `castDate lhs tzname` | `connection.ops.datetime_cast_date_sql(lhs, tzname)` | I | identical concrete op: the UNCHANGED date-cast callee applied to the same fragment and the selected zone. `opaque castDate`; applied identically on spec and impl sides, so no axiom consumed |
| 4 | `return …` | returned `sql` (`return sql, lhs_params`) | I | returned `lhs_params` unaffected by the fix; out of model scope |

## `implementation_truncTimeCast` ↔ `TruncTime.as_sql`

Identical to the date case, with `castTime` ↔ `datetime_cast_time_sql`:

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `lhs : String` | `lhs, lhs_params = compiler.compile(self.lhs)` | R | as above |
| 2 | zone-selection block | `tzname = self.get_tzname()` | R | the changed op, modeled deeply (`conversionZoneName`); shared with the date case |
| 3 | `castTime lhs tzname` | `connection.ops.datetime_cast_time_sql(lhs, tzname)` | I | UNCHANGED time-cast callee, applied identically |
| 4 | `return …` | returned `sql` | I | `lhs_params` out of scope |

## Axiom accounting
- **A-consumed:** none. The proof discharges each spec (a single `castX`
  application) directly; the casts are applied identically on both sides and the
  zone selection is concrete. The `opaque castDate` / `castTime` declarations are
  signatures only — no `_prop` axiom is consumed (the proof closed with
  `#print axioms` reporting no axioms).
- **A-reference:** `timezone._get_timezone_name(self.tzinfo)`. We model
  `self.tzinfo` by the zone NAME it extracts, so the modeled extraction is the
  identity on `requestedZone.get`. G-AX (`axiom_check.py`) validates that the real
  `_get_timezone_name` returns exactly the zone name for the relevant zones (and
  that `get_current_timezone_name` is the ambient name), confirming the
  `Option String` ↔ tzinfo bijection.
- No changed-inexpressible op.

## Discriminating clause (the G-DIFF / F2P signal)
The fix matters exactly when `useTz = true` and `requestedZone = some z`:
post-patch the conversion zone is `z` (the caller's zone), pre-patch it is
`currentZone` (the ambient zone). The two prepatch impls drop `requestedZone` and
emit `castX lhs (some currentZone)`; the frozen `problem_spec` requires
`castX lhs (some (z.getD currentZone)) = castX lhs (some z)`, which differ as
soon as `z ≠ currentZone`. Hence each prepatch `correct_*` cannot close.
`Solution_prepatch.lean` isolates the `TruncDate` site (date F2P behavior);
`Solution_prepatch_2.lean` isolates the `TruncTime` site (time F2P behavior) —
one prepatch per independently-observable fixed behavior.

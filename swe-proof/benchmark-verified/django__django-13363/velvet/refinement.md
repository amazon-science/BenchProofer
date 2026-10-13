# refinement.md — django__django-13363

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `dateCastZoneName` / `timeCastZoneName` `do` blocks and the deep
`resolveZoneName` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `ensures`, **A-reference** where a deep model is validated
== the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The date-cast site — `TruncDate.as_sql` (`datetime.py:292`)

Gold hunk:
```
- tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None
+ tzname = self.get_tzname()
```

| # | Solution.lean impl op (`dateCastZoneName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `tzAware : Bool` | `settings.USE_TZ` read inside `self.get_tzname()` | R | `Bool ↔ settings.USE_TZ` (mapping.md §2). |
| A2 | parameter `explicitZone : Option String` | `self.tzinfo` (a zone object or `None`), observed via its rendered name | R | `tzinfo is None ↔ none`; supplied zone ↔ `some (_get_timezone_name tzinfo)` (mapping.md §2). |
| A3 | parameter `currentZone : String` | `timezone.get_current_timezone_name()` (the ambient zone name) | R | the active zone's rendered name ↔ the `currentZone` string (mapping.md §2). |
| A4 | result `out = resolveZoneName tzAware explicitZone currentZone`: `none` when not aware; the explicit name when supplied, else the ambient name | `tzname = self.get_tzname()`, threaded into `connection.ops.datetime_cast_date_sql(lhs, tzname)` | A-reference + I | the changed selection is modeled **deeply**: `resolveZoneName` (pure region) and the verified `if/match` ARE the selection `get_tzname` performs. The control-flow ops (`if tzAware`, the `match explicitZone`, the `return`s) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `get_tzname` is the **A-reference** G-AX validates. The unchanged downstream cast callee (`datetime_cast_date_sql`) is deterministic in `tzname` — mapping.md §3.2 — so pinning `tzname` pins the cast. |

Discriminating content of the change — when `tzAware` and `explicitZone = some
z`, the result is `some z` (the supplied zone) **not** `some currentZone` (the
ambient zone) — lives in the `| some z => return some z` leg (model) ⇔ the
`self.tzinfo is not None` branch of `get_tzname` (real). The pre-patch code used
`get_current_timezone_name()` unconditionally; `Solution_prepatch_date.lean`
reproduces that (`if tzAware then return some currentZone`) and **fails**
`out = resolveZoneName …` on exactly that clause (G-DIFF).

## B. The time-cast site — `TruncTime.as_sql` (`datetime.py:305`)

Gold hunk (identical shape):
```
- tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None
+ tzname = self.get_tzname()
```

| # | Solution.lean impl op (`timeCastZoneName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1–B4 | as A1–A4, for `timeCastZoneName` | the `TruncTime.as_sql` hunk; `tzname` threaded into `datetime_cast_time_sql(lhs, tzname)` | R / A-reference + I | identical to site A; `timeCastZoneName` and `dateCastZoneName` share the same spec `resolveZoneName`. The two sites are **independently observable** (date vs time cast on different backends/columns), hence two prepatches. |

`Solution_prepatch_time.lean` reproduces the pre-patch buggy time-cast selection
and **fails** on the same discriminating clause (G-DIFF); its date method stays
gold-faithful, so it isolates the time-site fix.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — replacing
the inline `get_current_timezone_name()`-or-`None` selection with the
`tzinfo`-honouring `get_tzname()` selection — is modeled **deeply** (the
spelled-out `resolveZoneName`, an A-reference + I), not hidden behind an axiom
about the function under change. There are **no consumed axioms** in this bundle.
The only kind-A object, `resolveZoneName`, is an A-reference: a deep model of the
**unchanged** callee `get_tzname`, validated == the real callee by G-AX. No dead
axiom is shipped.

## D. verify(Solution) ⇒ resolved

`dateCastZoneName`/`timeCastZoneName` verify only if their output equals the
exact zone-name selection — `some z` (the explicit zone) when one is supplied and
aware (A4 / B4), `some currentZone` when none, `none` when not aware. By R
(`Bool ↔ USE_TZ`, name `str ↔ String`, `tzinfo ↔ Option String`) the verified
selection equals the `tzname` the patched `as_sql` computes; by G-AX the deep
model `resolveZoneName` equals the real `get_tzname` (A-reference); by G-CONF the
R/I transliteration of the selection agrees with the `tzname` the real patched
`as_sql` threads into the cast callee on ≥10⁵ inputs. Since the downstream cast
callee is unchanged and deterministic in `tzname`, a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
deep-model reference — and the gold patch resolves (G-RESOLVE). The F2P test
(`test_trunc_timezone_applied_before_truncation`) asserts the date/time aggregate
honours the passed `tzinfo` (`melb`/`pacific`) — exactly the `some z` clause the
prepatches fail on. Trust points are the two of plan §1.1: deep-model soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).

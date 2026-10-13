# refinement.md — django__django-14792

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_timezone_name` impl region + the `present_and_nonempty` pure
predicate) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model /
observation is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The name-resolution helper — `_get_timezone_name()` (`django/utils/timezone.py:74-76`)

Gold hunk:
```
 def _get_timezone_name(timezone):
-    """Return the name of ``timezone``."""
-    return str(timezone)
+    """..."""
+    return timezone.tzname(None) or str(timezone)
```

The body changes from "always return the full textual rendering" to "return the
short per-instant label when it is present and non-empty, otherwise the full
rendering". The operation introduced is the `or` short-circuit *selection*
between two unchanged textual observations of the tzinfo object.

| # | model.py impl op (`resolve_timezone_name`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `tz: TimeZone` | the `timezone` argument (a `datetime.tzinfo`) | R | the tzinfo object modelled as a minimal class carrying only the two touched observations (mapping.md §1, §2). |
| A2 | `label = tz.short_label` (`Optional[PSeq[int]]`) | `timezone.tzname(None)` | A-reference | the unchanged short-label query, modelled as the carried field. Content is opaque; the field IS the observation. `Optional[str]` ↔ `Optional[PSeq[int]]` (`None` ↔ absent, `''` ↔ empty seq). Validated == the real `tzname(None)` by G-AX (mapping.md §3.1). |
| A3 | `if label is not None and len(label) > 0:` (= `present_and_nonempty(label)`) | the Python truthiness test inside `... or ...` | R + I | `bool(s)` of an `Optional[str]` is `False` iff `s is None or s == ''`; the guard is its exact negation. The short-circuit `x or y` returns `x` when `bool(x)` else `y` — modelled as the `if/return label else return full_name` branch (identical control flow). |
| A4 | `return label` (the present, non-empty short label) | the left operand of `or` is returned when truthy | A-reference + I | returns exactly the carried short-label observation; tied structurally to the input (mapping.md §3.1). The FIX: the pre-patch helper never returned this branch. |
| A5 | `return tz.full_name` | `str(timezone)` (the right operand of `or`) | A-reference + I | the unchanged full-rendering query, modelled as the carried field; returned exactly when the short label is absent/empty (mapping.md §3.2). Identical to the pre-patch body, now the fallback. |

The discriminating content of the change — for a fixed-offset zone whose short
label `"+10"` differs from its full rendering `"Etc/GMT-10"`, the resolved name
is `"+10"` (not `"Etc/GMT-10"`) — lives in step **A4** (model returns
`tz.short_label` when `present_and_nonempty`) ⇔ the left operand of the new `or`
(real). The pre-patch helper returned `str(timezone)` unconditionally;
`model_prepatch.py` reproduces that (`return tz.full_name`) and **fails** the
postcondition `Implies(present_and_nonempty(tz.short_label), Result() ==
tz.short_label)`, which is exactly the spec sensing the change (G-DIFF).

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it drops the short-label branch
(steps A2–A4) and unconditionally `return tz.full_name`, exactly as the pre-patch
body was `return str(timezone)`. With the byte-identical frozen spec it **fails**
verification on the postcondition
`Implies(present_and_nonempty(tz.short_label), Result() == tz.short_label)`
(`model_prepatch.py:71` — "Postcondition might not hold"). That is precisely the
behaviour the F2P test observes: `test_get_timezone_name` asserts
`timezone._get_timezone_name(pytz.timezone('Etc/GMT-10')) == '+10'` (and the
`zoneinfo` analogue), which the pre-patch `str(timezone)` (= `'Etc/GMT-10'`)
violates. The spec is therefore strong enough that no implementation ignoring a
present, non-empty short label can verify.

The companion clause
`Implies(not present_and_nonempty(tz.short_label), Result() == tz.full_name)`
pins the fallback exactly to the full rendering when the short label is absent or
empty — keeping the spec faithful to the post-patch `or` on the `None`/`''` side
(the F2P named-zone cases: `zoneinfo.ZoneInfo('Europe/Madrid')` has
`tzname(None) is None`, so the result must be the full `'Europe/Madrid'`).
Together the two clauses force `Result()` to be exactly one of the two carried
observations, selected by present-and-non-empty — so a wrong impl cannot satisfy
the spec by fabricating a name or by always picking the wrong branch. Read-only
fractional permission on both fields (Required AND Ensured at `1/2`) blocks the
overwrite-the-input vacuity (directive 5).

The precondition additionally carries `Requires(MustTerminate(1))` — a
total-correctness obligation. The real operation is a bounded, straight-line
selection between two already-computed observations; a diverging implementation
(e.g. `while True: pass`) would satisfy both value postconditions only
vacuously under partial correctness while hanging every caller (and the F2P
test) forever. With the obligation, Nagini's obligation-leak check rejects any
non-terminating body, closing the divergence vacuity: only implementations that
actually RETURN one of the two observations verify.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the `tzname(None) or str(timezone)` *selection* — is modelled
**deeply** (`resolve_timezone_name`'s `if present_and_nonempty: return label else
return full_name`, with the truthiness predicate `present_and_nonempty`), not
hidden behind an axiom about the function under change. The two operands
(`tzname(None)`, `str(timezone)`) are **unchanged** object queries with opaque
content, modelled as the two carried fields and validated == the real callees by
G-AX (**A-reference**, mapping.md §3). There is **no consumed `@ContractOnly`
axiom** — the proof depends on no axiom's `Ensures`; the result is grounded
structurally in the two input fields. We never axiomatize the function under
change.

## D. verify(model) ⇒ resolved

`resolve_timezone_name` verifies only if it returns the short label exactly when
that label is present and non-empty (A4) and the full rendering otherwise (A5).
By R (the tzinfo object and its two textual observations ↔ `TimeZone.short_label`
/`full_name`; `Optional[str]` ↔ `Optional[PSeq[int]]`; `str` ↔ `PSeq[int]`; the
truthiness of an `Optional[str]` ↔ `present_and_nonempty`) and the identical
short-circuit control flow (A3), the verified body equals the gold
`timezone.tzname(None) or str(timezone)` on the tested inputs. By G-AX the deep
selection model equals the real expression over the F2P zones (datetime.timezone
/ pytz / zoneinfo) plus boundary + 5000 fuzz cases (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited observations — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: observation
soundness (G-AX) and refinement fidelity (this document, G-EQ); there is no
consumed axiom to trust.

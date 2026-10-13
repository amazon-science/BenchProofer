# refinement.md — django__django-10999

The operation-by-operation correspondence between `model.py`'s implementation
(`parse_clock_seconds`, the deep `clock_value` / `signed_total` / `pow60` spec,
and the validity rule) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-reference** (a deep model validated == the real
callee by axiom_check.py / G-AX — there are no **A-consumed** axioms here), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `standard_duration_re` driving `parse_duration`

Gold hunk (`django/utils/dateparse.py:29`):
```
-    r'((?:(?P<hours>-?\d+):)(?=\d+:\d+))?'
-    r'(?:(?P<minutes>-?\d+):)?'
-    r'(?P<seconds>-?\d+)'
+    r'(?P<sign>-?)'
+    r'((?:(?P<hours>\d+):)(?=\d+:\d+))?'
+    r'(?:(?P<minutes>\d+):)?'
+    r'(?P<seconds>\d+)'
```
The downstream `parse_duration` already reads `sign = -1 if kw.pop('sign','+')
== '-' else 1` and returns `days + sign * datetime.timedelta(**kw)`
(`dateparse.py:139,146`) — so promoting the per-field signs to a single leading
`(?P<sign>-?)` makes the leading minus negate the whole clock value and makes a
minus after a separator a non-match.

| # | model.py impl op (`parse_clock_seconds`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `fields: List[int]` (1..3 non-negative magnitudes) | the `(?P<hours>\d+)`/`(?P<minutes>\d+)`/`(?P<seconds>\d+)` named groups, each read via `float(v)`/`int(v)` | R | `str` → already-extracted non-negative `int` field magnitudes; the digit-run extraction `\d+` is unchanged by the patch (mapping.md §2). |
| A2 | parameter `leading_minus: bool` | the post-patch leading `(?P<sign>-?)` group capturing `'-'`, consumed as `sign = -1 if kw.pop('sign','+')=='-' else 1` | R | a captured `'-'` ↔ `leading_minus is True`; absent ↔ `False` (mapping.md §2). |
| A3 | parameter `inner_sign_seen: bool` | the post-patch fields being `\d+` (no per-field sign): a sign after a `:` cannot be consumed, so the literal does not match | R | a sign character after a separator ↔ `inner_sign_seen is True`; the regex non-match ↔ the absent value (mapping.md §2). |
| A4 | the loop building `total = Σ fields[k] * 60**(pos)` and the result `signed_total(ToSeq(fields), leading_minus)` (negate the whole when `leading_minus`); `None` when `inner_sign_seen` | `sign * datetime.timedelta(hours=H, minutes=M, seconds=S)` (with the post-patch single sign), and no match → `None` | A-reference | the changed interpretation is modeled **deeply**: `clock_value` is the positional base-60 combination the `timedelta(**kw)` performs, and `signed_total` is the whole-value `sign *` multiply. There is **no consumed axiom** for `parse_duration`/`timedelta`. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real post-patch `standard_duration_re` + `parse_duration` sign logic on boundary + 50 000 fuzz literals and asserts the real total seconds == `signed_total` and every inner-sign literal is a non-match (mapping.md §3.1). |
| A5 | result returned as a signed `int` of total seconds, `None` for no match | the produced `datetime.timedelta`, or `None` | R | two no-microsecond `timedelta`s are equal iff their integer total seconds are equal; the modeled literals carry no fractional part, so the comparison the tests make (`timedelta` equality) is exactly integer-total-seconds equality (mapping.md §2). |

## B. The two discriminating behaviours and their prepatches

The change fixes two independently-observable behaviours; `model.py` pins both,
and there is one verification-failing `model_prepatch_<k>` per behaviour, each
keeping the spec byte-identical (G-DIFF's `same_spec`).

1. **Whole-value sign distribution** (the leading minus negates the WHOLE
   clock value, not just the first field). Pinned by
   `Ensures(... Result() == signed_total(ToSeq(fields), leading_minus))`.
   `model_prepatch.py` reproduces the pre-patch skeleton — the minus reaches
   only the leading field's contribution (`total - 2*lead_contrib`) — and
   **fails** that postcondition (e.g. `-15:30`: model `-930` vs pre-patch
   `-870`). This is exactly the spec sensing the change.

2. **Inner-sign rejection** (a sign after a separator → no match). Pinned by
   `Ensures(Implies(inner_sign_seen, Result() is None))`. `model_prepatch_2.py`
   reproduces the pre-patch skeleton — per-field signs were allowed, so an
   inner-sign literal still produced a value (it does not short-circuit to
   `None`) — and **fails** that postcondition (e.g. `-01:-01`: model `None` vs
   pre-patch a value). This is the spec sensing the second change.

The third symptom in the issue — that the pre-patch `(?=\d+:\d+)` lookahead
rejected the leading-minus three-field form `-00:01:01` entirely — is the same
fix as (1): with the single leading sign the three-field negative form is a
valid literal and yields `signed_total` (G-AX confirms `-00:01:01 → -61`),
covered by behaviour (1)'s postcondition and prepatch.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely
*changed* — the sign distribution and the validity rule of the clock literal —
is modeled **deeply** (`clock_value` / `signed_total` / the
`inner_sign_seen ⇒ None` rule, an **A-reference** validated by G-AX), not
hidden behind an axiom about the function under change. There is **no consumed
`@ContractOnly` axiom** in this bundle: the digit-run extraction (`\d+`) is an
unchanged R-boundary (the model takes the already-extracted magnitudes), and
the `timedelta` arithmetic is spelled out as the base-60 `clock_value`.

## D. verify(model) ⇒ resolved

`parse_clock_seconds` verifies only if its result is the positional clock total
with the single leading sign applied to the whole value (A4) and `None` exactly
on inner-sign literals (A3). By R (field magnitudes ↔ `\d+` groups,
`leading_minus` ↔ the `(?P<sign>-?)` group, integer total seconds ↔ `timedelta`
equality) the verified interpretation equals the post-patch
`sign * datetime.timedelta(**kw)` on the tested literals; by G-AX the deep model
`signed_total`/`clock_value` equals the real post-patch pipeline (A-reference).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
trust point is exactly one of PLAN §1.1: refinement fidelity (this document,
G-EQ), with the A-reference soundness carried by G-AX; there is no axiom-
soundness trust point because no axiom is consumed.

# refinement.md — django__django-10999

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `parseDurationSeconds` `do` block, plus the deep `step`/`decode`/
`parseDuration` model it folds) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses an axiom's `ensures`, **A-reference** where a deep model of an
UNCHANGED callee is validated == the real callee by G-AX), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. This bundle has **no A-tagged
ops** (see §B): the only non-trivial operation is the function under change
itself, modeled deeply and concretely (I), so its fidelity to the patched
callee is a **G-CONF** obligation — not a G-AX axiom about an unchanged callee.
Claim: any impl verifying against this frozen spec, refined per the
map below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The single change site — `standard_duration_re` (`django/utils/dateparse.py:29-38`)

Gold hunk (the entire change):
```
-    r'((?:(?P<hours>-?\d+):)(?=\d+:\d+))?'
-    r'(?:(?P<minutes>-?\d+):)?'
-    r'(?P<seconds>-?\d+)'
+    r'(?P<sign>-?)'
+    r'((?:(?P<hours>\d+):)(?=\d+:\d+))?'
+    r'(?:(?P<minutes>\d+):)?'
+    r'(?P<seconds>\d+)'
```
The body of `parse_duration` (`dateparse.py:124-149`) is **unchanged**: it
already reads a `sign` group and computes `days + sign * timedelta(...)`. The
patch moves the optional `-` out of each component and captures it **once** at
the front as `(?P<sign>-?)`, so a single leading sign scales the whole
magnitude rather than attaching to individual components.

| # | Solution.lean impl op (`parseDurationSeconds`) | patch.diff behaviour | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text : List Char` | `value: str` arg of `parse_duration` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `require text ≠ []` and `require ∀ c ∈ text, isDigit c ∨ c = ':' ∨ c = '-'` | the empty `str` (falls to the postgres branch → `timedelta(0)`) and any string outside the `{0-9,:,-}` alphabet (days-word / fractional formats, handled by the **unchanged** `days`/`microseconds` groups) are excluded | R | honest, machine-checked domain restriction stated in the spec view (mapping.md §2); all discriminating F2P inputs are non-empty `{0-9,:,-}` strings. |
| A3 | `st := step st text[i]!` folded over `i = 0 … length` (the `while` loop), `invariant st = (text.take i).foldl step initPS` | the post-patch named-group assignment of `standard_duration_re`: one leading `-` → `sign`; non-empty colon-separated digit groups (≤3) folded base-sixty | I | the changed match op is modeled **DEEPLY and CONCRETELY** — `step`/`decode`/`parseDuration` (pure region) ARE the semantics, transliterated 1:1 to Python and refuted against the patched `parse_duration` by **G-CONF**. This is the function *under change*, so it is NOT a consumed axiom and NOT an A-reference (G-AX axiomatizes only *unchanged* callees). mapping.md §3.1. |
| A4 | `return decode st`: `none` for ill-formed; else `some (sign * (acc*60 + cur))` | `parse_duration` returns `None` for no-match; else `days + sign * timedelta(...)`, here `sign * timedelta(seconds=…)` | I | the sign multiplies the **entire** magnitude (`sign * timedelta(...)`), exactly `decode`'s `sign * (acc*60+cur)`. The `Option Int` (seconds) ↔ `timedelta` bridge is mapping.md §2; `decode` is **I**, concrete, refuted against the real post-patch assembly by **G-CONF**. |

Discriminating content of the change — a single leading `-` scales the WHOLE
magnitude (every group), not just the leading component — lives in `decode`'s
`sign * (acc*60 + cur)` (the sign is applied once, after the base-sixty fold of
all groups) and in `step`'s rule that a `-` is a sign **only** in first position
(`seen` guard) and invalid elsewhere (matching that the patched component
patterns no longer contain `-?`). `Solution_prepatch.lean` reproduces the
pre-patch behaviour — sign folded into the first group only, reset at each
separator (`acc := acc*60 + sign*cur; sign := 1`) — and **fails**
`out = parseDuration text` (G-DIFF) precisely on the rows `-15:30`, `-1:15:30`,
`-00:01:01`, `-01:01` (sign must scale later groups too) and `-01:-01` (an
inner `-` must be rejected, not accepted).

## B. No additional change sites; no axioms (A-consumed or A-reference)

The patch touches a single module-level pattern. `parse_duration`'s body, and
the other two patterns (`iso8601_duration_re`, `postgres_interval_re`), are
unchanged and never match a `{0-9,:,-}`-alphabet string (verified exhaustively
by G-CONF), so the deep model equals the full `parse_duration` on the modeled
domain. `re.compile`/`re.match`/`datetime.timedelta` are CPython and are
exercised concretely by G-CONF — there is **no consumed axiom** in this bundle.

There is also **no A-reference**, and therefore **no `axiom_check.py`** (G-AX
skips). G-AX axiomatizes the contract of a callee the changed function *calls
but does not change*, run against the repo at `base_commit` (the callee is the
same before and after the patch). Here the only non-trivial operation IS the
changed regex/assembly — the function under spec. Modeling it is a *refinement*
obligation, not a callee-axiom one: its fidelity to the **post-patch** callee is
checked by **G-CONF**, which applies `patch.diff` before comparing (gates.py
`apply_gold=True`). Axiomatizing the function-under-change against the
*unpatched* callee would be testing the fix against the bug — guaranteed to
disagree, and forbidden by SPEC_GUIDE §0 directive 7 ("NEVER axiomatize the
function under spec or the operation the patch changes").

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* —
the regex's sign/group assignment and the consequent whole-magnitude sign —
is modeled **deeply and concretely** (the spelled-out scan
`step`/`decode`/`parseDuration`, step A3/A4, tagged **I**), not hidden behind an
axiom about the function under change. There is no consumed `parseDuration`
axiom and no A-reference.

## D. verify(Solution) ⇒ resolved

`parseDurationSeconds` verifies only if its output equals `parseDuration text`
(the `ensures`), i.e. the exact left-to-right scan with a single leading sign
scaling the whole base-sixty magnitude (A3/A4). By R (`str ↔ List Char`,
seconds ↔ `timedelta`) the verified scan equals the post-patch
`parse_duration` on the modeled `{0-9,:,-}` inputs; by **G-CONF** the I
transliteration of the fold (`step`/`decode`/`parseDuration`) agrees with
`patch.diff`'s behaviour — the **patched** `parse_duration` — on the exhaustive
`{0-9,:,-}` domain (length ≤ 5) + ≥10⁵ fuzz inputs, 0 disagreements. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The trust point is
the single one of plan §1.1 that applies: refinement fidelity (this doc,
G-EQ + G-CONF). There is no callee-axiom trust point (no A-tagged op), so G-AX
skips.

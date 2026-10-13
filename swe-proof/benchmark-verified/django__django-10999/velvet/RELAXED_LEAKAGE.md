# RELAXED_LEAKAGE — django__django-10999 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

## The mismatch (problem_statement ↔ gold)

The gold patch (`django/utils/dateparse.py`, `standard_duration_re`) moves
the optional `-` out of every component pattern and captures it ONCE at the
front (`(?P<sign>-?)`); `parse_duration` multiplies the **whole** magnitude
by that sign (`days + sign * timedelta(...)`). Its discriminating behavioral
content is therefore:

- **(a) a single leading `-` negates the ENTIRE value** — `-15:30` → −930 s
  (= −(15·60+30)), `-00:01:01` → −61 s; and
- **(b) a `-` anywhere after the first character is INVALID** — `-01:-01` →
  `None` (pre-patch it matched, minutes=−1).

Neither (a) nor (b) is derivable from the public `problem_statement`. The PS
says only that the regex "doesn't match negative durations" and then
PROPOSES A SPECIFIC FIX — `r'((?:(?P<hours>-?\d+):)(?=-?\d+:-?\d+))?'` —
which KEEPS the per-component `-?`: under the PS's own fix, `-15:30` parses
as minutes=−15, seconds=+30 (→ −870, sign scales the first group only) and
`-01:-01` is ACCEPTED (→ −61 via per-component signs). That is the OPPOSITE
of the gold/F2P behavior on both facets. The actual design decision lives
ONLY in `hints_text` (maintainer comments: "I'd expect a leading minus sign
to negate the entire value ... minus 61 seconds"; "I don't think a minus
sign after a colon is valid"). Token scan of the problem_statement for
{entire, whole, magnitude, "negate the", "leading minus", "after a colon",
" 61", invalid, "overall sign"}: 0 hits (re-confirmed by the P2 audit,
verdict.md).

## The leak (what the spec view discloses beyond the PS)

The spec-view `pure`-region code and docstrings necessarily encode exactly
facets (a)+(b):

- `decode`: `some (st.sign * (st.acc * 60 + st.cur))` and its docstring "The
  overall sign multiplies the entire magnitude (every group), so the result
  of e.g. a two-group "a:b" with a leading minus is -(a*60 + b)."
- `step`: the `seen` guard (a `-` after any consumed character sets
  `valid := false`) and its docstring "A '-' is meaningful only as the very
  first character ... encountered anywhere else it makes the input
  ill-formed."
- `PS.sign` field comment: "the magnitude's overall sign (1, or -1 once a
  leading '-' is read)".

The leak is SEMANTIC (the model's behavior IS the discriminator); it is not
a lexical repo-symbol or diff-line echo — the mechanical G-LEAK screen
passes ("spec view clean"), and no gold token (`(?P<sign>-?)`,
`standard_duration_re` beyond what the PS itself quotes, `sign` as a regex
group name) appears in a leaking form (audit sub-review 3, verdict.md).

## Why the leak is unavoidable (faithful ⟹ leaking)

The frozen postcondition must pin the gold's F2P behavior: `-15:30` → −930,
`-1:15:30` → −4530, `-00:01:01` → −61, `-01:01` → −61, `-01:-01` → None
(all in-domain, all verified against the real post-gold `parse_duration`
in-container: bundled G-CONF 371,469 inputs, 0 disagreements; independent
audit differential 3,257,436 exhaustive `{0-9,:,-}` inputs, 0
disagreements). Any spec weak enough to HIDE the whole-magnitude sign and
the inner-minus rejection would admit the PS-faithful per-component
implementation — exactly `Solution_prepatch.lean`'s skeleton
(`acc := acc*60 + sign*cur; sign := 1`), which G-DIFF requires to FAIL and
which fails the hidden F2P tests. So a spec faithful to the gold MUST encode
the hints-only decision; PS-only + faithful is impossible (the PS's own
proposed fix contradicts the gold). This is a proven PS ↔ gold mismatch, not
lazy de-narration: the leak survives full de-narration because it lives in
`decode`'s executable arithmetic, not in prose.

## Core soundness (relaxation criteria 1–2, re-verified by the P2 audit)

- G-VERIFY: `Solution.lean` verifies (exit 0, no sorry).
- G-DIFF: `Solution_prepatch.lean` (the PS-style per-component sign) fails
  `prove_correct` on the discriminating `invariant_2` goal — the spec
  discriminates exactly the gold's bug-fix.
- G-CONF: 0 disagreements vs the real post-patch `parse_duration` over the
  exhaustive modeled domain (see above).
- G-RESOLVE: resolved.
- G-EQ / G-PANEL-1: SOUND + TIGHT (8 attacks re-run, none breaks the spec;
  positive control verifies).

Criteria 1 (core sound) and 2 (leak genuinely unavoidable) hold; this file +
the `relaxed_leakage` meta flag supply criterion 3 (in-bundle
documentation), which the original bundle omitted (audit defect D1).

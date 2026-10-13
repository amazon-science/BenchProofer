# RELAXED_LEAKAGE — matplotlib__matplotlib-21568 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`, via
the `relaxed_leakage` meta flag + this file). The same instance is already
dispositioned identically — and committed green — in the sibling `nagini/`
bundle (`nagini/RELAXED_LEAKAGE.md`, project decision 2026-06-14). (An earlier
revision of this file cited `RELAXED_LEAKAGE.md`, a source-repo-only doc
that does not exist here — see `prompts/README.md` on dangling source-repo
refs.)

## The mismatch

**Public `problem_statement`** ("[Bug]: Datetime axis with usetex is unclear"):
a pure SYMPTOM report. "The spacing for a datetime axis when using
`usetex=True` is unclear in matplotlib version 3.4 when comparing it to 3.3 …
The ideal case would be to have the spacing from version 3.3 in a tex format."
Plus two screenshots and environment boilerplate.

**Gold fix** (`lib/matplotlib/dates.py`, `_wrap_in_tex`): protect three math
code points so the TeX math renderer does not space/format them wrongly —
`'-' → '{-}'`, `':' → '{:}'`, `' ' → r'\;'` (was: only the dash protected).

The F2P tests pin exactly these three protections inside the wrapped output:
`$\mathdefault{1990{-}01{-}%02d}$`, `$\mathdefault{01{-}01\;%02d}$`,
`$\mathdefault{01\;00{:}%02d}$`, `$\mathdefault{04{:}00}$`, etc.

## Token scan of `problem_statement` (case-insensitive)

`_wrap_in_tex` 0 · `wrap` 0 · `replace` 0 · `mathdefault` 0 · `{-}` 0 ·
`{:}` 0 · `\;` 0 · `re.sub` 0 · `colon` 0 · `':'` 0 · `dash` 0 · `space` 0
(as a token) · `brace` 0 · `operator` 0.

The discriminating vocabulary — the three protected characters, the `{-}`/`{:}`/
`\;` tokens, the `$\mathdefault{…}$` wrapper, the patched symbol
`_wrap_in_tex`, and the chained-substitution mechanism — appears ONLY in
`hints_text` (the monkey-patch snippet) and the gold/`test_patch`. The public
issue names only the abstract symptom "spacing / usetex unclear".

## Why faithful + non-leaking is impossible

- A **non-leaking** spec (judged against `problem_statement` only) could pin at
  most "the label is rendered for a TeX math context" — it cannot constrain
  WHICH code points are protected, HOW, or what the delimiters are, because the
  public text supplies no such information. Any impl that returns the input
  unchanged (or protects only the dash, the pre-patch behaviour) would satisfy
  such a weak spec yet fail every F2P test.
- A **faithful** spec (one the prepatch fails and no wrong impl verifies — the
  `verify ⟹ correct` core) MUST state the per-code-point protection
  `: → {:}`, ' ' → `\;` (and `- → {-}`) and the exact delimiter literals,
  because that — and only that — is what the F2P tests observe (they compare
  the full wrapped strings). Stating it necessarily surfaces the
  `{:}`/`\;`/`{-}`/`$\mathdefault{…}$` tokens, which are not public.

Therefore the leak is in the **behaviour itself**, not removable by
de-narration. This bundle keeps the faithful spec and accepts the leak.

Note: the spec view still avoids the patched path/symbol names (`_wrap_in_tex`,
`dates.py`) and never narrates the edit — model identifiers (`mathProtect`,
`protectSeq`, `reSub`, `removeEmpty`) and their comments describe behavior,
not the diff. Only the unavoidable token/output vocabulary above is present,
and that is the tested behavior.

## Core soundness (unaffected by the relaxation)

- **G-VERIFY**: `Solution.lean` verifies (total-correctness semantics,
  `decreasing i` loop measure).
- **G-DIFF**: `Solution_prepatch.lean` (protects only `-`) FAILS, on exactly the
  `:`/` ` discriminating clause of `out = … protectSeq (reSub text) …`.
- **G-AX**: `protectSeq` deep model == the real chained per-code-point
  substitution over 23 boundary + 20 000 fuzz inputs; the two context callees
  (letter-run pre-processor / empty-group removal) are unchanged and
  uninterpreted.
- **G-CONF**: R/I shadow == patched behaviour over ≥10⁵ inputs (0 disagreements,
  seed 21568).
- **G-EQ / G-PANEL-1 / G-PANEL-2** (2026-08-05 audit): 7 attacks re-run, none
  breaks the spec; positive control verifies; faithfulness attack found 0
  divergences over 700k+ fuzz inputs.
- **G-RESOLVE**: `patch.diff` == gold verbatim; harness resolves.

Only the secondary no-leakage property is relaxed. The `verify ⟹ resolved`
guarantee is intact.

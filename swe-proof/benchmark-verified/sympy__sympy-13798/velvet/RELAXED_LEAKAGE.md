# Relaxed-leakage acceptance — sympy__sympy-13798 (velvet)

**Disposition: KEEP (relaxed leakage)** — the mechanical G-LEAK screen is clean
(the leak is semantic, not lexical); the residual is a *semantic* leak accepted
under the project relaxed-leakage policy. The policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed"); the G-LEAK gate honors it mechanically via the
`relaxed_leakage: true` meta flag plus this file
(`src/swebench_unified/gates/leak.py`).

## The instance

`LatexPrinter.__init__` (`sympy/printing/latex.py`) derives TWO separator
settings from the user-supplied `mul_symbol`:

* `mul_symbol_latex` — the GENERAL separator: the named-table value, else the
  supplied symbol verbatim. This facet is the PUBLICLY-requested one ("supply
  my own choice which is not in the list ... `\,`", with the expected output
  `'3 \\, x^{2} \\, y'` shown in the problem statement) and does not leak.
* `mul_symbol_latex_numbers` — the separator between NUMERIC factors: on a
  table miss, if the `.strip()`-ed symbol is one of the seven spacing-only
  forms `['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']` it falls back to
  ` \cdot `, else the symbol verbatim. This facet is the one that relaxes.

## The leak is genuinely unavoidable

**The public `problem_statement` names only the general/symbolic facet.** It
shows `latex(3*x**2*y)` with thin spaces and asks for an "arbitrary (and
backwards-compatible)" `mul_symbol`. Token scan: none of {number, numeric,
dot, cdot, spacing, quad, strip, 1.5, fall} appear in `problem_statement` (nor
in `hints_text`). There is no mention of a distinct numeric separator, of a
`\cdot` fallback, or of a spacing-form whitelist.

**The numeric facet lives only in the gold patch + hidden `test_patch`.** The
hidden F2P assertion `latex(1.5*3**x, mul_symbol='\\,') == r"1.5 \cdot 3^{x}"`
pins it: a consumer faithful to the problem statement alone ("use the supplied
symbol verbatim") would emit `1.5\,3^{x}` and FAIL.

**A faithful spec MUST encode it.** A spec that left the numeric separator
unconstrained (or made it the supplied symbol verbatim) would admit an
implementation that verifies yet fails that F2P assertion — a
`verify ⟹ correct` violation (directive 4). So the spec view's `numSep` (the
numeric-dot fallback) and `spacingSyms` (the seven-form whitelist, which is
the gold hunk's inline data and hence byte-equal to it) are unavoidable
disclosures. No PS-derivable reformulation can express them: the
numeric/general distinction, the ` \cdot ` value, and the whitelist are all
absent from the `problem_statement`.

Only the numeric-dot / spacing-whitelist facet relaxes. The general-separator
"verbatim on a table miss" facet IS PS-derivable ("arbitrary,
backwards-compatible", with the thin-space example output shown) and does not
leak. The four named table entries are public API (documented `mul_symbol`
choices) and do not leak.

## Core soundness (policy requirement) — all clean

* G-VERIFY pass — `resolveMulSeparators` verifies against
  `ensures out = resolveSpec sym`, a complete functional pin to a concrete,
  total, axiom-free pure function (no oracle to echo).
* G-DIFF pass — `Solution_prepatch.lean` (bare table index; rejects any
  non-named symbol) fails to verify against the byte-identical spec, exactly
  on the `mulTable sym = none` (F2P thin-space) goal.
* G-CONF pass — the R/I shadow (including the full-Unicode `str.strip()`
  model `pyStrip` and the control/Unicode whitespace boundary inputs) agrees
  with the real gold-patched `LatexPrinter` over the full fuzz domain,
  0 disagreements.
* G-RESOLVE pass — `patch.diff` is the gold patch verbatim; the harness
  reports resolved.
* No axioms (G-AX vacuous): the table and the whitelist are the changed
  function's own inline data, modeled directly per directive 7.

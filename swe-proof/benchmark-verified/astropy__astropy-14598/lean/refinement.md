# refinement.md — astropy__astropy-14598

Modeled function: `Card._split`, the per-subcard value-recovery body of the
CONTINUE branch (the exact code region the gold patch edits). The Lean
`implementation_segmentValue : List Char → Option (List Char)` is the
skeleton of that body for one subcard `vc`. The surrounding accumulation over
subcards (`values.append`, `"".join`) is unchanged by the patch and framed out.

## Patch ops ↔ implementation ops

| # | patch.diff op | implementation_segmentValue op | tag | note |
|---|---|---|---|---|
| 1 | `_strg_comment_RE = re.compile(f"({_strg})? *{_comm_field}?$")` — append `$` end-anchor to the pattern (card.py:69) | `matchToken vc` (and its helpers `scanToken` / `remainderOk`) require the post-quote remainder to reach end-of-input, vs the pre-patch `lookaheadOk` | A-reference | deep model of the changed regex; validated == real `re` capture by G-CONF (0 mismatches over ~10⁷ printable inputs). NOT axiomatized. |
| 2 | `m = self._strg_comment_RE.match(vc); if not m: return kw, vc` (unchanged control, card.py:856–858) | the `none` arm of the `match`: anchored pattern can now fail to match ⇒ `none` (caller keeps `vc` verbatim) | A-reference | the `$` makes a no-match reachable; modeled as `Option` |
| 3 | `value = m.group("strg") or ""` (card.py:861) | `some strg` arm binds the captured token (`"" ` modeled as `some []`) | I | identical: default-empty capture |
| 4 | `value = value.rstrip()` — DROP the trailing `.replace("''","'")` (card.py:862) | `value := dropTrailingWs value` with NO `collapseDoubledQuote` | R | `str.rstrip()` ↔ `dropTrailingWs` (ASCII ws). Removal of the collapse is the second half of the fix; prepatch impl still applies `collapseDoubledQuote`. |
| 5 | `if value and value[-1] == "&": value = value[:-1]` (card.py:863–864) | `value := dropTrailingAmp value` | I | drop single trailing `&` |
| 6 | `values.append(value)` (unchanged) | `return some value` | I | the subcard's contributed value |

Every op is R, A-reference, or I — no A-consumed axiom, no I-marked
changed-inexpressible op. Op 1+2 (the anchor) and op 4 (drop the collapse) are
the two coupled halves of the fix; they are modeled deeply, never axiomatized
(SPEC_GUIDE §3 / directive 7).

## Pre-patch (Solution_prepatch.lean) correspondence

Pre-patch impl = `matchTokenLoose` (op-1/2 un-anchored: `lookaheadOk`, always
matches) ∘ `dropTrailingWs` ∘ `collapseDoubledQuote` (op-4 bug present) ∘
`dropTrailingAmp`. On the discriminating segment `'xx''&'` (and any segment whose
recovered token contains an interior `''`, or whose tail has a space-separated
trailer / non-end-reaching quote), this produces a value that differs from the
fixed value, so `problem_spec_segmentValue` is FALSE for it ⇒ `correct_segmentValue`
is unclosable (G-DIFF). Confirmed: `¬ problem_spec_segmentValue "'xx''&'" (impl …)`
holds by `native_decide`.

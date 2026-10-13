# Relaxed-leakage rationale — astropy__astropy-14598

**Scope of this note.** This instance is a two-coupled-hunk
`problem_statement ↔ gold` mismatch: one hunk's discriminator is fully public,
the OTHER hunk's discriminator is mandatory for the F2P test yet appears only in
`hints_text` / gold / `test_patch`. A faithful spec (one whose verifying impl
refines to a patch the harness reports `resolved`) must pin both behaviors, so
the spec's postcondition necessarily *determines* the second hunk's outcome. What
the spec view must NOT do — and no longer does — is narrate that second
discriminator, or carry a helper shaped like it.

This note documents (a) the provenance of each discriminator, (b) the
de-narration that was applied after the 2026-08-13 G-PANEL-3 review, and (c) the
residual, purely behavioral determination that cannot be removed without making
the spec unfaithful.

## The two hunks and their discriminator provenance

Both hunks live in the long-string / CONTINUE value recovery inside
`Card._split`, and both are load-bearing for the sole F2P
`test_long_string_value_with_quotes` (3 assertions).

- **Hunk 1 (`card.py:862`)** — drop the duplicate per-field
  `.replace("''", "'")`. Discriminator: a doubled quote must NOT be collapsed at
  the per-field step. **PUBLIC.** The `problem_statement` names the doubled
  single quote, states that the bug turns it into a single quote, and shows the
  position/length-dependent `range(60,70)` / `range(50,70)` round-trip tables.
  This facet does not leak, and the spec models it plainly (by the ABSENCE of any
  doubled-delimiter collapse in `recovered`).

- **Hunk 2 (`card.py:69`)** — the capture regex gains a trailing `$` anchor,
  which changes WHICH delimiter closes the captured content. Discriminator on the
  F2P observable: "a string after the quotes is lost if there is a space in
  between" — the `"x"*100 + "'' aaa"` case (F2P assertion 3). **HINTS-ONLY.**
  Token scan of the solver-visible `problem_statement` (lowercased): `space` 0,
  `lost` 0, `after` 0, `string after` 0, `aaa` 0, `'' ` (quote-quote-space) 0,
  `comment` 0, `trailing` 0, `tail` 0, `anchor` 0, `regex` 0. Every one of those
  appears in `hints_text`, which carries the verbatim line:

  > "Additional issue, a string after the quotes is lost if there is a space in
  > between:
  > `fits.Card.fromstring(fits.Card("FOO", "x"*100 + "'' aaa", "comment").image).value`"

  The `problem_statement` shows only the no-space cases (`"x"*n+"''"` and
  `"x"*n+"''"+"x"*10`); in-container hunk isolation confirms both are resolved by
  hunk 1 ALONE. The space-straddle case is the only thing hunk 2 fixes, and it is
  absent from the public issue.

## De-narration applied (2026-08-13, after the G-PANEL-3 review)

The G-PANEL-3 reviewer identified the leak vehicle precisely: the spec view
"explicitly models this exact interior-delimiter-then-space span rule
(`captureTrunc` + its negation, plus the docstring/`captureBody` prose),
disclosing the hints-only discriminator." All three of those are gone:

- `captureTrunc` — a helper whose entire content was the space-straddle
  truncation rule, i.e. the hunk-2 bug spelled out as a definition — is
  **deleted**. The weak-close reading now exists only in `Solution_prepatch_2`'s
  elided `impl` region and as a rival in `properties.py`; neither is in any
  solver-visible spec view.
- `captureBody` and its prose — which described the span in terms of "the outer
  bookends" and the interior-delimiter-then-space exception — are **deleted**.
- The replacement, `recordContent`, states ONE uniform record-grammar rule with
  no special case for a space and no mention of a lost tail: the delimiter that
  closes the content is the one past which the record holds only padding and at
  most an annotation. This is the generic shape of a quoted, optionally
  annotated, column-padded record — the model any faithful reading of the
  record format produces — not a rule shaped like the hints-only witness.

The spec view also carries no patched-file name (`card.py` 0), no repo symbol
(`_split` / `Card` / `_strg_comment_RE` / `fits` 0), and no mechanism echo
(`replace` / `re.compile` / `m.group` / `regex` / `anchor` / `$` 0). Identifiers
are abstract (`quoteCh`, `annotCh`, `recordContent`, `recoverSegmentText`,
`field`). The mechanical G-LEAK screen passes.

## The residual: determination without disclosure

What remains is that the postcondition, being faithful, *determines* the hunk-2
outcome: a spec that did not pin which delimiter closes the content would admit
the hunk-2 bug and fail F2P assertion 3, so it could not be the shared contract
for this instance. In-container hunk isolation establishes the necessity:

- baseline: 16/16 round-trip failures.
- hunk 1 only: F2P assertions 1 & 2 pass, **assertion 3 FAILS** —
  `"x"*100+"'' xxx"` round-trips to `…''` (the ` xxx` tail dropped).
- hunk 2 only: still 16 failures (the doubled delimiter is still collapsed).
- both: 0 failures; all 3 assertions pass; `resolved`.

A solver must therefore derive the closing-delimiter rule from the record format
rather than from the spec's narration — which is the intended difficulty, since
the rule is a property of the format, and the space-straddle *symptom* (the thing
`hints_text` gives away) is nowhere stated. This is weaker disclosure than the
reviewed revision, where the discriminating case was a named definition. It is
recorded here rather than suppressed, so the residual is auditable, and it
matches the documented two-coupled-hunk precedents
(`sphinx-doc__sphinx-8265`, `django__django-11265`,
`matplotlib__matplotlib-24870`): the first facet is PS-derivable and does not
leak; only the second facet's determination is at issue.

**Disposition (corrected 2026-08-14, after the second G-PANEL-3 review).** An
earlier revision of this bundle argued the relaxed-leakage case in this note
while recording `meta.json gates.G-LEAK.status = "pass"` with detail
`"spec view clean"` — i.e. it took the exception without declaring it, and the
recorded detail was affirmatively wrong given this note's own concession. Per
SPEC_GUIDE §6 the exception is conditional on exactly that field. The bundle now
carries `relaxed_leakage: true` alongside this note, so `G-LEAK` records
`status = "relaxed"` with the standard detail
(`"RELAXED per RELAXED_LEAKAGE.md: semantic leak of gold discriminator;
unavoidable for a faithful spec"`) — the same bookkeeping as all three cited
precedents, each of which records `relaxed` rather than a clean pass.

The alternative — actually removing the disclosure — was checked and rejected on
faithfulness grounds, not convenience. Re-measured against the real regexes at
`base_commit` on the F2P assertion-3 witness segment
`vc = "'" + "x"*31 + "''''" + " xxx" + "'"`:

| card.py state | recovered value |
|---|---|
| neither hunk (baseline) | `x*31 + "''"` |
| hunk 1 only (`.replace` deleted, regex UNanchored) | `x*31 + "'''"` — ` xxx` tail LOST |
| hunk 2 only (`$` added, `.replace` kept) | `x*31 + "'' xxx"` |
| both (gold) | `x*31 + "''''" + " xxx"` |

Hunk-1-only loses the tail, so a spec that did not pin which delimiter closes the
content would admit the hunk-2 bug and fail F2P assertion 3. `closesContent` is
therefore load-bearing for faithfulness, and deleting it to clear the leak would
trade a declared disclosure for an undeclared unfaithfulness — the worse defect.

## Core soundness (unaffected by anything in this note)

Nothing here weakens the contract. The obligation is carried entirely by
`ensures out = recovered field`, over an UNRESTRICTED domain (the method has no
`require`), with the return type `Option (List Char)` so the recovery's own
non-record path is modeled rather than excluded. Both prepatch twins carry this
spec byte-identically and each fails verification at its own hunk's
discriminating clause. For the authoritative verdicts of G-VERIFY / G-DIFF /
G-EQ / G-GOLD / G-PBT / G-CONF / G-RESOLVE, read the recorded statuses in
`meta.json` — this note deliberately does not restate them.

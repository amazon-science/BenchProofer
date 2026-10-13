# RELAXED_LEAKAGE — astropy__astropy-7671 (lean)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

Policy: `prompts/lean/spec_guide.md` directive 6 ("**Exception —
relaxed-leakage:** for a proven `problem_statement ↔ gold` mismatch where a
faithful spec MUST name the discriminator, keep the instance with the leak
allowed"). The gate honors it mechanically
(`src/swebench_unified/gates/leak.py`) via the `relaxed_leakage` meta flag plus
this file, **even when the lexical screen passes** — which is exactly this
bundle's situation, and the reason the mechanism exists.

## Why a recorded relaxation, and not a spec edit

The G-PANEL-3 audit (verdict.md, Role 4) demonstrated a *semantic* leak by
blind gold-reconstruction: an agent given only the public `problem_statement`
and the computed spec view reproduced the gold regex
`^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*` character-for-character. The
reviewer's own recommendation was a recorded relaxation, not a weakening, and
that recommendation is correct. It was never filed: G-LEAK was recorded
`status="pass"`, `detail="spec view clean"`, and no `RELAXED_LEAKAGE.md`
existed, so a real character-exact leak was on record as clean. This file plus
the meta flag close that recording gap.

## The mismatch (problem_statement ↔ gold)

The public `problem_statement` shows only that
`LooseVersion('1.14.3') >= LooseVersion('1.14dev')` raises `TypeError`
(bpo-30272) and that `minversion('numpy', '1.14dev')` therefore fails. Token
scan of the problem_statement, re-confirmed here: **0 hits** for each of
`!`, `epoch`, `PEP`, `440`, `regex`, `regexp`, `prefix`, `dotted`, `group`,
`Unicode`, `ASCII`, `digit`, `normal`, `reduce`, `match`.

From the statement alone the natural guess is `^\d+(\.\d+)*`. Three parts of
the gold's grammar are not derivable from it:

1. the optional leading `<digits>!` group;
2. the no-leading-zero alternation `0|[1-9]\d*`;
3. the **non-uniform** digit classes — `\d` is Unicode-aware for a `str`
   pattern while the literals `0` / `[1-9]` are ASCII-only, so a release
   number's leading character is ASCII and its continuation is any character
   of the Unicode decimal-number category.

Two of the three are additionally **test-invisible**: gold and an epoch-free
variant agree on all six F2P/test strings, and gold and a uniformly-ASCII
variant likewise, so neither can be defended as "needed to pass the tests".

## Why the leak is unavoidable (faithful ⟹ leaking) — measured

The reduction is **the operation the patch changes**, so `spec_guide` §0.7 /
§3 forbid axiomatizing it: it must be modeled deeply, and G-CONF validates the
deep model against the real callee. The postcondition is an equality pinned to
`normalizeVersion version` in both branches, and in the branch where the ordering
answers at the reduced pair it reads

    result = some (if inclusive
                   then versionGe haveVersion (normalizeVersion version) h
                   else versionGt haveVersion (normalizeVersion version) h)

with **no precondition**, so a gold-faithful implementation satisfies it only
if `normalizeVersion` agrees with the real regex reduction at *every*
`List Char`. Each candidate de-leaking weakening therefore makes the **gold
implementation itself FAIL the spec**. Measured in the instance image
(Python 3.6.13, `unidata_version` 9.0.0), against the real inline regex:

| weakening | agrees on all six F2P strings | but diverges from the real regex at |
|---|---|---|
| drop the epoch alternative | yes | `'1!2'` → real `'1!2'`, weakened `'1'`; `'12!34.5x'` → `'12!34.5'` vs `'12'`; `'1!0'` → `'1!0'` vs `'1'`; `'1٥!5'` → `'1٥!5'` vs `'1٥'` |
| uniform ASCII digit classes | yes | `'1٥5'` → real `'1٥5'`, weakened `'1'`; `'1٥!5'` → `'1٥!5'` vs `'1'` |

So each "de-leaked" model is *unfaithful* on a non-empty input class — which
is precisely the G-PANEL-2 defect class this bundle was previously repaired
for. A faithful deep model of this particular changed op cannot avoid
reproducing the gold grammar, because for a fix whose entire behavioral
content *is* a regex literal, "deep model of the changed op" (required) and
"do not reveal the edit" (required) cannot both hold. That is the definition of
the unavoidable case.

Confirming that the table above is the real callee and not a reading of the
pattern: the model's explicit 54-range code-point table was checked
**exhaustively over all 0x110000 code points** inside the image — the table,
the Unicode `Nd` category and the set `\d` matches are all the same 580
characters (`table == Nd == \d`, 0 symmetric difference). `str.isdigit()` is
the wrong proxy (708 characters; it accepts the superscripts).

## What WAS done to the spec view (de-narration that costs no adequacy)

The prose transcription of the grammar handed a reader the regex in copy-ready
form on top of the executable code. It is removed. The module docstring no
longer walks through "optional epoch `<digits>!`, mandatory release number,
`0` or `1`–`9` followed by decimal digits, ASCII-leading / Unicode
continuation"; it now states the abstract behavior and points at
`releasePrefix` as the definition of record. The helper docstrings no longer
name the Unicode decimal-number category, the `Nd` abbreviation, the
ASCII/Unicode asymmetry, the superscript exclusion, or the "epoch".

This edit is **comment-only and provably so**: stripping all comments from the
pre-edit and post-edit `Solution.lean` yields byte-identical code. So the
modeled function, the postcondition, G-CONF faithfulness and every rival
rejection are unchanged by construction — no clause was weakened to buy
de-narration. It does NOT eliminate the leak (the `pure` region still
determines the grammar, as it must), which is why the recorded relaxation
above is the actual disposition.

## Core soundness (relaxation criteria 1–2)

Recorded gate verdicts, this repair's runs:

- G-VERIFY pass — `Solution.lean` verifies, `1 correct_*` closed, axioms clean.
- G-DIFF pass — `Solution_prepatch.lean` fails to verify: the spec still sees
  the bug.
- G-GOLD pass — gold-faithful impl verifies; prepatch fails.
- G-CONF pass — 0 disagreements vs the real patched `minversion` in-container.
- G-PBT pass — 10 spec cases behaved as expected (3 positive controls + the
  admissibility instances verify; all 5 uniqueness rivals rejected).
- G-MUT pass, G-HYGIENE pass, G-INTEGRITY pass, G-RESOLVE pass, G-AX skip
  (no consumed callee axioms).

Criterion 1 (core sound) and criterion 2 (leak genuinely unavoidable, measured
above) hold; this file plus the `relaxed_leakage` meta flag supply criterion 3
(in-bundle documentation).

## Scope of the relaxation: which facet is dispositioned

This section records what the relaxation does and does not cover, as a
statement of scope. It draws no conclusion about any verdict; the facts above
and the gate record are the whole of what this file offers.

**The facet covered.** Exactly one leaking facet is dispositioned here: the
`pure` region determines the reduction's grammar, including the optional
leading `<digits>!` group, the no-leading-zero alternation, and the non-uniform
digit classes. The measurements above are what that disposition rests on — the
`problem_statement` token scan (0 hits, re-confirmed), the two-row divergence
table showing each de-leaked variant unfaithful on a non-empty input class, and
the exhaustive code-point comparison inside the instance image.

**What is outside it.** Nothing in this file speaks to any other leaking line:
a spec-view identifier colliding with a patched repo symbol, returned fix
narration, or any leak elsewhere in the spec view is untouched by this
disposition and is not argued for anywhere above.

**What would break it.** The disposition depends on two things that are checkable
and could fail: core soundness (the gate record in the section above), and the
unavoidability claim. The latter is refuted by exhibiting a model that is BOTH
derivable from the public `problem_statement` AND in agreement with the real
reduction on the epoch and Unicode-digit input classes in the table — no such
model is claimed to be impossible in principle here, only that the two natural
candidates both diverge, as measured.

**On re-checking.** The measurements above are reproducible rather than
asserted, and are stated so they can be re-run rather than taken on trust:
`G-CONF` re-runs the model against the real callee in-container, the token scan
and the divergence table re-run from the `problem_statement` and the gold
regex, and the code-point comparison re-runs inside the instance image. A
reader who reaches a different result than the table records has found
something this file gets wrong.

Per `src/swebench_unified/gates/_audit.py`, leakage relaxation is a G-LEAK
concept: there is no "relaxed" status at the panel layer, and nothing
downstream re-applies the relaxation to a panel-layer verdict. That is a fact
about the pipeline's wiring, noted so a reader knows this file's flag does not
propagate; how the panel weighs the argument above is the panel's to decide.

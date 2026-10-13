# RELAXED_LEAKAGE — matplotlib__matplotlib-25479 (velvet)

Disposition: **KEEP with relaxed leakage**. Policy: the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = 'relaxed'`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`) via
`meta.json relaxed_leakage: true` + this in-bundle file. This disposition was
mandated by the bundle's own P2 audit verdict (`verdict.md`, ACTION ITEM):
the audit ACCEPTED the bundle and found the site-2 leak to be exactly the
relaxed-leakage pattern, but the disposition had not yet been recorded
in-bundle. This file records it.

## The problem_statement ↔ gold mismatch

The public `problem_statement` reports ONE behavior: registering a colormap
under a name different from the colormap object's own advertised name makes a
later pyplot lookup fail with `ValueError` — because the lookup consults the
stored colormap's own `.name`. Its entire content is the registration-name
confusion ("one has to make sure that the colormap name and the registered
name are the same"). That publicly motivates gold hunk 1 (`cm.py register`:
stamp the registration name onto the stored copy) and nothing else.

The gold patch has a SECOND hunk the public issue never hints at:
`colors.py Colormap.__eq__` drops the `self.name != other.name` disjunct, so
colormap value-equality becomes **name-independent**. Token scan of the
problem_statement: `equal`, `__eq__`, `==`, `compare`, `comparison`,
`colorbar_extend`, `_lut`, `duplicate`, `identical`, `rename`, `extend` are
ALL absent (the only 'lut' hit is the string `lut)` inside an unrelated pyplot
traceback line). It is absent from `hints_text` too. The discriminator lives
only in the hidden `test_patch`: `test_colormap_equals` flips
`assert cm_copy != cmap` → `assert cm_copy == cmap` after
`cm_copy.name = "Test"`, and `test_set_cmap_mismatched_name` asserts
`cmap_returned == cmap` (which, given hunk 1 renames the stored copy, holds
only under name-independent equality).

## Why faithful + non-leaking is impossible

A **faithful** spec must pin name-independent equality, because the
FAIL_TO_PASS tests assert exactly that: a renamed content-identical duplicate
compares equal, and the looked-up (renamed) registered colormap compares equal
to the original. `Solution_prepatch_2.lean`, which keeps the name conjunct in
the equality verdict, must FAIL verification (G-DIFF) — and it does, at
exactly `ensures out = colormapEqSpec a b`. A spec that pinned only the
publicly-described behavior (hunk 1's name stamping) would say nothing about
equality and would admit a wrong implementation that verifies yet fails
`test_colormap_equals` — violating G-EQ / verify⟹correct. The leak is in the
**behavior itself**, not in narration that could be de-narrated away: any
faithful formalization of the tested behavior discloses that the advertised
name does not participate in colormap equality, which is not derivable from
the public issue. This is the precise condition directive 6 accepts.

## Requirements check

1. **Core is sound.** G-VERIFY: `Solution.lean` verifies under
   `loom.semantics.termination "total"` (termination obligations discharged —
   no vacuous-divergence hole; the earlier audit's `while true` counterexample
   class no longer verifies). G-DIFF: both prepatch twins share the byte-equal
   spec (`same_spec` True) and fail at exactly the discriminating clauses
   (prepatch_1: `cmap.name = name` unprovable; prepatch_2: name-conjunct
   mismatch vs `colormapEqSpec`). G-MUT 7/7. G-CONF: 0 disagreements over
   100009 seeded inputs against the real patched repo in-container. G-AX
   vacuous (no axioms, no A-reference). G-RESOLVE: `patch.diff` is the gold
   patch verbatim, resolves, not flaky.
2. **The leak is genuinely unavoidable**, established above: the equality-site
   discriminator is demonstrably absent from `problem_statement` (and
   `hints_text`) and present only in gold / the hidden `test_patch`.
3. **Documented in-bundle** (this file); `meta.json relaxed_leakage: true`
   points here. The mechanical lexical G-LEAK screen itself passes (the spec
   view names no patched file/symbol — `extendStyle`/`lookupTable` are
   de-narrated renames of `colorbar_extend`/`_lut`; no `__eq__`, no
   `register`, no diff line) — the leak is semantic, as the policy expects.

## Scope of what is disclosed

The spec view disclosures: (1) a colormap stored under a chosen registration
name advertises that name while its content (end-style, colour lookup table)
is preserved — fully derivable from the public problem_statement; and (2)
colormap value-equality turns on the end-style and colour lookup table only,
names ignored ("a colormap and a renamed duplicate of it compare equal") —
the relaxed disclosure: it is the tested behavior, absent from the public
issue. Nothing about the patched files (`lib/matplotlib/cm.py`,
`lib/matplotlib/colors.py`), the `register`/`__eq__` symbols, the
`colorbar_extend`/`_lut` attributes, or the edit mechanics (dropping a
conjunct) is named in the spec view.

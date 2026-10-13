# RELAXED_LEAKAGE — sphinx-doc__sphinx-9673 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). This bundle's own P2 audit
(`verdict.md`) reached exactly this disposition — "leakage RELAXED is an
allowed disposition; the bundle carries a recording defect (G-LEAK
mis-recorded as clean pass + missing in-bundle RELAXED_LEAKAGE.md) that MUST
be corrected" — this file plus the meta flag IS that prescribed correction.
The same instance is already dispositioned identically in the sibling
`lean/` and `nagini/` bundles of this instance.

## The mismatch

The gold fix to `augment_descriptions_with_types`
(`sphinx/ext/autodoc/typehints.py:130` @ base 5fb51fb) treats the PLURAL reST
field marker `:returns:` as a synonym of the short `:return:` — two coupled
one-token widenings:

```python
-        elif parts[0] == 'return':
+        elif parts[0] in ('return', 'returns'):
             has_description.add('return')
...
     for name in annotations:
-        if name == 'return':
+        if name in ('return', 'returns'):
             continue
```

The sole F2P test (`test_autodoc_typehints_description_no_undoc`) documents a
function whose result marker is the plural `:returns:` and asserts the return
type (`Return type: int`) is now emitted. The discriminator is therefore the
PLURAL spelling of the reST return field marker.

The leaking lines in this bundle's spec view (frozen pure region of
`Solution.lean`): `def returnsTok : Tok := "returns".toList`, the widened
branch `p0 == returnTok || p0 == returnsTok` in `classifyField`, the skip
`name == returnTok || name == returnsTok` in `emitStep`, and the prose
("plural synonym", "Both accepted spellings", "the behavior of interest").
A reader of the spec view alone can reconstruct the exact gold edit — this
is the dispositioned facet.

## Why the leak is unavoidable

The discriminating vocabulary — the reST field marker `:returns:` (plural)
and the fact that it must be a SYNONYM of `:return:` — is **absent from the
solver-visible `problem_statement`**:

- The `problem_statement` is a Napoleon "return type missing from
  documentation" symptom report. It mentions `autodoc_typehints_description_target
  = "documented"`, Napoleon Google-style docstrings, and a missing return type.
- Token scan of `problem_statement`: reST markers `:returns:` = 0, `:return:`
  = 0, `synonym` = 0, `plural` = 0. Its only `Returns` token is the
  Google-style docstring SECTION HEADER `Returns:` (inside the reproduction
  docstring) — a **homograph** of, not the same artifact as, the reST field
  marker `:returns:`. Napoleon TRANSLATES the `Returns:` section into an
  internal reST `:returns:` field; the public text never names that field,
  never shows the colon-delimited marker, and never states that
  `:return:`/`:returns:` are two spellings autodoc must unify.
- The actual diagnosis — "napoleon generates a `returns` field internally.
  It hits the bug", with the `:return:` vs `:returns:` contrast — lives ONLY
  in `hints_text` (excluded from the leakage baseline), and the
  plural-field test input lives only in the hidden `test_patch`.

A faithful spec (one whose prepatch fails and which no wrong impl satisfies)
MUST pin the two-spelling synonym: drop the `returnsTok` disjuncts from
`classifyField`/`emitStep` and `buildFields` becomes exactly the PRE-patch
behavior, so `Solution_prepatch.lean` would verify and G-DIFF could not fire.
A spec derivable from `problem_statement` alone could model only the single
`"return"` spelling. Faithful + non-leaking is provably impossible here —
the definition of a `problem_statement ↔ gold` mismatch.

**On the homograph trap (recorded for future panels):** substring presence of
`Returns` in the `problem_statement` is NOT evidence the *field-marker*
discriminator is public — the Google docstring section header (Napoleon
source layer) and the generated reST info-field marker are distinct artifacts
at different layers. A prior (batch06) panel dissent was fooled by exactly
this homograph.

## Core soundness is intact (per the recorded P2 audit of THIS bundle)

- **G-VERIFY: pass** — `Solution.lean` verifies (4.2 s), proof closes,
  no sorry/axioms.
- **G-DIFF: pass** — `Solution_prepatch.lean` (classifyBuggy/emitBuggy
  recognize only the short `return`) genuinely fails on the discriminating
  `ensures out = buildFields fields annotations` goal: on
  `fields=[["returns"]]`, `ann=[("return","int")]` the spec emits
  `[Field.rtype "int"]`, the buggy impl emits `[]` — exactly the F2P case.
  `same_spec(Solution, prepatch) = True` (spec regions byte-identical).
- **G-EQ: pass (SOUND/TIGHT)** — 11 attacks re-run, none breaks the spec;
  positive control verifies; no kind-3 steps; no axioms.
- **G-PANEL-2: FAITHFUL** — op-by-op transliteration of the PATCHED function;
  bundle `conformance_check.py`: 100,012 cases (seed 9673), 0 disagreements
  vs the real patched callee; independent adversarial fuzz 200,000 cases,
  0 disagreements, 0 exceptions.
- **G-MUT: 20/20 killed.** **G-CONF: pass** (100,012 / 0). **G-AX: vacuous**
  (no consumed axioms, no deep-model references). **G-RESOLVE: resolved**
  (`patch.diff` == gold verbatim).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the plural `:returns:` recognized as a synonym of `:return:`).

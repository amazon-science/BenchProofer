# RELAXED_LEAKAGE — sphinx-doc__sphinx-9673

**Disposition: KEEP with relaxed leakage.**
`meta.json gates.G-LEAK.status = "relaxed"`.

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/lean/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`).
(The former `RELAXED_LEAKAGE.md` cited elsewhere in this bundle was a
source-repo-only doc that does not exist here — see `prompts/README.md` on
dangling source-repo refs.)

## The mismatch

The gold fix to `augment_descriptions_with_types` treats the PLURAL reST field
marker `:returns:` as a synonym of the short `:return:`:

```
parts[0] == 'return'        ->  parts[0] in ('return', 'returns')   # hunk 1
name == 'return'            ->  name in ('return', 'returns')       # hunk 2
```

The sole F2P test (`test_autodoc_typehints_description_no_undoc`) documents a
function whose result marker is the plural `:returns:` and asserts the return
type (`Return type: int`) is now emitted. The discriminator is therefore the
PLURAL spelling of the reST return field.

## Why the leak is unavoidable

The discriminating vocabulary — the reST field marker `:returns:` (plural) and
the fact that it must be a SYNONYM of `:return:` — is **absent from the
solver-visible `problem_statement`**:

- The `problem_statement` is a Napoleon "return type missing from documentation"
  symptom report. It mentions `autodoc_typehints_description_target =
  "documented"`, Napoleon Google-style docstrings, and a missing return type.
- Its only `Returns` token is the Google-style docstring SECTION HEADER
  `Returns:` (inside the reproduction docstring). That header is a **homograph**
  of — not — the reST field marker `:returns:`. Napoleon TRANSLATES the
  `Returns:` section into an internal reST `:returns:` field; the public text
  never names that field, never shows the colon-delimited marker, and never
  states that `:return:`/`:returns:` are two spellings that autodoc must unify.
- The actual diagnosis — "napoleon generates a `returns` field internally. It
  hits the bug" with the `:return:` vs `:returns:` contrast — lives ONLY in
  `hints_text`, and the plural-field test input lives only in the hidden
  `test_patch`.

A faithful spec (one whose prepatch fails and which no wrong impl satisfies) MUST
pin the two-spelling synonym: the post-conditions reference the keyword
`"returns"` alongside `"return"`. A spec derivable from `problem_statement` alone
could only model the single `"return"` spelling — which is exactly the pre-patch
behavior, so it would NOT reject the bug. Faithful + non-leaking is provably
impossible here.

## Note on the batch06 panel dissent

A prior panel pass was fooled by the `Returns:` (section header) / `:returns:`
(reST field marker) homograph and argued the discriminator was already public.
Substring presence of `Returns` in the `problem_statement` is NOT evidence the
*field-marker* discriminator is public — the header and the marker are distinct
artifacts at different layers (Napoleon source section vs generated reST field).

## Core soundness is intact

- G-VERIFY: `correct_augment` closes (proof agent), axioms clean.
- G-DIFF: `Solution_prepatch.lean` (both hunks reverted = literal pre-patch)
  fails on the exact-equality clause for a plural-only-result docstring.
- G-CONF: 0 / 120000 disagreements (seed 9673) between the R/I shadow and an
  independent reconstruction of the patched function.
- G-AX: vacuous (no consumed axiom, no A-reference).
- G-RESOLVE: `patch.diff == gold`, harness `resolved`.

Only the secondary no-leakage property is relaxed, for this one documented
instance.

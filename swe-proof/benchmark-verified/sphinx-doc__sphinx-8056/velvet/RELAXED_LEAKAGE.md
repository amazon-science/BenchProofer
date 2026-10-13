# Relaxed-leakage acceptance — sphinx-doc__sphinx-8056

**Disposition: KEEP with relaxed leakage.** Recorded during the P2 recovery
pass after the refinement de-narrated the two lexical/narrative leak vectors.
`meta.json relaxed_leakage = true`; `gates.G-LEAK` records `status: "relaxed"`
pointing at this file. In this unified repo the policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`, via
the `relaxed_leakage` meta flag + this file). (A former `RELAXED_LEAKAGE.md`
was a source-repo-only doc that does not exist here; references to it in older
in-bundle text mean this policy.) This file is the in-bundle adversarial
rationale per requirement 3.

## Why the residual leak is unavoidable (requirement 2)

The gold patch (`sphinx/ext/napoleon/docstring.py`) makes `_consume_fields` gain
a `multiple=False` parameter and, when set with a non-empty name, split the name
on commas and emit one field per comma-piece (stripped), each sharing the type
and description:

```python
if multiple and _name:
    for name in _name.split(","):
        fields.append((name.strip(), _type, _desc))
```

`_parse_parameters_section` then passes `multiple=True` under the
`napoleon_use_param` config.

- **`problem_statement` reports only the *combining* symptom and a *combined*
  expected output.** The PS shows `x1, x2 : array_like` rendering badly and its
  Expected behavior is the COMBINED form rendered properly:
  `x1, x2 (array_like, optional) - Input arrays...`. The PS never asks for
  splitting `x1, x2` into separate parameters. `hints_text` is empty
  (`napoleon_use_param` / `split` / `comma` / `field` all count 0 in PS).
- **The gold's actually-tested discriminator is the OPPOSITE: SPLIT.** The F2P
  `test_multiple_parameters` (the `napoleon_use_param=True` leg) asserts
  `x1, x2` becomes two separate `:param x1:` / `:param x2:` entries. The prepatch
  fails precisely on this split clause (unsolved goal
  `(if name/typ/desc≠[] then [f] else []) = expandOne multiple f`, diverging
  under `multiple ∧ name ≠ []`).
- **A faithful spec MUST encode the split** (`expandOne` under
  `multiple ∧ name≠[]` = `(splitOnComma f.name).map (stripWs …)`), otherwise a
  non-splitting impl would verify against the spec yet fail the `=True` F2P leg.
  A spec pinning only the PS-public combined facet is therefore non-faithful.
- The split mechanism is the **gold-internal choice**, not derivable from the PS
  (a PS-faithful solver would implement *combined* rendering, since the PS
  Expected behavior keeps the names combined). No PS-derivable reformulation
  models the gold fix. The disclosure cannot be de-narrated away.

This is the same pattern as the accepted precedents `sphinx-doc__sphinx-9602`
(Literal quoting facet hidden in gold/test) and `matplotlib__matplotlib-24870`
(filled-contour `[0,.5,1]` facet hidden in hints/gold): the public facet is
shown, the hidden tested facet must be disclosed by any faithful spec.

## What was de-narrated (now NOT leaking)

The refinement fixed the two avoidable lexical/narrative vectors flagged in the
original audit:

- **D1 (symbol echo):** `consumeFieldsExpand`/`parseParametersSection` →
  `splitSharedNameFields`/`buildParameterFieldSeq` (abstract behavior names with
  no transliteration of `_consume_fields`/`_parse_parameters_section`).
- **D2 (gating narration + flag echo):** flag `useParam` → `splitNames`
  (neutral); the docstring no longer narrates the `napoleon_use_param` /
  "per-parameter rendering style" gating.

A fresh grep of the spec view confirms NO residual `napoleon`, `_consume_fields`,
`_parse_parameters_section`, `docstring.py`, `use_param`, or rendering-style
narration. Only the SPLIT *behavior* itself remains disclosed — which is
unavoidable.

## Core soundness intact (requirement 1)

- G-VERIFY: `Solution.lean` verifies (exit 0).
- G-DIFF: `Solution_prepatch.lean` fails on the discriminating goal (exit 1).
- G-EQ: SOUND / TIGHT (full functional equality `out = expandFields … raw` over
  fully-free inputs; 7 spec-too-weak attacks all `same_spec=True` and verify
  exit 1; non-vacuous positive control exit 0; no kind-3; no ungrounded-oracle
  echo).
- G-AX: VACUOUS (no consumed axioms; `splitOnComma`/`stripWs` A-reference deep
  models SOUND on the full str.strip() whitespace set — `isWs` enumerates every
  `chr(c).isspace()` code point incl. U+00A0 — validated == real callees).
- Faithfulness: FAITHFUL (spec `expandFields` == real post-gold `_consume_fields`
  on 30007 inputs incl. all F2P shapes, 0 mismatch; end-to-end F2P rendering
  matches under both config settings).
- G-RESOLVE: resolved (patch.diff == gold, harness resolved).

Only the secondary no-leakage property is relaxed; the `verify ⟹ correct`
contract is unaffected.

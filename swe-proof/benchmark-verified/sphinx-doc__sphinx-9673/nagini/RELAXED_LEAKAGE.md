# RELAXED-LEAKAGE ACCEPTANCE: sphinx-doc__sphinx-9673

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision; see
RELAXED_LEAKAGE.md).** This instance is a `problem_statement <-> gold`
MISMATCH: the gold patch fixes the reported "missing return type" symptom by
treating the PLURAL return-description field marker (`returns`) as a synonym of
the SHORT one (`return`), and the F2P test exercises exactly that plural
spelling. But the plural-spelling discriminator is **absent from the
solver-visible `problem_statement`** and present only in `hints_text` and the
gold/`test_patch`. A spec faithful to the F2P test MUST pin the synonym (else
the prepatch verifies and G-DIFF cannot fire), while a spec restricted to the
public issue cannot — so faithful + non-leaking is provably impossible. The
batch06 adversarial panel confirmed the verification CORE is fully SOUND
(G-VERIFY/G-DIFF/G-EQ/G-AX/faithfulness clean) and the gold resolves
(G-RESOLVE), so `verify => correct` is UNAFFECTED; only the secondary
no-leakage property relaxes.

## The leaked discriminator: `:returns:` (plural) recognized as a synonym of `:return:`

The gold patch (`sphinx/ext/autodoc/typehints.py`,
`augment_descriptions_with_types`) is two coupled one-token edits:

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

The F2P test (`test_autodoc_typehints_description_no_undoc`) adds a function
documented with the PLURAL reST field marker:

```rst
.. autofunction:: target.typehints.decr

   :returns: decremented number
```

and asserts the rendered output now carries `Return type:` / `int`. Before the
fix, `parts[0] == 'return'` does not match the plural `returns`, the return
value is not counted as "described", and no return-type field is emitted — the
test fails. So the SHORT-vs-PLURAL synonym is a TESTED discriminator, not
cosmetic. (Confirmed in-bundle: `model_prepatch.py`, which reverts code-3
recognition in hunk 1 and the plural skip in hunk 2, FAILS verification on the
hunk-1 loop invariant AND the hunk-2 postcondition.)

## The discriminator is absent from `problem_statement`, present only in `hints_text`

Token check on `problem_statement` (verbatim from `instance.json`):

- lowercase substring `returns`: **ABSENT**
- reST field marker `:returns:`: **ABSENT**
- reST field marker `:return:`: **ABSENT**
- Google-style section header `Returns:`: PRESENT — but this is a HOMOGRAPH, not
  the discriminator (see below).

Token check on `hints_text` (never shown to the solver):

- lowercase substring `returns`: PRESENT
- reST field markers `:return:` and `:returns:`: PRESENT (the hint contrasts
  `func1` with `:return: blah` against `func2` with `:returns: blah`)
- the diagnosis "napoleon generates a `returns` field internally. It hits the
  bug.": PRESENT

The public issue ("autodoc_typehints_description_target not working with
Napoleon", Sphinx 4.2.0) is a pure SYMPTOM report: under Napoleon Google style,
return types are missing from the rendered documentation. Its only `Returns`
token is the Napoleon **Google-style docstring section header** `Returns:`
inside the reproduction docstring — a HOMOGRAPH of, not the same thing as, the
reST info-field marker `:returns:` that the gold actually keys on. The issue
never mentions reST field markers, `:return:` vs `:returns:`, the singular/plural
spelling distinction, or that Napoleon emits a `returns` field internally. That
entire diagnosis — the load-bearing discriminator — lives only in `hints_text`
and the gold/`test_patch`.

There is no PS-derivable reformulation that both models the gold fix (which the
F2P test exercises through the plural `:returns:` marker) and avoids naming the
plural spelling. Drop the synonym and the spec is unfaithful to the F2P test
(the prepatch verifies); name it and the spec view narrates a behavior absent
from the public issue. That is the definition of a PS<->gold mismatch.

## Why the mechanical G-LEAK screen passing is expected (the leak is semantic)

The mechanical screen passes: the spec view quotes no diff line, names no
patched path (`sphinx/ext/autodoc/typehints.py`) or symbol
(`augment_descriptions_with_types`), and embeds no patched identifier. It states
behavior abstractly ("EITHER of two interchangeable field markers: the short
marker and its plural spelling ... synonyms"). But that abstract behavior IS the
hints/gold-derived discriminator, ABSENT from `problem_statement` yet
LOAD-BEARING for faithfulness — which is precisely the case where a clean
mechanical `pass` is the WRONG label and `relaxed` is required. The panel's
adversarial reconstruction is binding and establishes the PS<->gold mismatch.

**Second-order lesson (recorded for the leakage screen):** the dissenting panel
reviewer was fooled by lexical surface overlap — the Google docstring section
header `Returns:` in the PS versus the reST info-field marker `:returns:` that
is the actual discriminator. Substring presence of `Returns` in the
`problem_statement` is NOT evidence the discriminator is public; for
field-marker / section-header bugs, leakage adjudication must distinguish the
reST `:returns:` field from the Google `Returns:` header.

## Why this is NOT a soundness defect

The `verify => correct` chain is intact and was re-verified:

- **G-VERIFY: PASS** — `model.py` verifies (58.3s, no flags, no float encoding,
  zero `@ContractOnly`).
- **G-DIFF: FAIL (prepatch)** — `model_prepatch.py` reverts hunk 1 (return
  description recognized on code 2 only, dropping the plural code 3) and hunk 2
  (`name == return_short` only) and FAILS on BOTH discriminating clauses: the
  hunk-1 loop invariant `described == has_return_description(ToSeq(field_kinds).drop(i))`
  AND the hunk-2 postcondition of `name_is_return_key`.
- **same_spec: TRUE** — axioms / pure / pre / post / invariants regions and the
  module docstring are byte-identical across `model.py` and `model_prepatch.py`;
  only the impl regions differ (`c == 2 or c == 3` vs `c == 2`; the
  `name == return_short or name == return_plural` vs `name == return_short`).
- **G-EQ: SOUND/TIGHT** — refinement.md all R / I, zero kind-3, zero axioms. The
  synonym recognition is modeled DEEPLY (front-recursive folds
  `has_return_description` / `has_return_type` over the actual `field_kinds`
  carrier) and grounded in the input per directive 8 — `Result()` is pinned to a
  structural fold of the real input sequence, never to an opaque oracle.
- **G-AX: VACUOUS (n/a)** — no consumed axioms and no A-reference deep-model
  checks; `axiom_check.py` is a self-contained stdlib structural cross-check
  (model decision == the patched return logic over exhaustive `len<=4` +
  fuzz field-lists, plus the plural-spelling discriminator), exit 0.
- **G-RESOLVE** — `patch.diff` == gold verbatim (817 B), applies cleanly at
  `base_commit`; F2P `test_autodoc_typehints_description_no_undoc` + 24 P2P.
  Harness `resolved` (orchestrator Docker run).

## Conclusion

KEEP under the relaxed-leakage policy: the core is sound and the gold resolves,
but the gold's plural-spelling (`:returns:` as a synonym of `:return:`)
discriminator is settled only in `hints_text` and the gold/`test_patch`, while
the public `problem_statement` is a Napoleon "missing return type" symptom report
whose only `Returns` token is the Google-style section header (a homograph). A
faithful spec cannot avoid narrating the two-spelling synonym behavior.
`meta.json` records `gates.G-LEAK.status = "relaxed"` with a pointer to this
document.

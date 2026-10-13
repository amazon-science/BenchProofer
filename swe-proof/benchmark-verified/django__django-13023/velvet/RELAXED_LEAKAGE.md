# RELAXED_LEAKAGE — django__django-13023 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition was prescribed by this bundle's own recorded P2 audit
(`verdict.md`, defect D1): "**Faithful + non-leaking is provably
impossible** → this is the textbook RELAXED-leakage situation … not a
gratuitous LEAKAGE, and not a soundness problem." The audit's precise fix —
ship this file and record the relaxed disposition — is what this file
implements.

## The mismatch

The gold fix to `DecimalField.to_python`
(`django/db/models/fields/__init__.py`, body line 1504) replaces

```
except decimal.InvalidOperation:
```

with

```
except (decimal.InvalidOperation, TypeError, ValueError):
```

Three members of the recoverable family; their public status differs:

- **`TypeError` — fully public.** The problem_statement is titled
  "DecimalField.to_python() raises TypeError on dict values" and states the
  expected behavior ("produces TypeError instead of ValidationError"). This
  facet does NOT leak.
- **`decimal.InvalidOperation` — pre-patch repo behavior, not gold-only.**
  The pre-patch code at base_commit already reads
  `except decimal.InvalidOperation:` (the unchanged line the gold patch
  broadens), and the pre-existing P2P test `test_to_python` already pinned
  `'abc'` → `ValidationError`. A problem_statement+repo solver reads this
  membership straight off the prepatch source; it reveals nothing about the
  gold edit.
- **`ValueError` — gold/test_patch-only. THIS is the leak.** Token scan of
  problem_statement for `ValueError` / `InvalidOperation` = 0 hits
  (`hints_text` is empty). The PS names only TypeError/dict/to_python/
  DecimalField/ValidationError. The `ValueError` member lives only in the
  gold diff and the hidden test_patch, whose F2P test `test_invalid_value`
  includes the inputs `()` and `[]` — and `decimal.Decimal(())` /
  `decimal.Decimal([])` raise **ValueError** ("argument must be a sequence
  of length 3"), not TypeError (re-confirmed executably at disposition
  time). A solver working from the problem_statement alone would broaden
  the `except` to add only `TypeError` and would fail `test_invalid_value`
  on `()` and `[]`.

The leaking token is the spec view's recoverable-family enumeration:
`isRecoverable .valueError => true` (with lemma `isRecoverable_valueError`),
the inductive constructor `| valueError`, and the docstring's "an
out-of-domain value". `valueError` echoes the gold-added `ValueError`,
absent from the public issue.

## Why the leak is unavoidable

Faithfulness forces the `ValueError` membership into the spec:

- The F2P test `test_invalid_value` pins `ValidationError` (never a raw
  exception) for `()` and `[]`, which fail inside `decimal.Decimal` with
  `ValueError`. So the post-gold behavior on real inputs REQUIRES that a
  `ValueError` from the interpretation attempt be normalised to the field's
  invalid-value error.
- Hence any spec faithful to the post-gold behavior — one that rejects the
  prepatch bug AND rejects the PS-only patch (catch `TypeError` but let
  `ValueError` propagate) — MUST make `valueError` recoverable. The G-EQ
  panel demonstrated exactly this: attack impls where `typeError`/`valueError`
  propagate (atk_1, atk_4) are rejected by the discriminating `ensures`
  clause; a spec without the `valueError` membership would admit them, a
  spec-too-weak defect.
- A spec derivable from the problem_statement alone could pin only
  `{invalidOperation (from the prepatch source), typeError}` — admitting an
  implementation that fails F2P `test_invalid_value` on `()`/`[]`. Faithful +
  non-leaking is provably impossible here.

This is the same faithful-must-leak shape as the dispositioned
sphinx-doc__sphinx-10466 instance (ascending-sort facet): the discriminator
exists only in gold + hidden tests, and the spec cannot be both faithful and
silent about it.

## Core soundness is intact (per the recorded P2 audit)

- G-VERIFY: Solution.lean verifies (2.6 s), proof closes without sorry.
- G-DIFF: `Solution_prepatch.lean` (only `invalidOperation` recoverable —
  the pre-patch single-member `except`) fails for the right reason: the
  `ensures` clause `isRecoverable e = true → out = validationError` is
  unsatisfied for `e ∈ {typeError, valueError}` — exactly the F2P bug.
- G-EQ: SOUND / TIGHT — spec-too-weak attacks (incl. the prepatch bug,
  propagate-everything, catch-everything, wrong-subset variants) all
  rejected, each on a specific `ensures`; positive control (structurally
  different correct impl) verifies.
- G-PANEL-2 (faithfulness): FAITHFUL — deep model `toDecimalResult` matches
  the real gold-patched `to_python` with 0 divergences over 300k
  differential-fuzz inputs plus adversarial edge cases (sNaN, inf, exotic
  types, bytes, non-ASCII digits).
- G-CONF: 0 / 100054 disagreements (seed 13023) against the real
  gold-patched `DecimalField.to_python`.
- G-MUT: 7/7 mutants killed. G-AX: vacuous (genuinely axiom-free).
  G-RESOLVE: resolved.

Only the secondary no-leakage property is relaxed, for this one documented
facet (the `ValueError` membership of the broadened `except` tuple).

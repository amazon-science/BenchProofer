# RELAXED_LEAKAGE — django__django-16667 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

The relaxed-leakage policy lives in the binding spec-construction rules,
`prompts/velvet/spec_guide.md` directive 6 ("**Exception — relaxed-leakage:**
for a proven `problem_statement ↔ gold` mismatch where a faithful spec MUST
name the discriminator, keep the instance with the leak allowed (`meta.json
gates.G-LEAK.status = "relaxed"`)"); the G-LEAK gate honors it mechanically
(`src/swebench_unified/gates/leak.py`, via the `relaxed_leakage` meta flag +
this file).

This disposition was prescribed by this bundle's own recorded G-PANEL-3 audit
(`verdict.md`, Role 4), whose "RECOMMENDED REMEDIATION" offers exactly two
options and judges option (a) — adopt the relaxation — "the likelier correct
disposition", because option (b) "weakens the spec below the F2P bar unless
the constant is recovered elsewhere". This file implements (a). The
unavoidability half of that recommendation was **not taken on trust**: it is
re-derived mechanically below.

## The mismatch

The public `problem_statement` is a pure crash report. It supplies the
traceback, names the exception type, and says the code "does not guard
against a possible OverflowError". It states the BUG; it never states the
fixed branch's RETURN VALUE. Token scan of
`instance.json['problem_statement']`: `0-0-0` → absent, `zero` → absent,
`pseudo` → absent, `except` → absent.

The gold patch's entire substance is two ADDED lines in
`SelectDateWidget.value_from_datadict` (`django/forms/widgets.py`, the
all-present try/except at lines 1158-1164 @ `base_commit`
`02c356f2f3945b8075735d485c3cf48cad991011`):

```
+            except OverflowError:
+                return "0-0-0"
```

Facet-by-facet public status:

- **The TRIGGER — public.** That the overflow outcome is the one to guard is
  named verbatim in the problem_statement (`OverflowError`, plus the
  `sys.maxsize+1` reproduction). The spec view's
  `ConstructOutcome.unrepresentable`, held apart from `notCalendar`, is the
  same distinction, and it is public.
- **The pre-existing ValueError fallback — public repo state.** The spec
  view's `pseudoTriple`/`orZero` model
  `"%s-%s-%s" % (y or 0, m or 0, d or 0)`, which is a CONTEXT (unchanged)
  line in `patch.diff` — pre-patch source at `base_commit`, readable by any
  solver. Disclosing it reveals nothing about the gold edit.
- **The exact OUTPUT constant `"0-0-0"` — gold/hidden-test only. THIS is the
  leak.** It is pinned by the hidden F2P test
  `test_value_from_datadict`, which asserts
  `((str(sys.maxsize + 1), "12", "1"), "0-0-0")`. At `base_commit` the string
  does not occur in `django/` **at all** (`git grep -- '0-0-0'` over
  `django/` at the base commit: zero hits); its only occurrences are inside
  `tests/forms_tests/widget_tests/test_selectdatewidget.py`, in
  `test_format_value`'s `valid_formats` list — a test of the unrelated
  INPUT-parsing method `format_value`, in a file the consumer does not see.
  The spec view discloses it as `allZeroTriple`, and binds it to the overflow
  outcome via the `ensures outcome = .unrepresentable → out = Except.ok
  allZeroTriple` clause.

Note the constant survives de-narration by VALUE, not by spelling. The
current spec view writes it compositionally as
`allZeroTriple := pseudoTriple [] [] []` rather than as a string literal, and
the lexical G-LEAK screen therefore passes ("spec view clean"). But the value
is unchanged: `example : allZeroTriple = "0-0-0".toList := by decide`
elaborates (exit 0), and `#eval String.mk allZeroTriple` prints `"0-0-0"`.
Rewriting the literal as a composition is not a de-leak, so this
disposition — not the lexical pass — is what makes the recording honest.

## Why the leak is unavoidable

Faithfulness forces the exact constant into the spec. Both directions were
executed, not argued.

**(1) The constant is a genuinely free design choice under the public text.**
The most natural problem_statement-only fix is to widen the existing handler
and reuse the pre-existing fallback the pre-patch code's own visible
structure suggests — `except (ValueError, OverflowError):` returning
`"%s-%s-%s" % (y or 0, m or 0, d or 0)`. That fully "guards against the
OverflowError" exactly as the public text asks. Run against the real branch
lifted verbatim from `widgets.py:1158-1164`:

```
witness (the hidden F2P input): (str(sys.maxsize+1), '12', '1')
  real gold branch  -> '0-0-0'
  PS-only alt fix   -> '9223372036854775808-12-1'
  F2P expects       -> '0-0-0'      => alt passes F2P? False
```

The public text does not fix the choice; the hidden test does. Note also the
non-obvious asymmetry the spec view discloses: the overflow leg DISCARDS the
user components (constant output) while the ValueError leg PRESERVES them
(`('2000','13','1') -> '2000-13-1'`). Both behaviours were confirmed by
running the real post-patch branch.

**(2) A spec that does NOT name the constant is too weak to be faithful.**
The reviewer's option (b) — take the remediation text as an opaque parameter,
requiring only that it is component-independent and that the branch returns a
value — was built and run through the real verifier. With the sentinel left
abstract (`ensures outcome = .unrepresentable → out = Except.ok (remediation
sentinel)`, plus the rendered echo, the pre-existing fallback, and
`ensures ∃ r, out = Except.ok r`), the module **VERIFIES (exit 0) for every
instantiation of the sentinel, including the wrong constant** — an impl
returning `"0-0-1"` satisfies it. Such an impl fails the F2P test, so option
(b) yields `verify ⇏ resolve`: a spec-too-weak defect, which is a strictly
worse artifact than a documented leak.

Hence any spec strong enough to reject a wrong-constant implementation must
name the constant. That the current spec IS that strong is witnessed by the
battery's `reject-wrong-sentinel-content` case (returns `"0-0-1"` on the
overflow leg): it is REJECTED, with a witness that elaborates against the
rival and is semantically refuted on gold. Faithful + non-leaking is
therefore provably impossible here — exactly the relaxed-leakage condition,
the same shape as the dispositioned django__django-16642 (two exact
media-type strings) and django__django-13023 instances.

## Core soundness is intact (re-measured, not inherited)

- **G-VERIFY / static gates:** `G-VERIFY=pass G-DIFF=pass G-GOLD=pass
  G-MUT=pass G-PBT=pass G-INTEGRITY=pass G-HYGIENE=pass G-LEAK=pass`.
- **Docker gates:** `G-RESOLVE=pass G-CONF=pass G-AX=pass` — G-CONF is
  0 disagreements over 100035 inputs (seed 16667) against the real patched
  `value_from_datadict`; G-RESOLVE resolves with `patch.diff` verbatim.
- **G-DIFF for the right reason:** the spec region is byte-identical across
  the twins (`same_spec(Solution.lean, Solution_prepatch.lean, velvet)` =
  True), and `Solution_prepatch.lean` FAILS on exactly the two discriminating
  clauses — `ensures_2: outcome = .unrepresentable → out = Except.ok
  allZeroTriple` and `ensures_5: out = dateText y m d outcome` — with an
  unsolved `⊢ False` on the `unrepresentable` case. The change-carrying
  content is in the spec, not smuggled into the impl.
- **The spec still rejects wrong implementations:** the two most on-point
  audit attacks were re-run against the frozen spec — `atk_2` (the overflow
  leg falls through to the component-bearing fallback) and `atk_3` (the two
  failure legs swapped) — both exit 1, i.e. still rejected.
- **G-PANEL-2 (faithfulness): pass** — no divergence found against the real
  post-patch callee across ~700k tested inputs, including the C-`long`
  boundaries and a `strftime` escape hunt.

Only the secondary no-leakage property is relaxed, for this one documented
facet: the exact output constant of the gold-added overflow leg.

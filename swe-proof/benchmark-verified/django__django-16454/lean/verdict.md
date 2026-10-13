# P2 adversarial audit — django__django-16454

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,9 @@
 def implementation_addSubparsers
     (sameFamily : Bool) (parentFlag : Option Bool) :
     Option (Option Bool) := Id.run do
-  -- The carried flag defaults to "not applicable"; only a same-family sub-parser
-  -- is wired to receive the parent's flag value.
   let mut carried : Option (Option Bool) := none
   if sameFamily then
-    carried := some parentFlag
+    carried := some none
   return carried
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,12 +56,10 @@
 def implementation_addSubparsers
     (sameFamily : Bool) (parentFlag : Option Bool) :
     Option (Option Bool) := Id.run do
-  -- The carried flag defaults to "not applicable"; only a same-family sub-parser
-  -- is wired to receive the parent's flag value.
-  let mut carried : Option (Option Bool) := none
   if sameFamily then
-    carried := some parentFlag
-  return carried
+    return none
+  else
+    return some parentFlag
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,12 +56,7 @@
 def implementation_addSubparsers
     (sameFamily : Bool) (parentFlag : Option Bool) :
     Option (Option Bool) := Id.run do
-  -- The carried flag defaults to "not applicable"; only a same-family sub-parser
-  -- is wired to receive the parent's flag value.
-  let mut carried : Option (Option Bool) := none
-  if sameFamily then
-    carried := some parentFlag
-  return carried
+  return some parentFlag
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,12 +56,9 @@
 def implementation_addSubparsers
     (sameFamily : Bool) (parentFlag : Option Bool) :
     Option (Option Bool) := Id.run do
-  -- The carried flag defaults to "not applicable"; only a same-family sub-parser
-  -- is wired to receive the parent's flag value.
-  let mut carried : Option (Option Bool) := none
-  if sameFamily then
-    carried := some parentFlag
-  return carried
+  match parentFlag with
+  | some _ => return some parentFlag
+  | none   => return none
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,9 +56,7 @@
 def implementation_addSubparsers
     (sameFamily : Bool) (parentFlag : Option Bool) :
     Option (Option Bool) := Id.run do
-  -- The carried flag defaults to "not applicable"; only a same-family sub-parser
-  -- is wired to receive the parent's flag value.
-  let mut carried : Option (Option Bool) := none
+  let mut carried : Option (Option Bool) := some none
   if sameFamily then
     carried := some parentFlag
   return carried
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,9 @@
 def implementation_addSubparsers
     (sameFamily : Bool) (parentFlag : Option Bool) :
     Option (Option Bool) := Id.run do
-  -- The carried flag defaults to "not applicable"; only a same-family sub-parser
-  -- is wired to receive the parent's flag value.
   let mut carried : Option (Option Bool) := none
   if sameFamily then
-    carried := some parentFlag
+    carried := some (parentFlag.map (fun b => !b))
   return carried
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
A command-line argument parser can spawn nested sub-parsers to dispatch
sub-commands. Such a parser carries a configuration flag that governs how it
reports argument errors to the user — for example, whether an invalid argument
yields a concise usage message or is surfaced directly as an exception.

When a parser constructs its sub-parsers, each sub-parser of the SAME family —
one that understands this configuration flag — should receive the parent's flag
value verbatim, so that argument-error reporting behaves consistently at every
nesting level. A sub-parser belonging to a FOREIGN family (one that does not
recognise the flag) receives nothing: the flag concept simply does not apply to
it.

The outcome is TOTAL: for any parent flag value and any requested sub-parser
family, construction yields a definite answer — either "a same-family sub-parser
carrying flag value v", or "a foreign sub-parser to which the flag does not
apply". It never fails to produce an answer.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The decision is a pure
-- computation over two inputs: whether the requested sub-parser family is the
-- same family that recognises the flag, and the parent's flag value. The
-- family test is modeled directly as a boolean input (a deep model of the
-- subclass relationship), and the downstream act of materialising the
-- sub-parser object is abstracted to the flag value the sub-parser ends up
-- carrying. Hence no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared helpers needed)
-- pure-end

-- post-conditions-start
/-- The outcome is TOTAL and fully pinned to the inputs.

  * When the requested sub-parser family is the SAME family that recognises the
    flag (`sameFamily = true`), the result is `some parentFlag`: a same-family
    sub-parser carrying EXACTLY the parent's flag value (`parentFlag : Option
    Bool`, where `none` is "flag unset", `some b` is the concrete value `b`).
  * When the requested family is FOREIGN (`sameFamily = false`), the result is
    `none`: the flag does not apply, and nothing is carried.

No output component is left free: the result is the exact function of the two
inputs, so both the family branch and the carried value are pinned. -/
def problem_spec_addSubparsers
    (sameFamily : Bool) (parentFlag : Option Bool)
    (result : Option (Option Bool)) : Prop :=
  result = (if sameFamily then some parentFlag else none)
-- post-conditions-end

-- impl-start
def implementation_addSubparsers
    (sameFamily : Bool) (parentFlag : Option Bool) :
    Option (Option Bool) := Id.run do
  let mut carried : Option (Option Bool) := none
  if sameFamily then
    carried := some parentFlag
  return carried
-- impl-end

-- proof-start
theorem correct_addSubparsers :
    ∀ (sameFamily : Bool) (parentFlag : Option Bool),
      problem_spec_addSubparsers sameFamily parentFlag
        (implementation_addSubparsers sameFamily parentFlag) := by
  intro sameFamily parentFlag
  unfold problem_spec_addSubparsers implementation_addSubparsers
  cases sameFamily <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL functional equality: problem_spec_addSubparsers := result = (if sameFamily then some parentFlag else none). Output fully pinned as a function of both inputs (sameFamily : Bool, parentFlag : Option Bool) -> Option (Option Bool); no free component. used venv python for same_spec.

Same_spec: all 7 files (pos + atk_1..6) return True (axioms/pure/pre/post byte-identical; only impl region edited).

Positive control (gold impl) atk_pos.lean: bash scripts/lean_verify.sh atk_pos.lean -> EXIT 0 (verifies, no sorry). #print axioms correct_addSubparsers -> "'correct_addSubparsers' does not depend on any axioms" (clean, exit 0).

6 DISTINCT same-spec wrong impls, all run via lean_verify.sh (300s), concurrently in 2 batches of <=4:
- atk_1 (prepatch bug: same-family carries `some none`, drops parentFlag) -> EXIT 1. Prepatch reproduced.
- atk_2 (control-flow: branches swapped) -> EXIT 1.
- atk_3 (control-flow-effect: ignore sameFamily, always `some parentFlag`) -> EXIT 1. Proof goal `(pure (some parentFlag)).run = if false = true then...` unprovable.
- atk_4 (ungrounded-oracle echo: decide on parentFlag emptiness instead of sameFamily) -> EXIT 1.
- atk_5 (boundary: foreign case returns `some none` instead of `none`) -> EXIT 1.
- atk_6 (partial-domain: same-family carries parentFlag.map (!b), negated) -> EXIT 1.

Every wrong impl fails to typecheck with a genuine proof-state mismatch (not an edit typo) -> NO wrong impl closes with clean axioms, so patches={} (protocol step 2 vacuous: nothing to materialize/resolve).

Refinement audit: 4 legs, all R (op2 issubclass family test, op3 flag propagation) or I (op1 none-default, op4 return). axioms=[], deep_model_references=[], conf_skip=false. No A-consumed / A-reference / kind-3 legs. issubclass is modeled deeply as boolean input sameFamily (R, exercised in G-CONF against real issubclass), not axiomatized -> no A-leg correspondence to break. Correspondence holds.

Verdict SOUND: 6 attacks run, positive control verifies with clean axioms, none of the same-spec wrong impls verifies, so no verify-but-incorrect impl exists (no verify=>correct break).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
A command-line argument parser can spawn nested sub-parsers to dispatch
sub-commands. Such a parser carries a configuration flag that governs how it
reports argument errors to the user — for example, whether an invalid argument
yields a concise usage message or is surfaced directly as an exception.

When a parser constructs its sub-parsers, each sub-parser of the SAME family —
one that understands this configuration flag — should receive the parent's flag
value verbatim, so that argument-error reporting behaves consistently at every
nesting level. A sub-parser belonging to a FOREIGN family (one that does not
recognise the flag) receives nothing: the flag concept simply does not apply to
it.

The outcome is TOTAL: for any parent flag value and any requested sub-parser
family, construction yields a definite answer — either "a same-family sub-parser
carrying flag value v", or "a foreign sub-parser to which the flag does not
apply". It never fails to produce an answer.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The decision is a pure
-- computation over two inputs: whether the requested sub-parser family is the
-- same family that recognises the flag, and the parent's flag value. The
-- family test is modeled directly as a boolean input (a deep model of the
-- subclass relationship), and the downstream act of materialising the
-- sub-parser object is abstracted to the flag value the sub-parser ends up
-- carrying. Hence no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared helpers needed)
-- pure-end

-- post-conditions-start
/-- The outcome is TOTAL and fully pinned to the inputs.

  * When the requested sub-parser family is the SAME family that recognises the
    flag (`sameFamily = true`), the result is `some parentFlag`: a same-family
    sub-parser carrying EXACTLY the parent's flag value (`parentFlag : Option
    Bool`, where `none` is "flag unset", `some b` is the concrete value `b`).
  * When the requested family is FOREIGN (`sameFamily = false`), the result is
    `none`: the flag does not apply, and nothing is carried.

No output component is left free: the result is the exact function of the two
inputs, so both the family branch and the carried value are pinned. -/
def problem_spec_addSubparsers
    (sameFamily : Bool) (parentFlag : Option Bool)
    (result : Option (Option Bool)) : Prop :=
  result = (if sameFamily then some parentFlag else none)
-- post-conditions-end

-- impl-start
def implementation_addSubparsers
    (sameFamily : Bool) (parentFlag : Option Bool) :
    Option (Option Bool) := Id.run do
  let mut carried : Option (Option Bool) := none
  if sameFamily then
    carried := some parentFlag
  return carried
-- impl-end

-- proof-start
theorem correct_addSubparsers :
    ∀ (sameFamily : Bool) (parentFlag : Option Bool),
      problem_spec_addSubparsers sameFamily parentFlag
        (implementation_addSubparsers sameFamily parentFlag) := by
  intro sameFamily parentFlag
  unfold problem_spec_addSubparsers implementation_addSubparsers
  cases sameFamily <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL functional equality: problem_spec_addSubparsers := result = (if sameFamily then some parentFlag else none). Output fully pinned as a function of both inputs (sameFamily : Bool, parentFlag : Option Bool) -> Option (Option Bool); no free component. used venv python for same_spec.

Same_spec: all 7 files (pos + atk_1..6) return True (axioms/pure/pre/post byte-identical; only impl region edited).

Positive control (gold impl) atk_pos.lean: bash scripts/lean_verify.sh atk_pos.lean -> EXIT 0 (verifies, no sorry). #print axioms correct_addSubparsers -> "'correct_addSubparsers' does not depend on any axioms" (clean, exit 0).

6 DISTINCT same-spec wrong impls, all run via lean_verify.sh (300s), concurrently in 2 batches of <=4:
- atk_1 (prepatch bug: same-family carries `some none`, drops parentFlag) -> EXIT 1. Prepatch reproduced.
- atk_2 (control-flow: branches swapped) -> EXIT 1.
- atk_3 (control-flow-effect: ignore sameFamily, always `some parentFlag`) -> EXIT 1. Proof goal `(pure (some parentFlag)).run = if false = true then...` unprovable.
- atk_4 (ungrounded-oracle echo: decide on parentFlag emptiness instead of sameFamily) -> EXIT 1.
- atk_5 (boundary: foreign case returns `some none` instead of `none`) -> EXIT 1.
- atk_6 (partial-domain: same-family carries parentFlag.map (!b), negated) -> EXIT 1.

Every wrong impl fails to typecheck with a genuine proof-state mismatch (not an edit typo) -> NO wrong impl closes with clean axioms, so patches={} (protocol step 2 vacuous: nothing to materialize/resolve).

Refinement audit: 4 legs, all R (op2 issubclass family test, op3 flag propagation) or I (op1 none-default, op4 return). axioms=[], deep_model_references=[], conf_skip=false. No A-consumed / A-reference / kind-3 legs. issubclass is modeled deeply as boolean input sameFamily (R, exercised in G-CONF against real issubclass), not axiomatized -> no A-leg correspondence to break. Correspondence holds.

Verdict SOUND: 6 attacks run, positive control verifies with clean axioms, none of the same-spec wrong impls verifies, so no verify-but-incorrect impl exists (no verify=>correct break).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness break attempt FAILED — spec is faithful to real repo behavior.

Modeled function: CommandParser.add_subparsers (gold patch, django/core/management/base.py:75-83). Spec: problem_spec_addSubparsers = (result = if sameFamily then some parentFlag else none). Model: sameFamily:Bool = issubclass(parser_class, CommandParser); parentFlag:Option Bool = self.called_from_command_line (None<->none); result:Option(Option Bool) = observable carried flag of the constructed sub-parser (none = foreign, no attribute).

Rigor performed:
1. Differential test of the spec's exact function vs the REAL patched CommandParser.add_subparsers (verbatim CommandParser reconstructed + gold override with functools.partial + super().add_subparsers) driven live via add_subparsers(parser_class=cls).add_parser('x'), reading getattr(sub,'called_from_command_line'). Same 100k fuzz as conformance_check.py (seed 16454, 3 flag values x {CommandParser, CommandParserSubclass, ArgumentParser, ForeignParser}): 0 disagreements.
2. Edge probes NOT in the 100k harness — all agree with spec:
   - default parser_class omitted (=type(self)=CommandParser, same-family): carried == parentFlag (True). Spec = some parentFlag. Match.
   - value fidelity same-family for pf in {None,True,False}: carried is EXACTLY pf each time (None->None, True->True, False->False). Spec = some parentFlag. Match — no aliasing/coercion drift.
   - foreign (argparse.ArgumentParser): sub-parser has NO called_from_command_line attribute -> none. Spec = none. Match.

The spec is neither too strong nor too weak: it pins BOTH branches (same-family carries EXACTLY the parent value; foreign carries nothing) and matches the real callee on every tested input including the branches G-CONF omits. The abstraction (partial/super().add_subparsers -> 'the carried flag value') is exact for the observable modeled here.

Ancillary checks: Solution.lean compiles (lean_verify exit 0); #print axioms correct_addSubparsers => 'does not depend on any axioms' (no sorryAx, proof is real). same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True (spec region byte-identical; only impl+proof differ, prepatch returns some none for same-family which correctly violates the some parentFlag clause on parentFlag=some b). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorously verified for django__django-16454 (lean).

Mechanical G-LEAK screen (leakage.screen over the spec_view): PASSED, hard_failures=[]. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region byte-identical, so no impl/proof content leaks through the projected view.

Semantic judgment (G-PANEL-3): the spec view is strictly LESS specific than the public problem_statement, so it leaks nothing beyond it.
- problem_statement already publicly names CommandParser, add_subparsers().add_parser(), and states the fix explicitly: 'We can correct this by ensuring that the subparser action returned by add_subparsers() copies the relevant arguments through to constructed subparsers.'
- The spec view uses only domain-neutral abstractions: 'configuration flag', 'sub-parser family', SAME vs FOREIGN family, 'parent's flag value verbatim', 'foreign receives nothing', 'outcome is TOTAL'. The post-condition problem_spec_addSubparsers models the outcome as (if sameFamily then some parentFlag else none) over inputs (sameFamily : Bool, parentFlag : Option Bool).
- The spec view contains NONE of the gold-patch specifics: no issubclass, functools.partial, parser_class, called_from_command_line, kwargs, super().add_subparsers, no CommandParser identifier, no file path django/core/management/base.py, no diff markers, no bug/fix narration. Changed gold symbols {'add_subparsers','error'} do not appear as spec-view identifiers or in comments.
- The same-family/foreign branch is a faithful behavioral post-condition any solver would derive from the public statement (the flag propagates to like-kind subparsers), not a reproduction of the gold's issubclass check.

The abstract Option(Option Bool) modeling and the flag-propagation post-condition reveal only what the problem_statement already discloses. No spec-view line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

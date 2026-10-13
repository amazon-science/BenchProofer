# P2 adversarial audit — django__django-12276

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_useRequiredAttribute
     (isHidden initialPresent : Bool) : Bool := Id.run do
-  return (!isHidden) && (!initialPresent)
+  return (!isHidden)
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_useRequiredAttribute
     (isHidden initialPresent : Bool) : Bool := Id.run do
-  return (!isHidden) && (!initialPresent)
+  return (!isHidden) && initialPresent
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_useRequiredAttribute
     (isHidden initialPresent : Bool) : Bool := Id.run do
-  return (!isHidden) && (!initialPresent)
+  return if isHidden then true else (!initialPresent)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_useRequiredAttribute
     (isHidden initialPresent : Bool) : Bool := Id.run do
-  return (!isHidden) && (!initialPresent)
+  return (!isHidden) || (!initialPresent)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_useRequiredAttribute
     (isHidden initialPresent : Bool) : Bool := Id.run do
-  return (!isHidden) && (!initialPresent)
+  return true
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_useRequiredAttribute
     (isHidden initialPresent : Bool) : Bool := Id.run do
-  return (!isHidden) && (!initialPresent)
+  return (!initialPresent)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_useRequiredAttribute
     (isHidden initialPresent : Bool) : Bool := Id.run do
-  return (!isHidden) && (!initialPresent)
+  let base := isHidden; return base && (!initialPresent)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a file-upload input element should advertise itself as
*required* in the rendered HTML.

A form input element carries the HTML `required` marker according to a base
rule: a non-hidden input is, in principle, required (a hidden input never is).

For an input that accepts a file, there is an extra consideration. When an
initial value is already present (for example a file already stored on the
object being edited), the element must NOT be marked required: the user is
allowed to leave the field blank and keep the existing value. A truthy initial
value therefore suppresses the required marker even when the base rule would
otherwise request it.

The desired rule for a file input is thus:

  * if the input is hidden, it is never required;
  * otherwise, it is required exactly when no initial value is present;
  * a present (truthy) initial value always suppresses the required marker.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The base rule
-- (a non-hidden input is required) is modeled directly as a structural predicate
-- on the observable inputs (hidden-ness, presence of an initial value), so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The element is marked required exactly when the base rule applies (the input
is not hidden) AND no initial value is present (the initial value is not truthy).

* `isHidden` — whether the input element is hidden;
* `initialPresent` — whether a truthy initial value is already present;
* `result` — whether the rendered element should carry the required marker. -/
def problem_spec_useRequiredAttribute
    (isHidden initialPresent : Bool) (result : Bool) : Prop :=
  result = (!isHidden && !initialPresent)
-- post-conditions-end

-- impl-start
def implementation_useRequiredAttribute
    (isHidden initialPresent : Bool) : Bool := Id.run do
  return (!isHidden) && (!initialPresent)
-- impl-end

-- proof-start
theorem correct_useRequiredAttribute :
    ∀ (isHidden initialPresent : Bool),
      problem_spec_useRequiredAttribute isHidden initialPresent
        (implementation_useRequiredAttribute isHidden initialPresent) := by
  intro isHidden initialPresent
  unfold problem_spec_useRequiredAttribute implementation_useRequiredAttribute
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec problem_spec_useRequiredAttribute = (result = (!isHidden && !initialPresent)) is a TOTAL functional equation over the finite Bool x Bool domain (4 points), fully pinning the impl. Any deviation on any point makes correct_useRequiredAttribute's rfl fail, so no wrong impl can produce a closing clean-axiom proof -> the mandatory materialize-and-resolve obligation (which fires only for a same-spec wrong impl whose proof CLOSES with clean axioms) is never triggered. patches={} accordingly.

Protocol executed (all commands; verify via `bash scripts/lean_verify.sh <f>`; same_spec via swebench_unified.markers.same_spec with lean backend):

same_spec check: pos_control + atk_1..7 ALL True (byte-identical axioms/pure/pre/post; only impl region edited).

Positive control (gold impl, pos_control.lean): EXIT=0 (verifies, no sorry). Explicit #print axioms correct_useRequiredAttribute -> 'does not depend on any axioms' (clean, EXIT=0).

7 DISTINCT same-spec wrong impls, run concurrently in two batches of 4 (background Bash jobs):
- atk_1 `return (!isHidden)` (PREPATCH BUG: ignores initialPresent; the exact `_prepatch` impl) -> EXIT=1, genuine rfl failure at line 61 -> spec correctly rejects the original bug (prepatch_reproduced=true).
- atk_2 `return (!isHidden) && initialPresent` (axis/negation swap on initial) -> EXIT=1, rfl fail line 61.
- atk_3 `return if isHidden then true else (!initialPresent)` (control-flow-effect; wrong on isHidden=true slice) -> EXIT=1, rfl fail line 61.
- atk_4 `return (!isHidden) || (!initialPresent)` (OR instead of AND) -> EXIT=1, rfl fail line 61.
- atk_5 `return true` (constant / partial-domain trivial oracle) -> EXIT=1, rfl fail line 61.
- atk_6 `return (!initialPresent)` (ignores isHidden entirely) -> EXIT=1, rfl fail line 61.
- atk_7 `let base := isHidden; return base && (!initialPresent)` (ungrounded/echo-shaped let, wrong: uses isHidden not !isHidden) -> EXIT=1, rfl fail line 61.

All failures confirmed to be genuine spec-mismatch `Tactic rfl failed` errors at the correctness proof (line 61), not unrelated compile errors. No wrong impl verifies -> none needs a materialized faithful patch / resolve run.

refinement.md audit: single impl leg (op 1, tag R) decomposed 1a R (!isHidden <-> super().use_required_attribute(initial) = not self.is_hidden), 1b R (!initialPresent <-> not initial truthiness), 1c I (&& <-> and). NO A-legs: axioms region is EMPTY and G-AX skips -- justified per SPEC_GUIDE §3 (base rule `not self.is_hidden` is short, unchanged, inlined DEEPLY as structural term !isHidden rather than axiomatized) and §0.7 (no dead axiom). No kind-3 legs. Correspondence to real callees (Widget.use_required_attribute at widgets.py:275-276; is_hidden at 209-211; the ADDED FileInput.use_required_attribute) holds per mapping.md symbol bindings at base_commit 53d8646f. A-leg correspondence audit is vacuously satisfied (no A-legs).

>=5 attacks run, none breaks the spec -> SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a file-upload input element should advertise itself as
*required* in the rendered HTML.

A form input element carries the HTML `required` marker according to a base
rule: a non-hidden input is, in principle, required (a hidden input never is).

For an input that accepts a file, there is an extra consideration. When an
initial value is already present (for example a file already stored on the
object being edited), the element must NOT be marked required: the user is
allowed to leave the field blank and keep the existing value. A truthy initial
value therefore suppresses the required marker even when the base rule would
otherwise request it.

The desired rule for a file input is thus:

  * if the input is hidden, it is never required;
  * otherwise, it is required exactly when no initial value is present;
  * a present (truthy) initial value always suppresses the required marker.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The base rule
-- (a non-hidden input is required) is modeled directly as a structural predicate
-- on the observable inputs (hidden-ness, presence of an initial value), so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The element is marked required exactly when the base rule applies (the input
is not hidden) AND no initial value is present (the initial value is not truthy).

* `isHidden` — whether the input element is hidden;
* `initialPresent` — whether a truthy initial value is already present;
* `result` — whether the rendered element should carry the required marker. -/
def problem_spec_useRequiredAttribute
    (isHidden initialPresent : Bool) (result : Bool) : Prop :=
  result = (!isHidden && !initialPresent)
-- post-conditions-end

-- impl-start
def implementation_useRequiredAttribute
    (isHidden initialPresent : Bool) : Bool := Id.run do
  return (!isHidden) && (!initialPresent)
-- impl-end

-- proof-start
theorem correct_useRequiredAttribute :
    ∀ (isHidden initialPresent : Bool),
      problem_spec_useRequiredAttribute isHidden initialPresent
        (implementation_useRequiredAttribute isHidden initialPresent) := by
  intro isHidden initialPresent
  unfold problem_spec_useRequiredAttribute implementation_useRequiredAttribute
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec problem_spec_useRequiredAttribute = (result = (!isHidden && !initialPresent)) is a TOTAL functional equation over the finite Bool x Bool domain (4 points), fully pinning the impl. Any deviation on any point makes correct_useRequiredAttribute's rfl fail, so no wrong impl can produce a closing clean-axiom proof -> the mandatory materialize-and-resolve obligation (which fires only for a same-spec wrong impl whose proof CLOSES with clean axioms) is never triggered. patches={} accordingly.

Protocol executed (all commands; verify via `bash scripts/lean_verify.sh <f>`; same_spec via swebench_unified.markers.same_spec with lean backend):

same_spec check: pos_control + atk_1..7 ALL True (byte-identical axioms/pure/pre/post; only impl region edited).

Positive control (gold impl, pos_control.lean): EXIT=0 (verifies, no sorry). Explicit #print axioms correct_useRequiredAttribute -> 'does not depend on any axioms' (clean, EXIT=0).

7 DISTINCT same-spec wrong impls, run concurrently in two batches of 4 (background Bash jobs):
- atk_1 `return (!isHidden)` (PREPATCH BUG: ignores initialPresent; the exact `_prepatch` impl) -> EXIT=1, genuine rfl failure at line 61 -> spec correctly rejects the original bug (prepatch_reproduced=true).
- atk_2 `return (!isHidden) && initialPresent` (axis/negation swap on initial) -> EXIT=1, rfl fail line 61.
- atk_3 `return if isHidden then true else (!initialPresent)` (control-flow-effect; wrong on isHidden=true slice) -> EXIT=1, rfl fail line 61.
- atk_4 `return (!isHidden) || (!initialPresent)` (OR instead of AND) -> EXIT=1, rfl fail line 61.
- atk_5 `return true` (constant / partial-domain trivial oracle) -> EXIT=1, rfl fail line 61.
- atk_6 `return (!initialPresent)` (ignores isHidden entirely) -> EXIT=1, rfl fail line 61.
- atk_7 `let base := isHidden; return base && (!initialPresent)` (ungrounded/echo-shaped let, wrong: uses isHidden not !isHidden) -> EXIT=1, rfl fail line 61.

All failures confirmed to be genuine spec-mismatch `Tactic rfl failed` errors at the correctness proof (line 61), not unrelated compile errors. No wrong impl verifies -> none needs a materialized faithful patch / resolve run.

refinement.md audit: single impl leg (op 1, tag R) decomposed 1a R (!isHidden <-> super().use_required_attribute(initial) = not self.is_hidden), 1b R (!initialPresent <-> not initial truthiness), 1c I (&& <-> and). NO A-legs: axioms region is EMPTY and G-AX skips -- justified per SPEC_GUIDE §3 (base rule `not self.is_hidden` is short, unchanged, inlined DEEPLY as structural term !isHidden rather than axiomatized) and §0.7 (no dead axiom). No kind-3 legs. Correspondence to real callees (Widget.use_required_attribute at widgets.py:275-276; is_hidden at 209-211; the ADDED FileInput.use_required_attribute) holds per mapping.md symbol bindings at base_commit 53d8646f. A-leg correspondence audit is vacuously satisfied (no A-legs).

>=5 attacks run, none breaks the spec -> SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-12276, Lean bundle, modeling FileInput.use_required_attribute (method ADDED by the gold patch).

### Checks performed
1. Spec byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) == True. The postcondition region (problem_spec_useRequiredAttribute) is unchanged between bug and fix variants; only the impl region differs. No spec drift between variants.
2. Lean verify: scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). #print axioms correct_useRequiredAttribute -> 'does not depend on any axioms' (no sorryAx; proof is genuine, rfl over Bool).
3. Real repo (base 53d8646f, gold patch) inspected in widgets.py:
   - Widget.use_required_attribute(self, initial) = `return not self.is_hidden` (line 274-276).
   - Patch adds FileInput.use_required_attribute (line 389-390): `return super().use_required_attribute(initial) and not initial`.
   - super() resolves Input->Widget, so post-patch behavior = (not self.is_hidden) and (not initial).

FAITHFULNESS VERDICT — FAITHFUL:
- Spec: result = (!isHidden && !initialPresent), with isHidden<->self.is_hidden, initialPresent<->bool(initial).
- Real: (not self.is_hidden) and (not initial). `not initial` reads only truthiness of initial, so `not initial` == !initialPresent under the stated bijection; `not self.is_hidden` == !isHidden. Both operands are bools, so Python `and` == Lean `&&` (identical truth tables). Over the full Bool x Bool domain (4 points) spec == real on every input; abstracting initial to bool(initial) loses nothing the method reads.
- isHidden is modeled as a FREE Boolean (the real FileInput has is_hidden==False always, since input_type=='file'). This makes the spec BROADER (frame-pinning the full base rule), not stronger: on every point of the extended domain the spec still equals what the real method computes. No over-strengthening; no input exists where the modeled function rejects a value the real callee would produce.
- The spec correctly excludes the prepatch bug (isHidden=false, initialPresent=true): spec demands false, prepatch (inherited base rule) yields true — matching F2P (use_required_attribute('resume.txt') is False). This is a genuine discriminating slice, confirming the spec is neither too weak nor too strong.

No diverging input found; spec is a faithful, exact model of the post-patch callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec == True over the lean backend); Solution.lean compiles under lean_verify.sh (exit 0). The spec view exposes only the imports, the docstring, empty axioms/pure regions, and the post-conditions predicate `result = (!isHidden && !initialPresent)`; the impl and proof regions are elided to placeholders. Everything visible is derivable from the public problem_statement, which already states the whole intent: 'FileInput shouldn't display required attribute when initial data exists' and proposes making required not be output when a file is already set. The spec's docstring/prose ('a truthy initial value suppresses the required marker'; 'required exactly when no initial value is present') is a faithful abstract restatement of that public behavior — i.e. it IS the specification, not a leak of the implementation. Crucially, the spec view contains none of the gold-patch specifics: no `super().use_required_attribute(initial) and not initial` code, no `FileInput`/`ClearableFileInput`/`Widget` symbol names, no mention of moving/overriding the method. Those details live only in mapping.md and refinement.md, which are NOT part of the spec view. The `isHidden` base-rule component models pre-existing unchanged behavior (not the gold edit), so it cannot leak the edit. No line reveals the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

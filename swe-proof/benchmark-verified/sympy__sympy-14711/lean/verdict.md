# P2 adversarial audit — sympy__sympy-14711

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,8 +70,6 @@
 def implementation_vectorAdd
     (selfArgs : List Int) (other : AddOperand) : Except Unit (List Int) :=
   Id.run do
-    if isAdditiveZero other then
-      return Except.ok selfArgs
     match other with
     | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
     | _                 => return Except.error ()
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     if isAdditiveZero other then
       return Except.ok selfArgs
     match other with
-    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
+    | .vector otherArgs => return Except.ok (otherArgs ++ selfArgs)
     | _                 => return Except.error ()
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,11 +70,7 @@
 def implementation_vectorAdd
     (selfArgs : List Int) (other : AddOperand) : Except Unit (List Int) :=
   Id.run do
-    if isAdditiveZero other then
-      return Except.ok selfArgs
-    match other with
-    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
-    | _                 => return Except.error ()
+    return Except.ok selfArgs
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,8 @@
       return Except.ok selfArgs
     match other with
     | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
-    | _                 => return Except.error ()
+    | .nonVector        => return Except.ok selfArgs
+    | .scalarZero       => return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,11 +70,10 @@
 def implementation_vectorAdd
     (selfArgs : List Int) (other : AddOperand) : Except Unit (List Int) :=
   Id.run do
-    if isAdditiveZero other then
-      return Except.ok selfArgs
     match other with
     | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
-    | _                 => return Except.error ()
+    | .scalarZero       => return Except.error ()
+    | .nonVector        => return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,11 +70,10 @@
 def implementation_vectorAdd
     (selfArgs : List Int) (other : AddOperand) : Except Unit (List Int) :=
   Id.run do
-    if isAdditiveZero other then
-      return Except.ok selfArgs
     match other with
     | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
-    | _                 => return Except.error ()
+    | .scalarZero       => return Except.ok selfArgs
+    | .nonVector        => return Except.ok []
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
     if isAdditiveZero other then
       return Except.ok selfArgs
     match other with
-    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
+    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs ++ otherArgs)
     | _                 => return Except.error ()
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Adding a value to a vector.

A vector is carried by its list of basis-weighted components (its *argument
list*). The sum of a vector with some other value is defined by cases on that
value:

* adding another vector appends the two component lists (the combined list is
  what is handed to the vector constructor downstream);
* adding the additive identity — the scalar zero — leaves the vector unchanged,
  yielding the vector's own component list;
* adding anything else is rejected as a type error.

In particular, the additive identity is a valid right operand: summing a vector
with zero must SUCCEED and return the original vector unchanged — it must not be
treated as an invalid operand and rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operand
-- classification (another vector / the additive identity / anything else) and
-- the resulting component list are modeled structurally over the observable
-- shape of the operand, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The right-hand operand of a vector addition, classified by its shape.

* `vector args` — another vector, carried by its component (argument) list;
* `scalarZero`  — the scalar zero (the additive identity);
* `nonVector`   — any other value, which is not a valid addend. -/
inductive AddOperand where
  | vector (args : List Int)
  | scalarZero
  | nonVector
deriving DecidableEq, Repr

/-- Whether an operand is equal to the additive identity. The scalar zero is the
identity; so is a vector carrying no components (an empty component list), since
it represents the zero vector. -/
def isAdditiveZero : AddOperand → Bool
  | .scalarZero => true
  | .vector []  => true
  | _           => false
-- pure-end

-- post-conditions-start
/-- The result of adding `other` to a vector with component list `selfArgs`.

The result is the component list handed to the vector constructor, or a type
error (`Except.error`) when the operand is not a valid addend:

* another vector contributes its components, appended after `selfArgs`;
* the additive identity (the scalar zero) leaves the vector unchanged, so the
  result is exactly `selfArgs`;
* any other value is rejected as a type error. -/
def problem_spec_vectorAdd
    (selfArgs : List Int) (other : AddOperand)
    (result : Except Unit (List Int)) : Prop :=
  match other with
  | .vector otherArgs => result = Except.ok (selfArgs ++ otherArgs)
  | .scalarZero       => result = Except.ok selfArgs
  | .nonVector        => result = Except.error ()
-- post-conditions-end

-- impl-start
def implementation_vectorAdd
    (selfArgs : List Int) (other : AddOperand) : Except Unit (List Int) :=
  Id.run do
    if isAdditiveZero other then
      return Except.ok selfArgs
    match other with
    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
    | _                 => return Except.error ()
-- impl-end
-- proof-start
theorem correct_vectorAdd :
    ∀ (selfArgs : List Int) (other : AddOperand),
      problem_spec_vectorAdd selfArgs other
        (implementation_vectorAdd selfArgs other) := by
  intro selfArgs other
  unfold problem_spec_vectorAdd implementation_vectorAdd
  cases other with
  | vector otherArgs =>
    cases otherArgs with
    | nil =>
      simp only [isAdditiveZero, Id.run, if_true, List.append_nil, pure]
    | cons a as => rfl
  | scalarZero => rfl
  | nonVector => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_vectorAdd is a TOTAL FUNCTION GRAPH: each of the 3 AddOperand constructors is pinned to a single result equality (no free vars, no disjunction, singleton error payload ()). Therefore any implementation_vectorAdd whose correct_vectorAdd closes must be extensionally equal to the spec on every input -- in particular scalarZero -> Except.ok selfArgs (the resolving no-op) and nonVector -> Except.error (). No closing-but-wrong impl exists; hence no faithful patch to resolve-run (requirement vacuously met).

Same-spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (lines 1-68 byte-identical; only impl region edited).

Positive control (gold impl) pos.lean: `bash scripts/lean_verify.sh pos.lean` -> EXIT=0. Axioms (pos_ax.lean, #print axioms correct_vectorAdd): 'correct_vectorAdd' depends on axioms: [propext, Quot.sound] -- clean, no sorryAx.

Attacks (all `bash scripts/lean_verify.sh atk_N.lean`, run concurrently in 2 batches of 4):
- atk_1 EXIT=1 (prepatch bug: drop guard, scalarZero falls to Except.error -- the actual non-resolving bug). Goal reduces to Except.ok selfArgs = Except.error () on scalarZero: false.
- atk_2 EXIT=1 (prepend: otherArgs ++ selfArgs). vector leg needs otherArgs++selfArgs = selfArgs++otherArgs: false in general.
- atk_3 EXIT=1 (partial-domain: always Except.ok selfArgs). nonVector leg needs Except.ok selfArgs = Except.error (): false.
- atk_4 EXIT=1 (boundary swap: nonVector->ok selfArgs, scalarZero->error). Both diverge.
- atk_5 EXIT=1 (ungrounded-oracle echo: scalarZero->Except.error). scalarZero needs Except.error () = Except.ok selfArgs: false.
- atk_6 EXIT=1 (wrong ok payload: nonVector->Except.ok []). nonVector needs Except.ok [] = Except.error (): false.
- atk_7 EXIT=1 (arithmetic-off: selfArgs ++ otherArgs ++ otherArgs). vector leg diverges.

Robustness: re-ran atk_1 with maximal automation `cases other <;> simp_all [Id.run] <;> first | rfl | decide | omega` (atk_1_strong.lean) -> EXIT=1, omega could not prove the goal -- confirms genuinely FALSE goals (constructor-distinct / list-order equalities), not weak-tactic false negatives.

No attack closed with clean axioms, so NO faithful patch required a run_resolve; the verify=>correct obligation holds by the function-graph argument plus the 7 executed refutations.

refinement.md / mapping.md AUDIT: all 3 legs tagged R (type refinement) -- no A-consumed, no A-reference, no kind-3 ungrounded oracle. axioms region is EMPTY (G-AX skips, corroborated by meta.json). The unchanged callee _check_vector (identity on Vector / TypeError otherwise) is correctly FOLDED into the AddOperand classification and the .nonVector -> Except.error leg, not separately axiomatized -- correspondence to the real callee holds (post-patch __add__ adds only the `if other == 0: return self` guard, matching op #1 isAdditiveZero guard). The .vector [] overlap (isAdditiveZero true) is behaviour-preserving since selfArgs ++ [] = selfArgs. A-leg audit: N/A (none present); model<->patch correspondence verified sound.

prepatch_reproduced=true: atk_1 IS the faithful Solution_prepatch impl (guard dropped); it fails to verify (exit 1), i.e. the prepatch bug does NOT satisfy the spec, as required (G-DIFF also records Solution_prepatch verification failed).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Adding a value to a vector.

A vector is carried by its list of basis-weighted components (its *argument
list*). The sum of a vector with some other value is defined by cases on that
value:

* adding another vector appends the two component lists (the combined list is
  what is handed to the vector constructor downstream);
* adding the additive identity — the scalar zero — leaves the vector unchanged,
  yielding the vector's own component list;
* adding anything else is rejected as a type error.

In particular, the additive identity is a valid right operand: summing a vector
with zero must SUCCEED and return the original vector unchanged — it must not be
treated as an invalid operand and rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operand
-- classification (another vector / the additive identity / anything else) and
-- the resulting component list are modeled structurally over the observable
-- shape of the operand, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The right-hand operand of a vector addition, classified by its shape.

* `vector args` — another vector, carried by its component (argument) list;
* `scalarZero`  — the scalar zero (the additive identity);
* `nonVector`   — any other value, which is not a valid addend. -/
inductive AddOperand where
  | vector (args : List Int)
  | scalarZero
  | nonVector
deriving DecidableEq, Repr

/-- Whether an operand is equal to the additive identity. The scalar zero is the
identity; so is a vector carrying no components (an empty component list), since
it represents the zero vector. -/
def isAdditiveZero : AddOperand → Bool
  | .scalarZero => true
  | .vector []  => true
  | _           => false
-- pure-end

-- post-conditions-start
/-- The result of adding `other` to a vector with component list `selfArgs`.

The result is the component list handed to the vector constructor, or a type
error (`Except.error`) when the operand is not a valid addend:

* another vector contributes its components, appended after `selfArgs`;
* the additive identity (the scalar zero) leaves the vector unchanged, so the
  result is exactly `selfArgs`;
* any other value is rejected as a type error. -/
def problem_spec_vectorAdd
    (selfArgs : List Int) (other : AddOperand)
    (result : Except Unit (List Int)) : Prop :=
  match other with
  | .vector otherArgs => result = Except.ok (selfArgs ++ otherArgs)
  | .scalarZero       => result = Except.ok selfArgs
  | .nonVector        => result = Except.error ()
-- post-conditions-end

-- impl-start
def implementation_vectorAdd
    (selfArgs : List Int) (other : AddOperand) : Except Unit (List Int) :=
  Id.run do
    if isAdditiveZero other then
      return Except.ok selfArgs
    match other with
    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
    | _                 => return Except.error ()
-- impl-end
-- proof-start
theorem correct_vectorAdd :
    ∀ (selfArgs : List Int) (other : AddOperand),
      problem_spec_vectorAdd selfArgs other
        (implementation_vectorAdd selfArgs other) := by
  intro selfArgs other
  unfold problem_spec_vectorAdd implementation_vectorAdd
  cases other with
  | vector otherArgs =>
    cases otherArgs with
    | nil =>
      simp only [isAdditiveZero, Id.run, if_true, List.append_nil, pure]
    | cons a as => rfl
  | scalarZero => rfl
  | nonVector => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_vectorAdd is a TOTAL FUNCTION GRAPH: each of the 3 AddOperand constructors is pinned to a single result equality (no free vars, no disjunction, singleton error payload ()). Therefore any implementation_vectorAdd whose correct_vectorAdd closes must be extensionally equal to the spec on every input -- in particular scalarZero -> Except.ok selfArgs (the resolving no-op) and nonVector -> Except.error (). No closing-but-wrong impl exists; hence no faithful patch to resolve-run (requirement vacuously met).

Same-spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (lines 1-68 byte-identical; only impl region edited).

Positive control (gold impl) pos.lean: `bash scripts/lean_verify.sh pos.lean` -> EXIT=0. Axioms (pos_ax.lean, #print axioms correct_vectorAdd): 'correct_vectorAdd' depends on axioms: [propext, Quot.sound] -- clean, no sorryAx.

Attacks (all `bash scripts/lean_verify.sh atk_N.lean`, run concurrently in 2 batches of 4):
- atk_1 EXIT=1 (prepatch bug: drop guard, scalarZero falls to Except.error -- the actual non-resolving bug). Goal reduces to Except.ok selfArgs = Except.error () on scalarZero: false.
- atk_2 EXIT=1 (prepend: otherArgs ++ selfArgs). vector leg needs otherArgs++selfArgs = selfArgs++otherArgs: false in general.
- atk_3 EXIT=1 (partial-domain: always Except.ok selfArgs). nonVector leg needs Except.ok selfArgs = Except.error (): false.
- atk_4 EXIT=1 (boundary swap: nonVector->ok selfArgs, scalarZero->error). Both diverge.
- atk_5 EXIT=1 (ungrounded-oracle echo: scalarZero->Except.error). scalarZero needs Except.error () = Except.ok selfArgs: false.
- atk_6 EXIT=1 (wrong ok payload: nonVector->Except.ok []). nonVector needs Except.ok [] = Except.error (): false.
- atk_7 EXIT=1 (arithmetic-off: selfArgs ++ otherArgs ++ otherArgs). vector leg diverges.

Robustness: re-ran atk_1 with maximal automation `cases other <;> simp_all [Id.run] <;> first | rfl | decide | omega` (atk_1_strong.lean) -> EXIT=1, omega could not prove the goal -- confirms genuinely FALSE goals (constructor-distinct / list-order equalities), not weak-tactic false negatives.

No attack closed with clean axioms, so NO faithful patch required a run_resolve; the verify=>correct obligation holds by the function-graph argument plus the 7 executed refutations.

refinement.md / mapping.md AUDIT: all 3 legs tagged R (type refinement) -- no A-consumed, no A-reference, no kind-3 ungrounded oracle. axioms region is EMPTY (G-AX skips, corroborated by meta.json). The unchanged callee _check_vector (identity on Vector / TypeError otherwise) is correctly FOLDED into the AddOperand classification and the .nonVector -> Except.error leg, not separately axiomatized -- correspondence to the real callee holds (post-patch __add__ adds only the `if other == 0: return self` guard, matching op #1 isAdditiveZero guard). The .vector [] overlap (isAdditiveZero true) is behaviour-preserving since selfArgs ++ [] = selfArgs. A-leg audit: N/A (none present); model<->patch correspondence verified sound.

prepatch_reproduced=true: atk_1 IS the faithful Solution_prepatch impl (guard dropped); it fails to verify (exit 1), i.e. the prepatch bug does NOT satisfy the spec, as required (G-DIFF also records Solution_prepatch verification failed).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verification performed: (a) scripts/lean_verify.sh on Solution.lean -> exit 0 (compiles, no sorry). (b) #print axioms correct_vectorAdd -> [propext, Quot.sound]; NO sorryAx, proof is genuine. (c) markers.same_spec(Solution, Solution_prepatch, LeanBackend.language) -> True: spec regions (axioms/pure/pre/post-conditions) byte-identical; only impl+proof differ (prepatch drops the leading isAdditiveZero guard, the injected bug). (d) Confirmed against real repo @ base_commit c6753448b5: __add__ pre-patch = 'other=_check_vector(other); return Vector(self.args+other.args)'; gold patch.diff adds 'if other==0: return self'; _check_vector raises TypeError('A Vector must be supplied') on non-Vector; __eq__ maps other==0 to Vector so empty-vector==0. All consistent with mapping.md/refinement.md. The spec is neither too strong nor too weak: post is a total case-split with equality on each branch (result = ...), and every branch matches the real post-patch callee modulo the declared, patch-orthogonal constructor abstraction. FAITHFUL.

Counterexample / evidence:

```
None that constitutes a defect. The divergence above is an EXPLICITLY declared abstraction boundary, not spec drift: (1) the collapse/zero-drop is performed by Vector.__init__, which is UNCHANGED by the patch and orthogonal to the additive-identity fix; (2) the model abstracts the component payload to opaque Int tokens, a resolution below which same-frame collapse is invisible by design; (3) the model faithfully captures self.args+other.args, the exact list handed to that unchanged constructor. On the CHANGED decision the model matches the real callee on every operand class: scalar 0 -> ok(selfArgs) (returns self); non-vector non-zero -> error (_check_vector raises TypeError); vector -> combine args; .vector [] overlap coincides with the identity branch since selfArgs++[]=selfArgs.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction assessment for sympy__sympy-14711 (lean). Gold edit: add guard `if other == 0: return self` to Vector.__add__.

Substrate verified:
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True: spec region (imports/docstring/axioms/pure/post-conditions) byte-identical between pre- and post-patch; only impl+proof differ (pre-patch drops the leading isAdditiveZero guard = the original bug). Correct paired-bundle structure.
- meta G-LEAK lexical screen = pass ('spec view clean'); code_version dceaf4cb9.

Leakage judgment: NO-LEAKAGE. The PUBLIC problem_statement is already maximally disclosive of the fix: its traceback quotes vector.py __add__ line 60 verbatim as `#if other == 0: return self` (the EXACT commented-out fix), names _check_vector raising TypeError('A Vector must be supplied') on the scalar 0, and pinpoints file/function. Everything the spec view expresses about the fix is a strict subset of what problem_statement already states.

The spec view (docstring + post-conditions region) says, in abstract Lean terms, that the additive identity must succeed and return the vector unchanged (.scalarZero => result = Except.ok selfArgs) rather than error. This is the required post-condition of any faithful specification, not a source-level disclosure: it names no Python file/line, no guard syntax, no _check_vector, no Vector class. It does not go beyond the public problem_statement (which discloses the literal patch line). No spec-view line reconstructs the gold edit beyond what problem_statement already contains. The impl and proof regions (where the actual fix-vs-bug lives) are elided from the spec view.

Note: I do NOT evaluate hints_text per instructions; comparison is spec view vs public problem_statement only.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

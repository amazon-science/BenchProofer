# P2 adversarial audit — django__django-15277

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec pins the entire output by full list-equality (result = base ++ (match maxLength with | none => [] | some n => [Validator.lengthBound (some n)])), which admits exactly one satisfying output per input (maxLength, base). Any type-matching impl whose correct_ closes is therefore extensionally equal to the gold impl on every input, so its faithful patch resolves identically. No closing-but-not-resolving impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,8 +54,7 @@
 def implementation_buildFieldValidators
     (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
   let mut validators := base
-  if maxLength.isSome then
-    validators := validators ++ [Validator.lengthBound maxLength]
+  validators := validators ++ [Validator.lengthBound maxLength]
   return validators
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,10 @@
 
 -- impl-start
 def implementation_buildFieldValidators
-    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
-  let mut validators := base
-  if maxLength.isSome then
-    validators := validators ++ [Validator.lengthBound maxLength]
-  return validators
+    (maxLength : Option Int) (base : List Validator) : List Validator :=
+  match maxLength with
+  | none => base
+  | some n => base ++ [Validator.lengthBound (some (n + 1))]
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,10 @@
 
 -- impl-start
 def implementation_buildFieldValidators
-    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
-  let mut validators := base
-  if maxLength.isSome then
-    validators := validators ++ [Validator.lengthBound maxLength]
-  return validators
+    (maxLength : Option Int) (base : List Validator) : List Validator :=
+  match maxLength with
+  | none => base
+  | some n => [Validator.lengthBound (some n)] ++ base
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,10 @@
 
 -- impl-start
 def implementation_buildFieldValidators
-    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
-  let mut validators := base
-  if maxLength.isSome then
-    validators := validators ++ [Validator.lengthBound maxLength]
-  return validators
+    (maxLength : Option Int) (base : List Validator) : List Validator :=
+  match maxLength with
+  | none => base ++ [Validator.basic 0]
+  | some n => base ++ [Validator.lengthBound (some n)]
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,8 @@
 
 -- impl-start
 def implementation_buildFieldValidators
-    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
-  let mut validators := base
-  if maxLength.isSome then
-    validators := validators ++ [Validator.lengthBound maxLength]
-  return validators
+    (maxLength : Option Int) (base : List Validator) : List Validator :=
+  base ++ [Validator.lengthBound (some 0)]
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,8 @@
 
 -- impl-start
 def implementation_buildFieldValidators
-    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
-  let mut validators := base
-  if maxLength.isSome then
-    validators := validators ++ [Validator.lengthBound maxLength]
-  return validators
+    (maxLength : Option Int) (base : List Validator) : List Validator :=
+  base
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,10 @@
 
 -- impl-start
 def implementation_buildFieldValidators
-    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
-  let mut validators := base
-  if maxLength.isSome then
-    validators := validators ++ [Validator.lengthBound maxLength]
-  return validators
+    (maxLength : Option Int) (base : List Validator) : List Validator :=
+  match maxLength with
+  | none => base
+  | some _ => base ++ [Validator.basic 0]
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the list of validators attached to a string-valued field.

A string field may declare an optional maximum length. Independent of that, the
field already carries a list of validators (those provided for its type together
with any supplied explicitly). During construction the field augments that list
with a length-bound validator that enforces the declared maximum length.

A length-bound validator is only meaningful when an actual maximum length is
declared: it carries the declared bound and compares candidate values against it.
When no maximum length is declared there is no bound to enforce, so a length-bound
validator carrying an absent bound would be inoperable. Accordingly, the
length-bound validator is appended exactly when — and only when — a maximum
length is declared; the incoming validators are preserved unchanged, in
order, in every case.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- length-bound validator's construction is the operation governed here, so it is
-- modeled structurally (its presence/absence in the list and the bound it
-- carries); no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A validator attached to a field.
* `basic tag` — any validator whose internal behavior is irrelevant here; `tag`
  distinguishes distinct such validators.
* `lengthBound limit` — a validator that enforces a maximum length, carrying that
  length as `limit`. A `lengthBound none` carries no usable bound. -/
inductive Validator where
  | basic (tag : Nat)
  | lengthBound (limit : Option Int)
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The resulting validator list is the incoming list of validators with a
length-bound validator appended exactly when a maximum length is declared. When a
maximum length `n` is declared, the appended validator carries the bound `n`; when
none is declared, nothing is appended. In both cases the incoming validators are
preserved unchanged and in order as a prefix. -/
def problem_spec_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) (result : List Validator) : Prop :=
  result = base ++ (match maxLength with
                    | none   => []
                    | some n => [Validator.lengthBound (some n)])
-- post-conditions-end

-- impl-start
def implementation_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) : List Validator :=
  match maxLength with
  | none => base
  | some n => base ++ [Validator.lengthBound (some n)]
-- impl-end

-- proof-start
theorem correct_buildFieldValidators :
    ∀ (maxLength : Option Int) (base : List Validator),
      problem_spec_buildFieldValidators maxLength base
        (implementation_buildFieldValidators maxLength base) := by
  intro maxLength base
  unfold implementation_buildFieldValidators problem_spec_buildFieldValidators
  cases maxLength with
  | none => simp [Id.run, bind, pure]
  | some n => simp [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

All 7 attacks are same_spec=True (spec/axiom/pure/pre/post byte-identical; only impl region edited), confirmed via swebench_unified.markers.same_spec on the lean backend. Verifications run concurrently (batches of 4) via scripts/lean_verify.sh.

### RESULTS (exit code from lean_verify.sh):
- pos.lean (alt-correct, pattern-match instead of Id.run mutation): EXIT 0 (verifies). #print axioms correct_buildFieldValidators => [propext] only (no sorryAx, clean). This is the required positive control.
- atk_1 (prepatch bug: unconditional `base ++ [lengthBound maxLength]`): EXIT 1 (fails to close). Reproduces the prepatch bug — on maxLength=none it yields base ++ [lengthBound none] but spec requires base. prepatch_reproduced=true.
- atk_2 (boundary: `some (n+1)` wrong bound): EXIT 1.
- atk_3 (control-flow-effect: reversed order, prepend `[lengthBound (some n)] ++ base`): EXIT 1.
- atk_4 (partial-domain: appends `basic 0` on none branch instead of nothing): EXIT 1.
- atk_5 (ungrounded-oracle echo: always append `lengthBound (some 0)`): EXIT 1.
- atk_6 (no append ever: `base`): EXIT 1.
- atk_7 (wrong validator kind: append `basic 0` on some branch): EXIT 1.

Step-2 obligation: patches only need materializing+resolving for wrong impls whose proof CLOSES with clean axioms. ZERO wrong impls closed, so there is no closing-clean-axiom impl to falsify against the harness — patches={}. No resolve run is applicable/required; nothing is left uncompleted.

WHY NO CLOSING WRONG IMPL EXISTS: the post-condition is a full-output equality to an input-grounded expression, so exactly one output satisfies it per input. correct_ is a universally-quantified equality; an impl that differs from gold on any input makes it a false proposition, unprovable in Lean's consistent logic. The axioms block is empty (no opaque/axiom callee) — the MaxLengthValidator construction is modeled DEEPLY (presence + carried Option Int bound), so there is no under-constrained oracle/axiom to abuse. No degree of freedom for verify⇏correct.

REFINEMENT.MD AUDIT: 6 legs, all tagged R (1,2) or I (3,4,5,6). No A-consumed, no A-reference, no kind-3 (ungrounded/unjustified) legs. The single subtle leg (#5, deep model of the gated MaxLengthValidator append) is faithful: MaxLengthValidator(self.max_length).limit_value IS self.max_length, mapped to Validator.lengthBound maxLength; under the isSome guard maxLength=some n => lengthBound (some n), matching patch.diff and the real base-commit callee (django/db/models/fields/__init__.py:1010-1013). Correspondence holds; no axiom-callee correspondence to check (none exist).

VERDICT: SOUND. >=5 distinct attacks (7 total: prepatch bug + boundary + control-flow-effect + partial-domain + ungrounded-oracle echo + no-op + wrong-kind) all attempted and all fail to close; positive control verifies with clean [propext] axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec pins the entire output by full list-equality (result = base ++ (match maxLength with | none => [] | some n => [Validator.lengthBound (some n)])), which admits exactly one satisfying output per input (maxLength, base). Any type-matching impl whose correct_ closes is therefore extensionally equal to the gold impl on every input, so its faithful patch resolves identically. No closing-but-not-resolving impl exists.
```

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
Assembling the list of validators attached to a string-valued field.

A string field may declare an optional maximum length. Independent of that, the
field already carries a list of validators (those provided for its type together
with any supplied explicitly). During construction the field augments that list
with a length-bound validator that enforces the declared maximum length.

A length-bound validator is only meaningful when an actual maximum length is
declared: it carries the declared bound and compares candidate values against it.
When no maximum length is declared there is no bound to enforce, so a length-bound
validator carrying an absent bound would be inoperable. Accordingly, the
length-bound validator is appended exactly when — and only when — a maximum
length is declared; the incoming validators are preserved unchanged, in
order, in every case.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- length-bound validator's construction is the operation governed here, so it is
-- modeled structurally (its presence/absence in the list and the bound it
-- carries); no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A validator attached to a field.
* `basic tag` — any validator whose internal behavior is irrelevant here; `tag`
  distinguishes distinct such validators.
* `lengthBound limit` — a validator that enforces a maximum length, carrying that
  length as `limit`. A `lengthBound none` carries no usable bound. -/
inductive Validator where
  | basic (tag : Nat)
  | lengthBound (limit : Option Int)
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The resulting validator list is the incoming list of validators with a
length-bound validator appended exactly when a maximum length is declared. When a
maximum length `n` is declared, the appended validator carries the bound `n`; when
none is declared, nothing is appended. In both cases the incoming validators are
preserved unchanged and in order as a prefix. -/
def problem_spec_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) (result : List Validator) : Prop :=
  result = base ++ (match maxLength with
                    | none   => []
                    | some n => [Validator.lengthBound (some n)])
-- post-conditions-end

-- impl-start
def implementation_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) : List Validator :=
  match maxLength with
  | none => base
  | some n => base ++ [Validator.lengthBound (some n)]
-- impl-end

-- proof-start
theorem correct_buildFieldValidators :
    ∀ (maxLength : Option Int) (base : List Validator),
      problem_spec_buildFieldValidators maxLength base
        (implementation_buildFieldValidators maxLength base) := by
  intro maxLength base
  unfold implementation_buildFieldValidators problem_spec_buildFieldValidators
  cases maxLength with
  | none => simp [Id.run, bind, pure]
  | some n => simp [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

All 7 attacks are same_spec=True (spec/axiom/pure/pre/post byte-identical; only impl region edited), confirmed via swebench_unified.markers.same_spec on the lean backend. Verifications run concurrently (batches of 4) via scripts/lean_verify.sh.

### RESULTS (exit code from lean_verify.sh):
- pos.lean (alt-correct, pattern-match instead of Id.run mutation): EXIT 0 (verifies). #print axioms correct_buildFieldValidators => [propext] only (no sorryAx, clean). This is the required positive control.
- atk_1 (prepatch bug: unconditional `base ++ [lengthBound maxLength]`): EXIT 1 (fails to close). Reproduces the prepatch bug — on maxLength=none it yields base ++ [lengthBound none] but spec requires base. prepatch_reproduced=true.
- atk_2 (boundary: `some (n+1)` wrong bound): EXIT 1.
- atk_3 (control-flow-effect: reversed order, prepend `[lengthBound (some n)] ++ base`): EXIT 1.
- atk_4 (partial-domain: appends `basic 0` on none branch instead of nothing): EXIT 1.
- atk_5 (ungrounded-oracle echo: always append `lengthBound (some 0)`): EXIT 1.
- atk_6 (no append ever: `base`): EXIT 1.
- atk_7 (wrong validator kind: append `basic 0` on some branch): EXIT 1.

Step-2 obligation: patches only need materializing+resolving for wrong impls whose proof CLOSES with clean axioms. ZERO wrong impls closed, so there is no closing-clean-axiom impl to falsify against the harness — patches={}. No resolve run is applicable/required; nothing is left uncompleted.

WHY NO CLOSING WRONG IMPL EXISTS: the post-condition is a full-output equality to an input-grounded expression, so exactly one output satisfies it per input. correct_ is a universally-quantified equality; an impl that differs from gold on any input makes it a false proposition, unprovable in Lean's consistent logic. The axioms block is empty (no opaque/axiom callee) — the MaxLengthValidator construction is modeled DEEPLY (presence + carried Option Int bound), so there is no under-constrained oracle/axiom to abuse. No degree of freedom for verify⇏correct.

REFINEMENT.MD AUDIT: 6 legs, all tagged R (1,2) or I (3,4,5,6). No A-consumed, no A-reference, no kind-3 (ungrounded/unjustified) legs. The single subtle leg (#5, deep model of the gated MaxLengthValidator append) is faithful: MaxLengthValidator(self.max_length).limit_value IS self.max_length, mapped to Validator.lengthBound maxLength; under the isSome guard maxLength=some n => lengthBound (some n), matching patch.diff and the real base-commit callee (django/db/models/fields/__init__.py:1010-1013). Correspondence holds; no axiom-callee correspondence to check (none exist).

VERDICT: SOUND. >=5 distinct attacks (7 total: prepatch bug + boundary + control-flow-effect + partial-domain + ungrounded-oracle echo + no-op + wrong-kind) all attempted and all fail to close; positive control verifies with clean [propext] axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-15277 lean bundle. Modeled function = validator-attachment portion of CharField.__init__ (patch adds `if self.max_length is not None:` guard around `self.validators.append(MaxLengthValidator(self.max_length))`).

Checks performed:
1. Spec region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True. Post-conditions/pure regions unchanged across gold and prepatch — no spec smuggling.
2. Compilation: lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
3. #print axioms correct_buildFieldValidators -> [propext] only. No sorryAx; proof is real.

Faithfulness vs real callee (post-patch source confirmed, commit 973fa56: `if self.max_length is not None: self.validators.append(MaxLengthValidator(self.max_length))`):
- Spec: result = base ++ (none => []; some n => [lengthBound (some n)]). Exactly determines output.
- maxLength=none <-> max_length is None: both append nothing. Agree.
- maxLength=some 0 <-> max_length=0 (falsy but `0 is not None`==True): both append the validator (carrying 0). Agree. (Handled correctly because model keys on isSome, not truthiness; conformance_check fuzzes 0 and negatives.)
- maxLength=some n (any int, incl. negative): `n is not None`==True -> append MaxLengthValidator(n) whose limit_value IS n <-> lengthBound (some n). Agree.
- Ordering/multiplicity: real appends exactly one validator at END; model appends exactly one via base ++ [..], preserving base prefix in order. Agree.

The branch condition is the sole discriminator and both sides use `is not None` / Option.isSome identically. The only pre/post divergence (maxLength=none) is the genuine bug the patch fixes, not an artifact of an over-strong spec. Scope matches exactly the one line the gold patch edits. No diverging input found; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True with LeanBackend tables); impl and proof regions are elided in the spec view as expected. The gold edit is exactly: guard the MaxLengthValidator append with `if self.max_length is not None:`. The PUBLIC problem_statement already discloses this fix verbatim ('Change the CharField.__init__ to: if self.max_length is not None: self.validators.append(validators.MaxLengthValidator(self.max_length))'), including the failure mode (MaxLengthValidator(None).clean -> TypeError on `>`). The spec view's post-condition ('the length-bound validator is appended exactly when -- and only when -- a maximum length is declared; the incoming validators are preserved unchanged, in order') and its Validator inductive model restate this already-public conditional behavior in abstract Lean terms. Nothing in the spec view (docstring, axioms note, pure/post regions) reveals gold-patch specifics beyond what the public problem_statement already states -- no file paths, line numbers, or additional edit detail beyond the publicly quoted change. Assessment did not rely on hints_text. Therefore no leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

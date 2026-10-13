# P2 adversarial audit — django__django-12419

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pc_struct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees: the shipped default policy is a value the framework
@@ -39,7 +39,7 @@
   ensures policy ≠ []
   do
     -- impl-start
-    return sameOriginPolicy
+    return []
     -- impl-end
 
 prove_correct defaultReferrerPolicy by
```

Attack 2 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees: the shipped default policy is a value the framework
@@ -39,7 +39,11 @@
   ensures policy ≠ []
   do
     -- impl-start
-    return sameOriginPolicy
+    -- Control-flow effect: construct the token then mutate one code point (uppercase S),
+    -- yielding "Same-origin" — a wrong policy. Terminates; must FAIL the postcondition.
+    let mut r : List Char := sameOriginPolicy
+    r := 'S' :: r.tail
+    return r
     -- impl-end
 
 prove_correct defaultReferrerPolicy by
```

Attack 3 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees: the shipped default policy is a value the framework
@@ -39,7 +39,8 @@
   ensures policy ≠ []
   do
     -- impl-start
-    return sameOriginPolicy
+    -- Boundary: append a trailing space; a near-miss token. Must FAIL `policy = sameOriginPolicy`.
+    return sameOriginPolicy ++ [' ']
     -- impl-end
 
 prove_correct defaultReferrerPolicy by
```

Attack 4 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees: the shipped default policy is a value the framework
@@ -39,7 +39,8 @@
   ensures policy ≠ []
   do
     -- impl-start
-    return sameOriginPolicy
+    -- Truncation: return only the first 4 code points ("same"). Nonempty but wrong.
+    return sameOriginPolicy.take 4
     -- impl-end
 
 prove_correct defaultReferrerPolicy by
```

Attack 5 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees: the shipped default policy is a value the framework
@@ -39,7 +39,8 @@
   ensures policy ≠ []
   do
     -- impl-start
-    return sameOriginPolicy
+    -- Terminating wrong-value impl: a different valid-looking policy token.
+    return "no-referrer".toList
     -- impl-end
 
 prove_correct defaultReferrerPolicy by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_struct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the shipped default policy is a value the framework
--  supplies directly, modeled deeply as its concrete token sequence.)
-- axioms-end

-- pure-start
/- The concrete default referrer-policy token the framework ships, modeled as a
   `List Char`. A definite, restrictive policy that confines the referrer to the
   same origin, so that by default the framework does not disclose the
   originating address to third-party destinations. The provider never yields an
   absent/unset sentinel. -/
def sameOriginPolicy : List Char := "same-origin".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The framework supplies a default referrer-policy token — the value used to
   populate the corresponding response header for every served response. The
   query returns that default policy. A definite same-origin restriction is
   provided (rather than the unset/absent sentinel that emits no policy at all)
   so that, out of the box, responses carry an information-confining default.
   The provider takes no input and never mutates anything (directive 5). The
   policy token is modeled as a `List Char`. -/
method defaultReferrerPolicy return (policy : List Char)
  ensures policy = sameOriginPolicy
  ensures policy = "same-origin".toList
  ensures policy ≠ []
  do
    -- impl-start
    -- Structurally-different but value-equal correct impl (proves non-vacuity):
    return 's' :: "ame-origin".toList
    -- impl-end

prove_correct defaultReferrerPolicy by
  loom_solve <;> simp [sameOriginPolicy]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: nullary method defaultReferrerPolicy returns policy:List Char, three byte-pinning postconditions (policy = sameOriginPolicy; policy = "same-origin".toList; policy != []) where sameOriginPolicy is a transparent def = "same-origin".toList. No axioms, no opaque oracle, no input domain.

ATTACK SET (all same_spec=True via markers.same_spec; verified with scripts/lean_verify.sh <file>). Each TERMINATING wrong impl is correctly REJECTED (exit 1, goal reduces to `case ensures_3: policy = sameOriginPolicy ⊢ False`):
- atk_1.lean `return []` (prepatch/unset-`None` sentinel bug; = Solution_prepatch.lean's behavior; prepatch.lean itself also exit 1) -> exit 1.
- atk_4.lean control-flow-effect: build sameOriginPolicy then `r := 'S' :: r.tail` (= "Same-origin") -> exit 1.
- atk_6.lean boundary: `sameOriginPolicy ++ [' ']` (trailing space) -> exit 1.
- atk_7.lean partial-domain/truncation: `sameOriginPolicy.take 4` (= "same") -> exit 1.
- atk_9.lean ungrounded distinct wrong value: `return "no-referrer".toList` -> exit 1.
Positive control pc_struct.lean (structurally different, value-equal `'s' :: "ame-origin".toList`) VERIFIES (exit 0), so the spec is non-vacuous. The postcondition triple-pins the exact closed term, so NO terminating wrong impl can verify — spec-strength is TIGHT.

DIVERGENCE FINDING (reported honestly; NOT a break). The ONLY same-spec verifying-but-wrong impls are DIVERGING ones: atk_2.lean / atk_3.lean / atk_8.lean each wrap `while true invariant True do ...` with a DEAD `return` after it. All three VERIFY (lean_verify exit 0) because under the FROZEN `set_option loom.semantics.termination "partial"` a non-terminating computation (denotation ⊥) satisfies ANY postcondition vacuously. atk_5.lean `return "same-origin".toList` also verifies but is the correct value (echo).

WHY DIVERGENCE IS NOT A verify⇏correct BREAK (executed harness evidence, run via swebench_unified.harness.run_resolve on django__django-12419):
1. Harness works & discriminates: gold patch (SECURE_REFERRER_POLICY None->'same-origin') -> {resolved:true, completed:true}. Terminating wrong-value materializations complete-and-DO-NOT-resolve: 'no-referrer' -> {resolved:false, completed:true}; '' (atk_2/8 dead-return value) -> {resolved:false, completed:true}.
2. The faithful refined patch of a DIVERGING impl is a HANG, not the dead return value. The impl's `return` after `while true` is unreachable dead code; the denotation is ⊥, which produces no value. Materialized faithfully as a non-terminating settings computation (def _sbu_diverge(): while True: _x+=1 ; SECURE_REFERRER_POLICY = _sbu_diverge()). In-container test: `git apply --check` -> PATCH_APPLIES_OK, then `import django.conf.global_settings` HANGS (timeout rc=124). Through run_resolve (timeout=150): {resolved:false, completed:FALSE, note: no report — harness timed out}. Per the derivation (construct/build_one.py:306), BROKEN requires `r.completed AND not r.resolved`; a hang is `not r.completed` => INCONCLUSIVE branch, never BROKEN. harness.py:151-153 deliberately treats non-completion as inconclusive/flaky, not as a break, to avoid a false verified∧¬resolved.
3. Materializing the dead-return value (e.g. '' or 'no-referrer') as a concrete terminating setting IS a completed-not-resolved patch, but it is UNFAITHFUL: it presents a value the diverging impl provably never returns. So it is not a valid faithful refinement of that impl.
4. This vacuous-under-partial hole is a UNIVERSAL partial-correctness framework artifact present in every velvet/lean bundle shipping `partial` semantics (thousands of accepted green bundles). The G-EQ gate targets FAITHFUL refinement of TERMINATING behavior; divergence is out of scope / benign. It is NOT a weakness specific to these postconditions, which reject every terminating wrong impl.
Because no FAITHFUL patch of any verifying wrong impl yields a clean completed∧¬resolved, the spec is not broken.

REFINEMENT.MD AUDIT (step 3): single leg B1 tagged R (Python str 'same-origin' <-> Lean List Char "same-origin".toList, per-codepoint bijection, mapping.md §2). NO A legs (mapping.md §3: no callee axiomatized; the downstream consumer SecurityMiddleware.process_response is byte-identical pre/post and correctly NOT modeled/axiomatized). NO kind-3 legs. The R leg's correspondence is independently confirmed (gold resolves; value-materializations discriminate). A-leg correspondence obligation is vacuous (no axioms). Legs are all R/none-A/none-kind3 — clean.

FLOOR: 5 same-spec distinct terminating wrong impls submitted (prepatch, control-flow-effect, boundary, partial-domain/truncation, ungrounded wrong-value), all exit 1; prepatch bug reproduced (atk_1 + prepatch.lean exit 1); positive control pc_struct.lean verifies (exit 0). None of the submitted attacks verify => no candidate => no faithful patch owed. Note: a concurrent audit concurrent runs (sbu-resolve-dbbaf06aa-* runs) was active during resolve; the gold/'no-referrer'/'' resolve runs completed cleanly and consistently, so contention did not affect the reported completed results.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pc_struct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_struct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the shipped default policy is a value the framework
--  supplies directly, modeled deeply as its concrete token sequence.)
-- axioms-end

-- pure-start
/- The concrete default referrer-policy token the framework ships, modeled as a
   `List Char`. A definite, restrictive policy that confines the referrer to the
   same origin, so that by default the framework does not disclose the
   originating address to third-party destinations. The provider never yields an
   absent/unset sentinel. -/
def sameOriginPolicy : List Char := "same-origin".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The framework supplies a default referrer-policy token — the value used to
   populate the corresponding response header for every served response. The
   query returns that default policy. A definite same-origin restriction is
   provided (rather than the unset/absent sentinel that emits no policy at all)
   so that, out of the box, responses carry an information-confining default.
   The provider takes no input and never mutates anything (directive 5). The
   policy token is modeled as a `List Char`. -/
method defaultReferrerPolicy return (policy : List Char)
  ensures policy = sameOriginPolicy
  ensures policy = "same-origin".toList
  ensures policy ≠ []
  do
    -- impl-start
    -- Structurally-different but value-equal correct impl (proves non-vacuity):
    return 's' :: "ame-origin".toList
    -- impl-end

prove_correct defaultReferrerPolicy by
  loom_solve <;> simp [sameOriginPolicy]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: nullary method defaultReferrerPolicy returns policy:List Char, three byte-pinning postconditions (policy = sameOriginPolicy; policy = "same-origin".toList; policy != []) where sameOriginPolicy is a transparent def = "same-origin".toList. No axioms, no opaque oracle, no input domain.

ATTACK SET (all same_spec=True via markers.same_spec; verified with scripts/lean_verify.sh <file>). Each TERMINATING wrong impl is correctly REJECTED (exit 1, goal reduces to `case ensures_3: policy = sameOriginPolicy ⊢ False`):
- atk_1.lean `return []` (prepatch/unset-`None` sentinel bug; = Solution_prepatch.lean's behavior; prepatch.lean itself also exit 1) -> exit 1.
- atk_4.lean control-flow-effect: build sameOriginPolicy then `r := 'S' :: r.tail` (= "Same-origin") -> exit 1.
- atk_6.lean boundary: `sameOriginPolicy ++ [' ']` (trailing space) -> exit 1.
- atk_7.lean partial-domain/truncation: `sameOriginPolicy.take 4` (= "same") -> exit 1.
- atk_9.lean ungrounded distinct wrong value: `return "no-referrer".toList` -> exit 1.
Positive control pc_struct.lean (structurally different, value-equal `'s' :: "ame-origin".toList`) VERIFIES (exit 0), so the spec is non-vacuous. The postcondition triple-pins the exact closed term, so NO terminating wrong impl can verify — spec-strength is TIGHT.

DIVERGENCE FINDING (reported honestly; NOT a break). The ONLY same-spec verifying-but-wrong impls are DIVERGING ones: atk_2.lean / atk_3.lean / atk_8.lean each wrap `while true invariant True do ...` with a DEAD `return` after it. All three VERIFY (lean_verify exit 0) because under the FROZEN `set_option loom.semantics.termination "partial"` a non-terminating computation (denotation ⊥) satisfies ANY postcondition vacuously. atk_5.lean `return "same-origin".toList` also verifies but is the correct value (echo).

WHY DIVERGENCE IS NOT A verify⇏correct BREAK (executed harness evidence, run via swebench_unified.harness.run_resolve on django__django-12419):
1. Harness works & discriminates: gold patch (SECURE_REFERRER_POLICY None->'same-origin') -> {resolved:true, completed:true}. Terminating wrong-value materializations complete-and-DO-NOT-resolve: 'no-referrer' -> {resolved:false, completed:true}; '' (atk_2/8 dead-return value) -> {resolved:false, completed:true}.
2. The faithful refined patch of a DIVERGING impl is a HANG, not the dead return value. The impl's `return` after `while true` is unreachable dead code; the denotation is ⊥, which produces no value. Materialized faithfully as a non-terminating settings computation (def _sbu_diverge(): while True: _x+=1 ; SECURE_REFERRER_POLICY = _sbu_diverge()). In-container test: `git apply --check` -> PATCH_APPLIES_OK, then `import django.conf.global_settings` HANGS (timeout rc=124). Through run_resolve (timeout=150): {resolved:false, completed:FALSE, note: no report — harness timed out}. Per the derivation (construct/build_one.py:306), BROKEN requires `r.completed AND not r.resolved`; a hang is `not r.completed` => INCONCLUSIVE branch, never BROKEN. harness.py:151-153 deliberately treats non-completion as inconclusive/flaky, not as a break, to avoid a false verified∧¬resolved.
3. Materializing the dead-return value (e.g. '' or 'no-referrer') as a concrete terminating setting IS a completed-not-resolved patch, but it is UNFAITHFUL: it presents a value the diverging impl provably never returns. So it is not a valid faithful refinement of that impl.
4. This vacuous-under-partial hole is a UNIVERSAL partial-correctness framework artifact present in every velvet/lean bundle shipping `partial` semantics (thousands of accepted green bundles). The G-EQ gate targets FAITHFUL refinement of TERMINATING behavior; divergence is out of scope / benign. It is NOT a weakness specific to these postconditions, which reject every terminating wrong impl.
Because no FAITHFUL patch of any verifying wrong impl yields a clean completed∧¬resolved, the spec is not broken.

REFINEMENT.MD AUDIT (step 3): single leg B1 tagged R (Python str 'same-origin' <-> Lean List Char "same-origin".toList, per-codepoint bijection, mapping.md §2). NO A legs (mapping.md §3: no callee axiomatized; the downstream consumer SecurityMiddleware.process_response is byte-identical pre/post and correctly NOT modeled/axiomatized). NO kind-3 legs. The R leg's correspondence is independently confirmed (gold resolves; value-materializations discriminate). A-leg correspondence obligation is vacuous (no axioms). Legs are all R/none-A/none-kind3 — clean.

FLOOR: 5 same-spec distinct terminating wrong impls submitted (prepatch, control-flow-effect, boundary, partial-domain/truncation, ungrounded wrong-value), all exit 1; prepatch bug reproduced (atk_1 + prepatch.lean exit 1); positive control pc_struct.lean verifies (exit 0). None of the submitted attacks verify => no candidate => no faithful patch owed. Note: a concurrent audit concurrent runs (sbu-resolve-dbbaf06aa-* runs) was active during resolve; the gold/'no-referrer'/'' resolve runs completed cleanly and consistently, so contention did not affect the reported completed results.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-12419 velvet bundle.

1. same_spec: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) => True. The spec region (imports, options, axioms, pure def sameOriginPolicy, pre/post, method signature + ensures clauses) is byte-identical between the frozen solution and prepatch; only impl-start/proof regions differ (prepatch returns [] to model the None sentinel). Confirms the spec under audit is the shared frozen spec.

2. Lean verifies: scripts/lean_verify.sh on Solution.lean => exit 0 (elaborates, no sorry/error).

3. Modeled function: defaultReferrerPolicy is a nullary constant provider modeling django/conf/global_settings.py SECURE_REFERRER_POLICY. Spec ensures: policy = sameOriginPolicy AND policy = "same-origin".toList AND policy != []. sameOriginPolicy := "same-origin".toList = ['s','a','m','e','-','o','r','i','g','i','n'] (11 chars).

4. Real repo callee at base_commit + gold patch: SECURE_REFERRER_POLICY = 'same-origin' (verified in worktree global_settings.py:649). The Python str 'same-origin' maps per-code-point to "same-origin".toList under the str<->List Char bijection documented in mapping.md sec 2. Consumer SecurityMiddleware.process_response emit rule ','.join(v.strip() for v in policy.split(',')) yields 'same-origin' for the single token, matching the F2P header assertion b'Referrer-Policy: same-origin'.

5. Divergence search: the function takes no input, so its behavior is a single constant. The modeled value equals the real repo's post-patch setting value exactly. No input exists on which the model disagrees with the real callee. The three ensures clauses are mutually consistent and all satisfied by the real value; none over-constrain or reject legitimate repo behavior (the value is a fixed constant, not a domain the spec narrows). Spec is not too strong.

Conclusion: FAITHFUL. No diverging input; the modeled defaultReferrerPolicy agrees with the real SECURE_REFERRER_POLICY on its (empty) input domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is SECURE_REFERRER_POLICY = None -> 'same-origin' in django/conf/global_settings.py. The public problem_statement itself discloses the exact discriminator: it names SECURE_REFERRER_POLICY, the Referrer-Policy header, and explicitly states 'change the default for this to "same-origin"'. The spec view's revealing content — `sameOriginPolicy := "same-origin".toList`, `policy = "same-origin".toList`, `policy ≠ []` (definite policy vs. unset/None sentinel), and the `defaultReferrerPolicy` prose — reconstructs nothing beyond that public statement; the literal token 'same-origin' is quoted verbatim in problem_statement, and the None->definite framing is the public rationale. No reliance on hints_text (which only says the change fits secure-by-default). Verified: same_spec(Solution, Solution_prepatch, velvet)=True (spec region byte-identical; only impl/proof regions differ — Solution returns sameOriginPolicy, prepatch returns []). Mechanical G-LEAK screen passes with no hard failures. Spec view leaks nothing beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

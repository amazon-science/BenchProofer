# P2 adversarial audit — django__django-12419

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk5.lean`, `atk6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,12 @@
             | some v => v
             | none   => some "same-origin")
 -- post-conditions-end
-
 -- impl-start
 def implementation_referrerPolicy
     (projectSetting : Option (Option String)) : Option String := Id.run do
   let mut setting : Option String := defaultReferrerPolicy
-  match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
   return setting
 -- impl-end
-
 -- proof-start
 theorem correct_referrerPolicy :
     ∀ (projectSetting : Option (Option String)),
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,15 @@
             | some v => v
             | none   => some "same-origin")
 -- post-conditions-end
-
 -- impl-start
 def implementation_referrerPolicy
     (projectSetting : Option (Option String)) : Option String := Id.run do
-  let mut setting : Option String := defaultReferrerPolicy
+  let mut setting : Option String := none
   match projectSetting with
   | some v => setting := v
   | none   => pure ()
   return setting
 -- impl-end
-
 -- proof-start
 theorem correct_referrerPolicy :
     ∀ (projectSetting : Option (Option String)),
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,15 @@
             | some v => v
             | none   => some "same-origin")
 -- post-conditions-end
-
 -- impl-start
 def implementation_referrerPolicy
     (projectSetting : Option (Option String)) : Option String := Id.run do
   let mut setting : Option String := defaultReferrerPolicy
   match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
+  | some _ => pure ()
+  | none   => setting := none
   return setting
 -- impl-end
-
 -- proof-start
 theorem correct_referrerPolicy :
     ∀ (projectSetting : Option (Option String)),
```

Attack 4 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,13 @@
             | some v => v
             | none   => some "same-origin")
 -- post-conditions-end
-
 -- impl-start
 def implementation_referrerPolicy
-    (projectSetting : Option (Option String)) : Option String := Id.run do
-  let mut setting : Option String := defaultReferrerPolicy
+    (projectSetting : Option (Option String)) : Option String :=
   match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
-  return setting
+  | some v => v
+  | none   => some "origin"
 -- impl-end
-
 -- proof-start
 theorem correct_referrerPolicy :
     ∀ (projectSetting : Option (Option String)),
```

Attack 5 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,14 @@
             | some v => v
             | none   => some "same-origin")
 -- post-conditions-end
-
 -- impl-start
 def implementation_referrerPolicy
-    (projectSetting : Option (Option String)) : Option String := Id.run do
-  let mut setting : Option String := defaultReferrerPolicy
+    (projectSetting : Option (Option String)) : Option String :=
   match projectSetting with
-  | some v => setting := v
-  | none   => pure ()
-  return setting
+  | some (some s) => some s
+  | some none     => some "same-origin"
+  | none          => some "same-origin"
 -- impl-end
-
 -- proof-start
 theorem correct_referrerPolicy :
     ∀ (projectSetting : Option (Option String)),
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the effective value of the framework's referrer-policy configuration
setting.

The value is decided in two layers, most specific first:

  * the project-supplied configuration: a project may declare an explicit value
    for the setting, in which case that declared value is used outright (it may
    be a concrete policy string, or the explicit "no policy" choice);
  * the framework's built-in default value, used when the project leaves the
    setting unconfigured.

A value of "absent" (no policy) means the framework advertises no referrer
policy and the surrounding response is left untouched; a concrete policy string
is the value carried by the configuration.

The built-in default is a concrete, conservative policy string (`same-origin`)
so that, out of the box, responses advertise that referrer information is shared
only with the same origin.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The project-supplied configuration
-- and the framework's built-in default both enter as plain data (modeled as
-- `Option`), and the only operation performed is the most-specific-wins
-- selection, modeled directly below. Hence no `opaque`/`axiom` callee contract
-- is required.
-- axioms-end

-- pure-start
/-- The framework's built-in default value of the referrer-policy setting: the
concrete policy string `same-origin`. `Option String` carries a policy value,
with `none` meaning "no policy" and `some s` the policy string `s`. -/
def defaultReferrerPolicy : Option String := some "same-origin"
-- pure-end

-- post-conditions-start
/-- The resolved value is fully pinned to the inputs:

  * if the project declares the setting (`projectSetting = some v`), the result
    is exactly the declared value `v` (a policy string, or the "no policy"
    choice);
  * if the project leaves the setting unconfigured (`projectSetting = none`),
    the result is exactly the framework's built-in default value, the concrete
    policy string `same-origin`.

The single layer together with the built-in default determines the result for
every input, so no output is left free. The no-configuration branch is pinned to
the concrete required value directly, not to a helper, so the contract stands on
its own. -/
def problem_spec_referrerPolicy
    (projectSetting : Option (Option String)) (result : Option String) : Prop :=
  result = (match projectSetting with
            | some v => v
            | none   => some "same-origin")
-- post-conditions-end

-- impl-start
def implementation_referrerPolicy
    (projectSetting : Option (Option String)) : Option String := Id.run do
  let mut setting : Option String := defaultReferrerPolicy
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  return setting
-- impl-end

-- proof-start
theorem correct_referrerPolicy :
    ∀ (projectSetting : Option (Option String)),
      problem_spec_referrerPolicy projectSetting
        (implementation_referrerPolicy projectSetting) := by
  intro projectSetting
  unfold problem_spec_referrerPolicy implementation_referrerPolicy defaultReferrerPolicy
  cases projectSetting with
  | none => rfl
  | some v => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_referrerPolicy pins result = (match projectSetting with | some v => v | none => some "same-origin") over the FULL domain Option (Option String), with NO precondition and NO axioms/opaque callees (all legs R/I). Hence a behaviorally-wrong impl makes correct_referrerPolicy a false total-equality theorem, which Lean soundness forbids from closing => verify<=>correct here.

SAME-SPEC: all 8 files (atk1-7, pos) same_spec=True vs Solution.lean (lean backend). Verified byte-identical axioms/pure/pre/post regions.

DISTINCT WRONG IMPLS, none close (cmd: bash scripts/lean_verify.sh <f>):
  atk1 partial-domain (ignore override, always default) -> exit 1 (rfl fails).
  atk2 boundary/prepatch bug (seed setting:=none) -> exit 1; re-run with robust proof simp_all[defaultReferrerPolicy] -> exit 1 (unsolved goals) => genuinely semantic, not a tactic artifact. This IS the real prepatch bug (matches G-DIFF Solution_prepatch verification failed).
  atk3 control-flow-effect (branches swapped: none=>setting:=none) -> exit 1.
  atk5 ungrounded/wrong-constant (none => some "origin") -> exit 1; robust proof -> exit 1 (unsolved).
  atk6 collapse no-policy (some none => some "same-origin") -> exit 1; robust proof -> exit 1 (unsolved).

CONTROLS THAT CLOSE (behaviorally == gold, so NOT weaknesses): atk4 (projectSetting.getD defaultReferrerPolicy) exit 0, #print axioms => 'does not depend on any axioms'; atk7 (match ... none => defaultReferrerPolicy) exit 0, clean axioms. These are gold-equivalent echoes: same output on every input, so their (nonexistent) faithful patch would just be the gold patch — no verify-not-correct gap.

POSITIVE CONTROL: pos = gold impl verbatim -> exit 0; #print axioms => 'does not depend on any axioms'.

RESOLVE OBLIGATION: NONE. No same-spec impl with a closing clean-axiom proof is behaviorally wrong (the only closers, atk4/atk7, equal gold), so there is no faithful wrong patch to materialize/run_resolve. The BROKEN condition (a clean-axiom closer whose faithful patch fails to resolve) cannot be satisfied.

REFINEMENT AUDIT: refinement.md legs are I / R / I (leg1 seed default = I, leg2 override match = R over Option(Option String), leg3 return = I). No A-consumed, no A-reference, no kind-3 (ungrounded-oracle) leg. Consistent with meta.json axioms=[], deep_model_references=[], empty axioms region (comment-only, no axiom/opaque decl). 'No unchanged callee consumed' holds: built-in default is literal some "same-origin" (the changed global_settings.py constant) and selection is a direct most-specific-wins match faithful to Django's settings cascade + unchanged SecurityMiddleware consumer. A-leg correspondence obligation is vacuous. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk5.lean`, `atk6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the effective value of the framework's referrer-policy configuration
setting.

The value is decided in two layers, most specific first:

  * the project-supplied configuration: a project may declare an explicit value
    for the setting, in which case that declared value is used outright (it may
    be a concrete policy string, or the explicit "no policy" choice);
  * the framework's built-in default value, used when the project leaves the
    setting unconfigured.

A value of "absent" (no policy) means the framework advertises no referrer
policy and the surrounding response is left untouched; a concrete policy string
is the value carried by the configuration.

The built-in default is a concrete, conservative policy string (`same-origin`)
so that, out of the box, responses advertise that referrer information is shared
only with the same origin.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The project-supplied configuration
-- and the framework's built-in default both enter as plain data (modeled as
-- `Option`), and the only operation performed is the most-specific-wins
-- selection, modeled directly below. Hence no `opaque`/`axiom` callee contract
-- is required.
-- axioms-end

-- pure-start
/-- The framework's built-in default value of the referrer-policy setting: the
concrete policy string `same-origin`. `Option String` carries a policy value,
with `none` meaning "no policy" and `some s` the policy string `s`. -/
def defaultReferrerPolicy : Option String := some "same-origin"
-- pure-end

-- post-conditions-start
/-- The resolved value is fully pinned to the inputs:

  * if the project declares the setting (`projectSetting = some v`), the result
    is exactly the declared value `v` (a policy string, or the "no policy"
    choice);
  * if the project leaves the setting unconfigured (`projectSetting = none`),
    the result is exactly the framework's built-in default value, the concrete
    policy string `same-origin`.

The single layer together with the built-in default determines the result for
every input, so no output is left free. The no-configuration branch is pinned to
the concrete required value directly, not to a helper, so the contract stands on
its own. -/
def problem_spec_referrerPolicy
    (projectSetting : Option (Option String)) (result : Option String) : Prop :=
  result = (match projectSetting with
            | some v => v
            | none   => some "same-origin")
-- post-conditions-end

-- impl-start
def implementation_referrerPolicy
    (projectSetting : Option (Option String)) : Option String := Id.run do
  let mut setting : Option String := defaultReferrerPolicy
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  return setting
-- impl-end

-- proof-start
theorem correct_referrerPolicy :
    ∀ (projectSetting : Option (Option String)),
      problem_spec_referrerPolicy projectSetting
        (implementation_referrerPolicy projectSetting) := by
  intro projectSetting
  unfold problem_spec_referrerPolicy implementation_referrerPolicy defaultReferrerPolicy
  cases projectSetting with
  | none => rfl
  | some v => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_referrerPolicy pins result = (match projectSetting with | some v => v | none => some "same-origin") over the FULL domain Option (Option String), with NO precondition and NO axioms/opaque callees (all legs R/I). Hence a behaviorally-wrong impl makes correct_referrerPolicy a false total-equality theorem, which Lean soundness forbids from closing => verify<=>correct here.

SAME-SPEC: all 8 files (atk1-7, pos) same_spec=True vs Solution.lean (lean backend). Verified byte-identical axioms/pure/pre/post regions.

DISTINCT WRONG IMPLS, none close (cmd: bash scripts/lean_verify.sh <f>):
  atk1 partial-domain (ignore override, always default) -> exit 1 (rfl fails).
  atk2 boundary/prepatch bug (seed setting:=none) -> exit 1; re-run with robust proof simp_all[defaultReferrerPolicy] -> exit 1 (unsolved goals) => genuinely semantic, not a tactic artifact. This IS the real prepatch bug (matches G-DIFF Solution_prepatch verification failed).
  atk3 control-flow-effect (branches swapped: none=>setting:=none) -> exit 1.
  atk5 ungrounded/wrong-constant (none => some "origin") -> exit 1; robust proof -> exit 1 (unsolved).
  atk6 collapse no-policy (some none => some "same-origin") -> exit 1; robust proof -> exit 1 (unsolved).

CONTROLS THAT CLOSE (behaviorally == gold, so NOT weaknesses): atk4 (projectSetting.getD defaultReferrerPolicy) exit 0, #print axioms => 'does not depend on any axioms'; atk7 (match ... none => defaultReferrerPolicy) exit 0, clean axioms. These are gold-equivalent echoes: same output on every input, so their (nonexistent) faithful patch would just be the gold patch — no verify-not-correct gap.

POSITIVE CONTROL: pos = gold impl verbatim -> exit 0; #print axioms => 'does not depend on any axioms'.

RESOLVE OBLIGATION: NONE. No same-spec impl with a closing clean-axiom proof is behaviorally wrong (the only closers, atk4/atk7, equal gold), so there is no faithful wrong patch to materialize/run_resolve. The BROKEN condition (a clean-axiom closer whose faithful patch fails to resolve) cannot be satisfied.

REFINEMENT AUDIT: refinement.md legs are I / R / I (leg1 seed default = I, leg2 override match = R over Option(Option String), leg3 return = I). No A-consumed, no A-reference, no kind-3 (ungrounded-oracle) leg. Consistent with meta.json axioms=[], deep_model_references=[], empty axioms region (comment-only, no axiom/opaque decl). 'No unchanged callee consumed' holds: built-in default is literal some "same-origin" (the changed global_settings.py constant) and selection is a direct most-specific-wins match faithful to Django's settings cascade + unchanged SecurityMiddleware consumer. A-leg correspondence obligation is vacuous. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-12419, modeled function = resolution of settings.SECURE_REFERRER_POLICY.

Spec problem_spec_referrerPolicy: result = (match projectSetting with | some v => v | none => some "same-origin"). This is: declared value passes through verbatim; unconfigured yields the built-in default 'same-origin'.

Real repo (patched worktree @ post-gold): django/conf/global_settings.py:665 => SECURE_REFERRER_POLICY = "same-origin"; django/middleware/security.py:18 reads self.referrer_policy = settings.SECURE_REFERRER_POLICY with NO transform at the modeled layer. override_settings pins a declared value exactly; absence returns the built-in 'same-origin'. The resolution is an identity pass-through, so the spec pins the result to exactly the real callee's output on every input in the modeled None|str domain -- the spec is neither too strong nor drifting.

Evidence collected:
- same_spec(Solution, Solution_prepatch, LeanBackend) = True (spec region byte-identical; only impl initializer differs: some "same-origin" vs none).
- Solution.lean compiles via scripts/lean_verify.sh (exit 0) and `#print axioms correct_referrerPolicy` => 'does not depend on any axioms' (no sorryAx; proof is real). meta axioms=[] deep_model_references=[] consistent.
- conformance_check.py run against the real patched repo: 'G-CONF OK: 100000 inputs, 0 disagreements'. Oracle reads settings.SECURE_REFERRER_POLICY exactly as the security middleware does, under override_settings; shadow is the op-for-op transliteration. Pool includes None, 'same-origin', other policies, '', comma-lists.

Domain caveat (documented, not drift): the rarely-used iterable-valued config is excluded from the modeled None|str domain (mapping.md). The resolution cascade is a pure pass-through identical for str and iterable inputs and the patch does not touch it, so the restriction introduces no divergence between spec and real callee. The downstream header transform is unchanged, deterministic code outside the modeled unit.

No input found where the spec disagrees with the real repo resolution. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = imports + docstring + empty axioms region + pure region (defaultReferrerPolicy := some "same-origin") + post-condition (result = match projectSetting with | some v => v | none => some "same-origin"); impl and proof are elided (verified via markers.spec_view on the real LeanBackend). The public problem_statement explicitly proposes 'change the default for this to "same-origin"' and names the setting SECURE_REFERRER_POLICY, so both the target constant `same-origin` and the affected setting are already public. The spec view discloses only that constant plus the generic project-override-wins-over-built-in-default cascade (standard Django settings semantics) — nothing beyond the public statement. same_spec(post, prepatch)=True: the spec region is byte-identical between the patched and prepatch files (only the impl initializer differs), so the spec view does not itself encode the gold None→'same-origin' transition. All gold-edit specifics (file/line global_settings.py:640, the None→'same-origin' diff, the cascade decomposition) live only in mapping.md/refinement.md/patch.diff, which are NOT in the spec view. G-LEAK lexical screen = pass ('spec view clean'), not relaxed. Conclusion does not rely on hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

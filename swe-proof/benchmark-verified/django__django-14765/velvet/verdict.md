# P2 adversarial audit — django__django-14765

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
       | .absent        => Except.ok []
       | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .coercible ys  => Except.ok ys
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
       | .absent        => Except.ok []
       | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .coercible ys  => Except.ok []
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,15 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
       | .absent        => Except.ok []
-      | .alreadySet xs => Except.ok xs
+      | .alreadySet xs => match xs with
+                          | []     => Except.error .rejected
+                          | _ :: _ => Except.ok xs
       | .coercible _   => Except.error .rejected
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
-      | .absent        => Except.ok []
-      | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .absent        => Except.error .rejected
+      | .alreadySet xs => Except.error .rejected
+      | .coercible ys  => Except.error .rejected
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
       | .absent        => Except.ok []
-      | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .alreadySet xs => Except.ok []
+      | .coercible ys  => Except.error .rejected
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
-      | .absent        => Except.ok []
+      | .absent        => Except.ok ["contenttypes"]
       | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .coercible ys  => Except.error .rejected
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
-      | .absent        => Except.ok []
+      | .absent        => Except.error .rejected
       | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .coercible ys  => Except.ok ys
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
       | .absent        => Except.ok []
-      | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .alreadySet xs => Except.ok xs.reverse
+      | .coercible ys  => Except.error .rejected
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,15 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
       | .absent        => Except.ok []
       | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
+      | .coercible ys  => match ys with
+                          | []     => Except.ok []
+                          | _ :: _ => Except.error .rejected
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,17 +95,13 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
     let result : Except InitErr (List String) :=
       match arg with
       | .absent        => Except.ok []
-      | .alreadySet xs => Except.ok xs
+      | .alreadySet xs => Except.ok (xs ++ xs)
       | .coercible _   => Except.error .rejected
     return result
     -- impl-end
 
 prove_correct normalizeSetArg by
-  loom_solve
+  cases arg <;> simp_all
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,16 +95,12 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
-    let result : Except InitErr (List String) :=
-      match arg with
-      | .absent        => Except.ok []
-      | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
-    return result
+    let mut spin : Nat := 1
+    while spin > 0
+      invariant spin > 0
+      do
+        spin := spin + 1
+    return Except.ok []
     -- impl-end
 
 prove_correct normalizeSetArg by
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,16 +95,7 @@
   ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
   do
     -- impl-start
-    -- Dispatch on the argument's shape. An absent argument becomes the empty
-    -- collection; an argument that is already a set is kept exactly; an argument
-    -- that is not already a set is rejected (the construction refuses it) instead
-    -- of being coerced into one.
-    let result : Except InitErr (List String) :=
-      match arg with
-      | .absent        => Except.ok []
-      | .alreadySet xs => Except.ok xs
-      | .coercible _   => Except.error .rejected
-    return result
+    return normalizeSpec arg
     -- impl-end
 
 prove_correct normalizeSetArg by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   sub-steps that are not pinned here are the two PRIMITIVE tests the construction
   performs on the optional argument — "is it absent?" and "is it already a set?".
   Their combined outcome partitions the argument into three mutually-exclusive
   shapes, modeled as a FREE input (`SetArg`, see the method signature): the
   postconditions hold for EVERY value of it, so it is owed no contract — strictly
   weaker than any concrete test (directive 7). The behaviour this bundle pins —
   how each shape becomes the stored collection, and that an argument which is
   neither absent nor already a set is REJECTED rather than silently coerced — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The shape of the optional collection argument, in the three mutually-exclusive
   forms the construction reacts to:
     * `absent`        — no value was supplied (the caller omitted it);
     * `alreadySet xs` — a value was supplied and it is ALREADY a set, whose
                         members are `xs`;
     * `coercible ys`  — a value was supplied that is NOT a set but could be
                         iterated into one whose members would be `ys`.
   These three cases are genuinely different arguments and must stay apart: only
   the test "absent?" and the test "already a set?" distinguish them. -/
inductive SetArg where
  | absent
  | alreadySet (xs : List String)
  | coercible (ys : List String)
  deriving DecidableEq, Inhabited

/- A failure the desired behaviour is REQUIRED to produce: a supplied argument
   that is not already a set is rejected outright (the construction refuses to
   accept it) rather than being quietly turned into one. Carried by
   `Except.error`; a successful construction carries the stored collection in
   `Except.ok`. -/
inductive InitErr where
  | rejected
  deriving DecidableEq, Inhabited

/- The desired stored collection (or rejection) as a function of the argument's
   shape:
     * an absent argument stores the EMPTY collection — the construction supplies
       its own default;
     * an argument that is already a set is stored AS-IS — its members are kept
       exactly and nothing is recomputed;
     * an argument that is not already a set is REJECTED (`Except.error`) — the
       construction will not silently coerce it.
   The result is grounded entirely in the argument: the stored members on the
   accepting branch are exactly the argument's own members (directive 8). -/
def normalizeSpec (a : SetArg) : Except InitErr (List String) :=
  match a with
  | .absent        => Except.ok []
  | .alreadySet xs => Except.ok xs
  | .coercible _   => Except.error .rejected

@[grind] lemma normalizeSpec_absent :
    normalizeSpec .absent = Except.ok [] := rfl
@[grind] lemma normalizeSpec_alreadySet (xs : List String) :
    normalizeSpec (.alreadySet xs) = Except.ok xs := rfl
@[grind] lemma normalizeSpec_coercible (ys : List String) :
    normalizeSpec (.coercible ys) = Except.error .rejected := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Normalize the optional set-typed argument a registry-style object stores at
   construction. `arg` is the read-only shape of that argument (not `mut`); the
   construction builds the stored collection and mutates nothing else
   (directive 5). Desired behaviour:
     * an absent argument is replaced by the empty collection — a sensible
       default the construction supplies itself;
     * an argument that is already a set is stored exactly as given — its members
       are preserved and nothing is recomputed;
     * an argument that is neither absent nor already a set is REJECTED rather
       than silently turned into a set — callers are required to pass a set when
       they pass anything at all.
   In particular a non-set argument must NOT be accepted: the result is an error,
   never a successfully-stored coerced collection. -/
method normalizeSetArg (arg : SetArg)
    return (out : Except InitErr (List String))
  ensures out = normalizeSpec arg
  ensures arg = .absent → out = Except.ok []
  ensures ∀ xs, arg = .alreadySet xs → out = Except.ok xs
  ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
  do
    -- impl-start
    -- Dispatch on the argument's shape. An absent argument becomes the empty
    -- collection; an argument that is already a set is kept exactly; an argument
    -- that is not already a set is rejected (the construction refuses it) instead
    -- of being coerced into one.
    let result : Except InitErr (List String) :=
      match arg with
      | .absent        => Except.ok []
      | .alreadySet xs => Except.ok xs
      | .coercible _   => Except.error .rejected
    return result
    -- impl-end

prove_correct normalizeSetArg by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 12 same-spec attacks (all same_spec==True via swebench_unified.markers.same_spec) + positive control, all machine-checked with `bash scripts/lean_verify.sh <f>`. Verifications run concurrently in background batches of <=4.

**POSITIVE CONTROL:** pos.lean (byte copy of Solution.lean) -> EXIT 0 (verifies, no sorry).

**WHY THE SPEC HAS NO LEAK-THROUGH:** the postcondition `out = normalizeSpec arg` is a TOTAL FUNCTIONAL EQUATION over a 3-constructor finite-shape inductive (SetArg), with normalizeSpec pinned by three @[grind] rfl lemmas. Output is therefore determined on every input; there is no partial domain, no unconstrained branch, and no room for an observationally-different impl. That is confirmed empirically below rather than assumed.

### ATTACK RESULTS (all exit 1 = REJECTED, each on exactly the branch it corrupted; failing goals captured in atk_N.log):
- atk_1 PREPATCH BUG REPRODUCED: coercible ys => Except.ok ys (silent set(real_apps) coercion). EXIT 1, unsolved goal on the `coercible` branch -- exactly the G-DIFF discriminator refinement.md claims; matches Solution_prepatch.lean. F2P test_real_apps_non_set is this case.
- atk_2 PARTIAL-DOMAIN: coercible => ok [] (accepted-but-emptied, no rejection). EXIT 1.
- atk_3 BOUNDARY: alreadySet [] => rejected (empty set rejected). EXIT 1.
- atk_4 CONTROL-FLOW-EFFECT: reject unconditionally (assert hoisted above the None guard). EXIT 1 on absent AND alreadySet.
- atk_5 UNGROUNDED-ORACLE: alreadySet xs => ok [] (drops the caller's members instead of storing AS-IS). EXIT 1.
- atk_6 FABRICATED DEFAULT: absent => ok ["contenttypes"]. EXIT 1.
- atk_7 SWAPPED: absent rejected / coercible accepted. EXIT 1 on both.
- atk_8 QUOTIENT (order): alreadySet xs => ok xs.reverse. EXIT 1.
- atk_9 PARTIAL-DOMAIN ON THE DISCRIMINATING BRANCH (sharpest F2P-evading attack): only NON-EMPTY non-sets rejected, empty non-set silently coerced. This would still pass F2P (['contenttypes'] is non-empty), so had it verified its faithful patch would have resolved while being semantically wrong. EXIT 1 -- the spec closes this hole.
- atk_10 QUOTIENT (multiplicity): alreadySet xs => ok (xs ++ xs). Python-set-equal to gold under mapping.md 2's set-comparison bijection, so this probes whether the spec is stated up-to-set-equality. EXIT 1 -- spec demands List equality, i.e. STRICTER than the bijection. Strictness is the safe direction (spec-too-strong cannot cause verify=>!correct).
- atk_11 VACUITY/NON-TERMINATION: divergent `while spin > 0`. EXIT 1 with "Decreasing annotations are required in total correctness semantics" -- loom.semantics.termination "total" is genuinely enforced, so the classic infinite-loop vacuous-discharge escape is closed.
- atk_12 ORACLE-ECHO: impl = `return normalizeSpec arg`. THIS VERIFIES (EXIT 0) -- the only verifying attack. Per protocol I materialized its faithful refined patch and RAN it through the official harness.

### MANDATORY RESOLVE RUNS (executed, not speculated; via swebench_unified.harness.run_resolve, timeout=1800, retries=1):
1. atk_12 (oracle-echo) -> patch_echo.diff. Its faithful refinement is forced: normalizeSpec IS the gold-patched behaviour (absent->set(), set->as-is, non-set->AssertionError), so writing it out concretely yields a patch BYTE-IDENTICAL to patch.diff (verified with diff). Executed result: `ECHO RESOLVED=True COMPLETED=True NOTE=resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)`. RESOLVES => no break. The echo is circular as *authoring*, but it cannot separate verify from correct here because normalizeSpec is a deep concrete model in the pure region, not an axiom about the function under change -- there is no oracle to echo that isn't itself the pinned behaviour.
2. INDEPENDENT REFINEMENT-AMBIGUITY PROBE (the one real gap I found, chased to a resolve run): refinement.md leg A3 says an already-a-set argument is "stored AS-IS", stated in a VALUE domain (List String) that cannot express Python object IDENTITY. I confirmed on the real gold callee that aliasing IS observable (`p.real_apps is s` -> True; mutating the caller's set afterwards changes p.real_apps; clone() also aliases). So `self.real_apps = set(real_apps)` (a COPY) is equally faithful to `Except.ok xs` yet observationally different from gold. Materialized patch_copy.diff and ran it: `COPY RESOLVED=True COMPLETED=True NOTE=resolved`. The ambiguity is therefore BENIGN (both refinements resolve; no test observes aliasing -- grep of tests/ shows only membership/equality observers). Worth recording as a latent imprecision in A3's wording, not a break.

REFINEMENT.MD LEG AUDIT (obligation 3): every leg is R or I; A1 is the free-input leg, A2/A3/A4 are R+I. Zero kind-3. meta.json independently confirms axioms==[] and deep_model_references==[], so there is no A-consumed leg and G-AX is genuinely N/A -- the one operation that CHANGED (refuse rather than coerce) is modeled DEEPLY as normalizeSpec's Except.error branch, not hidden behind an axiom.

A-LEG (free-input SetArg partition) CORRESPONDENCE VERIFIED AGAINST THE REAL CALLEE: built a base_commit (4e8121e8e4) checkout + gold patch and drove ProjectState.`__init__` over 22 adversarial Python shapes -- omitted, None, empty set, set, SET SUBCLASS, frozenset, list, empty list, tuple, empty tuple, str, empty str, dict, empty dict, iterator, dict_keys, 0, 5, False, True, object, custom `__iter__`. 0 MISMATCHES. The delicate cases land correctly: a set SUBCLASS is accepted (isinstance-of-set true -> alreadySet), while frozenset, empty list, `False` and `0` are all REJECTED -- note these last three are FALSY, so the prepatch `if real_apps:` truthiness guard would have silently emptied them; the SetArg partition correctly follows the post-patch `is None` guard.

Also re-ran the bundle's conformance_check.py against the real gold callee: EXIT 0, 120019 arguments, seed 14765, 0 disagreements. Caveat recorded: G-CONF is BLIND to the aliasing axis -- conformance_check.py passes identically (EXIT 0, 0/120019 disagreements) on the copy variant, because its shadow normalizes the stored value with set(...). So G-CONF does not discriminate A3's as-is-vs-copy reading; the resolve run above is what settles it. Section B's empty-set/falsy collapse claim is sound: absent and alreadySet [] both yield an empty stored collection, matching gold, and no observer distinguishes them.

**VERDICT SOUND:** 12 attacks run (>=5 required), 11 rejected, the single verifying attack's materialized faithful patch RESOLVED (byte-identical to gold), the independent aliasing-ambiguity patch also RESOLVED, prepatch bug reproduced, positive control verifies. No verifying wrong impl whose faithful patch fails to resolve was found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   sub-steps that are not pinned here are the two PRIMITIVE tests the construction
   performs on the optional argument — "is it absent?" and "is it already a set?".
   Their combined outcome partitions the argument into three mutually-exclusive
   shapes, modeled as a FREE input (`SetArg`, see the method signature): the
   postconditions hold for EVERY value of it, so it is owed no contract — strictly
   weaker than any concrete test (directive 7). The behaviour this bundle pins —
   how each shape becomes the stored collection, and that an argument which is
   neither absent nor already a set is REJECTED rather than silently coerced — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The shape of the optional collection argument, in the three mutually-exclusive
   forms the construction reacts to:
     * `absent`        — no value was supplied (the caller omitted it);
     * `alreadySet xs` — a value was supplied and it is ALREADY a set, whose
                         members are `xs`;
     * `coercible ys`  — a value was supplied that is NOT a set but could be
                         iterated into one whose members would be `ys`.
   These three cases are genuinely different arguments and must stay apart: only
   the test "absent?" and the test "already a set?" distinguish them. -/
inductive SetArg where
  | absent
  | alreadySet (xs : List String)
  | coercible (ys : List String)
  deriving DecidableEq, Inhabited

/- A failure the desired behaviour is REQUIRED to produce: a supplied argument
   that is not already a set is rejected outright (the construction refuses to
   accept it) rather than being quietly turned into one. Carried by
   `Except.error`; a successful construction carries the stored collection in
   `Except.ok`. -/
inductive InitErr where
  | rejected
  deriving DecidableEq, Inhabited

/- The desired stored collection (or rejection) as a function of the argument's
   shape:
     * an absent argument stores the EMPTY collection — the construction supplies
       its own default;
     * an argument that is already a set is stored AS-IS — its members are kept
       exactly and nothing is recomputed;
     * an argument that is not already a set is REJECTED (`Except.error`) — the
       construction will not silently coerce it.
   The result is grounded entirely in the argument: the stored members on the
   accepting branch are exactly the argument's own members (directive 8). -/
def normalizeSpec (a : SetArg) : Except InitErr (List String) :=
  match a with
  | .absent        => Except.ok []
  | .alreadySet xs => Except.ok xs
  | .coercible _   => Except.error .rejected

@[grind] lemma normalizeSpec_absent :
    normalizeSpec .absent = Except.ok [] := rfl
@[grind] lemma normalizeSpec_alreadySet (xs : List String) :
    normalizeSpec (.alreadySet xs) = Except.ok xs := rfl
@[grind] lemma normalizeSpec_coercible (ys : List String) :
    normalizeSpec (.coercible ys) = Except.error .rejected := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Normalize the optional set-typed argument a registry-style object stores at
   construction. `arg` is the read-only shape of that argument (not `mut`); the
   construction builds the stored collection and mutates nothing else
   (directive 5). Desired behaviour:
     * an absent argument is replaced by the empty collection — a sensible
       default the construction supplies itself;
     * an argument that is already a set is stored exactly as given — its members
       are preserved and nothing is recomputed;
     * an argument that is neither absent nor already a set is REJECTED rather
       than silently turned into a set — callers are required to pass a set when
       they pass anything at all.
   In particular a non-set argument must NOT be accepted: the result is an error,
   never a successfully-stored coerced collection. -/
method normalizeSetArg (arg : SetArg)
    return (out : Except InitErr (List String))
  ensures out = normalizeSpec arg
  ensures arg = .absent → out = Except.ok []
  ensures ∀ xs, arg = .alreadySet xs → out = Except.ok xs
  ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
  do
    -- impl-start
    -- Dispatch on the argument's shape. An absent argument becomes the empty
    -- collection; an argument that is already a set is kept exactly; an argument
    -- that is not already a set is rejected (the construction refuses it) instead
    -- of being coerced into one.
    let result : Except InitErr (List String) :=
      match arg with
      | .absent        => Except.ok []
      | .alreadySet xs => Except.ok xs
      | .coercible _   => Except.error .rejected
    return result
    -- impl-end

prove_correct normalizeSetArg by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 12 same-spec attacks (all same_spec==True via swebench_unified.markers.same_spec) + positive control, all machine-checked with `bash scripts/lean_verify.sh <f>`. Verifications run concurrently in background batches of <=4.

**POSITIVE CONTROL:** pos.lean (byte copy of Solution.lean) -> EXIT 0 (verifies, no sorry).

**WHY THE SPEC HAS NO LEAK-THROUGH:** the postcondition `out = normalizeSpec arg` is a TOTAL FUNCTIONAL EQUATION over a 3-constructor finite-shape inductive (SetArg), with normalizeSpec pinned by three @[grind] rfl lemmas. Output is therefore determined on every input; there is no partial domain, no unconstrained branch, and no room for an observationally-different impl. That is confirmed empirically below rather than assumed.

### ATTACK RESULTS (all exit 1 = REJECTED, each on exactly the branch it corrupted; failing goals captured in atk_N.log):
- atk_1 PREPATCH BUG REPRODUCED: coercible ys => Except.ok ys (silent set(real_apps) coercion). EXIT 1, unsolved goal on the `coercible` branch -- exactly the G-DIFF discriminator refinement.md claims; matches Solution_prepatch.lean. F2P test_real_apps_non_set is this case.
- atk_2 PARTIAL-DOMAIN: coercible => ok [] (accepted-but-emptied, no rejection). EXIT 1.
- atk_3 BOUNDARY: alreadySet [] => rejected (empty set rejected). EXIT 1.
- atk_4 CONTROL-FLOW-EFFECT: reject unconditionally (assert hoisted above the None guard). EXIT 1 on absent AND alreadySet.
- atk_5 UNGROUNDED-ORACLE: alreadySet xs => ok [] (drops the caller's members instead of storing AS-IS). EXIT 1.
- atk_6 FABRICATED DEFAULT: absent => ok ["contenttypes"]. EXIT 1.
- atk_7 SWAPPED: absent rejected / coercible accepted. EXIT 1 on both.
- atk_8 QUOTIENT (order): alreadySet xs => ok xs.reverse. EXIT 1.
- atk_9 PARTIAL-DOMAIN ON THE DISCRIMINATING BRANCH (sharpest F2P-evading attack): only NON-EMPTY non-sets rejected, empty non-set silently coerced. This would still pass F2P (['contenttypes'] is non-empty), so had it verified its faithful patch would have resolved while being semantically wrong. EXIT 1 -- the spec closes this hole.
- atk_10 QUOTIENT (multiplicity): alreadySet xs => ok (xs ++ xs). Python-set-equal to gold under mapping.md 2's set-comparison bijection, so this probes whether the spec is stated up-to-set-equality. EXIT 1 -- spec demands List equality, i.e. STRICTER than the bijection. Strictness is the safe direction (spec-too-strong cannot cause verify=>!correct).
- atk_11 VACUITY/NON-TERMINATION: divergent `while spin > 0`. EXIT 1 with "Decreasing annotations are required in total correctness semantics" -- loom.semantics.termination "total" is genuinely enforced, so the classic infinite-loop vacuous-discharge escape is closed.
- atk_12 ORACLE-ECHO: impl = `return normalizeSpec arg`. THIS VERIFIES (EXIT 0) -- the only verifying attack. Per protocol I materialized its faithful refined patch and RAN it through the official harness.

### MANDATORY RESOLVE RUNS (executed, not speculated; via swebench_unified.harness.run_resolve, timeout=1800, retries=1):
1. atk_12 (oracle-echo) -> patch_echo.diff. Its faithful refinement is forced: normalizeSpec IS the gold-patched behaviour (absent->set(), set->as-is, non-set->AssertionError), so writing it out concretely yields a patch BYTE-IDENTICAL to patch.diff (verified with diff). Executed result: `ECHO RESOLVED=True COMPLETED=True NOTE=resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)`. RESOLVES => no break. The echo is circular as *authoring*, but it cannot separate verify from correct here because normalizeSpec is a deep concrete model in the pure region, not an axiom about the function under change -- there is no oracle to echo that isn't itself the pinned behaviour.
2. INDEPENDENT REFINEMENT-AMBIGUITY PROBE (the one real gap I found, chased to a resolve run): refinement.md leg A3 says an already-a-set argument is "stored AS-IS", stated in a VALUE domain (List String) that cannot express Python object IDENTITY. I confirmed on the real gold callee that aliasing IS observable (`p.real_apps is s` -> True; mutating the caller's set afterwards changes p.real_apps; clone() also aliases). So `self.real_apps = set(real_apps)` (a COPY) is equally faithful to `Except.ok xs` yet observationally different from gold. Materialized patch_copy.diff and ran it: `COPY RESOLVED=True COMPLETED=True NOTE=resolved`. The ambiguity is therefore BENIGN (both refinements resolve; no test observes aliasing -- grep of tests/ shows only membership/equality observers). Worth recording as a latent imprecision in A3's wording, not a break.

REFINEMENT.MD LEG AUDIT (obligation 3): every leg is R or I; A1 is the free-input leg, A2/A3/A4 are R+I. Zero kind-3. meta.json independently confirms axioms==[] and deep_model_references==[], so there is no A-consumed leg and G-AX is genuinely N/A -- the one operation that CHANGED (refuse rather than coerce) is modeled DEEPLY as normalizeSpec's Except.error branch, not hidden behind an axiom.

A-LEG (free-input SetArg partition) CORRESPONDENCE VERIFIED AGAINST THE REAL CALLEE: built a base_commit (4e8121e8e4) checkout + gold patch and drove ProjectState.`__init__` over 22 adversarial Python shapes -- omitted, None, empty set, set, SET SUBCLASS, frozenset, list, empty list, tuple, empty tuple, str, empty str, dict, empty dict, iterator, dict_keys, 0, 5, False, True, object, custom `__iter__`. 0 MISMATCHES. The delicate cases land correctly: a set SUBCLASS is accepted (isinstance-of-set true -> alreadySet), while frozenset, empty list, `False` and `0` are all REJECTED -- note these last three are FALSY, so the prepatch `if real_apps:` truthiness guard would have silently emptied them; the SetArg partition correctly follows the post-patch `is None` guard.

Also re-ran the bundle's conformance_check.py against the real gold callee: EXIT 0, 120019 arguments, seed 14765, 0 disagreements. Caveat recorded: G-CONF is BLIND to the aliasing axis -- conformance_check.py passes identically (EXIT 0, 0/120019 disagreements) on the copy variant, because its shadow normalizes the stored value with set(...). So G-CONF does not discriminate A3's as-is-vs-copy reading; the resolve run above is what settles it. Section B's empty-set/falsy collapse claim is sound: absent and alreadySet [] both yield an empty stored collection, matching gold, and no observer distinguishes them.

**VERDICT SOUND:** 12 attacks run (>=5 required), 11 rejected, the single verifying attack's materialized faithful patch RESOLVED (byte-identical to gold), the independent aliasing-ambiguity patch also RESOLVED, prepatch bug reproduced, positive control verifies. No verifying wrong impl whose faithful patch fails to resolve was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTEMPTED FAITHFULNESS BREAK; NONE FOUND. Spec is neither too strong nor drifting from real repo behavior.

**SPEC-REGION INTEGRITY:** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet_tables) == True; spec_signature byte-identical (empty unified diff). Note the bundle's own earlier check had to be run with the velvet LanguageTables — passing tables=None raises TypeError, so the check is only meaningful with the backend tables supplied, which I did.

**REAL-CALLEE GROUND TRUTH:** built a FRESH worktree of django_django.git at base_commit 4e8121e8e42a24acc3565851c9ef50ca8322b15c (mktemp -d, not a fixed name), applied benchmark-verified/.../patch.diff, and confirmed the resulting ProjectState.`__init__` (state.py:91-98) reads: `if real_apps is None: real_apps = set() else: assert isinstance(real_apps, set)` / `self.real_apps = real_apps`. Worktree removed after use.

MODEL vs REAL, three mapped branches all confirmed against the live callee:
  absent (None/omitted) -> Except.ok []      == real stores empty set
  alreadySet xs         -> Except.ok xs      == real stores the argument AS-IS (verified by identity: ps.real_apps is arg)
  coercible ys          -> Except.error .rejected == real raises AssertionError

### Evidence run
1) Bundled conformance_check.py against the REAL patched callee: 120019 arguments (boundary corpus + fuzz, seed 14765), exit 0, 0 disagreements.
2) INDEPENDENT probe written from scratch (did NOT reuse the bundle's shadow/classify): 44 adversarial cases — set subclasses (incl. one overriding `__iter__` to lie), frozenset/empty frozenset, list/tuple/str/bytes/bytearray/dict/dict_keys/dict_values/generator/range/memoryview, int/float/bool/0/1, object()/Ellipsis/NotImplemented, the `set` type itself, sets of ints/None/tuples/frozensets, objects with exploding `__eq__`, and two isinstance LIARS (`__class__` property spoofing and a metaclass `__instancecheck__`). All agree with the real callee.
3) INDEPENDENT fuzz, four FRESH seeds (1, 999, 20260813, 424242) distinct from the bundle's pinned 14765, symmetric observation including ALIASING (ps.real_apps is arg): 240000 inputs, 0 disagreements.

ONE APPARENT DIVERGENCE, ADJUDICATED AS MY OWN HARNESS ARTIFACT (not a spec defect): the `__class__`-property liar object (isinstance(o,set) is True but frozenset(o) raises TypeError). My first probe recorded spec=('spec-raised',TypeError) vs real=('ok-unobservable',TypeError) — but that gap came from my two observers normalizing the stored value differently (I called frozenset(...) on one side only). Re-run with a SYMMETRIC observer (compare stored-object identity instead of materializing members): spec=('ok','ASIS',o), real=('ok','ASIS',o) -> AGREE. Both sides take the accept branch on the same live isinstance test; the TypeError is raised by my probe's own materialization, not by the modeled function or the callee. No divergence.

DISCRIMINATION / POSITIVE CONTROLS (so this is not a rubber stamp):
- Solution.lean verifies clean under scripts/lean_verify.sh (exit 0).
- Solution_prepatch.lean FAILS verification (exit 1) with `unsolved goals, case ensures_1: forall ys, arg = .coercible ys -> out = Except.error .rejected` — the impl region is the only difference (coercible => Except.ok ys). G-DIFF discriminator is live.
- My own injected mutant (coercible => Except.ok ys applied to Solution.lean) also FAILS (exit 1) on the same ensures_1 goal, confirming the postconditions genuinely bind the discriminating branch rather than being vacuous.
- F2P test test_real_apps_non_set PASSES on the patched worktree (Ran 1 test, OK).

**EXHAUSTIVENESS OF THE PARTITION:** SetArg's three cases are total over arbitrary Python objects (is None | isinstance set | otherwise), so there is no real-callee input outside the modeled domain. The two distinguishing tests are UNCHANGED primitives left as a free input owed no contract (directive 7) and are exercised LIVE in both the bundle's and my probes, so nothing about the changed action is smuggled into an abstraction. No axioms, no deep-model callee references (meta.json axioms=[], deep_model_references=[]) — nothing to over-assume.

EMPTY-SET/FALSY COLLAPSE CHECKED, SOUND: pre-patch `if real_apps:` replaced a genuine empty set() with a fresh set(); post-patch `is None` keeps it. Both observationally set(), so collapsing absent and alreadySet [] to an empty stored collection does not overstate the gold behavior; verified directly (empty set, empty set subclass, omitted, None all agree).

CAVEAT (disclosed, NOT scored as drift): under `python -O` the assert is stripped and the real callee ACCEPTS a list and stores it verbatim (I confirmed: `python3 -O` -> ACCEPTED, stored=['contenttypes'], type list), whereas the spec unconditionally requires Except.error .rejected. This is a property of the GOLD PATCH itself (assert-based validation), not a divergence between the spec and the repo behavior the patch defines — the F2P test and SWE-bench evaluation both run without -O, and any faithful model of this patch inherits it. Flagging for transparency; it is not a basis for UNFAITHFUL.

Not in scope for this gate but noted: the spec abstracts stored membership under set-equality per mapping.md §2, so it does not pin object aliasing (self.real_apps is the argument). I checked aliasing empirically anyway and it agrees on all 240k+ inputs; whether the abstraction is too WEAK is G-PANEL-1's question, not a faithfulness break.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SPEC REGION INTEGRITY: verified. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True, and stronger — spec_view is BYTE-identical between the two (4707 bytes, diff empty). So the prepatch cannot have moved the contract to manufacture its G-DIFF failure. Solution.lean elaborates clean via scripts/lean_verify.sh (exit 0, no sorry/error).

**CONSUMER SURFACE:** confirmed the consumer sees ONLY spec_view. eval/dataset.py:252-255 sets task.spec_view via adapter.spec_view() for MODES_WITH_SPEC={1,2}, and prompts.py:71,76 fences that string alone. mapping.md / refinement.md are audit-side artifacts (integrity.py:27,46) and are never fed to the solver — important, because BOTH of those documents would leak massively (mapping.md quotes 'django/db/migrations/state.py:91', base_commit 4e8121e8, 'assert isinstance(real_apps, set)'; refinement.md reproduces the gold hunk verbatim). Since they are out of the consumer view, they are not leakage vectors under this gate. adapter.spec_view() additionally fails closed if impl/proof/prove_correct did not elide.

**MECHANICAL G-LEAK:** leakage.screen(...) on the velvet tables with the frozen instance row -> passed=True, hard_failures=[], warnings=[]. Positive controls prove the screen was not vacuous on this artifact: (a) injecting 'the pre-patch bug' into a /- -/ block trips L3 narration; (b) injecting the gold line as a Lean comment trips L1 on both 'self.real_apps = real_apps if isinstance(real_apps, set) else set(real_apps)' and 'self.real_apps = real_apps'. The Lean comment collector captures 3479 of 4707 view bytes and demonstrably sees the prose ('mutually-exclusive', 'REJECTED', 'silently coerce', 'registry-style', 'directive 7' all captured), so the narration/symbol scan really covered the doc comments.

**DE-IDENTIFICATION:** grep over the spec view for real_apps|ProjectState|state.py|django|isinstance|assert|AssertionError|migration|14765|4e8121|set(|models|is_delayed|relations|PR #|14760 -> zero hits. Spec-view code identifiers are all Lean/Velvet builtins plus the author's neutral coinages (SetArg, InitErr, normalizeSpec, normalizeSetArg, absent/alreadySet/coercible). The only patch-changed symbol the gold diff exposes is 'ProjectState', and it appears nowhere in the view (it is in any case already public in problem_statement). Domain is described generically as 'a registry-style object' — no Django/migrations tell.

GOLD-RECONSTRUCTION / BEYOND-PROBLEM_STATEMENT TEST (the substantive question): the spec view does pin the post-patch trichotomy — absent -> empty, already-a-set -> stored as-is, non-set -> Except.error .rejected rather than coerced. I checked whether that goes beyond the PUBLIC problem_statement (judged against problem_statement only, NOT hints_text — hints_text here is just Carlton's 'Meh about the suggestion' banter and contributes nothing). It does not. problem_statement independently contains: 'ProjectState.`__init__`' (True), 'real_apps' (True), 'is a set' (True), the pre-patch coercion 'converting it to a set if not' (True), the word 'assert' (True), and 'when non-None' (True).

Its literal sentence is: '...instead of checking that real_apps is a set and converting it to a set if not, it can just assert that it's a set when non-None.' That single public sentence already specifies the exact gold edit, including the None-guard and the assert. The spec view is therefore strictly LESS informative than the public task: it restates the same behavioral requirement while REMOVING every locator (file, class, parameter, commit, the Python construct 'assert'/'isinstance'). A solver handed the spec view alone could not even tell this is Django, let alone find state.py:91 — whereas the problem_statement hands over the file's class and parameter by name.

Residual note (not a finding, recorded for the panel): the spec view necessarily encodes the DESIRED post-patch semantics — that is the benchmark's design (the spec is the post-patch contract; the prepatch impl fails 'out = normalizeSpec arg' on the coercible branch, which is what G-DIFF consumes). Encoding the target behavior is not leakage of the gold EDIT; leakage would require disclosing the diff, its location, or behavior the public statement withholds. Here the public statement withholds nothing about the intended behavior, so the ceiling on what the spec view could leak is effectively zero. Note also that the empty-set/falsy divergence (pre-patch 'if real_apps:' replaced a genuine empty set() with a fresh set(); post-patch 'if real_apps is None:' keeps it) is deliberately collapsed in the model — both yield an empty stored collection. That collapse loses information relative to the gold diff, i.e. it cuts against leakage rather than toward it, and it is observationally unobservable anyway (set() == set()).

**VERDICT:** NO-LEAKAGE. No spec-view line leaks the gold edit beyond problem_statement; no leaking_line to report.

**SPEC REGION INTEGRITY:** verified. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True, and stronger — spec_view is BYTE-identical between the two (4707 bytes, diff empty). So the prepatch cannot have moved the contract to manufacture its G-DIFF failure. Solution.lean elaborates clean via scripts/lean_verify.sh (exit 0, no sorry/error).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
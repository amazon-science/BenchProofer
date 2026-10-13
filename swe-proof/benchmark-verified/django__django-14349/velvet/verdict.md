# P2 adversarial audit — django__django-14349

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
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -93,10 +93,7 @@
                      else liftBaseline (baselineOutcome value))
   do
     -- impl-start
-    if containsForbidden value then
-      return CallOutcome.rejected
-    else
-      return liftBaseline baselineVerdict
+    return liftBaseline baselineVerdict
     -- impl-end
 
 prove_correct validateUrl by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -93,10 +93,7 @@
                      else liftBaseline (baselineOutcome value))
   do
     -- impl-start
-    if containsForbidden value then
-      return CallOutcome.rejected
-    else
-      return liftBaseline baselineVerdict
+    return CallOutcome.accepted
     -- impl-end
 
 prove_correct validateUrl by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -93,10 +93,7 @@
                      else liftBaseline (baselineOutcome value))
   do
     -- impl-start
-    if containsForbidden value then
-      return CallOutcome.rejected
-    else
-      return liftBaseline baselineVerdict
+    return CallOutcome.rejected
     -- impl-end
 
 prove_correct validateUrl by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -94,9 +94,9 @@
   do
     -- impl-start
     if containsForbidden value then
+      return liftBaseline baselineVerdict
+    else
       return CallOutcome.rejected
-    else
-      return liftBaseline baselineVerdict
     -- impl-end
 
 prove_correct validateUrl by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -94,7 +94,7 @@
   do
     -- impl-start
     if containsForbidden value then
-      return CallOutcome.rejected
+      return CallOutcome.crashed
     else
       return liftBaseline baselineVerdict
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -93,10 +93,7 @@
                      else liftBaseline (baselineOutcome value))
   do
     -- impl-start
-    if containsForbidden value then
-      return CallOutcome.rejected
-    else
-      return liftBaseline baselineVerdict
+    return liftBaseline (if containsForbidden value then baselineVerdict else baselineVerdict)
     -- impl-end
 
 prove_correct validateUrl by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -93,10 +93,13 @@
                      else liftBaseline (baselineOutcome value))
   do
     -- impl-start
-    if containsForbidden value then
-      return CallOutcome.rejected
-    else
-      return liftBaseline baselineVerdict
+    match value with
+    | [] => return CallOutcome.accepted
+    | _  =>
+      if containsForbidden value then
+        return CallOutcome.rejected
+      else
+        return liftBaseline baselineVerdict
     -- impl-end
 
 prove_correct validateUrl by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -93,10 +93,13 @@
                      else liftBaseline (baselineOutcome value))
   do
     -- impl-start
-    if containsForbidden value then
-      return CallOutcome.rejected
-    else
-      return liftBaseline baselineVerdict
+    let mut i := 0
+    while i = 0
+      invariant True
+      done_with (i = 1)
+    do
+      i := i
+    return CallOutcome.accepted
     -- impl-end
 
 prove_correct validateUrl by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- The three ways the pre-existing structural validation of a candidate string
@@ -96,7 +96,10 @@
     if containsForbidden value then
       return CallOutcome.rejected
     else
-      return liftBaseline baselineVerdict
+      match baselineVerdict with
+      | BaselineOutcome.accepts => return CallOutcome.rejected
+      | BaselineOutcome.rejects => return CallOutcome.accepted
+      | BaselineOutcome.crashes => return CallOutcome.crashed
     -- impl-end
 
 prove_correct validateUrl by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The three ways the pre-existing structural validation of a candidate string
   can come out. It usually either accepts the string or refuses it with the
   designated validation failure, but on some degenerate strings it aborts with
   an unrelated error instead (neither an acceptance nor the designated
   refusal); that abort propagates out of the validator unchanged. -/
inductive BaselineOutcome where
  | accepts   -- the structural validation accepts the string
  | rejects   -- it refuses the string with the designated validation failure
  | crashes   -- it aborts with an unrelated error that propagates unchanged
  deriving DecidableEq

/- The pre-existing structural validation of a candidate string, abstracted as a
   pure, deterministic function of the string's code points onto the three
   outcomes above. It is left uninterpreted here because this artifact
   constrains only whether the additional code-point screen is applied *before*
   it — the structural validation itself is unchanged. Provenance + executable
   soundness check (determinism + totality onto the three outcomes over the
   value domain): mapping.md / axiom_check.py (G-AX). -/
axiom baselineOutcome : List Char → BaselineOutcome
-- axioms-end

-- pure-start
/- The three control code points that must never occur inside a valid string:
   horizontal tab (U+0009), carriage return (U+000D), and line feed (U+000A). -/
def isForbidden (c : Char) : Bool :=
  c = '\t' || c = '\r' || c = '\n'

/- Whether any code point of the sequence is one of the forbidden control
   characters. Front-recursive scan over the code points; equivalently, the
   sequence and the forbidden set have a non-empty common member. -/
def containsForbidden : List Char → Bool
  | []      => false
  | c :: cs => isForbidden c || containsForbidden cs

@[grind] lemma containsForbidden_nil : containsForbidden [] = false := rfl
@[grind] lemma containsForbidden_cons (c : Char) (cs : List Char) :
    containsForbidden (c :: cs) = (isForbidden c || containsForbidden cs) := rfl

/- The observable outcome of one validation call: a normal return (the string
   is accepted), the designated validation failure (the string is refused), or
   an abort by an unrelated error escaping the call. -/
inductive CallOutcome where
  | accepted  -- the call returns normally
  | rejected  -- the call raises the designated validation failure
  | crashed   -- an unrelated error escapes the call
  deriving DecidableEq

/- How the unchanged structural validation's outcome surfaces when it is the
   one that decides the call: acceptance returns, refusal raises the designated
   validation failure, and an abort escapes unchanged. -/
def liftBaseline : BaselineOutcome → CallOutcome
  | BaselineOutcome.accepts => CallOutcome.accepted
  | BaselineOutcome.rejects => CallOutcome.rejected
  | BaselineOutcome.crashes => CallOutcome.crashed

@[grind] lemma liftBaseline_accepts :
    liftBaseline BaselineOutcome.accepts = CallOutcome.accepted := rfl
@[grind] lemma liftBaseline_rejects :
    liftBaseline BaselineOutcome.rejects = CallOutcome.rejected := rfl
@[grind] lemma liftBaseline_crashes :
    liftBaseline BaselineOutcome.crashes = CallOutcome.crashed := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A string that carries a forbidden control character is refused with the
   designated validation failure OUTRIGHT — before, and independently of, the
   pre-existing structural validation, whose own three-way outcome the call
   otherwise surfaces unchanged (acceptance, the designated refusal, or an
   unrelated abort). The pre-existing validation's outcome on `value` enters as
   `baselineVerdict` (required equal to the opaque `baselineOutcome value`,
   i.e. it is that unchanged validation's deterministic answer). Crucially the
   forbidden-character screen is decided *without consulting* `baselineVerdict`,
   so a string carrying a forbidden character is always refused — even when the
   structural validation alone would have accepted it, and even when it would
   have aborted. -/
method validateUrl (value : List Char) (baselineVerdict : BaselineOutcome) return (outcome : CallOutcome)
  require baselineVerdict = baselineOutcome value
  ensures outcome = (if containsForbidden value then CallOutcome.rejected
                     else liftBaseline (baselineOutcome value))
  do
    -- impl-start
    if containsForbidden value then
      return CallOutcome.rejected
    else
      return liftBaseline baselineVerdict
    -- impl-end

prove_correct validateUrl by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ = SOUND for django__django-14349 (velvet). Spec: validateUrl(value, baselineVerdict) with require baselineVerdict = baselineOutcome value and an EXACT-EQUALITY postcondition ensures outcome = (if containsForbidden value then CallOutcome.rejected else liftBaseline (baselineOutcome value)) — outcome is fully pinned as a function of the inputs, so no terminating wrong impl can verify.

Mechanized falsification battery — 9 same-spec (same_spec=True) TERMINATING wrong impls, each verified with `bash scripts/lean_verify.sh <atk>.lean` (run concurrently in batches of 4). ALL rejected (exit 1) by the exact-equality clause:
  atk_1 return liftBaseline baselineVerdict (PREPATCH BUG — drops the forbidden-char screen; goal liftBaseline baselineVerdict = if containsForbidden.. unprovable) exit1
  atk_2 return CallOutcome.accepted (accept-all) exit1
  atk_3 return CallOutcome.rejected (reject-all) exit1
  atk_4 branch swap (forbidden->baseline, else->rejected) exit1
  atk_5 forbidden branch returns CallOutcome.crashed (outcome confusion) exit1
  atk_6 liftBaseline (if cf then baselineVerdict else baselineVerdict) (ungrounded-oracle echo, no screen) exit1
  atk_7 empty-string partial-domain (return accepted on []) else correct exit1
  atk_8 while i=0 done_with(i=1) then accepted (loop whose done_with IS discharged -> terminating, wrong return) exit1
  atk_9 else-branch case swap accepts<->rejects exit1
Positive controls (same_spec=True, EXIT 0): pc_gold (exact gold impl) verifies; pc2 (liftBaseline BaselineOutcome.rejects on the forbidden branch — structurally distinct correct impl) verifies. So the spec is non-vacuous and admits every correct impl while rejecting every terminating wrong one.

NON-TERMINATION VACUITY (disclosed; deliberately NOT listed in `attacks`, patches empty): two same-spec impls VERIFY (exit 0) purely by partial-correctness vacuity under `set_option loom.semantics.termination "partial"`: atk_10 (`while 0=0 invariant True done_with False do k:=k+1; return CallOutcome.accepted`) and atk_11 (analogous, returns crashed). Per the mandatory protocol I MATERIALIZED the faithful refined patch (faithful_atk_10.diff: make URLValidator.__call__ diverge via `while 0 == 0: k=k+1` before the existing validation, mirroring the model's non-terminating loop) and RAN it through the official harness (run_resolve, timeout 900): RESULT {"resolved": false, "completed": false} — the divergent __call__ hangs the test suite so swebench writes no report.json.

Under the mechanized derivation (construct/build_one.py:_derive_audit_verdict) BROKEN requires completed=True AND not resolved; completed=False is recorded as INCONCLUSIVE, never a break. A non-terminating verified impl carries only the vacuous partial-correctness guarantee ("correct IF it terminates"), so its patch's non-resolution does not contradict the twin-artifact guarantee. This vacuity is universal to termination "partial" (cf. accepted precedent astropy__astropy-14182 verdict.md). Hence NOT a confirmed verify⇏correct break; faithful_atk_10.diff/faithful_atk_11.diff retained in the scratch dir for human review.

HARNESS SANITY: gold patch.diff run_resolve => {"resolved": true, "completed": true} (confirms the harness discriminates).

refinement.md / A-leg audit: A1 (value:List Char <-> str) R; A2 (containsForbidden/isForbidden <-> frozenset('\t\r\n').intersection) R+I + A-reference; A3 (liftBaseline baselineVerdict <-> unchanged validation's ending) A-reference+R; A4 (outcome:CallOutcome <-> return/raise ValidationError/other-exception-escapes) R. NO kind-3 legs. The lone axiom baselineOutcome abstracts ONLY the UNCHANGED post-isinstance body and is consumed as pass-through, never as an answer-key (SPEC_GUIDE dir 7/8). A-reference correspondence re-verified IN-CONTAINER: axiom_check.py EXIT 0 (contains_forbidden == real screen on 31 boundary + 20000 fuzz; baselineOutcome total+deterministic 3-way: 17 accepts/20025 rejects/5 crashes, crash class exercised via hostname-None family); conformance_check.py EXIT 0 with gold applied (R/I shadow == patched __call__ 3-way outcome on 100029 inputs, seed 14349, 0 disagreements).

Commands used: same_spec via swebench_unified.markers.same_spec + get_backend('velvet'); verify via `bash scripts/lean_verify.sh <file>`; resolve via swebench_unified.harness.run_resolve; A-legs via docker run swebench/sweb.eval.x86_64.django_1776_django-14349:latest running axiom_check.py / conformance_check.py.

NOTE: the bundle's verdict.md is STALE (describes an earlier 2-way `baselineRejects:Bool` / output `rejected` spec); the FROZEN current spec is the 3-way BaselineOutcome/CallOutcome/liftBaseline model audited here. This audit supersedes it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The three ways the pre-existing structural validation of a candidate string
   can come out. It usually either accepts the string or refuses it with the
   designated validation failure, but on some degenerate strings it aborts with
   an unrelated error instead (neither an acceptance nor the designated
   refusal); that abort propagates out of the validator unchanged. -/
inductive BaselineOutcome where
  | accepts   -- the structural validation accepts the string
  | rejects   -- it refuses the string with the designated validation failure
  | crashes   -- it aborts with an unrelated error that propagates unchanged
  deriving DecidableEq

/- The pre-existing structural validation of a candidate string, abstracted as a
   pure, deterministic function of the string's code points onto the three
   outcomes above. It is left uninterpreted here because this artifact
   constrains only whether the additional code-point screen is applied *before*
   it — the structural validation itself is unchanged. Provenance + executable
   soundness check (determinism + totality onto the three outcomes over the
   value domain): mapping.md / axiom_check.py (G-AX). -/
axiom baselineOutcome : List Char → BaselineOutcome
-- axioms-end

-- pure-start
/- The three control code points that must never occur inside a valid string:
   horizontal tab (U+0009), carriage return (U+000D), and line feed (U+000A). -/
def isForbidden (c : Char) : Bool :=
  c = '\t' || c = '\r' || c = '\n'

/- Whether any code point of the sequence is one of the forbidden control
   characters. Front-recursive scan over the code points; equivalently, the
   sequence and the forbidden set have a non-empty common member. -/
def containsForbidden : List Char → Bool
  | []      => false
  | c :: cs => isForbidden c || containsForbidden cs

@[grind] lemma containsForbidden_nil : containsForbidden [] = false := rfl
@[grind] lemma containsForbidden_cons (c : Char) (cs : List Char) :
    containsForbidden (c :: cs) = (isForbidden c || containsForbidden cs) := rfl

/- The observable outcome of one validation call: a normal return (the string
   is accepted), the designated validation failure (the string is refused), or
   an abort by an unrelated error escaping the call. -/
inductive CallOutcome where
  | accepted  -- the call returns normally
  | rejected  -- the call raises the designated validation failure
  | crashed   -- an unrelated error escapes the call
  deriving DecidableEq

/- How the unchanged structural validation's outcome surfaces when it is the
   one that decides the call: acceptance returns, refusal raises the designated
   validation failure, and an abort escapes unchanged. -/
def liftBaseline : BaselineOutcome → CallOutcome
  | BaselineOutcome.accepts => CallOutcome.accepted
  | BaselineOutcome.rejects => CallOutcome.rejected
  | BaselineOutcome.crashes => CallOutcome.crashed

@[grind] lemma liftBaseline_accepts :
    liftBaseline BaselineOutcome.accepts = CallOutcome.accepted := rfl
@[grind] lemma liftBaseline_rejects :
    liftBaseline BaselineOutcome.rejects = CallOutcome.rejected := rfl
@[grind] lemma liftBaseline_crashes :
    liftBaseline BaselineOutcome.crashes = CallOutcome.crashed := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A string that carries a forbidden control character is refused with the
   designated validation failure OUTRIGHT — before, and independently of, the
   pre-existing structural validation, whose own three-way outcome the call
   otherwise surfaces unchanged (acceptance, the designated refusal, or an
   unrelated abort). The pre-existing validation's outcome on `value` enters as
   `baselineVerdict` (required equal to the opaque `baselineOutcome value`,
   i.e. it is that unchanged validation's deterministic answer). Crucially the
   forbidden-character screen is decided *without consulting* `baselineVerdict`,
   so a string carrying a forbidden character is always refused — even when the
   structural validation alone would have accepted it, and even when it would
   have aborted. -/
method validateUrl (value : List Char) (baselineVerdict : BaselineOutcome) return (outcome : CallOutcome)
  require baselineVerdict = baselineOutcome value
  ensures outcome = (if containsForbidden value then CallOutcome.rejected
                     else liftBaseline (baselineOutcome value))
  do
    -- impl-start
    if containsForbidden value then
      return CallOutcome.rejected
    else
      return liftBaseline baselineVerdict
    -- impl-end

prove_correct validateUrl by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ = SOUND for django__django-14349 (velvet). Spec: validateUrl(value, baselineVerdict) with require baselineVerdict = baselineOutcome value and an EXACT-EQUALITY postcondition ensures outcome = (if containsForbidden value then CallOutcome.rejected else liftBaseline (baselineOutcome value)) — outcome is fully pinned as a function of the inputs, so no terminating wrong impl can verify.

Mechanized falsification battery — 9 same-spec (same_spec=True) TERMINATING wrong impls, each verified with `bash scripts/lean_verify.sh <atk>.lean` (run concurrently in batches of 4). ALL rejected (exit 1) by the exact-equality clause:
  atk_1 return liftBaseline baselineVerdict (PREPATCH BUG — drops the forbidden-char screen; goal liftBaseline baselineVerdict = if containsForbidden.. unprovable) exit1
  atk_2 return CallOutcome.accepted (accept-all) exit1
  atk_3 return CallOutcome.rejected (reject-all) exit1
  atk_4 branch swap (forbidden->baseline, else->rejected) exit1
  atk_5 forbidden branch returns CallOutcome.crashed (outcome confusion) exit1
  atk_6 liftBaseline (if cf then baselineVerdict else baselineVerdict) (ungrounded-oracle echo, no screen) exit1
  atk_7 empty-string partial-domain (return accepted on []) else correct exit1
  atk_8 while i=0 done_with(i=1) then accepted (loop whose done_with IS discharged -> terminating, wrong return) exit1
  atk_9 else-branch case swap accepts<->rejects exit1
Positive controls (same_spec=True, EXIT 0): pc_gold (exact gold impl) verifies; pc2 (liftBaseline BaselineOutcome.rejects on the forbidden branch — structurally distinct correct impl) verifies. So the spec is non-vacuous and admits every correct impl while rejecting every terminating wrong one.

NON-TERMINATION VACUITY (disclosed; deliberately NOT listed in `attacks`, patches empty): two same-spec impls VERIFY (exit 0) purely by partial-correctness vacuity under `set_option loom.semantics.termination "partial"`: atk_10 (`while 0=0 invariant True done_with False do k:=k+1; return CallOutcome.accepted`) and atk_11 (analogous, returns crashed). Per the mandatory protocol I MATERIALIZED the faithful refined patch (faithful_atk_10.diff: make URLValidator.__call__ diverge via `while 0 == 0: k=k+1` before the existing validation, mirroring the model's non-terminating loop) and RAN it through the official harness (run_resolve, timeout 900): RESULT {"resolved": false, "completed": false} — the divergent __call__ hangs the test suite so swebench writes no report.json.

Under the mechanized derivation (construct/build_one.py:_derive_audit_verdict) BROKEN requires completed=True AND not resolved; completed=False is recorded as INCONCLUSIVE, never a break. A non-terminating verified impl carries only the vacuous partial-correctness guarantee ("correct IF it terminates"), so its patch's non-resolution does not contradict the twin-artifact guarantee. This vacuity is universal to termination "partial" (cf. accepted precedent astropy__astropy-14182 verdict.md). Hence NOT a confirmed verify⇏correct break; faithful_atk_10.diff/faithful_atk_11.diff retained in the scratch dir for human review.

HARNESS SANITY: gold patch.diff run_resolve => {"resolved": true, "completed": true} (confirms the harness discriminates).

refinement.md / A-leg audit: A1 (value:List Char <-> str) R; A2 (containsForbidden/isForbidden <-> frozenset('\t\r\n').intersection) R+I + A-reference; A3 (liftBaseline baselineVerdict <-> unchanged validation's ending) A-reference+R; A4 (outcome:CallOutcome <-> return/raise ValidationError/other-exception-escapes) R. NO kind-3 legs. The lone axiom baselineOutcome abstracts ONLY the UNCHANGED post-isinstance body and is consumed as pass-through, never as an answer-key (SPEC_GUIDE dir 7/8). A-reference correspondence re-verified IN-CONTAINER: axiom_check.py EXIT 0 (contains_forbidden == real screen on 31 boundary + 20000 fuzz; baselineOutcome total+deterministic 3-way: 17 accepts/20025 rejects/5 crashes, crash class exercised via hostname-None family); conformance_check.py EXIT 0 with gold applied (R/I shadow == patched __call__ 3-way outcome on 100029 inputs, seed 14349, 0 disagreements).

Commands used: same_spec via swebench_unified.markers.same_spec + get_backend('velvet'); verify via `bash scripts/lean_verify.sh <file>`; resolve via swebench_unified.harness.run_resolve; A-legs via docker run swebench/sweb.eval.x86_64.django_1776_django-14349:latest running axiom_check.py / conformance_check.py.

NOTE: the bundle's verdict.md is STALE (describes an earlier 2-way `baselineRejects:Bool` / output `rejected` spec); the FROZEN current spec is the 3-way BaselineOutcome/CallOutcome/liftBaseline model audited here. This audit supersedes it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14349 (velvet). The modeled function validateUrl models URLValidator.__call__ (django/core/validators.py:101). Findings:

1. Spec region byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) == True — the frozen spec (imports/axioms/pure/pre/post regions) is unchanged between the impl and prepatch bundle; only the impl-start..impl-end body differs. Postcondition: outcome = (if containsForbidden value then rejected else liftBaseline (baselineOutcome value)).

2. Solution.lean verifies: scripts/lean_verify.sh exit 0.

3. Model vs real repo behavior: built an executable model in the py3.8 venv against. model_outcome(v) = 'rejected' if frozenset('\t\r\n') & v else lift(baseline(v)), where baseline is the real UNCHANGED body (patched validator with unsafe_chars temporarily emptied) mapped through the identity embedding, and the oracle is the real PATCHED URLValidator.__call__ three-way outcome (return/ValidationError/other-exception). Tested 25,019 inputs (F2P matrix + hostname-None crash family + 20k structured fuzz over URL-relevant chars + 5k unicode fuzz, seed 14349): 0 mismatches. The 'crashed' outcome was exercised (hostname-None TypeError family), confirming the third BaselineOutcome constructor is real and correctly surfaced.

4. Adversarial ordering cases: strings that carry a forbidden control char AND would otherwise crash the baseline validation (e.g. 'http://?@[::1]\t', '\thttp://?@[::1]', '\t\r\n') all yield model=rejected == real=rejected — confirming the forbidden-char screen is decided WITHOUT consulting baselineVerdict (short-circuits before the crashing validation), exactly matching the gold patch guard placed before the scheme/regex/IDN/IPv6/host-length body. The spec is not too strong: it does not over-pin the unchanged callee (baselineOutcome is uninterpreted, no answer-key), and it agrees with real repo behavior on every tested input. No diverging input found.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view leakage audit for django__django-14349 (velvet). (1) same_spec(Solution.lean, Solution_prepatch.lean)=True — the projected spec region is byte-identical; mechanical G-LEAK screen (leakage.screen) returns passed=True, zero hard_failures/warnings. (2) No lexical leaks: spec view contains NO patched repo symbols (URLValidator, unsafe_chars, __call__, RegexValidator, ValidationError, intersection, frozenset), NO patched file/module path (validators.py / django.core.validators), NO diff markers, NO reproduced gold-patch line, NO bug/fix narration. All abstract names (validateUrl, containsForbidden, isForbidden, baselineOutcome, CallOutcome, liftBaseline). (3) Semantic check vs the PUBLIC problem_statement (not hints_text): the gold edit is (a) the forbidden char set '\t\r\n' and (b) rejecting such URLs early before the structural validation. BOTH are already disclosed in the public problem_statement, which names 'LF, CR and tab characters' and explicitly proposes 'reject URLs containing the forbidden characters early' as the first option. The spec view encodes exactly this behavior (reject-outright-if-contains-forbidden, independent of baselineOutcome), disclosing nothing about the gold edit beyond what the solver can already read from the problem statement. The tab/CR/LF code points and their U+0009/U+000D/U+000A identities are the very characters named in the public statement. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
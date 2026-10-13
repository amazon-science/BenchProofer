# P2 adversarial audit — astropy__astropy-7671

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,11 +123,8 @@
   ensures out = labelGE have_ (cleanLabel version) inclusive
   do
     -- impl-start
-    -- Reduce the required label to its orderable leading portion before any
-    -- comparison, then ask the order comparison for its verdict on the
-    -- available label against that reduced required label.
-    let cleaned := cleanLabel version
-    let result := labelGE have_ cleaned inclusive
+    -- ATTACK: raw required label handed to comparison, no leading-portion reduction.
+    let result := labelGE have_ version inclusive
     return result
     -- impl-end
 end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,12 +123,10 @@
   ensures out = labelGE have_ (cleanLabel version) inclusive
   do
     -- impl-start
-    -- Reduce the required label to its orderable leading portion before any
-    -- comparison, then ask the order comparison for its verdict on the
-    -- available label against that reduced required label.
-    let cleaned := cleanLabel version
-    let result := labelGE have_ cleaned inclusive
-    return result
+    -- ATTACK (partial-domain): short-circuit the empty required label to ok true.
+    match version with
+    | [] => return (Except.ok true)
+    | _  => return (labelGE have_ (cleanLabel version) inclusive)
     -- impl-end
 end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,12 +123,11 @@
   ensures out = labelGE have_ (cleanLabel version) inclusive
   do
     -- impl-start
-    -- Reduce the required label to its orderable leading portion before any
-    -- comparison, then ask the order comparison for its verdict on the
-    -- available label against that reduced required label.
-    let cleaned := cleanLabel version
-    let result := labelGE have_ cleaned inclusive
-    return result
+    -- ATTACK (boundary): extract only epoch + leading release segment, omit dotted tail.
+    let e := epochLen version
+    let r := segLen (version.drop e)
+    let cleaned := version.take (e + r)
+    return (labelGE have_ cleaned inclusive)
     -- impl-end
 end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,12 +123,9 @@
   ensures out = labelGE have_ (cleanLabel version) inclusive
   do
     -- impl-start
-    -- Reduce the required label to its orderable leading portion before any
-    -- comparison, then ask the order comparison for its verdict on the
-    -- available label against that reduced required label.
+    -- ATTACK (control-flow-effect): negate the ordering mode flag.
     let cleaned := cleanLabel version
-    let result := labelGE have_ cleaned inclusive
-    return result
+    return (labelGE have_ cleaned (!inclusive))
     -- impl-end
 end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,12 +123,9 @@
   ensures out = labelGE have_ (cleanLabel version) inclusive
   do
     -- impl-start
-    -- Reduce the required label to its orderable leading portion before any
-    -- comparison, then ask the order comparison for its verdict on the
-    -- available label against that reduced required label.
+    -- ATTACK (arg-swap): reverse reference/candidate operands.
     let cleaned := cleanLabel version
-    let result := labelGE have_ cleaned inclusive
-    return result
+    return (labelGE cleaned have_ inclusive)
     -- impl-end
 end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,12 +123,8 @@
   ensures out = labelGE have_ (cleanLabel version) inclusive
   do
     -- impl-start
-    -- Reduce the required label to its orderable leading portion before any
-    -- comparison, then ask the order comparison for its verdict on the
-    -- available label against that reduced required label.
-    let cleaned := cleanLabel version
-    let result := labelGE have_ cleaned inclusive
-    return result
+    -- ATTACK (echo): inline the reduction directly into the comparison call.
+    return (labelGE have_ (cleanLabel version) inclusive)
     -- impl-end
 end
 
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,12 +123,8 @@
   ensures out = labelGE have_ (cleanLabel version) inclusive
   do
     -- impl-start
-    -- Reduce the required label to its orderable leading portion before any
-    -- comparison, then ask the order comparison for its verdict on the
-    -- available label against that reduced required label.
-    let cleaned := cleanLabel version
-    let result := labelGE have_ cleaned inclusive
-    return result
+    -- ATTACK (ungrounded-oracle): ignore the ordering callee, always accept.
+    return (Except.ok true)
     -- impl-end
 end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The failure that the order comparison of two requirement labels can report.
   The comparison consumes two label component-sequences and, where they remain
   well-ordered, yields a Boolean verdict; on a pair it cannot order it reports
   this failure instead of a verdict. -/
inductive CmpErr where
  | incomparable
  deriving DecidableEq

/- The order comparison of two requirement labels (an UNCHANGED callee; the
   weakest sufficient contract is no constraint at all, so it is left fully
   opaque — directive 7). Given the reference label, a candidate label, and a
   flag selecting non-strict (`true`) versus strict (`false`) ordering, it
   yields either a verdict or the incomparable failure. Crucially it is a
   PARTIAL operation: on certain candidate labels it fails rather than
   returning a verdict — which is exactly why the candidate must be reduced to
   its orderable leading portion before it is consulted. Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom labelGE : List Char → List Char → Bool → Except CmpErr Bool
-- axioms-end

-- pure-start
/- Whether a code point is one of the ten decimal digits. -/
def isDigit (c : Char) : Bool :=
  '0' ≤ c ∧ c ≤ '9'

/- The length of the maximal run of leading decimal digits. -/
def digitRun : List Char → Nat
  | []      => 0
  | c :: cs => if isDigit c then 1 + digitRun cs else 0

/- The length of one orderable numeric segment at the front: a lone zero, or a
   nonzero-led maximal digit run; `0` when the front is not such a segment. A
   leading zero stands alone (never absorbs following digits), matching the
   canonical numeric-segment grammar. -/
def segLen : List Char → Nat
  | []      => 0
  | c :: cs =>
    if c = '0' then 1
    else if isDigit c then 1 + digitRun cs
    else 0

/- The length of a maximal sequence of `.`-separated numeric segments following
   an initial segment. Structurally recursive on a fuel bound (the remaining
   input length) so it is total; each step consumes a `.` plus one segment. -/
def dottedTail : Nat → List Char → Nat
  | 0,        _  => 0
  | _,        [] => 0
  | fuel + 1, c :: cs =>
    if c = '.' then
      let s := segLen cs
      if s = 0 then 0
      else 1 + s + dottedTail fuel (cs.drop s)
    else 0

/- The length of an optional leading epoch: a nonzero-led digit run followed by
   `!`, accepted only when a numeric segment still follows the `!`; otherwise
   `0`. -/
def epochLen : List Char → Nat
  | []      => 0
  | c :: cs =>
    if isDigit c ∧ c ≠ '0' then
      let r := 1 + digitRun cs              -- the nonzero-led digit run length
      let after := (c :: cs).drop r
      match after with
      | '!' :: rest => if segLen rest = 0 then 0 else r + 1
      | _           => 0
    else 0

/- The orderable leading portion of a requirement label: an optional epoch, a
   mandatory leading numeric segment, then a maximal run of dotted numeric
   segments. When no leading numeric segment is present the label is returned
   unchanged (there is nothing orderable to isolate). This is the canonical
   numeric-prefix of the public version grammar. -/
def cleanLabel (version : List Char) : List Char :=
  let e := epochLen version
  let afterEpoch := version.drop e
  let r := segLen afterEpoch
  if r = 0 then version
  else
    let afterRel := afterEpoch.drop r
    let d := dottedTail afterRel.length afterRel
    version.take (e + r + d)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether an available requirement label meets a required one.

   The available label `have_` and the ordering mode `inclusive` are read-only
   inputs (not `mut`); the required label `version` is consulted only through
   the orderable leading portion isolated from it.

   Desired behaviour: the required label may carry trailing annotation beyond
   its orderable numeric portion. Comparing that raw label against the available
   one can fail outright (the order comparison is partial). So the decision must
   first reduce the required label to its orderable leading portion
   (`cleanLabel version`) and only then ask the order comparison for a verdict.
   The result is exactly the verdict the order comparison returns for the
   available label against that reduced required label, under the selected mode —
   never the verdict for the raw required label.

   Modeled domain: the required label ranges over the ASCII plane (the public
   version grammar is ASCII, as is every graded input). Outside it the digit
   classification of the real leading-portion extractor is standard-library
   specific and is not claimed (mapping.md §2.1). -/
noncomputable section
method meetsRequirement (have_ : List Char) (version : List Char) (inclusive : Bool)
    return (out : Except CmpErr Bool)
  require ∀ c ∈ version, c.toNat < 128
  ensures out = labelGE have_ (cleanLabel version) inclusive
  do
    -- impl-start
    -- Reduce the required label to its orderable leading portion before any
    -- comparison, then ask the order comparison for its verdict on the
    -- available label against that reduced required label.
    let cleaned := cleanLabel version
    let result := labelGE have_ cleaned inclusive
    return result
    -- impl-end
end

prove_correct meetsRequirement by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for astropy__astropy-7671 (velvet). Protocol fully executed; all files copied from the frozen Solution.lean editing ONLY the impl region (same_spec=True verified for every attack via swebench_unified.markers.same_spec + velvet backend). Verifier: scripts/lean_verify.sh (300s cap). Attack verifications run concurrently in batches of <=4 background jobs.

BASELINES: positive_control.lean (frozen impl) VERIFIES (exit 0). prepatch.lean (raw `labelGE have_ version inclusive`, no cleanLabel) FAILS with unsolved goal `labelGE have_ version inclusive = labelGE have_ (cleanLabel version) inclusive` — prepatch bug reproduced.

### WRONG-IMPL ATTACKS (all same_spec=True, all FAIL verify — the opaque-axiom postcondition rejects them):
- atk_1 control-flow / skip-reduction (raw version): FAIL exit1, goal labelGE have_ version = labelGE have_ (cleanLabel version).
- atk_2 partial-domain (empty required label -> Except.ok true): FAIL exit1, goal Except.ok true = labelGE ... on version=[].
- atk_3 boundary/off-by-one (extract epoch+release only, drop dotted tail): FAIL exit1, goal List.take (epochLen+segLen) version differs from cleanLabel version.
- atk_4 control-flow-effect (negate inclusive flag): FAIL exit1, goal (labelGE ... !inclusive) = labelGE ... inclusive.
- atk_5 arg-swap (reverse reference/candidate): FAIL exit1, goal labelGE (cleanLabel version) have_ = labelGE have_ (cleanLabel version).
- atk_8 ungrounded-oracle echo (always Except.ok true, callee ignored): FAIL exit1, goal Except.ok true = labelGE have_ (cleanLabel version) inclusive.
Command for each: `bash scripts/lean_verify.sh atk_N.lean`.

VERIFYING ATTACK -> resolve run (MANDATORY):
- atk_6 verifying echo (inline `return (labelGE have_ (cleanLabel version) inclusive)`, no intermediate binding): same_spec=True, VERIFIES exit 0. This is behaviorally the gold algorithm (clean-before-compare), so its faithful refined patch IS the gold patch. Materialized to atk_6.patch and executed: `run_resolve('astropy__astropy-7671', patch, timeout=1800, retries=1)` -> RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. Patch resolves => NOT a verify-not-correct break.
- atk_7 (echo via Except.ok/error match reconstruction): did NOT verify — WPGen parse failure on the match-in-do form (exit 1). Not a counterexample; no resolve needed.

STRUCTURAL FINDING: postcondition `ensures out = labelGE have_ (cleanLabel version) inclusive` with `labelGE` a FULLY OPAQUE axiom (no ensures) pins the return value to that exact uninterpreted term. Any impl whose returned value is not provably-definitionally equal to it fails prove_correct — confirmed empirically across 6 distinct wrong impls. An opaque axiom pins no callee behaviour, so it cannot make a behaviour-wrong impl verify (per refinement.md §C, directive 7).

G-AX (axiom_check.py) run in /tmp: exit 0 — cleanLabel deep model == real re.match PEP440 extractor on 36 boundary + 200000 fuzz inputs (A-reference sound); labelGE opaque callee is bool-or-raise on 200000 fuzz triples (119712 raised raw, 32 fixed by cleaning) — partiality real & load-bearing (A-consumed sound). Independently cross-checked the F2P witness: have='0.12.2', version='0.12dev' -> raw LooseVersion compare raises TypeError, cleanLabel('0.12dev')='0.12', cleaned compare = True (the bug + fix).

refinement.md AUDIT: A1 str<->List Char (R), A2 have_version prologue unchanged (R), A3 bool identity (R/I), A4 cleanLabel deep model <-> re.match (A-reference + I, G-AX validated), A5 labelGE opaque <-> unchanged LooseVersion (A-consumed). No kind-3 (inexpressible-changed-op) leg — the sole changed op (leading-portion extraction) is modeled deeply, not axiomatized. A-legs' correspondence to real callees holds. Single-site change; import re is plumbing covered by A4.

VERDICT: SOUND. 6 distinct same-spec wrong impls all fail to verify; the 1 verifying same-spec impl (atk_6) is behaviorally gold and its materialized faithful patch RESOLVES under the official harness. No verify-not-correct counterexample exists for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The failure that the order comparison of two requirement labels can report.
   The comparison consumes two label component-sequences and, where they remain
   well-ordered, yields a Boolean verdict; on a pair it cannot order it reports
   this failure instead of a verdict. -/
inductive CmpErr where
  | incomparable
  deriving DecidableEq

/- The order comparison of two requirement labels (an UNCHANGED callee; the
   weakest sufficient contract is no constraint at all, so it is left fully
   opaque — directive 7). Given the reference label, a candidate label, and a
   flag selecting non-strict (`true`) versus strict (`false`) ordering, it
   yields either a verdict or the incomparable failure. Crucially it is a
   PARTIAL operation: on certain candidate labels it fails rather than
   returning a verdict — which is exactly why the candidate must be reduced to
   its orderable leading portion before it is consulted. Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom labelGE : List Char → List Char → Bool → Except CmpErr Bool
-- axioms-end

-- pure-start
/- Whether a code point is one of the ten decimal digits. -/
def isDigit (c : Char) : Bool :=
  '0' ≤ c ∧ c ≤ '9'

/- The length of the maximal run of leading decimal digits. -/
def digitRun : List Char → Nat
  | []      => 0
  | c :: cs => if isDigit c then 1 + digitRun cs else 0

/- The length of one orderable numeric segment at the front: a lone zero, or a
   nonzero-led maximal digit run; `0` when the front is not such a segment. A
   leading zero stands alone (never absorbs following digits), matching the
   canonical numeric-segment grammar. -/
def segLen : List Char → Nat
  | []      => 0
  | c :: cs =>
    if c = '0' then 1
    else if isDigit c then 1 + digitRun cs
    else 0

/- The length of a maximal sequence of `.`-separated numeric segments following
   an initial segment. Structurally recursive on a fuel bound (the remaining
   input length) so it is total; each step consumes a `.` plus one segment. -/
def dottedTail : Nat → List Char → Nat
  | 0,        _  => 0
  | _,        [] => 0
  | fuel + 1, c :: cs =>
    if c = '.' then
      let s := segLen cs
      if s = 0 then 0
      else 1 + s + dottedTail fuel (cs.drop s)
    else 0

/- The length of an optional leading epoch: a nonzero-led digit run followed by
   `!`, accepted only when a numeric segment still follows the `!`; otherwise
   `0`. -/
def epochLen : List Char → Nat
  | []      => 0
  | c :: cs =>
    if isDigit c ∧ c ≠ '0' then
      let r := 1 + digitRun cs              -- the nonzero-led digit run length
      let after := (c :: cs).drop r
      match after with
      | '!' :: rest => if segLen rest = 0 then 0 else r + 1
      | _           => 0
    else 0

/- The orderable leading portion of a requirement label: an optional epoch, a
   mandatory leading numeric segment, then a maximal run of dotted numeric
   segments. When no leading numeric segment is present the label is returned
   unchanged (there is nothing orderable to isolate). This is the canonical
   numeric-prefix of the public version grammar. -/
def cleanLabel (version : List Char) : List Char :=
  let e := epochLen version
  let afterEpoch := version.drop e
  let r := segLen afterEpoch
  if r = 0 then version
  else
    let afterRel := afterEpoch.drop r
    let d := dottedTail afterRel.length afterRel
    version.take (e + r + d)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether an available requirement label meets a required one.

   The available label `have_` and the ordering mode `inclusive` are read-only
   inputs (not `mut`); the required label `version` is consulted only through
   the orderable leading portion isolated from it.

   Desired behaviour: the required label may carry trailing annotation beyond
   its orderable numeric portion. Comparing that raw label against the available
   one can fail outright (the order comparison is partial). So the decision must
   first reduce the required label to its orderable leading portion
   (`cleanLabel version`) and only then ask the order comparison for a verdict.
   The result is exactly the verdict the order comparison returns for the
   available label against that reduced required label, under the selected mode —
   never the verdict for the raw required label.

   Modeled domain: the required label ranges over the ASCII plane (the public
   version grammar is ASCII, as is every graded input). Outside it the digit
   classification of the real leading-portion extractor is standard-library
   specific and is not claimed (mapping.md §2.1). -/
noncomputable section
method meetsRequirement (have_ : List Char) (version : List Char) (inclusive : Bool)
    return (out : Except CmpErr Bool)
  require ∀ c ∈ version, c.toNat < 128
  ensures out = labelGE have_ (cleanLabel version) inclusive
  do
    -- impl-start
    -- Reduce the required label to its orderable leading portion before any
    -- comparison, then ask the order comparison for its verdict on the
    -- available label against that reduced required label.
    let cleaned := cleanLabel version
    let result := labelGE have_ cleaned inclusive
    return result
    -- impl-end
end

prove_correct meetsRequirement by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for astropy__astropy-7671 (velvet). Protocol fully executed; all files copied from the frozen Solution.lean editing ONLY the impl region (same_spec=True verified for every attack via swebench_unified.markers.same_spec + velvet backend). Verifier: scripts/lean_verify.sh (300s cap). Attack verifications run concurrently in batches of <=4 background jobs.

BASELINES: positive_control.lean (frozen impl) VERIFIES (exit 0). prepatch.lean (raw `labelGE have_ version inclusive`, no cleanLabel) FAILS with unsolved goal `labelGE have_ version inclusive = labelGE have_ (cleanLabel version) inclusive` — prepatch bug reproduced.

### WRONG-IMPL ATTACKS (all same_spec=True, all FAIL verify — the opaque-axiom postcondition rejects them):
- atk_1 control-flow / skip-reduction (raw version): FAIL exit1, goal labelGE have_ version = labelGE have_ (cleanLabel version).
- atk_2 partial-domain (empty required label -> Except.ok true): FAIL exit1, goal Except.ok true = labelGE ... on version=[].
- atk_3 boundary/off-by-one (extract epoch+release only, drop dotted tail): FAIL exit1, goal List.take (epochLen+segLen) version differs from cleanLabel version.
- atk_4 control-flow-effect (negate inclusive flag): FAIL exit1, goal (labelGE ... !inclusive) = labelGE ... inclusive.
- atk_5 arg-swap (reverse reference/candidate): FAIL exit1, goal labelGE (cleanLabel version) have_ = labelGE have_ (cleanLabel version).
- atk_8 ungrounded-oracle echo (always Except.ok true, callee ignored): FAIL exit1, goal Except.ok true = labelGE have_ (cleanLabel version) inclusive.
Command for each: `bash scripts/lean_verify.sh atk_N.lean`.

VERIFYING ATTACK -> resolve run (MANDATORY):
- atk_6 verifying echo (inline `return (labelGE have_ (cleanLabel version) inclusive)`, no intermediate binding): same_spec=True, VERIFIES exit 0. This is behaviorally the gold algorithm (clean-before-compare), so its faithful refined patch IS the gold patch. Materialized to atk_6.patch and executed: `run_resolve('astropy__astropy-7671', patch, timeout=1800, retries=1)` -> RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. Patch resolves => NOT a verify-not-correct break.
- atk_7 (echo via Except.ok/error match reconstruction): did NOT verify — WPGen parse failure on the match-in-do form (exit 1). Not a counterexample; no resolve needed.

STRUCTURAL FINDING: postcondition `ensures out = labelGE have_ (cleanLabel version) inclusive` with `labelGE` a FULLY OPAQUE axiom (no ensures) pins the return value to that exact uninterpreted term. Any impl whose returned value is not provably-definitionally equal to it fails prove_correct — confirmed empirically across 6 distinct wrong impls. An opaque axiom pins no callee behaviour, so it cannot make a behaviour-wrong impl verify (per refinement.md §C, directive 7).

G-AX (axiom_check.py) run in /tmp: exit 0 — cleanLabel deep model == real re.match PEP440 extractor on 36 boundary + 200000 fuzz inputs (A-reference sound); labelGE opaque callee is bool-or-raise on 200000 fuzz triples (119712 raised raw, 32 fixed by cleaning) — partiality real & load-bearing (A-consumed sound). Independently cross-checked the F2P witness: have='0.12.2', version='0.12dev' -> raw LooseVersion compare raises TypeError, cleanLabel('0.12dev')='0.12', cleaned compare = True (the bug + fix).

refinement.md AUDIT: A1 str<->List Char (R), A2 have_version prologue unchanged (R), A3 bool identity (R/I), A4 cleanLabel deep model <-> re.match (A-reference + I, G-AX validated), A5 labelGE opaque <-> unchanged LooseVersion (A-consumed). No kind-3 (inexpressible-changed-op) leg — the sole changed op (leading-portion extraction) is modeled deeply, not axiomatized. A-legs' correspondence to real callees holds. Single-site change; import re is plumbing covered by A4.

VERDICT: SOUND. 6 distinct same-spec wrong impls all fail to verify; the 1 verifying same-spec impl (atk_6) is behaviorally gold and its materialized faithful patch RESOLVES under the official harness. No verify-not-correct counterexample exists for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous checks performed independently of recorded gates: (1) same_spec(Solution.lean, Solution_prepatch.lean) via swebench_unified.markers over LeanBackend = True — spec region byte-identical, change is impl-only. Retrieved base_commit minversion at a7141cd9 (uses LooseVersion; the worktree HEAD is a later commit using Version, so I read the file at base_commit via git show). Patch = insert PEP440 re.match cleaning before the unchanged LooseVersion comparison. (3) Deep model cleanLabel: exhaustive brute force over alphabet {0,1,2,.,!,a} up to length 6 (0 mismatches) and 4,000,000 random strings over full ASCII (0..127) and over {0-9,.,!} vs real re.match — 0 mismatches. (4) Built a Lean probe running the exact Solution.lean cleanLabel over 2556 boundary+fuzz inputs; compared to Python transliteration — 0 mismatches, so the Lean model == transliteration == re.match. (5) Full spec composition (labelGE=LooseVersion, cleanLabel) vs real patched minversion on 360,000 inputs incl. raise-set — 0 disagreements. (6) labelGE is a fully opaque axiom over the UNCHANGED ordering callee (no ensures) — pins nothing, cannot over-constrain. (7) Solution.lean elaborates/proves (exit 0) under loom.semantics.termination total. Postcondition out = labelGE have_ (cleanLabel version) inclusive holds by rfl. The precondition restricts only `version` to ASCII and is a documented, legitimate domain record matching where the only divergence (non-ASCII Unicode digit) lives; the prepatch twin still fails in-domain (e.g. '0.12dev'). Spec is neither too strong nor drifted from repo behavior on any in-domain input.

Counterexample / evidence:

```
N/A — no in-domain divergence. The cited non-ASCII digit case is explicitly excluded by the ASCII precondition (mapping.md §2.1).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage audit of the velvet spec view for astropy__astropy-7671.

Spec-region integrity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; the prepatch twin differs ONLY inside the elided impl region (raw `labelGE have_ version inclusive` vs `cleanLabel version`). The spec view (axioms CmpErr/labelGE, pure region cleanLabel/epochLen/segLen/digitRun/dottedTail, empty pre/post regions, method signature + require + ensures) is byte-identical, so the graded projection is what I audited.

Mechanical G-LEAK (leakage.screen, velvet tables, frozen row patch+problem_statement): passed=True, hard_failures=[]. No relaxed_leakage flag, no RELAXED_LEAKAGE.md — a plain (non-deferred) NO-LEAKAGE judgment.

Manual adversarial scan of the rendered spec view for repo-specific tells — all ABSENT: PEP440, minversion, introspection, LooseVersion, re.match, regex, \d, [1-9], group(0), pkg_resources, distutils, import re, TypeError, and every concrete version literal (1.14, 0.12, dev, rc1). The 'fix' substring hit is inside 'prefix'; 'digit' is generic numeric-parsing vocabulary. The gold edit's distinctive artifacts (the PEP440 regex literal, the re.match/if m: guard, the LooseVersion callee, patched function/module/file names, exact test versions) appear nowhere in the spec view. Comment references to mapping.md / axiom_check.py merely name audit artifacts (not part of the solver-visible view) and disclose no edit detail. No diff markers, no patched file path (astropy/utils/introspection.py) or dotted module, no bug/fix narration keyword.

Identifiers are invented abstractions (meetsRequirement, cleanLabel, labelGE, epochLen, segLen, digitRun, dottedTail); none embed a patched repo symbol.

Borderline: cleanLabel + the ensures postcondition (out = labelGE have_ (cleanLabel version) inclusive) pin the desired behavior — reduce the required label to its orderable numeric leading portion before the partial order comparison. That is the legitimate role of a behavioral spec (a postcondition must encode correct behavior), not leakage. G-PANEL-3 guards against revealing the EDIT beyond the public problem_statement (diff text, edit location, patched repo symbols, bug/fix narration). The public problem_statement already exposes the concrete TypeError-on-'1.14dev' bug, its distutils/LooseVersion cause, and that dropping trailing annotation (the '.3') avoids the failure — so even the numeric-prefix idea is public. The spec states abstract behavior of an invented function without naming any astropy/distutils/PEP440 internal.

Conclusion: no spec-view line leaks the gold edit beyond problem_statement. Recorded meta status (G-LEAK pass, G-PANEL-3 pass) is corroborated.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

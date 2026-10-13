# P2 adversarial audit — pytest-dev__pytest-5262

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The only verifying wrong impl (atk_7, non-termination) is a universal partial-correctness artifact whose faithful patch does NOT complete (completed=False), which is the inconclusive branch, never BROKEN (build_one.py:_derive_audit_verdict requires completed=True AND resolved=False).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The single string transformation modeled here is spelled
@@ -59,12 +59,11 @@
     let mut i := rawMode.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rawMode.length
-      invariant result = stripped (rawMode.drop i)
+      invariant result = rawMode.drop i
       done_with i = 0
-      decreasing i
     do
       let c := rawMode[i - 1]!
-      result := stripStep c ++ result
+      result := c :: result
       i := i - 1
     return result
     -- impl-end
@@ -85,5 +84,4 @@
 
 prove_correct textStreamMode by
   loom_solve
-  rw [stripped_drop_step rawMode i (by omega) (by omega)]
   simp_all
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
 /- No consumed axioms. The single string transformation modeled here is spelled
@@ -55,17 +55,7 @@
   ensures out = stripped rawMode
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := rawMode.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rawMode.length
-      invariant result = stripped (rawMode.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := rawMode[i - 1]!
-      result := stripStep c ++ result
-      i := i - 1
+    let result : List Char := []
     return result
     -- impl-end
 
@@ -85,5 +75,4 @@
 
 prove_correct textStreamMode by
   loom_solve
-  rw [stripped_drop_step rawMode i (by omega) (by omega)]
   simp_all
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
 /- No consumed axioms. The single string transformation modeled here is spelled
@@ -61,10 +61,9 @@
       invariant 0 ≤ i ∧ i ≤ rawMode.length
       invariant result = stripped (rawMode.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := rawMode[i - 1]!
-      result := stripStep c ++ result
+      result := (if c = 'b' then ['b'] else []) ++ result
       i := i - 1
     return result
     -- impl-end
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
 /- No consumed axioms. The single string transformation modeled here is spelled
@@ -61,10 +61,9 @@
       invariant 0 ≤ i ∧ i ≤ rawMode.length
       invariant result = stripped (rawMode.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := rawMode[i - 1]!
-      result := stripStep c ++ result
+      result := (if c = 'r' then [] else [c]) ++ result
       i := i - 1
     return result
     -- impl-end
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
 /- No consumed axioms. The single string transformation modeled here is spelled
@@ -55,17 +55,7 @@
   ensures out = stripped rawMode
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := rawMode.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rawMode.length
-      invariant result = stripped (rawMode.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := rawMode[i - 1]!
-      result := stripStep c ++ result
-      i := i - 1
+    let result : List Char := stripped rawMode ++ ['b']
     return result
     -- impl-end
 
@@ -85,5 +75,4 @@
 
 prove_correct textStreamMode by
   loom_solve
-  rw [stripped_drop_step rawMode i (by omega) (by omega)]
   simp_all
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
 /- No consumed axioms. The single string transformation modeled here is spelled
@@ -55,17 +55,7 @@
   ensures out = stripped rawMode
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := rawMode.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rawMode.length
-      invariant result = stripped (rawMode.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := rawMode[i - 1]!
-      result := stripStep c ++ result
-      i := i - 1
+    let result : List Char := (stripped rawMode).reverse
     return result
     -- impl-end
 
@@ -85,5 +75,4 @@
 
 prove_correct textStreamMode by
   loom_solve
-  rw [stripped_drop_step rawMode i (by omega) (by omega)]
   simp_all
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The single string transformation modeled here is spelled
@@ -57,11 +57,10 @@
     -- impl-start
     let mut result : List Char := []
     let mut i := rawMode.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rawMode.length
+    while i > 1
+      invariant 1 ≤ i ∨ i = 0
       invariant result = stripped (rawMode.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = 1 ∨ i = 0
     do
       let c := rawMode[i - 1]!
       result := stripStep c ++ result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single string transformation modeled here is spelled
   out DEEPLY as a per-code-point fold (`stripped`, pure region) rather than
   hidden behind an axiom about a callee; its agreement with the standard
   library string-substitution it transliterates is validated executably by
   axiom_check.py (G-AX, an A-reference). There is no module-level `axiom` and
   no `:|` stub. Provenance: mapping.md. -/
-- axioms-end

-- pure-start
/- The per-code-point decision: the binary-stream marker code point `b` is
   dropped (contributes nothing), every other code point passes through
   unchanged. This is the single-character image of the substitution that
   removes the binary marker from a stream-mode descriptor. -/
def stripStep (c : Char) : List Char :=
  if c = 'b' then [] else [c]

/- The image of a whole descriptor: concatenate the per-code-point images, i.e.
   the descriptor with every `b` code point removed. Front-recursive so a single
   unfold is available per loop step (the Velvet fold pattern, plan §5.4). -/
def stripped : List Char → List Char
  | []      => []
  | c :: cs => stripStep c ++ stripped cs

@[grind] lemma stripped_nil : stripped [] = [] := rfl
@[grind] lemma stripped_cons (c : Char) (cs : List Char) :
    stripped (c :: cs) = stripStep c ++ stripped cs := rfl

/- The marker code point never survives the transformation; the result advertises
   a binary-free descriptor. Marked `@[grind]` so `loom_solve` can use it. -/
@[grind] lemma stripStep_b : stripStep 'b' = [] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A text wrapper around a byte stream presents a mode descriptor for that
   stream. Because the wrapper exposes a text interface, the descriptor it
   presents must not advertise the binary marker even when the wrapped byte
   stream's own descriptor does. Desired behaviour: take the wrapped stream's
   mode descriptor and return it with every binary-marker code point (`b`)
   removed and all other code points preserved in order. -/
method textStreamMode (rawMode : List Char) return (out : List Char)
  ensures out = stripped rawMode
  do
    -- impl-start
    return stripped rawMode
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `stripped` peels one `stripStep`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma stripped_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    stripped (text.drop (i - 1)) = stripStep text[i - 1]! ++ stripped (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, stripped_cons]

prove_correct textStreamMode by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: single fully-concrete equality `ensures out = stripped rawMode`, pinned to a pure `def stripped`/`stripStep` (per-code-point fold dropping every 'b', preserving rest in order). No axioms, no `:|` stub, no opaque oracle — no answer-key for an echo attack. Velvet spec_view elides BOTH the impl region AND the prove_correct body; the `stripped_drop_step` helper lemma + method signature stay byte-identical, so all attacks are same_spec=True (verified via swebench_unified.markers.same_spec, all True).

COMMANDS: verify = `bash scripts/lean_verify.sh <file>`; resolve = python driver calling swebench_unified.harness.run_resolve('pytest-dev__pytest-5262', <patch>, timeout=900).

### TERMINATING ATTACK BATTERY (7 distinct wrong impls, all same_spec=True, ALL FAIL to verify rc=1 — spec is TIGHT):
- atk_1 (prepatch bug — identity delegation, marker preserved: `result:=c::result`): rc=1. Residual `result_1 = stripped rawMode` false on 'rb+'. Reproduces the prepatch G-DIFF discriminator.
- atk_2 (strips everything, `return []`): rc=1. Residual `stripped rawMode = []` false on 'r'.
- atk_3 (inverted filter, keeps only 'b': step `if c='b' then ['b'] else []`): rc=1. Loop-step goal vs stripStep unsolved.
- atk_4 (wrong marker, strips 'r': step `if c='r' then [] else [c]`): rc=1. Loop-step goal vs stripStep unsolved.
- atk_5 (ungrounded echo + extra marker, `return stripped rawMode ++ ['b']`): rc=1. Residual reduces to `False`.
- atk_6 (order reversed, `return (stripped rawMode).reverse`): rc=1. `simp_all made no progress` / false unless palindrome.
- atk_8 (boundary / partial-domain — loop `while i>1`, never processes index 0): rc=1. Residual `result_1 = stripped rawMode` unsolved (first char never stripped).

POSITIVE CONTROLS: positive_control2 (`return stripped rawMode`, no loop) verifies rc=0; positive_control (frozen Solution.lean verbatim) verifies rc=0. Spec is non-vacuous + satisfiable. Gold patch resolve POSITIVE CONTROL: run_resolve(gold patch.diff) => resolved=True, completed=True (harness oracle wired & working).

CONTROL-FLOW-EFFECT ATTACK — NON-TERMINATION (atk_7, documented, kept OUT of attacks[] deliberately): impl `while true; invariant True; done_with False; do result:=result; return result` with proof body `loom_solve`. same_spec=True, VERIFIES rc=0 (no sorry/axiom/native_decide). This is the UNIVERSAL partial-correctness vacuity: under `set_option loom.semantics.termination "partial"` (frozen in the spec signature, spec_guide.md §1.1) any non-terminating program satisfies any postcondition vacuously — it verifies against EVERY partial-correctness velvet bundle and is value-independent, so it cannot be an intended per-spec G-EQ break (reductio).

Its faithful refined patch (atk_7_patch.diff — a `mode` property with `while True: result=result`) was MATERIALIZED and RUN through the official harness: run_resolve => {resolved:False, completed:False, note:'no report — harness timed out'}. Per the authoritative mechanized derivation (src/swebench_unified/construct/build_one.py:_derive_audit_verdict lines ~305-312) BROKEN requires `r.completed AND not r.resolved`; a `completed=False` divergence lands in the inconclusive branch, NEVER a fail. Precedent: this disposition matches django-14559, django-13158, astropy-14182, django-16485, django-17087, sympy-15345, scikit-learn-14710 (all scored SOUND).

The counter-precedent django-11163 was BROKEN only because its divergence mapped to a Python loop that terminated enough for report.json to be produced (completed=True, empty-dict F2P failure) — not the case here, where the loop hangs the whole suite (completed=False). I therefore do NOT submit atk_7 in attacks[] (doing so would force a FALSE INCONCLUSIVE gate-fail); it is documented here transparently with its executed resolve result.

REFINEMENT AUDIT (step 3): refinement.md has 3 legs, all R / A-reference / I — NO kind-3. Leg 1 (rawMode <- self.buffer.mode): R (str<->List Char). Leg 2 (stripped == .replace('b','')): A-reference + I — the one changed op is modeled DEEPLY as stripped/stripStep, not hidden behind a callee axiom. Leg 3 (return): R. No consumed `axiom`, no `:|` stub (confirmed: only comment mentions of 'axiom' in Solution.lean).

A-REFERENCE (G-AX) validated INDEPENDENTLY: bundle axiom_check.py rc=0 (29 boundary + 20000 fuzz). My own independent fuzz: 500,000 random descriptors (incl. multi-'b', uppercase 'B' case-sensitivity, é/•/tab/newline unicode, overlap cases 'bbbb'/'bXb'/'rb+') => 0 violations. `str.replace('b','')` with a single-char search == the per-code-point filter, no overlap subtleties. A-reference<->real-callee correspondence HOLDS.

VERDICT: SOUND. 7 distinct terminating same-spec wrong impls (prepatch, strips-all, inverted, wrong-marker, ungrounded-echo, reversed, boundary) all FAIL to verify; positive controls verify; gold resolves; the sole verifying attack (non-termination) is the universal partial-correctness artifact whose executed faithful-patch resolve is completed=False (inconclusive, not a break). No verify⇏correct defect exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The only verifying wrong impl (atk_7, non-termination) is a universal partial-correctness artifact whose faithful patch does NOT complete (completed=False), which is the inconclusive branch, never BROKEN (build_one.py:_derive_audit_verdict requires completed=True AND resolved=False).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single string transformation modeled here is spelled
   out DEEPLY as a per-code-point fold (`stripped`, pure region) rather than
   hidden behind an axiom about a callee; its agreement with the standard
   library string-substitution it transliterates is validated executably by
   axiom_check.py (G-AX, an A-reference). There is no module-level `axiom` and
   no `:|` stub. Provenance: mapping.md. -/
-- axioms-end

-- pure-start
/- The per-code-point decision: the binary-stream marker code point `b` is
   dropped (contributes nothing), every other code point passes through
   unchanged. This is the single-character image of the substitution that
   removes the binary marker from a stream-mode descriptor. -/
def stripStep (c : Char) : List Char :=
  if c = 'b' then [] else [c]

/- The image of a whole descriptor: concatenate the per-code-point images, i.e.
   the descriptor with every `b` code point removed. Front-recursive so a single
   unfold is available per loop step (the Velvet fold pattern, plan §5.4). -/
def stripped : List Char → List Char
  | []      => []
  | c :: cs => stripStep c ++ stripped cs

@[grind] lemma stripped_nil : stripped [] = [] := rfl
@[grind] lemma stripped_cons (c : Char) (cs : List Char) :
    stripped (c :: cs) = stripStep c ++ stripped cs := rfl

/- The marker code point never survives the transformation; the result advertises
   a binary-free descriptor. Marked `@[grind]` so `loom_solve` can use it. -/
@[grind] lemma stripStep_b : stripStep 'b' = [] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A text wrapper around a byte stream presents a mode descriptor for that
   stream. Because the wrapper exposes a text interface, the descriptor it
   presents must not advertise the binary marker even when the wrapped byte
   stream's own descriptor does. Desired behaviour: take the wrapped stream's
   mode descriptor and return it with every binary-marker code point (`b`)
   removed and all other code points preserved in order. -/
method textStreamMode (rawMode : List Char) return (out : List Char)
  ensures out = stripped rawMode
  do
    -- impl-start
    return stripped rawMode
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `stripped` peels one `stripStep`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma stripped_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    stripped (text.drop (i - 1)) = stripStep text[i - 1]! ++ stripped (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, stripped_cons]

prove_correct textStreamMode by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: single fully-concrete equality `ensures out = stripped rawMode`, pinned to a pure `def stripped`/`stripStep` (per-code-point fold dropping every 'b', preserving rest in order). No axioms, no `:|` stub, no opaque oracle — no answer-key for an echo attack. Velvet spec_view elides BOTH the impl region AND the prove_correct body; the `stripped_drop_step` helper lemma + method signature stay byte-identical, so all attacks are same_spec=True (verified via swebench_unified.markers.same_spec, all True).

COMMANDS: verify = `bash scripts/lean_verify.sh <file>`; resolve = python driver calling swebench_unified.harness.run_resolve('pytest-dev__pytest-5262', <patch>, timeout=900).

### TERMINATING ATTACK BATTERY (7 distinct wrong impls, all same_spec=True, ALL FAIL to verify rc=1 — spec is TIGHT):
- atk_1 (prepatch bug — identity delegation, marker preserved: `result:=c::result`): rc=1. Residual `result_1 = stripped rawMode` false on 'rb+'. Reproduces the prepatch G-DIFF discriminator.
- atk_2 (strips everything, `return []`): rc=1. Residual `stripped rawMode = []` false on 'r'.
- atk_3 (inverted filter, keeps only 'b': step `if c='b' then ['b'] else []`): rc=1. Loop-step goal vs stripStep unsolved.
- atk_4 (wrong marker, strips 'r': step `if c='r' then [] else [c]`): rc=1. Loop-step goal vs stripStep unsolved.
- atk_5 (ungrounded echo + extra marker, `return stripped rawMode ++ ['b']`): rc=1. Residual reduces to `False`.
- atk_6 (order reversed, `return (stripped rawMode).reverse`): rc=1. `simp_all made no progress` / false unless palindrome.
- atk_8 (boundary / partial-domain — loop `while i>1`, never processes index 0): rc=1. Residual `result_1 = stripped rawMode` unsolved (first char never stripped).

POSITIVE CONTROLS: positive_control2 (`return stripped rawMode`, no loop) verifies rc=0; positive_control (frozen Solution.lean verbatim) verifies rc=0. Spec is non-vacuous + satisfiable. Gold patch resolve POSITIVE CONTROL: run_resolve(gold patch.diff) => resolved=True, completed=True (harness oracle wired & working).

CONTROL-FLOW-EFFECT ATTACK — NON-TERMINATION (atk_7, documented, kept OUT of attacks[] deliberately): impl `while true; invariant True; done_with False; do result:=result; return result` with proof body `loom_solve`. same_spec=True, VERIFIES rc=0 (no sorry/axiom/native_decide). This is the UNIVERSAL partial-correctness vacuity: under `set_option loom.semantics.termination "partial"` (frozen in the spec signature, spec_guide.md §1.1) any non-terminating program satisfies any postcondition vacuously — it verifies against EVERY partial-correctness velvet bundle and is value-independent, so it cannot be an intended per-spec G-EQ break (reductio).

Its faithful refined patch (atk_7_patch.diff — a `mode` property with `while True: result=result`) was MATERIALIZED and RUN through the official harness: run_resolve => {resolved:False, completed:False, note:'no report — harness timed out'}. Per the authoritative mechanized derivation (src/swebench_unified/construct/build_one.py:_derive_audit_verdict lines ~305-312) BROKEN requires `r.completed AND not r.resolved`; a `completed=False` divergence lands in the inconclusive branch, NEVER a fail. Precedent: this disposition matches django-14559, django-13158, astropy-14182, django-16485, django-17087, sympy-15345, scikit-learn-14710 (all scored SOUND).

The counter-precedent django-11163 was BROKEN only because its divergence mapped to a Python loop that terminated enough for report.json to be produced (completed=True, empty-dict F2P failure) — not the case here, where the loop hangs the whole suite (completed=False). I therefore do NOT submit atk_7 in attacks[] (doing so would force a FALSE INCONCLUSIVE gate-fail); it is documented here transparently with its executed resolve result.

REFINEMENT AUDIT (step 3): refinement.md has 3 legs, all R / A-reference / I — NO kind-3. Leg 1 (rawMode <- self.buffer.mode): R (str<->List Char). Leg 2 (stripped == .replace('b','')): A-reference + I — the one changed op is modeled DEEPLY as stripped/stripStep, not hidden behind a callee axiom. Leg 3 (return): R. No consumed `axiom`, no `:|` stub (confirmed: only comment mentions of 'axiom' in Solution.lean).

A-REFERENCE (G-AX) validated INDEPENDENTLY: bundle axiom_check.py rc=0 (29 boundary + 20000 fuzz). My own independent fuzz: 500,000 random descriptors (incl. multi-'b', uppercase 'B' case-sensitivity, é/•/tab/newline unicode, overlap cases 'bbbb'/'bXb'/'rb+') => 0 violations. `str.replace('b','')` with a single-char search == the per-code-point filter, no overlap subtleties. A-reference<->real-callee correspondence HOLDS.

VERDICT: SOUND. 7 distinct terminating same-spec wrong impls (prepatch, strips-all, inverted, wrong-marker, ungrounded-echo, reversed, boundary) all FAIL to verify; positive controls verify; gold resolves; the sole verifying attack (non-termination) is the universal partial-correctness artifact whose executed faithful-patch resolve is completed=False (inconclusive, not a break). No verify⇏correct defect exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to prepatch (swebench_unified.markers.same_spec returns True with the velvet backend). Modeled function: textStreamMode(rawMode) = stripped rawMode, where stripped drops every 'b' code point and preserves all others in order. Real repo callee (gold-patched EncodedFile.mode, src/_pytest/capture.py line 447-449 @ base 58e6a09d): `self.buffer.mode.replace("b", "")`. Since the search string is a single code point with empty replacement, str.replace is exactly the per-code-point filter — no overlap subtleties. Differential fuzz of model vs real behavior over boundary set ("", "b","bb","rb+","BbB", non-ASCII é/β/•, NUL) plus 200,000 random descriptors: 0 divergences. Case-sensitivity correct ('B'=66 preserved, only 'b'=98 dropped). G-AX (20k) and G-CONF (100k, seed 5262) both pass in-container against the real patched property with 0 disagreements. lean_verify.sh on Solution.lean exits 0. The ensures clause is neither too strong nor too weak: it demands precisely the .replace("b","") behavior and nothing more. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reviewed the consumer spec view (spec_view of Solution.lean) plus the public problem_statement; the auditor-side refinement.md/mapping.md quote the gold code verbatim but are never shown to solvers so are out of scope. Mechanical G-LEAK screen PASSES (no failures): no gold-patch line reproduced (the gold's `self.buffer.mode.replace("b", "")` does not appear — spec models it abstractly as `stripped`/`stripStep`), no diff markers, no patched file path `src/_pytest/capture.py` or dotted module path, changed symbols {mode,name} do not leak (`mode` is already public in the problem_statement; no spec identifier embeds `name`), and no narration terms. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec region is byte-identical and carries no smuggled discriminator (only the impl/proof regions differ). Semantically the spec's behavioral content — 'take the wrapped stream's mode descriptor and return it with every binary marker code point (`b`) removed, other code points preserved in order' — is a faithful restatement of what the PUBLIC problem_statement already demands: title 'mode should not include `b` (binary)', 'EncodedFile incorrectly advertises rb+, the mode of the underlying stream', and 'Youtube-dl looks for `b` in out.mode'. The F2P discriminator ('b' not in mode) is literally the public issue's requirement. The spec exposes no localization or mechanism (property on EncodedFile, .replace call) beyond the public statement. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
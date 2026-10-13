# P2 adversarial audit — django__django-10973

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch_quote.lean`, `atk_2_diverge.lean`, `atk_3_offbyone.lean`, `atk_4_empty.lean`, `atk_5_reverse.lean`, `atk_7_dup.lean`, `atk_8_marker.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None survives. The only same-spec impls that verify are the positive control (verbatim backward copy) and atk_6 (`return passwd`); both are behaviourally the gold verbatim-password exposure. atk_6's faithful refined patch is the gold patch itself and run_resolve returned RESOLVED=True (completed=True). No verifying wrong impl produces a non-resolving patch.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_quote.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,11 @@
       decreasing i
     do
       let c := passwd[i - 1]!
-      result := c :: result
+      let e : List Char :=
+        if c = '\\' then ['\\', '\\']
+        else if c = ':' then ['\\', ':']
+        else [c]
+      result := e ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,16 +42,12 @@
   do
     -- impl-start
     let mut result : List Char := []
-    let mut i := passwd.length
+    let mut i := passwd.length + 1
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ passwd.length
-      invariant result = passwd.drop i
-      done_with i = 0
-      decreasing i
+      invariant True
+      done_with False
     do
-      let c := passwd[i - 1]!
-      result := c :: result
-      i := i - 1
+      i := i
     return result
     -- impl-end
 
@@ -70,5 +66,3 @@
 
 prove_correct passwordEnvValue by
   loom_solve
-  rw [drop_copy_step passwd i (by omega) (by omega)]
-  simp_all
```

Attack 3 — `atk_3_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,7 @@
   do
     -- impl-start
     let mut result : List Char := []
-    let mut i := passwd.length
+    let mut i := passwd.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ passwd.length
       invariant result = passwd.drop i
```

Attack 4 — `atk_4_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,17 +41,7 @@
   ensures (out.length > 0) = (passwd.length > 0)
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := passwd.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ passwd.length
-      invariant result = passwd.drop i
-      done_with i = 0
-      decreasing i
-    do
-      let c := passwd[i - 1]!
-      result := c :: result
-      i := i - 1
+    let result : List Char := []
     return result
     -- impl-end
 
@@ -70,5 +60,3 @@
 
 prove_correct passwordEnvValue by
   loom_solve
-  rw [drop_copy_step passwd i (by omega) (by omega)]
-  simp_all
```

Attack 5 — `atk_5_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,16 +42,16 @@
   do
     -- impl-start
     let mut result : List Char := []
-    let mut i := passwd.length
-    while i > 0
+    let mut i := 0
+    while i < passwd.length
       invariant 0 ≤ i ∧ i ≤ passwd.length
-      invariant result = passwd.drop i
-      done_with i = 0
-      decreasing i
+      invariant result = (passwd.take i).reverse
+      done_with i = passwd.length
+      decreasing passwd.length - i
     do
-      let c := passwd[i - 1]!
+      let c := passwd[i]!
       result := c :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -70,5 +70,4 @@
 
 prove_correct passwordEnvValue by
   loom_solve
-  rw [drop_copy_step passwd i (by omega) (by omega)]
-  simp_all
+  sorry
```

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,18 +41,7 @@
   ensures (out.length > 0) = (passwd.length > 0)
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := passwd.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ passwd.length
-      invariant result = passwd.drop i
-      done_with i = 0
-      decreasing i
-    do
-      let c := passwd[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return passwd
     -- impl-end
 
 /- The backward-copy step: dropping one fewer element exposes the element at
@@ -70,5 +59,3 @@
 
 prove_correct passwordEnvValue by
   loom_solve
-  rw [drop_copy_step passwd i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk_7_dup.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
       decreasing i
     do
       let c := passwd[i - 1]!
-      result := c :: result
+      result := c :: c :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_8_marker.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,11 +41,11 @@
   ensures (out.length > 0) = (passwd.length > 0)
   do
     -- impl-start
-    let mut result : List Char := []
+    let mut result : List Char := ['X']
     let mut i := passwd.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ passwd.length
-      invariant result = passwd.drop i
+      invariant result = passwd.drop i ++ ['X']
       done_with i = 0
       decreasing i
     do
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The changed behaviour — the value exposed to the child
--  process for the connection password — is modeled DEEPLY: it is the password
--  sequence copied code point by code point, spelled out directly in the loop.
--  The proof consumes no callee contract.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: the exposed value is the input sequence verbatim,
--  built by the impl loop as a per-code-point copy.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A database shell launcher hands the connection password to the child process
   through a dedicated mechanism. The value exposed to the child for the password
   is the password sequence itself: element i of the exposed value is code point i
   of the input password, for every position — so the exposed value equals the
   input password and has the same length.

   The mechanism is populated (the exposed value is non-empty) exactly when the
   input password is non-empty.

   The password is read-only and the operation mutates none of its inputs
   (directive 5); the password and the exposed value are modeled as `List Char`
   of code points. -/
method passwordEnvValue (passwd : List Char) return (out : List Char)
  ensures out = passwd
  ensures (out.length > 0) = (passwd.length > 0)
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := passwd.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ passwd.length
      invariant result = passwd.drop i
      done_with i = 0
      decreasing i
    do
      let c := passwd[i - 1]!
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-copy step: dropping one fewer element exposes the element at
   `i-1` on the front, so `passwd.drop (i-1)` is that element consed onto
   `passwd.drop i`. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma drop_copy_step (passwd : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ passwd.length) :
    passwd.drop (i - 1) = passwd[i - 1]! :: passwd.drop i := by
  have hlt : i - 1 < passwd.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct passwordEnvValue by
  loom_solve
  rw [drop_copy_step passwd i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 files (8 attacks + pc) confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend) against the frozen Solution.lean — edits confined to the impl region; axioms/pure/pre/post/postconditions byte-identical.

VERIFY CMD (each): bash scripts/lean_verify.sh <file>  (run concurrently, ≤4 at a time as background jobs).
### RESULTS (exit 0=verifies, 1=error/fails):
- pc.lean (correct verbatim copy) => exit 0 VERIFIES (positive control OK).
- atk_1_prepatch_quote.lean (prepatch bug: `_escape_pgpass` per-code-point quoting `\`->`\\`, `:`->`\:`) => exit 1 FAILS. PREPATCH BUG REPRODUCED: loop invariant result=passwd.drop i cannot be re-established when a code point expands to a 2-char quote; postcondition out=passwd broken on colon/backslash passwords. This is the F2P discriminator.
- atk_2_diverge.lean (non-terminating loop, invariant True/done_with False) => exit 1 FAILS: `Decreasing annotations required in total correctness semantics` + unprovable WPGen. Total-correctness closes the divergence hole (refinement.md C.1).
- atk_3_offbyone.lean (boundary: start i at length-1, drops last char) => exit 1 FAILS: unsolved goal [] = List.drop (length-1) passwd.
- atk_4_empty.lean (partial-domain: `return []`) => exit 1 FAILS: both ensures unprovable ([]=passwd, length guard).
- atk_5_reverse.lean (control-flow: forward cons -> reversed output) => exit 1 FAILS: result_1 = passwd unprovable (reverse != identity).
- atk_6_echo.lean (`return passwd`, verbatim identity) => exit 0 VERIFIES. This is NOT a wrong impl — it is behaviourally the gold verbatim exposure. Per echo-attack policy its faithful refined patch (= gold patch verbatim) WAS materialized and RUN through the official harness.
- atk_7_dup.lean (control-flow-effect: cons head twice, doubled length) => exit 1 FAILS: goal reduces to False.
- atk_8_marker.lean (ungrounded-oracle echo: injected fixed 'X' marker) => exit 1 FAILS: result_1 = passwd unprovable (trailing ['X']).

RESOLVE RUN (atk_6, the only verifying candidate besides pc): swebench_unified.harness.run_resolve('django__django-10973', <gold patch>, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved'. Faithful patch stored at atk_6_faithful_patch.diff (byte-identical to bundle patch.diff). verify => resolve holds; NO verify⇏correct witness found.

REFINEMENT AUDIT (refinement.md): A1=R, A2=R+I, A3=I, A4=R — every leg is R / A-reference / I; NO consumed axiom (A-consumed), NO kind-3 (unexpressible-changed-op). The single A-reference is the deep model pgpassQuoteSeq/pgpassQuote validated == removed `_escape_pgpass` (client.py:9-13). Ran axiom_check.py => exit 0: 'G-AX OK: pgpassQuoteSeq deep model (== removed _escape_pgpass) sound on 15 boundary + 20000 fuzz inputs; post-patch verbatim exposure diverges from legacy quoting exactly on ":"/"\\" (F2P discriminators).' The A-reference lives only in Solution_prepatch.lean's elided impl region, never in the consumer spec view. Correspondence to the real callees (verbatim str(passwd) exposure via os.environ.copy()/subprocess.run env=, and the removed _escape_pgpass) holds.

CONCLUSION: The postcondition out=passwd under total correctness pins the modeled function exactly to the identity/verbatim exposure; every distinct wrong impl (partial-domain, boundary off-by-one, control-flow reverse/dup, divergence, ungrounded marker echo, and the prepatch quoting bug) FAILS to verify, and the one verifying same-spec candidate is gold-equivalent with a RESOLVING patch. verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch_quote.lean`, `atk_2_diverge.lean`, `atk_3_offbyone.lean`, `atk_4_empty.lean`, `atk_5_reverse.lean`, `atk_7_dup.lean`, `atk_8_marker.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None survives. The only same-spec impls that verify are the positive control (verbatim backward copy) and atk_6 (`return passwd`); both are behaviourally the gold verbatim-password exposure. atk_6's faithful refined patch is the gold patch itself and run_resolve returned RESOLVED=True (completed=True). No verifying wrong impl produces a non-resolving patch.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_quote.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_diverge.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_empty.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_reverse.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_dup.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_marker.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The changed behaviour — the value exposed to the child
--  process for the connection password — is modeled DEEPLY: it is the password
--  sequence copied code point by code point, spelled out directly in the loop.
--  The proof consumes no callee contract.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: the exposed value is the input sequence verbatim,
--  built by the impl loop as a per-code-point copy.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A database shell launcher hands the connection password to the child process
   through a dedicated mechanism. The value exposed to the child for the password
   is the password sequence itself: element i of the exposed value is code point i
   of the input password, for every position — so the exposed value equals the
   input password and has the same length.

   The mechanism is populated (the exposed value is non-empty) exactly when the
   input password is non-empty.

   The password is read-only and the operation mutates none of its inputs
   (directive 5); the password and the exposed value are modeled as `List Char`
   of code points. -/
method passwordEnvValue (passwd : List Char) return (out : List Char)
  ensures out = passwd
  ensures (out.length > 0) = (passwd.length > 0)
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := passwd.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ passwd.length
      invariant result = passwd.drop i
      done_with i = 0
      decreasing i
    do
      let c := passwd[i - 1]!
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-copy step: dropping one fewer element exposes the element at
   `i-1` on the front, so `passwd.drop (i-1)` is that element consed onto
   `passwd.drop i`. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma drop_copy_step (passwd : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ passwd.length) :
    passwd.drop (i - 1) = passwd[i - 1]! :: passwd.drop i := by
  have hlt : i - 1 < passwd.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct passwordEnvValue by
  loom_solve
  rw [drop_copy_step passwd i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 files (8 attacks + pc) confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend) against the frozen Solution.lean — edits confined to the impl region; axioms/pure/pre/post/postconditions byte-identical.

VERIFY CMD (each): bash scripts/lean_verify.sh <file>  (run concurrently, ≤4 at a time as background jobs).
### RESULTS (exit 0=verifies, 1=error/fails):
- pc.lean (correct verbatim copy) => exit 0 VERIFIES (positive control OK).
- atk_1_prepatch_quote.lean (prepatch bug: `_escape_pgpass` per-code-point quoting `\`->`\\`, `:`->`\:`) => exit 1 FAILS. PREPATCH BUG REPRODUCED: loop invariant result=passwd.drop i cannot be re-established when a code point expands to a 2-char quote; postcondition out=passwd broken on colon/backslash passwords. This is the F2P discriminator.
- atk_2_diverge.lean (non-terminating loop, invariant True/done_with False) => exit 1 FAILS: `Decreasing annotations required in total correctness semantics` + unprovable WPGen. Total-correctness closes the divergence hole (refinement.md C.1).
- atk_3_offbyone.lean (boundary: start i at length-1, drops last char) => exit 1 FAILS: unsolved goal [] = List.drop (length-1) passwd.
- atk_4_empty.lean (partial-domain: `return []`) => exit 1 FAILS: both ensures unprovable ([]=passwd, length guard).
- atk_5_reverse.lean (control-flow: forward cons -> reversed output) => exit 1 FAILS: result_1 = passwd unprovable (reverse != identity).
- atk_6_echo.lean (`return passwd`, verbatim identity) => exit 0 VERIFIES. This is NOT a wrong impl — it is behaviourally the gold verbatim exposure. Per echo-attack policy its faithful refined patch (= gold patch verbatim) WAS materialized and RUN through the official harness.
- atk_7_dup.lean (control-flow-effect: cons head twice, doubled length) => exit 1 FAILS: goal reduces to False.
- atk_8_marker.lean (ungrounded-oracle echo: injected fixed 'X' marker) => exit 1 FAILS: result_1 = passwd unprovable (trailing ['X']).

RESOLVE RUN (atk_6, the only verifying candidate besides pc): swebench_unified.harness.run_resolve('django__django-10973', <gold patch>, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved'. Faithful patch stored at atk_6_faithful_patch.diff (byte-identical to bundle patch.diff). verify => resolve holds; NO verify⇏correct witness found.

REFINEMENT AUDIT (refinement.md): A1=R, A2=R+I, A3=I, A4=R — every leg is R / A-reference / I; NO consumed axiom (A-consumed), NO kind-3 (unexpressible-changed-op). The single A-reference is the deep model pgpassQuoteSeq/pgpassQuote validated == removed `_escape_pgpass` (client.py:9-13). Ran axiom_check.py => exit 0: 'G-AX OK: pgpassQuoteSeq deep model (== removed _escape_pgpass) sound on 15 boundary + 20000 fuzz inputs; post-patch verbatim exposure diverges from legacy quoting exactly on ":"/"\\" (F2P discriminators).' The A-reference lives only in Solution_prepatch.lean's elided impl region, never in the consumer spec view. Correspondence to the real callees (verbatim str(passwd) exposure via os.environ.copy()/subprocess.run env=, and the removed _escape_pgpass) holds.

CONCLUSION: The postcondition out=passwd under total correctness pins the modeled function exactly to the identity/verbatim exposure; every distinct wrong impl (partial-domain, boundary off-by-one, control-flow reverse/dup, divergence, ungrounded marker echo, and the prepatch quoting bug) FAILS to verify, and the one verifying same-spec candidate is gold-equivalent with a RESOLVING patch. verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: could not break faithfulness. The modeled function passwordEnvValue (spec: `out = passwd` and `(out.length>0)=(passwd.length>0)`) matches the real post-patch callee (django/db/backends/postgresql/client.py:runshell_db, base_commit ddb2936) on every input in the modeling domain.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean, lean) = True — the consumer spec view is byte-identical; the prepatch differs only inside the elided impl region.
2. Solution.lean verifies (lean_verify exit 0) under total-correctness; Solution_prepatch.lean (legacy pgpassQuote fold) FAILS to verify (invariant result=passwd.drop i unprovable when a code point expands to a 2-char quote) — the spec genuinely senses the change (G-DIFF holds, spec is tight, not vacuous).
3. Real repo post-patch: subprocess_env['PGPASSWORD'] = str(passwd), set iff `if passwd:` (truthy). Gold test observes env.get('PGPASSWORD') = the assigned string verbatim. For a str password, str(passwd) is the identity, so exposed value == passwd verbatim; presence guard `if passwd:` ⇔ len>0. Both postconditions match the real callee on every str input, incl. empty, colon (some:password→some:password), backslash, and accented (sésame).
4. axiom_check.py reproduces the removed _escape_pgpass verbatim and confirms (a) the deep A-reference model equals it, (b) the post-patch verbatim exposure equals the raw password, and (c) the colon/backslash divergence witnesses — matching the F2P behavior change.

The spec is NOT too strong / does not drift: it pins exactly the post-patch behavior without demanding more than the real code does. Non-str password objects are an explicitly disclosed modeling boundary (str↔List Char, str() identity in mapping.md §2), not silent unfaithful drift. No diverging input exists in the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view of Solution.lean (computed via markers.spec_view with LeanBackend) contains: the method sig `passwordEnvValue (passwd : List Char) return (out : List Char)` with postconditions `out = passwd` and `(out.length > 0) = (passwd.length > 0)`, plus an abstract docstring ('a database shell launcher hands the connection password to the child process through a dedicated mechanism; the exposed value equals the input password and is non-empty iff the password is non-empty'). The impl region is elided ('implementation elided — supplied by the consumer'). same_spec(Solution.lean, Solution_prepatch.lean) = True (verified). Mechanical G-LEAK screen passes (no hard failures/warnings).

Leakage judged vs PUBLIC problem_statement ONLY (not hints). The problem_statement already discloses the full gold approach explicitly: 'Use subprocess.run and PGPASSWORD ... pass a custom environment for the subprocess ... to set PGPASSWORD'. The spec view is strictly MORE abstract than that — it never names PGPASSWORD, subprocess.run, os.environ, client.py, _escape_pgpass, .pgpass, or NamedTemporaryFile. The 'exposed value = password verbatim' discriminator is a faithful behavioral abstraction directly implied by the public 'set PGPASSWORD = str(passwd)' (an env var carries the raw value; no .pgpass escaping). No diff markers, no patched file/module path, no reproduced gold-patch line, no bug/fix/patch narration. The removed-mechanism diagnosis (legacy quoting fold pgpassQuoteSeq / _escape_pgpass) lives exclusively in Solution_prepatch.lean's elided impl region, never entering the consumer spec view (SPEC_GUIDE directive 6). No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

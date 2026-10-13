# P2 adversarial audit — sphinx-doc__sphinx-9320

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_00_prepatch.lean`, `atk_07_hoisted.lean`, `atk_08_empty_refused.lean`, `atk_09_partial_short.lean`, `atk_10_accept_all.lean`, `atk_11_domain_as_verdict.lean`, `atk_12_derived_probe_as_verdict.lean`, `atk_13_empty_via_expansion.lean`, `atk_15_return_derived_expansion.lean`, `atk_04a_raw_match.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_01_derived_probe.lean`, `atk_02_strictAccepts_derived.lean`, `atk_03_const_probe.lean`, `atk_04b_raw_via_empty_fact.lean`, `atk_05_derived_submit_nul.lean`, `atk_06_oracle_echo.lean`, `atk_14_derived_submit_tilde.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl's faithful refined patch failed to resolve. All 7 verifying same-spec impls resolved under the official harness (completed=true, patch_successfully_applied=true, FAIL_TO_PASS 1/1 on tests/test_quickstart.py::test_exits_when_existing_confpy, PASS_TO_PASS 9/9).

The headline finding is that the PRIOR PASS'S BREAK IS CLOSED. verdict.md (09:17) recorded three verifying-but-not-resolving impls (atk_A1_derived_probe / atk_A3_strictAccepts_derived / atk_A2_const_probe), all exploiting `opaque pathExpanded : List Char -> List Char` — a TOTAL function type whose read at a derived argument refined to an unguarded `path.expanduser('~\x00' + x)` that raises ValueError('embedded null byte') on the F2P input x=''. Solution.lean was repaired afterwards (09:50): the expansion is now a PARTIAL `opaque rawExpansion : (entry : List Char) -> expansionAnswers entry = true -> List Char` plus a derived total `def pathExpanded` that is definitionally the GUARDED reading.

I re-encoded all three prior counterexamples verbatim in place against the frozen spec. All three STILL VERIFY (rc=0) — and MUST, being outcome-neutral — but their faithful refined patches now RESOLVE, because mapping.md §1.1 binds a read of `pathExpanded X` to the guarded `path.expanduser(X) if _answers(X) else ''`, which is total. Measured directly: `_expanded('~\x00') == ''` and `path.isdir('') is False`, so the derived read answers False instead of escaping and the SystemExit the F2P test needs still fires. The guard is in the TERM, which is the one place a refinement cannot drop it.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01_derived_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,13 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- PRIOR COUNTEREXAMPLE #1 re-encoded: read the freely-readable primitives at
+    -- a DERIVED entry the `require` says nothing about.
     if entry = [] then
-      return Except.ok []
+      if pathIsDir (pathExpanded ('~' :: Char.ofNat 0 :: entry)) then
+        return Except.ok []
+      else
+        return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
```

Attack 2 — `atk_02_strictAccepts_derived.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,12 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- PRIOR COUNTEREXAMPLE #2 re-encoded: the derived free DECISION.
     if entry = [] then
-      return Except.ok []
+      if strictAccepts ('~' :: Char.ofNat 0 :: entry) then
+        return Except.ok []
+      else
+        return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
```

Attack 3 — `atk_03_const_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,18 +249,25 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
-    if entry = [] then
-      return Except.ok []
-    else
+    -- PRIOR COUNTEREXAMPLE #3 re-encoded: a CONSTANT hostile entry.
+    if pathIsDir (pathExpanded ['~', Char.ofNat 0, 'a']) then
+      if entry = [] then
+        return Except.ok []
+      else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
         return Except.ok accepted
       else
         return Except.error ()
+    else
+      if entry = [] then
+        return Except.ok []
+      else
+      if strictAccepts entry then
+        let accepted ← strictPathValidator entry
+        return Except.ok accepted
+      else
+        return Except.error ()
     -- impl-end
 
 prove_correct optionalPathValidator by
```

Attack 4 — `atk_04b_raw_via_empty_fact.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,14 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- Read the RAW expansion using the freely-available domain proof
+    -- `expansionAnswers_empty`; the argument it unlocks is [] only.
     if entry = [] then
-      return Except.ok []
+      let _raw := rawExpansion [] expansionAnswers_empty
+      if pathIsDir _raw then
+        return Except.ok []
+      else
+        return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
```

Attack 5 — `atk_05_derived_submit_nul.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,13 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- Earn a SUBMISSION at the NUL-derived argument, shipped-positive syntax.
     if entry = [] then
-      return Except.ok []
+      if strictAccepts ('~' :: Char.ofNat 0 :: entry) then
+        let _probe ← strictPathValidator ('~' :: Char.ofNat 0 :: entry)
+        return Except.ok []
+      else
+        return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
@@ -265,3 +266,4 @@
 
 prove_correct optionalPathValidator by
   loom_solve
+  all_goals exact ⟨accepted_in_domain _ (by assumption), by assumption⟩
```

Attack 6 — `atk_06_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,18 +249,13 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- UNGROUNDED-ORACLE ECHO: return the postcondition's RHS verbatim; the
+    -- strict validator is never invoked.
     if entry = [] then
       return Except.ok []
     else
-      if strictAccepts entry then
-        let accepted ← strictPathValidator entry
-        return Except.ok accepted
-      else
-        return Except.error ()
+      return (if strictAccepts entry then Except.ok (pathExpanded entry)
+              else Except.error ())
     -- impl-end
 
 prove_correct optionalPathValidator by
```

Attack 7 — `atk_14_derived_submit_tilde.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,14 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- Earn and FIRE a submission of the derived '~' :: entry -- live on the F2P
+    -- input -- then discard the answer and accept the empty entry.
     if entry = [] then
-      return Except.ok []
+      if strictAccepts ('~' :: entry) then
+        let _probe ← strictPathValidator ('~' :: entry)
+        return Except.ok []
+      else
+        return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
@@ -265,3 +267,4 @@
 
 prove_correct optionalPathValidator by
   loom_solve
+  all_goals exact ⟨accepted_in_domain _ (by assumption), by assumption⟩
```

Attack 8 — `atk_00_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,18 +249,14 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
-    if entry = [] then
-      return Except.ok []
+    -- Every entry is governed by the strict validator: an entry it accepts is
+    -- submitted to it and comes back as the accepted value; one it does not
+    -- accept is turned away.
+    if strictAccepts entry then
+      let accepted ← strictPathValidator entry
+      return Except.ok accepted
     else
-      if strictAccepts entry then
-        let accepted ← strictPathValidator entry
-        return Except.ok accepted
-      else
-        return Except.error ()
+      return Except.error ()
     -- impl-end
 
 prove_correct optionalPathValidator by
```

Attack 9 — `atk_07_hoisted.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,16 +249,14 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- PRIOR COUNTEREXAMPLE (reject lane): hoist the submission above the
+    -- decision, so the empty entry is handed to the strict validator.
+    let answer ← strictPathValidator entry
     if entry = [] then
       return Except.ok []
     else
       if strictAccepts entry then
-        let accepted ← strictPathValidator entry
-        return Except.ok accepted
+        return Except.ok answer
       else
         return Except.error ()
     -- impl-end
```

Attack 10 — `atk_08_empty_refused.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,9 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- BOUNDARY attack: refuse the empty entry.
     if entry = [] then
-      return Except.ok []
+      return Except.error ()
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
```

Attack 11 — `atk_09_partial_short.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,11 +249,9 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
-    if entry = [] then
+    -- PARTIAL-DOMAIN attack: handle [] correctly and give SHORT entries the
+    -- empty affordance instead of the strict validator's verdict.
+    if entry.length ≤ 1 then
       return Except.ok []
     else
       if strictAccepts entry then
```

Attack 12 — `atk_10_accept_all.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,18 +249,8 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
-    if entry = [] then
-      return Except.ok []
-    else
-      if strictAccepts entry then
-        let accepted ← strictPathValidator entry
-        return Except.ok accepted
-      else
-        return Except.error ()
+    -- UNGROUNDED attack: accept everything, carrying the guarded expansion.
+    return Except.ok (pathExpanded entry)
     -- impl-end
 
 prove_correct optionalPathValidator by
```

Attack 13 — `atk_11_domain_as_verdict.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,18 +249,11 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
-    if entry = [] then
+    -- Answer from the DOMAIN condition instead of from the decision.
+    if expansionAnswers entry then
+      return Except.error ()
+    else
       return Except.ok []
-    else
-      if strictAccepts entry then
-        let accepted ← strictPathValidator entry
-        return Except.ok accepted
-      else
-        return Except.error ()
     -- impl-end
 
 prove_correct optionalPathValidator by
```

Attack 14 — `atk_12_derived_probe_as_verdict.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,12 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- ANSWER from a derived read rather than merely consulting it.
     if entry = [] then
-      return Except.ok []
+      if pathIsDir (pathExpanded ('~' :: Char.ofNat 0 :: entry)) then
+        return Except.error ()
+      else
+        return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
```

Attack 15 — `atk_13_empty_via_expansion.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,9 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- Return the guarded expansion of `entry` on the empty branch.
     if entry = [] then
-      return Except.ok []
+      return Except.ok (pathExpanded entry)
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
```

Attack 16 — `atk_15_return_derived_expansion.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,13 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- Return the DERIVED entry's expansion on the empty branch instead of [].
     if entry = [] then
-      return Except.ok []
+      if strictAccepts ('~' :: entry) then
+        let probe ← strictPathValidator ('~' :: entry)
+        return Except.ok probe
+      else
+        return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
@@ -265,3 +266,4 @@
 
 prove_correct optionalPathValidator by
   loom_solve
+  all_goals exact ⟨accepted_in_domain _ (by assumption), by assumption⟩
```

Attack 17 — `atk_04a_raw_match.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,12 +249,14 @@
            else Except.error ())
   do
     -- impl-start
-    -- An empty entry is accepted verbatim and is never handed to the strict
-    -- validator. A non-empty entry the strict validator accepts is submitted to
-    -- it and comes back as the accepted value; one it does not accept is turned
-    -- away.
+    -- Reach the PARTIAL rawExpansion at a DERIVED argument, binding the branch
+    -- proof with `match h : ...` rather than a dependent `if`.
     if entry = [] then
-      return Except.ok []
+      match h : strictAccepts ('~' :: Char.ofNat 0 :: entry) with
+      | true =>
+        let _raw := rawExpansion ('~' :: Char.ofNat 0 :: entry) (accepted_in_domain _ h)
+        return Except.ok []
+      | false => return Except.ok []
     else
       if strictAccepts entry then
         let accepted ← strictPathValidator entry
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE/SETUP.** base_commit worktree via `git worktree add --detach e05cef574b8f23ab1b57f57e7da6dee509a4e230`. Spec pinned at sha256 85817573100b21736e0261182f303fa1436566a7fe8787b9804f876c18425f62. All 17 attack files + pos_control confirmed same_spec=True (only the impl region and, where noted, the tactic tail were edited; axioms/pure/pre/post byte-identical). All 7 diffs confirmed `git apply --check` rc=0 in the base_commit worktree, re-checked after the resolve runs with the tree clean.

### COMMANDS (from swe-proof):
  verify:    bash scripts/lean_verify.sh <name>.lean
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<name>.lean').read(), b.language))"
  resolve:   python resolve.py <name>  -> swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9320', <diff>, timeout=1800, retries=1); report dumped to <name>.resolve.json
  applychk:  git apply --check <name>.diff
Verifications and resolve runs were scheduled concurrently as detached background jobs, at most 4 at a time.

**CONTROLS.** pos_control.lean (byte-identical copy of shipped Solution.lean) verifies, rc=0 — non-vacuity. Prepatch reproduced: atk_00_prepatch.lean (shipped Solution_prepatch.lean) rc=1, failing exactly `case «ensures_2: entry = [] -> out = Except.ok []»` in BOTH branches (goals `entry = [] -> Except.ok x = Except.ok []` and `entry = [] -> Except.error () = Except.ok []`), i.e. the reported bug is the discriminating clause.

### RESULTS (17 attacks: 7 verify + all 7 RESOLVE; 9 refuted; 1 encoding-blocked):
  VERIFY + RESOLVE=TRUE (F2P 1/1, P2P 9/9, applied=true, completed=true):
    atk_01_derived_probe          verify 0  resolve TRUE  [prior CE #1 re-encoded]
    atk_02_strictAccepts_derived  verify 0  resolve TRUE  [prior CE #2 re-encoded]
    atk_03_const_probe            verify 0  resolve TRUE  [prior CE #3 re-encoded, constant entry]
    atk_04b_raw_via_empty_fact    verify 0  resolve TRUE  [reads the PARTIAL rawExpansion via expansionAnswers_empty]
    atk_05_derived_submit_nul     verify 0  resolve TRUE  [earns a submission of '~'+NUL+entry via accepted_in_domain]
    atk_06_oracle_echo            verify 0  resolve TRUE  [ungrounded-oracle echo: postcondition RHS inlined, is_path never invoked]
    atk_14_derived_submit_tilde   verify 0  resolve TRUE  [earns and FIRES a submission of the LIVE derived '~'+entry]
  REFUTED (rc=1, each on a NAMED clause — not an encoding accident):
    atk_07_hoisted                 case «submission_earned_1: (expansionAnswers entry = true ∧ strictAccepts entry = true)»
    atk_08_empty_refused           case «ensures_2: entry = [] -> out = Except.ok []»
    atk_09_partial_short           case «ensures_1: entry ≠ [] -> ...»  [partial-domain]
    atk_10_accept_all              case «ensures_1»                      [ungrounded]
    atk_11_domain_as_verdict       case «ensures_1»                      [answers FROM the require]
    atk_12_derived_probe_as_verdict case «ensures_2»                     [answers FROM a derived read]
    atk_13_empty_via_expansion     case «ensures_2»                      [A-leg value fidelity]
    atk_15_return_derived_expansion rc=1                                [returns the derived entry's expansion]
    atk_00_prepatch                case «ensures_2»                      [the prepatch bug]
  ENCODING-BLOCKED, reported as such and NOT counted as a refutation: atk_04a_raw_match and the first atk_04/atk_05 encoding hit a WPGen limitation on a dependent `if h :` / `match h :` in the impl region (`Failed to parse an assertion without names: WPGen`), which is a tooling limit, not a spec judgement. atk_05 was RE-ENCODED in the shipped-positive style (plain `if` + retuned tactic tail) and then verified AND resolved, so the family it was probing is covered by executed evidence rather than left open.

WHY THE REPAIR HOLDS (the A-leg question). The repair moved the guard from a comment into the term. Two independent checks:
  1. **STRUCTURAL:** there is no unguarded read left to refine. `rawExpansion` takes a proof of `expansionAnswers entry = true`, so it cannot be applied where no proof exists; the only freely readable forms (`pathExpanded`, `strictAccepts`, `pathIsDir`, `expansionAnswers`) are total on BOTH sides of mapping.md §1.1. atk_04b is the honest limit case: the one domain proof available anywhere is `expansionAnswers_empty`, which unlocks the raw expansion at `[]` ONLY, whose refinement `path.expanduser('')` is total. It resolved.
  2. **THE LICENCE THE REPAIR INTRODUCED IS SOUND.** `accepted_in_domain` (a theorem) lets an impl that shows a DERIVED argument accepted submit that argument. I attacked this twice — atk_05 on the dead NUL family and atk_14 on the LIVE '~'+entry family, where on the F2P input the derived entry is '~', which really is accepted, so the extra submission genuinely fires in Python. Both verify and both resolve. I also audited the theorem against the REAL primitives over a hostile alphabet the shipped gates omit (NUL, high/low surrogates, '~root'): 21,720 reads at three arguments each, 10,015 out-of-domain, 35 accepted — 0 violations of `accepted => in domain`, 0 submissions that failed to come back, 0 value mismatches. `os.path.isdir` is genuinely total (it catches OSError AND ValueError itself, returning False for an embedded NUL or a lone surrogate), so `pathIsDir` keeping a total function type is faithful; the only non-total primitive is `expanduser`, and that is exactly the one now behind a proof.

REFINEMENT.MD LEG AUDIT (§A table A0-A6). Every leg is R, A-reference, or I; there is NO kind-3 and NO A-consumed leg, so §C's "no kind-3" claim is formally satisfied and the operation that changed (the empty affordance in front of the strict validator) is modeled DIRECTLY at A2-A4 rather than hidden behind an axiom about the function under change. A0/A1/A2/A5/A6 = R (A2 = R+I); A3 = A-reference + R; A4 = A-reference + I. Both A-leg correspondences now HOLD:
  - A3 (strictAccepts <-> isdir of the GUARDED expansion): HOLDS. The justification no longer rests on a false totality claim about `expanduser` — it rests on the guard being inside `pathExpanded`, and it correctly separates what the guard buys (free reads at any argument) from what the `require` buys (an outcome to pin, and the guarded reading equalling `expanduser` verbatim inside the domain). Verified behaviourally: the three prior breakers now resolve.
  - A4 (strictPathValidator <-> is_path, opaque VelvetM PROGRAM): HOLDS. Modeling the callee as a program is what makes a submission earnable; atk_07 (hoisted) is still refuted on the `submission_earned_1` side condition, so the structural obligation is live, while pos-decision-inlined-style impls that never submit still verify.
  - §D's joint-satisfiability model: I EXTRACTED the Lean block from refinement.md §D and machine-checked it — refD_model.lean, rc=0. It now mirrors the guarded SHAPE (mRawExpansion carries the domain proof, mExpanded is the guarded reading) and, importantly, §D self-corrects a claim an earlier revision had backwards: it ships `m_unguarded_fact3_also_holds` (the guard on fact 3 is redundant-but-harmless, since off the domain the guarded expansion is [] and mIsDir [] = false) in place of the earlier `m_unguarded_fact3_would_be_false`, which is unprovable once the read is guarded. mapping.md §3 fact 3 states the same thing. The prose and the machine-checked model agree.
  - §E's verify=>resolved argument is consistent with the executed evidence: the domain excludes only entries on which the patch changed nothing (`is_path('~\x00abc')` escapes identically pre- and post-patch, measured), and the F2P input '' is inside the domain by the checked fact `expansionAnswers_empty`.

### RESIDUAL OBSERVATIONS (not defects, not gate-affecting):
  - atk_06_oracle_echo verifies and resolves. It never invokes the strict validator at all, computing the verdict from the free primitives instead. That is admitted by design (properties.py ships the same shape as `pos-decision-inlined`; the obligation is behavioural and never requires the callee to be consulted), and its refinement is behaviourally identical to gold on the tested inputs, so admitting it is fidelity rather than laxity. Worth recording only because a future spec revision that tried to demand the delegation would have to change the clauses, not the impl.
  - **HOST/ENV:** the host was heavily loaded (load avg ~144). Six of the seven resolves needed attempt 2/2 after a transient first-attempt infrastructure failure, but every reported result has completed=true with a real report.json (patch_successfully_applied=true, F2P 1/1, P2P 9/9), and no run was left incomplete. No resolve was left unexecuted and no verdict rests on speculation.
  - Bundle mtimes moved DURING this audit (mapping.md and refinement.md 10:04, properties.py 10:09, vs Solution.lean 09:50). My verdict is pinned to the Solution.lean sha256 above; the prose I audited is the 10:04 revision. verdict.md (09:17) still records the SUPERSEDED break and should be re-stamped from this pass.

**VERDICT:** SOUND. 17 same-spec attacks run (>= the 5-6 required, spanning the 3 prior counterexamples, the prepatch bug, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, answer-from-the-domain, answer-from-a-derived-read, and both derived-submission families). 7 verified; every one of those 7 had its faithful refined patch materialized, `git apply --check`ed at base_commit, and RUN through the official harness — all 7 resolved. Nothing exhibits verify=>correct failure, so the guard repair closes the family that broke the prior revision.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_00_prepatch.lean`, `atk_07_hoisted.lean`, `atk_08_empty_refused.lean`, `atk_09_partial_short.lean`, `atk_10_accept_all.lean`, `atk_11_domain_as_verdict.lean`, `atk_12_derived_probe_as_verdict.lean`, `atk_13_empty_via_expansion.lean`, `atk_15_return_derived_expansion.lean`, `atk_04a_raw_match.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_01_derived_probe.lean`, `atk_02_strictAccepts_derived.lean`, `atk_03_const_probe.lean`, `atk_04b_raw_via_empty_fact.lean`, `atk_05_derived_submit_nul.lean`, `atk_06_oracle_echo.lean`, `atk_14_derived_submit_tilde.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl's faithful refined patch failed to resolve. All 7 verifying same-spec impls resolved under the official harness (completed=true, patch_successfully_applied=true, FAIL_TO_PASS 1/1 on tests/test_quickstart.py::test_exits_when_existing_confpy, PASS_TO_PASS 9/9).

The headline finding is that the PRIOR PASS'S BREAK IS CLOSED. verdict.md (09:17) recorded three verifying-but-not-resolving impls (atk_A1_derived_probe / atk_A3_strictAccepts_derived / atk_A2_const_probe), all exploiting `opaque pathExpanded : List Char -> List Char` — a TOTAL function type whose read at a derived argument refined to an unguarded `path.expanduser('~\x00' + x)` that raises ValueError('embedded null byte') on the F2P input x=''. Solution.lean was repaired afterwards (09:50): the expansion is now a PARTIAL `opaque rawExpansion : (entry : List Char) -> expansionAnswers entry = true -> List Char` plus a derived total `def pathExpanded` that is definitionally the GUARDED reading.

I re-encoded all three prior counterexamples verbatim in place against the frozen spec. All three STILL VERIFY (rc=0) — and MUST, being outcome-neutral — but their faithful refined patches now RESOLVE, because mapping.md §1.1 binds a read of `pathExpanded X` to the guarded `path.expanduser(X) if _answers(X) else ''`, which is total. Measured directly: `_expanded('~\x00') == ''` and `path.isdir('') is False`, so the derived read answers False instead of escaping and the SystemExit the F2P test needs still fires. The guard is in the TERM, which is the one place a refinement cannot drop it.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_01_derived_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_02_strictAccepts_derived.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_03_const_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_04b_raw_via_empty_fact.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 5 — `atk_05_derived_submit_nul.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_06_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 7 — `atk_14_derived_submit_tilde.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_00_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_07_hoisted.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_08_empty_refused.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_09_partial_short.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_10_accept_all.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_11_domain_as_verdict.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_12_derived_probe_as_verdict.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_13_empty_via_expansion.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_15_return_derived_expansion.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_04a_raw_match.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE/SETUP.** base_commit worktree via `git worktree add --detach e05cef574b8f23ab1b57f57e7da6dee509a4e230`. Spec pinned at sha256 85817573100b21736e0261182f303fa1436566a7fe8787b9804f876c18425f62. All 17 attack files + pos_control confirmed same_spec=True (only the impl region and, where noted, the tactic tail were edited; axioms/pure/pre/post byte-identical). All 7 diffs confirmed `git apply --check` rc=0 in the base_commit worktree, re-checked after the resolve runs with the tree clean.

### COMMANDS (from swe-proof):
  verify:    bash scripts/lean_verify.sh <name>.lean
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<name>.lean').read(), b.language))"
  resolve:   python resolve.py <name>  -> swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9320', <diff>, timeout=1800, retries=1); report dumped to <name>.resolve.json
  applychk:  git apply --check <name>.diff
Verifications and resolve runs were scheduled concurrently as detached background jobs, at most 4 at a time.

**CONTROLS.** pos_control.lean (byte-identical copy of shipped Solution.lean) verifies, rc=0 — non-vacuity. Prepatch reproduced: atk_00_prepatch.lean (shipped Solution_prepatch.lean) rc=1, failing exactly `case «ensures_2: entry = [] -> out = Except.ok []»` in BOTH branches (goals `entry = [] -> Except.ok x = Except.ok []` and `entry = [] -> Except.error () = Except.ok []`), i.e. the reported bug is the discriminating clause.

### RESULTS (17 attacks: 7 verify + all 7 RESOLVE; 9 refuted; 1 encoding-blocked):
  VERIFY + RESOLVE=TRUE (F2P 1/1, P2P 9/9, applied=true, completed=true):
    atk_01_derived_probe          verify 0  resolve TRUE  [prior CE #1 re-encoded]
    atk_02_strictAccepts_derived  verify 0  resolve TRUE  [prior CE #2 re-encoded]
    atk_03_const_probe            verify 0  resolve TRUE  [prior CE #3 re-encoded, constant entry]
    atk_04b_raw_via_empty_fact    verify 0  resolve TRUE  [reads the PARTIAL rawExpansion via expansionAnswers_empty]
    atk_05_derived_submit_nul     verify 0  resolve TRUE  [earns a submission of '~'+NUL+entry via accepted_in_domain]
    atk_06_oracle_echo            verify 0  resolve TRUE  [ungrounded-oracle echo: postcondition RHS inlined, is_path never invoked]
    atk_14_derived_submit_tilde   verify 0  resolve TRUE  [earns and FIRES a submission of the LIVE derived '~'+entry]
  REFUTED (rc=1, each on a NAMED clause — not an encoding accident):
    atk_07_hoisted                 case «submission_earned_1: (expansionAnswers entry = true ∧ strictAccepts entry = true)»
    atk_08_empty_refused           case «ensures_2: entry = [] -> out = Except.ok []»
    atk_09_partial_short           case «ensures_1: entry ≠ [] -> ...»  [partial-domain]
    atk_10_accept_all              case «ensures_1»                      [ungrounded]
    atk_11_domain_as_verdict       case «ensures_1»                      [answers FROM the require]
    atk_12_derived_probe_as_verdict case «ensures_2»                     [answers FROM a derived read]
    atk_13_empty_via_expansion     case «ensures_2»                      [A-leg value fidelity]
    atk_15_return_derived_expansion rc=1                                [returns the derived entry's expansion]
    atk_00_prepatch                case «ensures_2»                      [the prepatch bug]
  ENCODING-BLOCKED, reported as such and NOT counted as a refutation: atk_04a_raw_match and the first atk_04/atk_05 encoding hit a WPGen limitation on a dependent `if h :` / `match h :` in the impl region (`Failed to parse an assertion without names: WPGen`), which is a tooling limit, not a spec judgement. atk_05 was RE-ENCODED in the shipped-positive style (plain `if` + retuned tactic tail) and then verified AND resolved, so the family it was probing is covered by executed evidence rather than left open.

WHY THE REPAIR HOLDS (the A-leg question). The repair moved the guard from a comment into the term. Two independent checks:
  1. **STRUCTURAL:** there is no unguarded read left to refine. `rawExpansion` takes a proof of `expansionAnswers entry = true`, so it cannot be applied where no proof exists; the only freely readable forms (`pathExpanded`, `strictAccepts`, `pathIsDir`, `expansionAnswers`) are total on BOTH sides of mapping.md §1.1. atk_04b is the honest limit case: the one domain proof available anywhere is `expansionAnswers_empty`, which unlocks the raw expansion at `[]` ONLY, whose refinement `path.expanduser('')` is total. It resolved.
  2. **THE LICENCE THE REPAIR INTRODUCED IS SOUND.** `accepted_in_domain` (a theorem) lets an impl that shows a DERIVED argument accepted submit that argument. I attacked this twice — atk_05 on the dead NUL family and atk_14 on the LIVE '~'+entry family, where on the F2P input the derived entry is '~', which really is accepted, so the extra submission genuinely fires in Python. Both verify and both resolve. I also audited the theorem against the REAL primitives over a hostile alphabet the shipped gates omit (NUL, high/low surrogates, '~root'): 21,720 reads at three arguments each, 10,015 out-of-domain, 35 accepted — 0 violations of `accepted => in domain`, 0 submissions that failed to come back, 0 value mismatches. `os.path.isdir` is genuinely total (it catches OSError AND ValueError itself, returning False for an embedded NUL or a lone surrogate), so `pathIsDir` keeping a total function type is faithful; the only non-total primitive is `expanduser`, and that is exactly the one now behind a proof.

REFINEMENT.MD LEG AUDIT (§A table A0-A6). Every leg is R, A-reference, or I; there is NO kind-3 and NO A-consumed leg, so §C's "no kind-3" claim is formally satisfied and the operation that changed (the empty affordance in front of the strict validator) is modeled DIRECTLY at A2-A4 rather than hidden behind an axiom about the function under change. A0/A1/A2/A5/A6 = R (A2 = R+I); A3 = A-reference + R; A4 = A-reference + I. Both A-leg correspondences now HOLD:
  - A3 (strictAccepts <-> isdir of the GUARDED expansion): HOLDS. The justification no longer rests on a false totality claim about `expanduser` — it rests on the guard being inside `pathExpanded`, and it correctly separates what the guard buys (free reads at any argument) from what the `require` buys (an outcome to pin, and the guarded reading equalling `expanduser` verbatim inside the domain). Verified behaviourally: the three prior breakers now resolve.
  - A4 (strictPathValidator <-> is_path, opaque VelvetM PROGRAM): HOLDS. Modeling the callee as a program is what makes a submission earnable; atk_07 (hoisted) is still refuted on the `submission_earned_1` side condition, so the structural obligation is live, while pos-decision-inlined-style impls that never submit still verify.
  - §D's joint-satisfiability model: I EXTRACTED the Lean block from refinement.md §D and machine-checked it — refD_model.lean, rc=0. It now mirrors the guarded SHAPE (mRawExpansion carries the domain proof, mExpanded is the guarded reading) and, importantly, §D self-corrects a claim an earlier revision had backwards: it ships `m_unguarded_fact3_also_holds` (the guard on fact 3 is redundant-but-harmless, since off the domain the guarded expansion is [] and mIsDir [] = false) in place of the earlier `m_unguarded_fact3_would_be_false`, which is unprovable once the read is guarded. mapping.md §3 fact 3 states the same thing. The prose and the machine-checked model agree.
  - §E's verify=>resolved argument is consistent with the executed evidence: the domain excludes only entries on which the patch changed nothing (`is_path('~\x00abc')` escapes identically pre- and post-patch, measured), and the F2P input '' is inside the domain by the checked fact `expansionAnswers_empty`.

### RESIDUAL OBSERVATIONS (not defects, not gate-affecting):
  - atk_06_oracle_echo verifies and resolves. It never invokes the strict validator at all, computing the verdict from the free primitives instead. That is admitted by design (properties.py ships the same shape as `pos-decision-inlined`; the obligation is behavioural and never requires the callee to be consulted), and its refinement is behaviourally identical to gold on the tested inputs, so admitting it is fidelity rather than laxity. Worth recording only because a future spec revision that tried to demand the delegation would have to change the clauses, not the impl.
  - **HOST/ENV:** the host was heavily loaded (load avg ~144). Six of the seven resolves needed attempt 2/2 after a transient first-attempt infrastructure failure, but every reported result has completed=true with a real report.json (patch_successfully_applied=true, F2P 1/1, P2P 9/9), and no run was left incomplete. No resolve was left unexecuted and no verdict rests on speculation.
  - Bundle mtimes moved DURING this audit (mapping.md and refinement.md 10:04, properties.py 10:09, vs Solution.lean 09:50). My verdict is pinned to the Solution.lean sha256 above; the prose I audited is the 10:04 revision. verdict.md (09:17) still records the SUPERSEDED break and should be re-stamped from this pass.

**VERDICT:** SOUND. 17 same-spec attacks run (>= the 5-6 required, spanning the 3 prior counterexamples, the prepatch bug, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, answer-from-the-domain, answer-from-a-derived-read, and both derived-submission families). 7 verified; every one of those 7 had its faithful refined patch materialized, `git apply --check`ed at base_commit, and RUN through the official harness — all 7 resolved. Nothing exhibits verify=>correct failure, so the guard repair closes the family that broke the prior revision.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFUL — no diverging input found. Independent (not re-run of shipped gates) differential testing of the modeled function against the REAL patched callee, plus independent re-derivation of all five axioms against the base commit.

**SETUP.** Reference for `optionalPathValidator` =  (base e05cef574 + patch.diff applied; confirmed `is_path_or_empty` present in patched, absent in base). Reference for the axioms =  (base commit). Note the env python (3.10.20) trips `sys.version_info > (3,10)` in sphinx/util/typing.py (`from types import Union`), so I extracted `is_path` / `is_path_or_empty` / `ValidationError` from the real source TEXT via ast (atk2b_9320_extract.py) rather than importing the package — the callee bodies are the real bytes.

1. **SPEC-REGION IDENTITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, backend.language) = True. Two controls: weakening `require expansionAnswers entry = true` → `require True` gives False (the checker does cover the require); a whitespace-only edit inside an ensures gives True (normalization is whitespace-level only, as expected). Spec region is genuinely frozen across the prepatch.

2. MODELED FUNCTION vs REAL PATCHED FUNCTION — ~180k inputs, 4 independent harnesses, seeds of my own choosing (31337 / 777 / 20260816), not the bundle's 9320. Modeled oracle: `''→ok ''`; else `ok guarded_expansion(x)` if `isdir(guarded)` else `error`.
  - atk2b_9320_diff.py: 60050 inputs (boundary + 60k fuzz over an alphabet carrying NUL, high AND low surrogates, `~`, real usernames). buckets oo/acc/ref = 697/14065/45288. 0 in-domain disagreements, 0 in-domain escapes (domain not too large), 0 out-of-domain returns (domain not too small).
  - atk2b_9320_users.py: 80281 inputs seeded from 40 REAL /etc/passwd usernames (`~<user>`, `~<user>/..`, `~<user>\x00`, case-flipped). buckets 6541/16514/57226. 0 violations.
  - atk2b_9320_env.py: real on-disk dirs with adversarial names (a directory literally NAMED `~`, `~root`, embedded newline, low surrogate, spaces), a live symlink, a DANGLING symlink, a regular file, `dir/`, `dir//`, `dir/.`, `dir/..`, `file/` — crossed with 6 HOME settings incl. HOME=<a dir named `~`>, HOME='', HOME unset. 168 checks, 0 violations.
  - atk2b_9320_edge.py: 100k-char entries, 60-deep nesting, ENAMETOOLONG paths, `~`*100, chr(0x10FFFF) runs, Unicode case-folding traps (İ/ẛ/ß), crossed with pathological HOME ('/', '//', '///', 'rel/ative', ''). 275 checks, 0 violations.

3. THE TWO ENSURES CLAUSES, SEPARATELY. Empty clause: real `is_path_or_empty('')` returns `''` → `Except.ok []` under mapping.md §2, and it is reached WITHOUT calling `is_path` (the patch's `if x == '': return x` short-circuits) — so the routing-around content is real, not just the value. Non-empty clause: real returns `path.expanduser(x)` VERBATIM where accepted (matches `pathExpanded entry`, not `x`) and raises ValidationError otherwise; 0 counterexamples across all four harnesses.

4. AXIOMS RE-DERIVED AT BASE COMMIT (atk2b_9320_ax.py, 40054 inputs, seed 777, buckets 649/1850/37555). fact1 expanduser('')=='' ✓; fact2 isdir('') is False ✓; fact5 answers('') ✓; derived strictAccepts_empty=false ✓ and end-to-end `is_path('')` does not come back ✓ (the load-bearing premise for the reported bug). axiom3 (in-domain ∧ accepted → returns guarded expansion verbatim): 0 violations. axiom4 (UNGUARDED: ¬accepted → does not come back): 0 violations — I specifically checked the unguarded region (out-of-domain entries), where it holds because the getpwnam escape propagates through `is_path` too. Theorem accepted_in_domain (accepts → answers): 0 violations. §1.1 totality: `isdir` and the guarded expansion took control away from nobody at 3 arguments each (the entry, and the derived `'~'+NUL+entry` / `'~'+high-surrogate+entry` that the require says nothing about) — ~120k reads, 0 escapes. So no read a verifying impl may perform refines to Python that escapes.

5. THE `require` IS NOT AN OVER-BROAD EXCUSE. I attacked it from both sides. Too large? No — every out-of-domain input escaped for real, so the spec is not excusing a specifiable input. Too small? No — every in-domain input came back with a value or ValidationError. And it is NOT vacuous on Lean-representable inputs: `'~' :: Char.ofNat 0 :: rest` IS a legal Lean `List Char` and IS out of domain in Python, so the restriction does real work rather than only fencing off inputs Lean cannot express. Conversely the empty entry — the one input the change is about — is INSIDE the domain by a checked fact, so the discriminating clause is non-vacuous.

6. **VERIFIER.** scripts/lean_verify.sh on the frozen Solution.lean: exit 0. On Solution_prepatch.lean: exit 1, failing exactly `case «ensures_2: entry = [] → out = Except.ok []»` with goal `entry = [] → Except.error () = Except.ok []` — the discriminating clause is what the prepatch violates, with the require in context.

**NOT-A-DEFECT ITEMS I CONSIDERED AND REJECTED.** (a) The domain restriction excluding `~`+NUL entries: this is a legitimate spec-too-strong REPAIR, not a drift — the real patched function has a third outcome there (neither ok nor ValidationError) that mapping.md §2.2 / refinement.md §C disclose and measure; comparing against the base version there would be the base-commit trap the brief warns about (the patch changes nothing on those entries anyway). (b) The impl-shape restriction (gold's own `return is_path(x)` control flow cannot verify under termination "total"): a restriction on which shapes may establish the clauses, disclosed in refinement.md §C, and it adds no obligation the real post-patch behavior violates — the frozen impl refines patched behavior exactly, which is what my 180k-input fuzz measured. (c) Lean `Char` excluding surrogates: a carrier-coverage gap that makes the spec narrower, never stronger.

**CONCLUSION.** On every input where the spec claims an outcome, the modeled function agrees with the real patched `is_path_or_empty`; all five axioms hold of the real base-commit callee including in the unguarded region; the domain is measured tight in both directions. No diverging input exists that I could find, so no defect is claimed.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** judged the CONSUMER spec view derived exactly as the harness does -- markers.spec_view(Solution.lean, VelvetBackend().language); impl region and prove_correct body collapse to 'implementation elided / proof elided' (256 view lines, dumped to specview_9320.txt). All measurements below are mine, run on the CURRENT bytes.

**NO RELAXATION IN PLAY:** there is no RELAXED_LEAKAGE.md anywhere under the instance dir (checked instance root + velvet/ + lean/ + nagini/ + ears/), and meta.json has no relaxed_leakage key (keys are additional_change_sites, axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, schema_version, spec_provenance, string_modeling, version). So this is an ordinary full-strictness leakage judgement, not an inherited disposition.

SPEC REGION IDENTICAL (I ran it): markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend().language) -> True. The only diff between the two files is inside impl-start/impl-end (prepatch routes every entry through strictAccepts; post adds the `if entry = [] then return Except.ok []` branch). No spec-region drift between the gold and prepatch impls, so the spec view I judged is the one the consumer sees for either.

NON-VACUITY (I ran it): scripts/lean_verify.sh Solution.lean -> exit 0. scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, 'unsolved goals' at 262:36, case <<ensures_2: entry = [] -> out = Except.ok []>>, both branches (|- entry = [] -> Except.ok x = Except.ok [] and |- entry = [] -> Except.error () = Except.ok []). So the empty-entry discriminating clause is load-bearing against the PRE-patch impl -- the clause I am judging is real, not inert prose.

MECHANICAL SCREEN (I ran it): leakage.screen(Solution.lean, velvet tables, gold patch, problem_statement, test_patch) -> hard_failures=[], warnings=[]. Independently re-derived the screen inputs: changed files ['sphinx/cmd/quickstart.py'], changed symbols ['ask_user', 'is_path', 'is_path_or_empty'], changed lines ['def is_path_or_empty(x: str) -> str:', "if x == '':", 'return x', 'return is_path(x)', "'', is_path)", "'', is_path_or_empty)"]. Grepped the view for each of these plus 'quickstart', 'do_prompt', 'sys.exit', 'conf.py', 'sphinx', 'allow_empty', 'ValidationError', 'monkeypatch', 'test_': ZERO hits. No file path, no module path, no patched symbol, no diff marker, no narration verb (fix/bug/patch/previously/...) anywhere in the view.

**HINTS NOT ECHOED:** hints_text says the tool 'should exit with status 1 immediately'. The spec view says nothing about an exit, an exit status, or immediacy -- it speaks only of an outcome value (Except.ok [] vs Except.error ()). Judged against problem_statement only, as required.

**DISCRIMINATOR IS PUBLIC.** The facet the spec view discloses is: an empty entry is an accepted sentinel returned verbatim and never submitted to the strict validator; every non-empty entry gets the strict validator's verdict (lines 216-234, and the two `ensures` at 246-249). Every element of that is derivable from problem_statement alone: it states the prompt is 'Please enter a new root path name (or just Enter to exit)', that pressing Enter (the empty entry -- the only input the whole report is about) is rejected with 'Please enter a valid path name' (i.e. a path-name validity check currently governs and refuses it), and that the expected behavior is for the empty entry to be accepted and acted upon. 'Empty must be accepted rather than refused by the path-name check, non-empty unchanged' IS the public bug report; the spec view restates that behavior and stops there. Strip the narration and the spec still fails on the prepatch impl (measured above), so the clause is load-bearing rather than decorative -- and it is load-bearing on a fact the task already hands the solver.

**WHAT THE VIEW WITHHOLDS:** it does not say the edit adds a NEW top-level function; does not say the change site is a `do_prompt` call's validator argument; does not name the file, module, or any of the three patched symbols; does not disclose the delegation shape (`if x == '': return x; return is_path(x)`). The modeled callee is called `strictPathValidator`/`strictAccepts`/`pathExpanded` -- none embeds `is_path`, `is_path_or_empty`, or `ask_user`. Axiomatizing the unchanged callee is structurally forced (a submission with a turns-away fact cannot be specified without it) and is what mapping.md/axiom_check.py are for; it localizes nothing.

BENIGN, RECORDED FOR THE RECORD: view line 105 names the stdlib symbol `os.path.isdir` ('`os.path.isdir` of the guarded expansion can only be true where the expansion answered'). It is not a patched symbol, not on any changed line, and the gold patch does not touch it; it describes the unchanged callee's directory test, which the public error message 'Please enter a valid path name' already implies. Not edit-localizing, so not a leak -- but it is the one repo-grounded identifier in the view and I looked at it deliberately rather than letting the screen's patched-symbol-only rule pass it silently.

FINDING -- INHERITANCE HAZARD IN verdict.md (not reviewer-directed instruction, but reported as asked): the non-ledger files are clean -- grep -rniE 'attacker|reviewer|G-PANEL|honest verdict|you should submit|NO-LEAKAGE|do not submit|record (this|it) as' over mapping.md, refinement.md, properties.py, axiom_check.py, conformance_check.py returns ZERO hits, so nothing in the spec-adjacent material tries to tell me how to record. verdict.md (the gate ledger) DOES carry two prior G-PANEL-3 records ending 'CONCLUSION: no line of the spec view carries edit-localizing information beyond the public problem_statement. Verdict NO-LEAKAGE', including a pre-written 'NO FILE ADDRESSES THE REVIEWER' paragraph and the exact grep line to justify it. That is a retained prior verdict in the ledger rather than an instruction planted for me, and I did not inherit it: I re-derived same_spec, both verify runs, the screen, and the symbol/line extraction from scratch. Flagging it because a reader could mistake that pre-formatted paragraph for a measurement.

STALE STAMPS (freshness, not leakage): current Solution.lean sha256 is 85817573100b21736e0261182f303fa1436566a7fe8787b9804f876c18425f62 (mtime 09:50), which matches NO gate stamp -- G-AX/G-CONF/G-LEAK/G-MUT/G-EQ/G-PANEL-3 recorded b37d358b... and G-DIFF/G-GOLD/G-VERIFY recorded 2159b4d2... (09:41). So every stamped gate on this bundle, including the prior G-LEAK pass and the prior G-PANEL-3 NO-LEAKAGE, predates the current bytes. My verdict rests only on what I re-ran on 85817573..., where verify passes, prepatch fails, same_spec holds, and the screen is clean. Worth a re-stamp regardless of this gate.

OUT OF SCOPE, NOTED: G-EQ and G-PANEL-1 are fail on this bundle (spec-too-weak -- atk_A1_derived_probe.lean verifies but its patch does not resolve, a derived-argument read of the non-total expansion primitive). That is a strength defect, orthogonal to leakage: a spec that is too weak discloses less, not more, and no relaxation argument here depends on those gates passing.

**VERDICT:** NO-LEAKAGE. The spec view discloses exactly the empty-entry-accepted-vs-refused facet the public problem_statement already reports, and nothing about where or how the repo edit is made.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

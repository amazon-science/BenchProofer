# P2 adversarial audit — django__django-14404

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_double_slash.lean`, `atk_4_no_slash.lean`, `atk_5_order_swap.lean`, `atk_6_prepend_slash.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   ensures ∃ rest, out = mountPrefix ++ rest
   do
     -- impl-start
-    let result := fullPath mountPrefix localPath ++ ['/']
+    let result := localPath ++ ['/']
     return result
     -- impl-end
 
```

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   ensures ∃ rest, out = mountPrefix ++ rest
   do
     -- impl-start
-    let result := fullPath mountPrefix localPath ++ ['/']
+    let result := if mountPrefix = ([] : List Char) then fullPath mountPrefix localPath ++ ['/'] else localPath ++ ['/']
     return result
     -- impl-end
 
```

Attack 3 — `atk_3_double_slash.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   ensures ∃ rest, out = mountPrefix ++ rest
   do
     -- impl-start
-    let result := fullPath mountPrefix localPath ++ ['/']
+    let result := fullPath mountPrefix localPath ++ ['/', '/']
     return result
     -- impl-end
 
```

Attack 4 — `atk_4_no_slash.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   ensures ∃ rest, out = mountPrefix ++ rest
   do
     -- impl-start
-    let result := fullPath mountPrefix localPath ++ ['/']
+    let result := fullPath mountPrefix localPath
     return result
     -- impl-end
 
```

Attack 5 — `atk_5_order_swap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   ensures ∃ rest, out = mountPrefix ++ rest
   do
     -- impl-start
-    let result := fullPath mountPrefix localPath ++ ['/']
+    let result := localPath ++ mountPrefix ++ ['/']
     return result
     -- impl-end
 
```

Attack 6 — `atk_6_prepend_slash.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   ensures ∃ rest, out = mountPrefix ++ rest
   do
     -- impl-start
-    let result := fullPath mountPrefix localPath ++ ['/']
+    let result := ['/'] ++ fullPath mountPrefix localPath
     return result
     -- impl-end
 
```

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,7 +70,7 @@
   ensures ∃ rest, out = mountPrefix ++ rest
   do
     -- impl-start
-    let result := fullPath mountPrefix localPath ++ ['/']
+    let result := redirectTarget mountPrefix localPath
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The deployment mount point under which a request is
--  served is an environment-supplied prefix that is prepended, verbatim, to the
--  per-request local path to recover the request's full, client-facing
--  path. That full path is modeled DEEPLY (`fullPath` below) as the
--  concatenation of the two carriers, and `fullPath == the request's real full
--  path` is validated executably by axiom_check.py (G-AX) — an A-reference, not
--  a consumed axiom. Nothing about an unchanged library callee is assumed.)
-- axioms-end

-- pure-start
/- The request's full, client-facing path: the deployment mount-point
   prefix under which the application is served, followed by the per-request
   local path. When the application is mounted at the server root the prefix is
   empty and the full path coincides with the local path; otherwise the prefix
   is a genuine, non-empty component of every client-facing URL.

   This is a deep model of the request's full path (an unchanged framework
   attribute); `fullPath == that real attribute` is validated by axiom_check.py
   (G-AX), so it is an A-reference, not a consumed axiom. -/
def fullPath (mountPrefix localPath : List Char) : List Char :=
  mountPrefix ++ localPath

/- The trailing-slash redirect destination: the request's full path with a
   single '/' appended. The destination is assembled from the FULL path — the
   client-facing one that includes the deployment mount-point prefix — so
   that a client served under a non-root mount point is redirected to a URL that
   stays under that same mount point. -/
def redirectTarget (mountPrefix localPath : List Char) : List Char :=
  fullPath mountPrefix localPath ++ ['/']

@[grind] lemma redirectTarget_def (mountPrefix localPath : List Char) :
    redirectTarget mountPrefix localPath = mountPrefix ++ localPath ++ ['/'] := by
  simp [redirectTarget, fullPath, List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the trailing-slash redirect destination for a request that is missing
   its trailing slash, from two read-only inputs:

   - `mountPrefix`: the deployment mount-point prefix under which the
     application is served (empty when mounted at the server root, a genuine
     non-empty prefix otherwise);
   - `localPath`: the per-request local path within the application.

   Neither input is mutated (directive 5). The destination MUST be built from
   the request's FULL client-facing path — the mount-point prefix followed
   by the local path — with a single trailing '/' appended, so that the prefix
   is preserved in the redirect. A destination assembled from the local path
   alone would strip the mount-point prefix and send the client outside the
   application's mount point; that is exactly the behaviour this specification
   forbids. -/
method appendSlashRedirect (mountPrefix : List Char) (localPath : List Char)
    return (out : List Char)
  ensures out = redirectTarget mountPrefix localPath
  ensures out = mountPrefix ++ localPath ++ ['/']
  ensures ∃ rest, out = mountPrefix ++ rest
  do
    -- impl-start
    let result := fullPath mountPrefix localPath ++ ['/']
    return result
    -- impl-end

prove_correct appendSlashRedirect by
  loom_solve
  all_goals first
    | (exact ⟨localPath ++ ['/'], by simp [fullPath, List.append_assoc]⟩)
    | simp [redirectTarget, fullPath, List.append_assoc]
```

Prepatch bug re-encoded as an attack: `True`.

REAL PROJECT ROOT; env set with FSx HOME per the audit protocol. All 7 attacks are same_spec==True (verified via swebench_unified.markers.same_spec + get_backend('velvet').language). same_spec elides both impl and prove_correct body, so the gold proof tactic was kept and simply fails to close for genuinely-wrong impls.

Spec character: appendSlashRedirect is a FULLY FUNCTIONALLY PINNED total-correctness spec — postconditions force out = redirectTarget mountPrefix localPath = mountPrefix ++ localPath ++ ['/'] for every input, plus the frame clause ∃ rest, out = mountPrefix ++ rest. There is no free choice, so any behavioral deviation is un-verifiable.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently in 2 batches of 4):
- pos_control (gold impl: fullPath ++ ['/']): EXIT 0 (verifies) — positive control OK.
- atk_1_prepatch (localPath ++ ['/'] — the recorded prepatch bug, drops mount prefix): EXIT 1 (unsolved goals) — prepatch reproduced.
- atk_2_partial_domain (if mountPrefix=[] then correct else prepatch): EXIT 1.
- atk_3_double_slash (fullPath ++ ['/','/']): EXIT 1.
- atk_4_no_slash (fullPath, no trailing slash): EXIT 1.
- atk_5_order_swap (localPath ++ mountPrefix ++ ['/']): EXIT 1.
- atk_6_prepend_slash (['/'] ++ fullPath): EXIT 1.
- atk_7_echo (redirectTarget mountPrefix localPath — ungrounded-oracle echo, behaviorally == gold): EXIT 0 (verifies).

Only the echo attack verifies (it computes the exact spec value via the oracle name; behaviorally identical to gold, not a wrong impl). Per protocol I MATERIALIZED its faithful patch (= the gold hunk: '%s/' % request.path) and RAN it through the official harness:
  run_resolve('django__django-14404', patch, timeout=1800, retries=1) => RESOLVED=True, COMPLETED=True, note='resolved'.
  FAIL_TO_PASS both pass: test_missing_slash_append_slash_true_force_script_name, test_missing_slash_append_slash_true_script_name. PASS_TO_PASS all pass; 0 failures.
The only verifying impl's faithful patch RESOLVES, so verify⇏correct is NOT exhibited — no break.

refinement.md leg audit: A1/A2 = R (param type refinements, G-CONF-covered); A3 = A-reference + I (deep fullPath model of request.path; I concat + A-reference equality); A4 = I + R (single-slash template + HttpResponsePermanentRedirect identity). B: no consumed axioms (axioms region is comment-only — confirmed). C: no kind-3. The single A-reference correspondence (fullPath/redirectTarget == real request.path / '%s/' % request.path) is independently machine-validated: meta.json G-AX pass = 'sound on 56 boundary + 20000 fuzz (script_name, path_info) pairs' and is corroborated by the echo resolve run above. No kind-3 leg; every leg is R / A-reference / I.

All six genuinely-wrong impls (partial-domain, two boundary variants, order-swap, control-flow-effect via if, ungrounded-oracle echo covered separately) fail verification, and the one verifying impl resolves. The spec is tight.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_double_slash.lean`, `atk_4_no_slash.lean`, `atk_5_order_swap.lean`, `atk_6_prepend_slash.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_double_slash.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_no_slash.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_order_swap.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_prepend_slash.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The deployment mount point under which a request is
--  served is an environment-supplied prefix that is prepended, verbatim, to the
--  per-request local path to recover the request's full, client-facing
--  path. That full path is modeled DEEPLY (`fullPath` below) as the
--  concatenation of the two carriers, and `fullPath == the request's real full
--  path` is validated executably by axiom_check.py (G-AX) — an A-reference, not
--  a consumed axiom. Nothing about an unchanged library callee is assumed.)
-- axioms-end

-- pure-start
/- The request's full, client-facing path: the deployment mount-point
   prefix under which the application is served, followed by the per-request
   local path. When the application is mounted at the server root the prefix is
   empty and the full path coincides with the local path; otherwise the prefix
   is a genuine, non-empty component of every client-facing URL.

   This is a deep model of the request's full path (an unchanged framework
   attribute); `fullPath == that real attribute` is validated by axiom_check.py
   (G-AX), so it is an A-reference, not a consumed axiom. -/
def fullPath (mountPrefix localPath : List Char) : List Char :=
  mountPrefix ++ localPath

/- The trailing-slash redirect destination: the request's full path with a
   single '/' appended. The destination is assembled from the FULL path — the
   client-facing one that includes the deployment mount-point prefix — so
   that a client served under a non-root mount point is redirected to a URL that
   stays under that same mount point. -/
def redirectTarget (mountPrefix localPath : List Char) : List Char :=
  fullPath mountPrefix localPath ++ ['/']

@[grind] lemma redirectTarget_def (mountPrefix localPath : List Char) :
    redirectTarget mountPrefix localPath = mountPrefix ++ localPath ++ ['/'] := by
  simp [redirectTarget, fullPath, List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the trailing-slash redirect destination for a request that is missing
   its trailing slash, from two read-only inputs:

   - `mountPrefix`: the deployment mount-point prefix under which the
     application is served (empty when mounted at the server root, a genuine
     non-empty prefix otherwise);
   - `localPath`: the per-request local path within the application.

   Neither input is mutated (directive 5). The destination MUST be built from
   the request's FULL client-facing path — the mount-point prefix followed
   by the local path — with a single trailing '/' appended, so that the prefix
   is preserved in the redirect. A destination assembled from the local path
   alone would strip the mount-point prefix and send the client outside the
   application's mount point; that is exactly the behaviour this specification
   forbids. -/
method appendSlashRedirect (mountPrefix : List Char) (localPath : List Char)
    return (out : List Char)
  ensures out = redirectTarget mountPrefix localPath
  ensures out = mountPrefix ++ localPath ++ ['/']
  ensures ∃ rest, out = mountPrefix ++ rest
  do
    -- impl-start
    let result := fullPath mountPrefix localPath ++ ['/']
    return result
    -- impl-end

prove_correct appendSlashRedirect by
  loom_solve
  all_goals first
    | (exact ⟨localPath ++ ['/'], by simp [fullPath, List.append_assoc]⟩)
    | simp [redirectTarget, fullPath, List.append_assoc]
```

Prepatch bug re-encoded as an attack: `True`.

REAL PROJECT ROOT; env set with FSx HOME per the audit protocol. All 7 attacks are same_spec==True (verified via swebench_unified.markers.same_spec + get_backend('velvet').language). same_spec elides both impl and prove_correct body, so the gold proof tactic was kept and simply fails to close for genuinely-wrong impls.

Spec character: appendSlashRedirect is a FULLY FUNCTIONALLY PINNED total-correctness spec — postconditions force out = redirectTarget mountPrefix localPath = mountPrefix ++ localPath ++ ['/'] for every input, plus the frame clause ∃ rest, out = mountPrefix ++ rest. There is no free choice, so any behavioral deviation is un-verifiable.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently in 2 batches of 4):
- pos_control (gold impl: fullPath ++ ['/']): EXIT 0 (verifies) — positive control OK.
- atk_1_prepatch (localPath ++ ['/'] — the recorded prepatch bug, drops mount prefix): EXIT 1 (unsolved goals) — prepatch reproduced.
- atk_2_partial_domain (if mountPrefix=[] then correct else prepatch): EXIT 1.
- atk_3_double_slash (fullPath ++ ['/','/']): EXIT 1.
- atk_4_no_slash (fullPath, no trailing slash): EXIT 1.
- atk_5_order_swap (localPath ++ mountPrefix ++ ['/']): EXIT 1.
- atk_6_prepend_slash (['/'] ++ fullPath): EXIT 1.
- atk_7_echo (redirectTarget mountPrefix localPath — ungrounded-oracle echo, behaviorally == gold): EXIT 0 (verifies).

Only the echo attack verifies (it computes the exact spec value via the oracle name; behaviorally identical to gold, not a wrong impl). Per protocol I MATERIALIZED its faithful patch (= the gold hunk: '%s/' % request.path) and RAN it through the official harness:
  run_resolve('django__django-14404', patch, timeout=1800, retries=1) => RESOLVED=True, COMPLETED=True, note='resolved'.
  FAIL_TO_PASS both pass: test_missing_slash_append_slash_true_force_script_name, test_missing_slash_append_slash_true_script_name. PASS_TO_PASS all pass; 0 failures.
The only verifying impl's faithful patch RESOLVES, so verify⇏correct is NOT exhibited — no break.

refinement.md leg audit: A1/A2 = R (param type refinements, G-CONF-covered); A3 = A-reference + I (deep fullPath model of request.path; I concat + A-reference equality); A4 = I + R (single-slash template + HttpResponsePermanentRedirect identity). B: no consumed axioms (axioms region is comment-only — confirmed). C: no kind-3. The single A-reference correspondence (fullPath/redirectTarget == real request.path / '%s/' % request.path) is independently machine-validated: meta.json G-AX pass = 'sound on 56 boundary + 20000 fuzz (script_name, path_info) pairs' and is corroborated by the echo resolve run above. No kind-3 leg; every leg is R / A-reference / I.

All six genuinely-wrong impls (partial-domain, two boundary variants, order-swap, control-flow-effect via if, ungrounded-oracle echo covered separately) fail verification, and the one verifying impl resolves. The spec is tight.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified independently: (a) same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with the velvet backend — spec view byte-identical; (b) Solution.lean verifies (lean_verify.sh exit 0); (c) Solution_prepatch.lean (result:=localPath++['/']) FAILS with unsolved goal `mountPrefix = []`, confirming the spec discriminates exactly the mount-prefix-preservation change (G-DIFF). The model models request.path DEEPLY (mp ++ lp) rather than axiomatizing; G-AX/axiom_check.py validates it against the real attribute. The single behavioral change (destination built from request.path incl. prefix, not request.path_info) is captured by the frame clause ∃rest,out=mountPrefix++rest. Termination='total' is faithful (straight-line string format always terminates). The one divergence class (non-leading-slash path_info) is provably outside the operational domain because the redirect only fires after a successful resolve(), which requires a leading slash. Spec is neither too strong nor drifting: gold satisfies it on every reachable input, and it forbids the prepatch behavior. Verdict: FAITHFUL.

Counterexample / evidence:

```
No reachable counterexample. Over 80,000 realistic fuzz pairs (leading-slash path_info, ASCII URL alphabet, incl. SCRIPT_NAME and FORCE_SCRIPT_NAME-shaped prefixes) plus axiom_check's 56 boundary + 20,000 seeded-14404 fuzz pairs on real WSGIRequests built by RequestFactory: request.path == fullPath(script_name.rstrip('/'), request.path_info) and '%s/' % request.path == redirectTarget(...) held on every case (0 mismatches). Gold patched catch_all_view satisfies out=mountPrefix++localPath++['/'], out=redirectTarget, and ∃rest,out=mountPrefix++rest on all reachable inputs.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) == True. The spec view (imports/set_options/axioms/pure/pre/post + method signature & ensures) is identical across patched and prepatch; only the elided impl+proof differ.

Baseline (public problem_statement): 'catch_all_view returns redirect to \'%s/\' % request.path_info (script name cut off there) instead of \'%s/\' % request.path (with the script name)'. This ALREADY names both the pre-patch and post-patch expressions and states the exact fix verbatim; the entire gold patch is that single substitution (build the redirect destination from the full path that carries the script-name/mount prefix, plus trailing slash).

Spec-view content assessed line-by-line: the pure helpers fullPath = mountPrefix ++ localPath, redirectTarget = fullPath ++ ['/'], and the appendSlashRedirect ensures clauses (out = mountPrefix ++ localPath ++ ['/']; ∃ rest, out = mountPrefix ++ rest) restate the same publicly-disclosed 'with the script name' / mount-prefix-preservation requirement in abstract Lean terms. This does not narrow the solution space beyond what problem_statement already gives. The spec-view comments describe only the abstract 'full path = deployment mount-point prefix ++ local path' relationship — exactly the public statement's content. No gold-patch file/line source text is quoted in the consumer-visible spec view: references to sites.py:423,430 / wsgi.py:75-76 and axiom_check.py appear ONLY in the narrative docs mapping.md and refinement.md, which are not part of the spec view; and even those merely re-describe the publicly stated request.path relationship. No spec-view line reveals gold-edit content beyond the public problem_statement (hints_text excluded from baseline as required).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

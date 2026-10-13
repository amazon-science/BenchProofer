# P2 adversarial audit — django__django-16612

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 11 same-spec admissible wrong impls were encoded and verified; 10 were REJECTED with genuine `unsolved goals` (not syntax errors) after a 14-way tactic chain (rfl / simp / decide / simp_all / split<;>simp / congr / aesop / ext ...), so each rejection is a refusal by the specification rather than a lazy tactic script. The single attack that verified (atk_7, the ungrounded-oracle echo that inlines the spec RHS) is a CORRECT echo of the gold, not a weakness: its materialized faithful patch RESOLVES under the official harness (both FAIL_TO_PASS + all 335 PASS_TO_PASS pass), and a 200k-input differential test shows 0 disagreements against the real `request.get_full_path(force_append_slash=True)`. There is therefore no verifying-but-incorrect artifact. The spec is an exact functional equality that pins `result` uniquely per input, so any impl differing on ANY input leaves an unclosable goal.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,10 +62,9 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
-  let escapedPath := escapePathComponent path
-  let trailingSlash := if path.endsWith "/" then "" else "/"
-  let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
-  return escapedPath ++ trailingSlash ++ querySuffix
+  -- prepatch bug: "%s/" % request.path -- raw path, unconditional trailing
+  -- slash, query string discarded.
+  return path ++ "/"
 -- impl-end
 
 -- proof-start
@@ -75,5 +74,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -63,7 +63,9 @@
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
   let escapedPath := escapePathComponent path
-  let trailingSlash := if path.endsWith "/" then "" else "/"
+  -- boundary defect: also suppresses the slash when the path is EMPTY, so the
+  -- impl agrees with the spec on every non-empty path and differs only at "".
+  let trailingSlash := if path.endsWith "/" || path == "" then "" else "/"
   let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
   return escapedPath ++ trailingSlash ++ querySuffix
 -- impl-end
@@ -75,5 +77,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,7 +64,9 @@
     (path queryString : String) : String := Id.run do
   let escapedPath := escapePathComponent path
   let trailingSlash := if path.endsWith "/" then "" else "/"
-  let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
+  -- A-leg attack: encode the QUERY string with the PATH encoder. Verifies iff
+  -- the two distinct `opaque` leaves are provably equal.
+  let querySuffix := if queryString = "" then "" else "?" ++ escapePathComponent queryString
   return escapedPath ++ trailingSlash ++ querySuffix
 -- impl-end
 
@@ -75,5 +77,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,7 +62,9 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
-  let escapedPath := escapePathComponent path
+  -- A-leg attack: drop the path encoder entirely. Verifies iff the opaque
+  -- leaf `escapePathComponent` is provably the identity function.
+  let escapedPath := path
   let trailingSlash := if path.endsWith "/" then "" else "/"
   let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
   return escapedPath ++ trailingSlash ++ querySuffix
@@ -75,5 +77,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,7 +62,10 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
-  let escapedPath := escapePathComponent path
+  -- A-leg attack: apply the path encoder TWICE. Verifies iff the opaque leaf
+  -- `escapePathComponent` is provably idempotent. The faithful patch
+  -- double-escapes every `%`, so `/a%20b` redirects to `/a%2520b/`.
+  let escapedPath := escapePathComponent (escapePathComponent path)
   let trailingSlash := if path.endsWith "/" then "" else "/"
   let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
   return escapedPath ++ trailingSlash ++ querySuffix
@@ -75,5 +78,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,10 +62,14 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
-  let escapedPath := escapePathComponent path
-  let trailingSlash := if path.endsWith "/" then "" else "/"
-  let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
-  return escapedPath ++ trailingSlash ++ querySuffix
+  -- control-flow-effect attack: build the target with a mutable accumulator in
+  -- the identity monad and a finite `for`, appending the query suffix on EVERY
+  -- iteration. The list has two elements, so a present query string lands twice.
+  let mut acc := escapePathComponent path
+  acc := acc ++ (if path.endsWith "/" then "" else "/")
+  for _ in [1, 2] do
+    acc := acc ++ (if queryString = "" then "" else "?" ++ encodeQueryString queryString)
+  return acc
 -- impl-end
 
 -- proof-start
@@ -75,5 +79,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,10 +62,12 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
-  let escapedPath := escapePathComponent path
-  let trailingSlash := if path.endsWith "/" then "" else "/"
-  let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
-  return escapedPath ++ trailingSlash ++ querySuffix
+  -- ungrounded-oracle echo: do not compute the target at all -- CHOOSE a string
+  -- that satisfies the postcondition. Verifies for ANY postcondition that is
+  -- satisfiable; it is a real weakness only if the spec fails to pin the value.
+  return escapePathComponent path
+      ++ (if path.endsWith "/" then "" else "/")
+      ++ (if queryString = "" then "" else "?" ++ encodeQueryString queryString)
 -- impl-end
 
 -- proof-start
@@ -75,5 +77,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,7 +64,10 @@
     (path queryString : String) : String := Id.run do
   let escapedPath := escapePathComponent path
   let trailingSlash := if path.endsWith "/" then "" else "/"
-  let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
+  -- boundary defect on the QUERY branch: the falsy test is widened from
+  -- `queryString = ""` to "no `=` anywhere", so a bare flag query like `?debug`
+  -- is silently dropped while `?id=1` survives.
+  let querySuffix := if !(queryString.contains '=') then "" else "?" ++ encodeQueryString queryString
   return escapedPath ++ trailingSlash ++ querySuffix
 -- impl-end
 
@@ -75,5 +78,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,7 +62,9 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
-  let escapedPath := escapePathComponent path
+  -- A-leg attack (opposite direction from atk_3): encode the PATH with the
+  -- QUERY encoder. Verifies iff the two distinct opaque leaves are provably equal.
+  let escapedPath := encodeQueryString path
   let trailingSlash := if path.endsWith "/" then "" else "/"
   let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
   return escapedPath ++ trailingSlash ++ querySuffix
@@ -75,5 +77,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,10 +62,11 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
+  -- boundary attack: keep the query string (so the F2P assertion is met) but
+  -- append the slash UNCONDITIONALLY, double-slashing an already-terminated path.
   let escapedPath := escapePathComponent path
-  let trailingSlash := if path.endsWith "/" then "" else "/"
   let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
-  return escapedPath ++ trailingSlash ++ querySuffix
+  return escapedPath ++ "/" ++ querySuffix
 -- impl-end
 
 -- proof-start
@@ -75,5 +76,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -62,10 +62,15 @@
 -- impl-start
 def implementation_redirectTargetWithTrailingSlash
     (path queryString : String) : String := Id.run do
+  -- control-flow-effect attack: decide the trailing slash with a mutable flag
+  -- driven by a finite `for` over the path's characters, flagging ANY '/' rather
+  -- than only a final one, so `/a/b` is judged already-terminated.
+  let mut hasSlash := false
+  for c in path.data do
+    if c == '/' then hasSlash := true
   let escapedPath := escapePathComponent path
-  let trailingSlash := if path.endsWith "/" then "" else "/"
   let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
-  return escapedPath ++ trailingSlash ++ querySuffix
+  return escapedPath ++ (if hasSlash then "" else "/") ++ querySuffix
 -- impl-end
 
 -- proof-start
@@ -75,5 +80,19 @@
         (implementation_redirectTargetWithTrailingSlash path queryString) := by
   intro path queryString
   unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
-  rfl
+  first
+    | rfl
+    | (simp; rfl)
+    | simp
+    | decide
+    | simp_all
+    | (split <;> rfl)
+    | (split <;> simp)
+    | (split <;> split <;> simp_all)
+    | (simp [String.endsWith, String.startsWith] <;> rfl)
+    | (simp only [String.append_eq, List.append_assoc]; rfl)
+    | (congr 1 <;> simp_all)
+    | aesop
+    | (simp_arith; rfl)
+    | (ext; simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all files; every attack built by copying the frozen Solution.lean and editing ONLY the impl region, so same_spec=True and unsound_evasions=[] for all 11 + the control — confirmed via swebench_unified.markers.same_spec and variant_scope.unsound_evasions).

**COMMANDS:** verification `bash scripts/lean_verify.sh <D>/atk_N.lean` from the repo root, run 4-at-a-time as concurrent background jobs (3 batches). Axiom probes appended `#print axioms correct_redirectTargetWithTrailingSlash` to a copy (atk_7_ax.lean, pos_control_ax.lean). Resolve: `run_resolve('django__django-16612', open(atk_7.diff).read())` from swebench_unified.harness.

### RESULTS (exit codes in exits.txt, stderr/stdout in atk_N.log):
- atk_1 exit=1 — PREPATCH BUG re-encoded: `return path ++ "/"`. Impl body is BYTE-IDENTICAL to Solution_prepatch.lean's (verified programmatically), so prepatch_reproduced=true. Goal left: `path ++ "/" = escapePathComponent path ++ ... ++ (query suffix)`.
- atk_2 exit=1 — PARTIAL-DOMAIN/boundary: slash suppressed also at `path = ""` (`path.endsWith "/" || path == ""`); agrees with gold on every non-empty path, differs only at "". Rejected.
- atk_3 exit=1 — A-LEG SWAP: query encoded with the PATH encoder (`escapePathComponent queryString`). Verifies only if the two distinct opaque leaves are provably equal; rejected.
- atk_4 exit=1 — A-LEG DROPPED: raw `path` instead of `escapePathComponent path`. Verifies only if the leaf is provably the identity; rejected.
- atk_5 exit=1 — A-LEG IDEMPOTENCE: `escapePathComponent (escapePathComponent path)` (double-escapes every %). Rejected.
- atk_6 exit=1 — CONTROL-FLOW-EFFECT: mutable accumulator in Id.run with a finite `for _ in [1,2]` appending the query suffix twice. Rejected (goal shows the doubled suffix).
- atk_7 exit=0 — UNGROUNDED-ORACLE ECHO (inlined spec RHS). VERIFIES; `#print axioms` = `[propext]`, i.e. CLEAN (STANDARD_AXIOMS = propext/Classical.choice/Quot.sound, no sorryAx). Per protocol its faithful patch was materialized (atk_7.diff — inlines `escape_uri_path(path) + ("" if path.endswith("/") else "/") + (("?" + iri_to_uri(qs)) if qs else "")` at the catch_all_view call site, plus the encoder import), checked with `git apply --check` in a base_commit worktree (exit 0), and RUN through run_resolve: **RESOLVED=True, patch_successfully_applied=True, FAIL_TO_PASS 2/2 success, PASS_TO_PASS 335/335 success, 0 failures** (resolve_atk7.out). Per `_derive_audit_verdict`, a candidate whose faithful patch DOES resolve is a correct echo of the gold and must NOT fail the gate. Independently corroborated: 200,000-input differential test of the patch expression vs the REAL `request.get_full_path(force_append_slash=True)` gave 0 disagreements.
- atk_8 exit=1 — PARTIAL-DOMAIN on the query branch: falsy test widened from `queryString = ""` to "contains no '='", so a bare-flag query (`?debug`) is dropped while `?id=1` survives. Rejected.
- atk_9 exit=1 — A-LEG SWAP, opposite direction: path encoded with the QUERY encoder (`encodeQueryString path`). Rejected.
- atk_10 exit=1 — BOUNDARY: query preserved (so the F2P assertion would pass) but the slash appended UNCONDITIONALLY, double-slashing an already-terminated path. Rejected. Note this attack would satisfy the F2P tests, yet the spec still refuses it — the spec is strictly stronger than the test suite here.
- atk_11 exit=1 — CONTROL-FLOW-EFFECT: trailing slash decided by a mutable flag driven by a finite `for` over `path.data`, flagging ANY '/' rather than a final one (so `/a/b` is judged already-terminated). Rejected.
- POSITIVE CONTROL pos_control.lean exit=0, `#print axioms` = `[propext]` (clean). The frozen impl verifies; the spec is satisfiable, so the 10 rejections are discriminating rather than vacuous.

A-LEG AUDIT (step 3 — refinement.md). All 4 rows are tagged R / R-I / A-reference / I; there is NO kind-3 leg and NO A-consumed row, and that claim is CORRECT: both callees enter as `opaque escapePathComponent/encodeQueryString : String → String` and appear IDENTICALLY on both sides of the postcondition equality, so `correct_*` closes by `rfl` for ANY such functions and consumes no callee property. Consistent with this, `#print axioms` reports only `propext` — no declared `_prop` axiom exists to be consumed, so `declared_axiom_names` is empty and nothing stronger needs validating.

Correspondence to the real callees HOLDS at base_commit: row 1 `escapePathComponent` ↔ `django.utils.encoding.escape_uri_path` = `quote(path, safe="/:@&+$,-_.!~*'()")`; row 3 `encodeQueryString` ↔ `iri_to_uri` = `quote(iri, safe="/#%[]=:;$&()+,!?*@'~")`. Both are pure, total, deterministic `str→str` wrappers over `urllib.parse.quote` — exactly and only the property the `opaque … : String → String` declarations assert, which is what axiom_check.py validates. Their safe-sets DIFFER, so they are genuinely distinct functions; I confirmed empirically that they disagree on 'a=1&b=2', 'q=x?y', 'p#q', 'a;b', 'x=1'. That is why atk_3 and atk_9 (which conflate the two leaves) are correctly unprovable — the opacity is not hiding an equality the model silently assumes.

Row 2's flag reduction is sound: the post-patch call site fixes `force_append_slash=True`, so `"/" if force_append_slash and not path.endswith("/") else ""` genuinely reduces to the modeled conditional; I read the base_commit source (django/http/request.py:182, django/contrib/admin/sites.py:456) to confirm `get_full_path`/`_get_full_path` are unchanged by patch.diff, so modeling them as governed-but-unchanged is faithful. Row 4's concatenation order matches the `"%s%s%s"` format positionally. mapping.md's type bijection (str↔String identity, falsy QUERY_STRING ⇔ `queryString = ""`) is accurate: `""` is the only falsy value `META.get("QUERY_STRING", "")` can return here.

**WHY SOUND:** the postcondition is a total functional equality pinning `result` uniquely for every `(path, queryString)`, with no existential, no partial-domain guard, and no unconstrained component. Every wrong impl therefore leaves an unclosable goal, which is what the 10 rejections show; and the one impl that closes is extensionally equal to the gold and resolves. verify⇒correct is not falsified on this artifact. Housekeeping: the temporary base_commit worktree I created under my scratch dir was removed with `git worktree remove --force`; a pre-existing `stash@{0}` in the django mirror was NOT mine and was left untouched.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 11 same-spec admissible wrong impls were encoded and verified; 10 were REJECTED with genuine `unsolved goals` (not syntax errors) after a 14-way tactic chain (rfl / simp / decide / simp_all / split<;>simp / congr / aesop / ext ...), so each rejection is a refusal by the specification rather than a lazy tactic script. The single attack that verified (atk_7, the ungrounded-oracle echo that inlines the spec RHS) is a CORRECT echo of the gold, not a weakness: its materialized faithful patch RESOLVES under the official harness (both FAIL_TO_PASS + all 335 PASS_TO_PASS pass), and a 200k-input differential test shows 0 disagreements against the real `request.get_full_path(force_append_slash=True)`. There is therefore no verifying-but-incorrect artifact. The spec is an exact functional equality that pins `result` uniquely per input, so any impl differing on ANY input leaves an unclosable goal.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all files; every attack built by copying the frozen Solution.lean and editing ONLY the impl region, so same_spec=True and unsound_evasions=[] for all 11 + the control — confirmed via swebench_unified.markers.same_spec and variant_scope.unsound_evasions).

**COMMANDS:** verification `bash scripts/lean_verify.sh <D>/atk_N.lean` from the repo root, run 4-at-a-time as concurrent background jobs (3 batches). Axiom probes appended `#print axioms correct_redirectTargetWithTrailingSlash` to a copy (atk_7_ax.lean, pos_control_ax.lean). Resolve: `run_resolve('django__django-16612', open(atk_7.diff).read())` from swebench_unified.harness.

### RESULTS (exit codes in exits.txt, stderr/stdout in atk_N.log):
- atk_1 exit=1 — PREPATCH BUG re-encoded: `return path ++ "/"`. Impl body is BYTE-IDENTICAL to Solution_prepatch.lean's (verified programmatically), so prepatch_reproduced=true. Goal left: `path ++ "/" = escapePathComponent path ++ ... ++ (query suffix)`.
- atk_2 exit=1 — PARTIAL-DOMAIN/boundary: slash suppressed also at `path = ""` (`path.endsWith "/" || path == ""`); agrees with gold on every non-empty path, differs only at "". Rejected.
- atk_3 exit=1 — A-LEG SWAP: query encoded with the PATH encoder (`escapePathComponent queryString`). Verifies only if the two distinct opaque leaves are provably equal; rejected.
- atk_4 exit=1 — A-LEG DROPPED: raw `path` instead of `escapePathComponent path`. Verifies only if the leaf is provably the identity; rejected.
- atk_5 exit=1 — A-LEG IDEMPOTENCE: `escapePathComponent (escapePathComponent path)` (double-escapes every %). Rejected.
- atk_6 exit=1 — CONTROL-FLOW-EFFECT: mutable accumulator in Id.run with a finite `for _ in [1,2]` appending the query suffix twice. Rejected (goal shows the doubled suffix).
- atk_7 exit=0 — UNGROUNDED-ORACLE ECHO (inlined spec RHS). VERIFIES; `#print axioms` = `[propext]`, i.e. CLEAN (STANDARD_AXIOMS = propext/Classical.choice/Quot.sound, no sorryAx). Per protocol its faithful patch was materialized (atk_7.diff — inlines `escape_uri_path(path) + ("" if path.endswith("/") else "/") + (("?" + iri_to_uri(qs)) if qs else "")` at the catch_all_view call site, plus the encoder import), checked with `git apply --check` in a base_commit worktree (exit 0), and RUN through run_resolve: **RESOLVED=True, patch_successfully_applied=True, FAIL_TO_PASS 2/2 success, PASS_TO_PASS 335/335 success, 0 failures** (resolve_atk7.out). Per `_derive_audit_verdict`, a candidate whose faithful patch DOES resolve is a correct echo of the gold and must NOT fail the gate. Independently corroborated: 200,000-input differential test of the patch expression vs the REAL `request.get_full_path(force_append_slash=True)` gave 0 disagreements.
- atk_8 exit=1 — PARTIAL-DOMAIN on the query branch: falsy test widened from `queryString = ""` to "contains no '='", so a bare-flag query (`?debug`) is dropped while `?id=1` survives. Rejected.
- atk_9 exit=1 — A-LEG SWAP, opposite direction: path encoded with the QUERY encoder (`encodeQueryString path`). Rejected.
- atk_10 exit=1 — BOUNDARY: query preserved (so the F2P assertion would pass) but the slash appended UNCONDITIONALLY, double-slashing an already-terminated path. Rejected. Note this attack would satisfy the F2P tests, yet the spec still refuses it — the spec is strictly stronger than the test suite here.
- atk_11 exit=1 — CONTROL-FLOW-EFFECT: trailing slash decided by a mutable flag driven by a finite `for` over `path.data`, flagging ANY '/' rather than a final one (so `/a/b` is judged already-terminated). Rejected.
- POSITIVE CONTROL pos_control.lean exit=0, `#print axioms` = `[propext]` (clean). The frozen impl verifies; the spec is satisfiable, so the 10 rejections are discriminating rather than vacuous.

A-LEG AUDIT (step 3 — refinement.md). All 4 rows are tagged R / R-I / A-reference / I; there is NO kind-3 leg and NO A-consumed row, and that claim is CORRECT: both callees enter as `opaque escapePathComponent/encodeQueryString : String → String` and appear IDENTICALLY on both sides of the postcondition equality, so `correct_*` closes by `rfl` for ANY such functions and consumes no callee property. Consistent with this, `#print axioms` reports only `propext` — no declared `_prop` axiom exists to be consumed, so `declared_axiom_names` is empty and nothing stronger needs validating.

Correspondence to the real callees HOLDS at base_commit: row 1 `escapePathComponent` ↔ `django.utils.encoding.escape_uri_path` = `quote(path, safe="/:@&+$,-_.!~*'()")`; row 3 `encodeQueryString` ↔ `iri_to_uri` = `quote(iri, safe="/#%[]=:;$&()+,!?*@'~")`. Both are pure, total, deterministic `str→str` wrappers over `urllib.parse.quote` — exactly and only the property the `opaque … : String → String` declarations assert, which is what axiom_check.py validates. Their safe-sets DIFFER, so they are genuinely distinct functions; I confirmed empirically that they disagree on 'a=1&b=2', 'q=x?y', 'p#q', 'a;b', 'x=1'. That is why atk_3 and atk_9 (which conflate the two leaves) are correctly unprovable — the opacity is not hiding an equality the model silently assumes.

Row 2's flag reduction is sound: the post-patch call site fixes `force_append_slash=True`, so `"/" if force_append_slash and not path.endswith("/") else ""` genuinely reduces to the modeled conditional; I read the base_commit source (django/http/request.py:182, django/contrib/admin/sites.py:456) to confirm `get_full_path`/`_get_full_path` are unchanged by patch.diff, so modeling them as governed-but-unchanged is faithful. Row 4's concatenation order matches the `"%s%s%s"` format positionally. mapping.md's type bijection (str↔String identity, falsy QUERY_STRING ⇔ `queryString = ""`) is accurate: `""` is the only falsy value `META.get("QUERY_STRING", "")` can return here.

**WHY SOUND:** the postcondition is a total functional equality pinning `result` uniquely for every `(path, queryString)`, with no existential, no partial-domain guard, and no unconstrained component. Every wrong impl therefore leaves an unclosable goal, which is what the 10 rejections show; and the one impl that closes is extensionally equal to the gold and resolves. verify⇒correct is not falsified on this artifact. Housekeeping: the temporary base_commit worktree I created under my scratch dir was removed with `git worktree remove --force`; a pre-existing `stash@{0}` in the django mirror was NOT mine and was left untouched.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK LANE:** faithfulness-break (spec too strong / drifts from real repo behavior). Found NO diverging input. Reference = worktree at base_commit 55bcbd8d17 with patch.diff APPLIED (per protocol); base commit used only for the untouched callees the axioms model.

### Setup
- Fresh worktree */base from a local django clone at base_commit; patch.diff applies clean; post-patch call site confirmed = HttpResponsePermanentRedirect(request.get_full_path(force_append_slash=True)) at django/contrib/admin/sites.py:456.
- Governing (patch-UNCHANGED) callee HttpRequest.`_get_full_path` @ django/http/request.py:182 read verbatim: "%s%s%s" % (escape_uri_path(path), "/" if force_append_slash and not path.endswith("/") else "", ("?" + iri_to_uri(META.get("QUERY_STRING",""))) if META.get("QUERY_STRING","") else ""). With force_append_slash fixed True this reduces EXACTLY to the Lean post-condition, piece-for-piece and in the same concatenation order.
- Stale editable django  was shadowing imports; every run below asserts django.`__file__` starts with the worktree path, so all evidence is against the intended source, not the stale tree.

### EVIDENCE (no divergence on any input)
1. Differential fuzz, A-reference leaves left as the REAL repo callees (escape_uri_path, iri_to_uri), shadow-of-Lean-impl vs live request.get_full_path(force_append_slash=True): 120,374 (path, queryString) cases, seed 16612 -> 0 mismatches. Corpus deliberately covers both trailing-slash polarities, empty/"//"/bare-"a" paths, percent-escape triggers, reserved chars, spaces, newlines, unicode (é ♥ 日 emoji), pre-escaped %2F / bare % / malformed %zz, and falsy-looking-but-nonempty query strings ("0", "false", " ", "?", "#frag").
2. EXHAUSTIVE sweep: all strings of length <=3 over a branch-covering 14-char alphabet (/ % ? a = & + space # ♥ : ; ~ ') for BOTH arguments = 2955 x 2955 = 8,732,025 pairs, real vs spec -> 0 mismatches. This is exhaustive over the branch structure, not sampled.
3. LIVE call-site check (the strongest faithfulness probe, and the one that validates the mapping.md type bijection rather than assuming it): wrapped the real AdminSite.catch_all_view, captured every actual 301 Location together with request.path and request.META.get("QUERY_STRING",""), and compared against the spec formula. 6 observed redirects, ALL exact matches - including the SCRIPT_NAME=/prefix/ cases, which confirms request.path (not path_info) is the correct binding and that the spec is parameterised over the inputs the view really feeds it. So the spec is faithful at the call site, not merely against `_get_full_path` in isolation.
4. Real F2P suite: admin_views.tests.AdminSiteFinalCatchAllPatternTests 29/29 OK on the patched worktree, both named FAIL_TO_PASS tests passing. (The single failure in the instrumented run is my probe's own artifact - wrapping catch_all_view drops its @no_append_slash marker; the uninstrumented run is clean 29/29.)

### SPEC-STRENGTH ANALYSIS (the "too strong" question)
- The post-condition is an exact equality that fully pins the result - maximally strong. Too-strong is only a DEFECT if it rejects behavior the real repo exhibits, and 8.7M exhaustive + 120k fuzz + 6 live call-site observations produce zero such input. Strong-and-exact here is correct, not drift.
- No hidden state: `_get_full_path` reads only its path argument (= self.path) and META["QUERY_STRING"]; both are spec parameters. A missing QUERY_STRING key yields "" via .get default, which maps to Lean "", so the falsy-test <-> (queryString = "") bijection is exact - "" is genuinely the only falsy str reachable.
- Flag dependency force_append_slash=True is correctly recorded and is in fact what the post-patch call site hard-codes; the spec does not silently generalize over the flag.
- Axiom totality: escape_uri_path / iri_to_uri probed on boundary + adversarial strings (NUL, \x7f, \x80, U+10FFFF, replacement char, BOM, 5000-char) - total, deterministic, str->str, matching the only property the `opaque _ : String -> String` declarations assert. They raise UnicodeEncodeError ONLY on lone surrogates, which are NOT representable in Lean String (Char excludes D800-DFFF), so they are total on the modeled domain and the opaque-leaf modeling is faithful. No `_prop` axiom is consumed.
- Proof integrity: Solution.lean lean_verify exit 0; standalone rebuild with `#print axioms correct_redirectTargetWithTrailingSlash` -> depends on axioms: [propext]. NO sorryAx - the proof is real, not faked.
- Transcription legs independently machine-checked in Lean: String.endsWith "/" agrees with Python str.endswith("/") on 12 boundary inputs (incl. "", "/", "//", "%2F", "/♥", "/\n") by decide; ++ associativity confirms the "%s%s%s" order is preserved.

### DISCRIMINATION (spec is not vacuous)
- same_spec(Solution, Solution_prepatch, lean tables) = True and the axioms..post-conditions region diffs byte-identical, so the two files share one spec.
- Solution_prepatch.lean (impl `path ++ "/"`) FAILS to elaborate: rfl cannot equate (pure (path ++ "/")).run with escapePathComponent path ++ (slash conditional) ++ (query suffix). The discriminating clause is exactly the dropped query string the F2P tests assert - the spec rejects the real pre-patch bug.

**CONCLUSION:** no input on which the modeled function disagrees with the real post-patch callee. Spec is faithful, exactly pinned, non-vacuous, and correctly discriminates the bug. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

ROLE 3 (leakage / gold-reconstruction), django__django-16612 / lean. NO relaxation present: no RELAXED_LEAKAGE.md anywhere in the bundle tree (find -iname '*relax*' empty) and no `relaxed_leakage` key in meta.json (top keys walked for /relax|leak/ -> only gates/G-LEAK). So this is judged as a plain strict-mode leakage review, not an inherited disposition.

SPEC SURFACE MEASURED (not asserted). Computed the projection myself: PYTHONPATH=src python3 -> swebench_unified.markers.spec_view(Solution.lean, get_backend('lean')). Spec view = docstring narration + axioms region (two `opaque _ : String -> String`) + empty pure region + post-conditions (`problem_spec_redirectTargetWithTrailingSlash` = escapePathComponent path ++ (if path.endsWith "/" then "" else "/") ++ (if queryString = "" then "" else "?" ++ encodeQueryString queryString)); impl and proof regions both collapse to elision placeholders. Idempotent under re-projection (spec_view(view)==view). same_spec(Solution.lean, Solution_prepatch.lean, lean) = True -> the spec view is branch-independent and cannot itself indicate which of the two impls is the fix.

**MECHANICAL SCREEN RE-RUN:** leakage.screen(Solution.lean, lean backend, instance.patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]; same for Solution_prepatch.lean. instance.json['patch'] == patch.diff byte-for-byte. Vector by vector against the gold diff: changed_lines = ['return HttpResponsePermanentRedirect("%s/" % request.path)', 'return HttpResponsePermanentRedirect(', 'request.get_full_path(force_append_slash=True)', ')'] -- none reproduced (normalized) in the view; changed_files = django/contrib/admin/sites.py -- absent, and dotted module path absent; changed_symbols = {'catch_all_view'} -- absent from every spec-view identifier and comment; `_NARRATION_RE`.findall(view) = [] (no bug/fix/patch/previously/broken vocabulary).

GOLD-RECONSTRUCTION PROBE (the substantive question). Explicitly grepped the view for every symbol that would localize the edit: get_full_path, force_append_slash, escape_uri_path, iri_to_uri, QUERY_STRING, catch_all_view, HttpResponsePermanentRedirect, sites.py, admin, django, Http404, APPEND_SLASH, should_append_slash, request.path, '%s/', '?id=', '31747' -- ALL absent. Cross-check the other direction: the only patch tokens (len>=4) present in the view are the English words 'else', 'path', 'request'. The two callees enter as ABSTRACT opaque names (escapePathComponent / encodeQueryString); the real callee names appear only in mapping.md and refinement.md, which are not part of the spec view a consumer is handed. A solver reading the view learns the required OUTPUT SHAPE, not the mechanism -- it does not name get_full_path(force_append_slash=True), so the one-line delegation that is the gold edit still has to be discovered.

**WHAT THE VIEW REVEALS vs THE PUBLIC STATEMENT.** The discriminating clause is the query-string suffix. That is already fully public in problem_statement, not merely adjacent to it: the title is 'AdminSite.catch_all_view() drops query string in redirects', it prints Expected http://.../admin/auth/foo/?id=123 vs Actual http://.../admin/auth/foo/, it names request.META['QUERY_STRING'], and it quotes the pre-patch line `return HttpResponsePermanentRedirect("%s/" % request.path)` verbatim. So the statement is strictly MORE revealing than the spec view on the discriminator (it even hands over the old line, which the view does not). I did NOT consult hints_text for screening; I read it only to confirm it is where get_full_path/force_append_slash live -- and those are exactly the strings the view omits, which is the correct direction (screening against hints would have excused a real leak, and no leak needs excusing here).

The two clauses that go BEYOND the statement -- percent-escaping the path, and the trailing slash being conditional on `path.endsWith "/"` -- are not edit-localization: they are the unchanged public body of HttpRequest.`_get_full_path` at base_commit, which I read directly (git show 55bcbd8d172b689811fae17cde2f09218dd74e9c:django/http/request.py, lines 182-192: escape_uri_path(path), then "/" if force_append_slash and not path.endswith("/") else "", then ("?" + iri_to_uri(QUERY_STRING)) if QUERY_STRING else ""). They describe the output shape of a function the patch does not touch and are derivable from the base-commit tree the solver has; they do not disclose that the fix is to CALL that function.

CORE GATES CONFIRMED SOUND BY MY OWN RUNS (so the disposition does not rest on stamped detail): scripts/lean_verify.sh Solution.lean -> exit 0; appended `#print axioms correct_redirectTargetWithTrailingSlash` in a mktemp dir -> 'depends on axioms: [propext]', no sorryAx, so the proof is real, not fake. scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, and it fails for exactly the right reason: `rfl` cannot equate (pure (path ++ "/")).run with the spec's escaped-path ++ slash-conditional ++ query-suffix. Stripping the query clause is what makes the pre-patch impl verify, i.e. that clause is load-bearing, which is the test for a faithful spec rather than a leaky one.

NO ARTIFACT STEERING (checked because it is a finding in its own right). leakage.reviewer_directed() returns [] on Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, verdict.md, meta.json, conformance_check.py, axiom_check.py. Hand-grepped for addresses-the-reviewer / prescribes-the-verdict / recording-convention phrasing: the only hits are the prior G-PANEL-3 record in verdict.md and meta.json reporting a past agent_verdict of NO-LEAKAGE. Those are gate ledger entries describing a previous run, not instructions to me, and I did not rely on them -- every claim above is from a command I ran in this session.

OUT-OF-FACET OBSERVATION (not leakage, flagging for the integrity/hygiene lane): meta.json region_hashes['proof'] = bac59b8f... matches NEITHER Solution.lean's proof region (2a55090349...) nor Solution_prepatch.lean's (baf1d6e5dd...). Every SPEC region hash does match (axioms 7f1b7757, pure 6d34f45f, post-conditions 7e2a9fdc) and so does spec_view (78bb683b), so the frozen spec surface is intact and this cannot affect the leakage verdict -- the proof region is elided from the view. But a recorded proof hash matching no file on disk suggests the proof region was reflowed after the hash was stamped, or the stamp is stale; worth a G-INTEGRITY re-stamp check.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
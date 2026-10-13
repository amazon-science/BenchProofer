# P2 adversarial audit — django__django-15098

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `ctl_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 16 same-spec attacks (all same_spec=True, unsound_evasions=[]); 14 rejected by the verifier (exit 1, `rfl` failed); the 2 that verify (atk_9, atk_10) are extensional/definitional RESHAPES of the gold impl, not wrong impls, and each one's FAITHFUL refined patch RESOLVES under the official harness (atk_9_faithful: completed=True resolved=True attempts=1; atk_10_faithful: completed=True resolved=True attempts=1). They are correct echoes, not weaknesses. Root cause of the tightness: problem_spec_langCodeFromPath is a TOTAL functional equation, result = (if allAscii path then match langPrefix path with none => none | some lc => resolveVariant lc else nonAsciiOutcome path). Both opaque symbols (resolveVariant, nonAsciiOutcome) occur IDENTICALLY on both sides, so no _prop axiom exists to consume and there is no free region anywhere in the domain: every closing impl is extensionally equal to the fully-pinned RHS, including off-ASCII. HONEST-NEGATIVE NOTE: my first patch for atk_10 (pinning get_supported_language_variant(lang_code, strict=True), atk_10.diff) did NOT resolve (completed=True resolved=False attempts=3, F2P both failed, patch_applied=True). I did NOT report that as BROKEN, because it is NOT a faithful refinement: atk_10's Lean impl applies the SAME opaque resolveVariant to the SAME argument lc as gold, and mapping.md fixes the correspondence resolveVariant lc <-> get_supported_language_variant(lc, strict=False) (strict held at its default; no caller in django/ or tests/ passes strict). strict=True has no counterpart in atk_10's impl, so the oracle rejected MY EDIT, not the spec (build_one._patch_not_a_faithful_refinement). Rebuilt faithfully (bind-shaped early return, matcher and callee untouched) it resolves.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,7 +120,7 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
+      match langPrefixN 1 path with
       | none => return none
       | some lc => return resolveVariant lc
     else
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,7 +120,7 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
+      match langPrefixN 3 path with
       | none => return none
       | some lc => return resolveVariant lc
     else
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,9 +120,14 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
-      | none => return none
-      | some lc => return resolveVariant lc
+      if path.length <= 8 then
+        match langPrefix path with
+        | none => return none
+        | some lc => return resolveVariant lc
+      else
+        match langPrefixN 1 path with
+        | none => return none
+        | some lc => return resolveVariant lc
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,9 +120,12 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
-      | none => return none
-      | some lc => return resolveVariant lc
+      if path.contains '\n' then
+        return none
+      else
+        match langPrefix path with
+        | none => return none
+        | some lc => return resolveVariant lc
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -119,7 +119,7 @@
 -- impl-start
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
-    if allAscii path then
+    if !allAscii path then
       match langPrefix path with
       | none => return none
       | some lc => return resolveVariant lc
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -119,12 +119,7 @@
 -- impl-start
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
-    if allAscii path then
-      match langPrefix path with
-      | none => return none
-      | some lc => return resolveVariant lc
-    else
-      return nonAsciiOutcome path
+    return nonAsciiOutcome path
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -122,7 +122,7 @@
     if allAscii path then
       match langPrefix path with
       | none => return none
-      | some lc => return resolveVariant lc
+      | some _ => return resolveVariant path
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,9 +120,9 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
-      | none => return none
-      | some lc => return resolveVariant lc
+      match langPrefixN 2 path, langPrefixN 0 path with
+      | some lc, none => return resolveVariant lc
+      | _, _ => return none
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -119,12 +119,12 @@
 -- impl-start
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
-    if allAscii path then
+    if !allAscii path then
+      return nonAsciiOutcome path
+    else
       match langPrefix path with
       | none => return none
       | some lc => return resolveVariant lc
-    else
-      return nonAsciiOutcome path
 -- impl-end
 
 -- proof-start
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,9 +120,7 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
-      | none => return none
-      | some lc => return resolveVariant lc
+      return (langPrefix path).bind resolveVariant
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,9 +120,14 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
-      | none => return none
-      | some lc => return resolveVariant lc
+      if path.contains '@' then
+        match langPrefixN 1 path with
+        | none => return none
+        | some lc => return resolveVariant lc
+      else
+        match langPrefix path with
+        | none => return none
+        | some lc => return resolveVariant lc
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -121,7 +121,9 @@
   Id.run do
     if allAscii path then
       match langPrefix path with
-      | none => return none
+      | none => match langPrefix ('/' :: path) with
+                | none => return none
+                | some lc => return resolveVariant lc
       | some lc => return resolveVariant lc
     else
       return nonAsciiOutcome path
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,9 +120,7 @@
 def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
   Id.run do
     if allAscii path then
-      match langPrefix path with
-      | none => return none
-      | some lc => return resolveVariant lc
+      return resolveVariant path
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -122,9 +122,9 @@
     if allAscii path then
       match langPrefix path with
       | none => return none
-      | some lc => return resolveVariant lc
+      | some lc => return nonAsciiOutcome lc
     else
-      return nonAsciiOutcome path
+      return resolveVariant path
 -- impl-end
 
 -- proof-start
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -122,7 +122,11 @@
     if allAscii path then
       match langPrefix path with
       | none => return none
-      | some lc => return resolveVariant lc
+      | some lc =>
+          if lc.contains '@' then
+            return resolveVariant (lc.takeWhile (fun c => c != '@'))
+          else
+            return resolveVariant lc
     else
       return nonAsciiOutcome path
 -- impl-end
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -122,7 +122,11 @@
     if allAscii path then
       match langPrefix path with
       | none => return none
-      | some lc => return resolveVariant lc
+      | some lc =>
+          if lc.length > 12 then
+            return none
+          else
+            return resolveVariant lc
     else
       return nonAsciiOutcome path
 -- impl-end
@@ -132,6 +136,12 @@
     problem_spec_langCodeFromPath path (implementation_langCodeFromPath path) := by
   intro path
   unfold problem_spec_langCodeFromPath implementation_langCodeFromPath
-  by_cases h : allAscii path <;> simp [h, Id.run] <;>
-    cases langPrefix path <;> rfl
+  by_cases h : allAscii path <;>
+    simp [h, Id.run, langPrefix, langPrefixN] <;>
+    first
+      | rfl
+      | (split <;> rfl)
+      | (cases langPrefix path <;> rfl)
+      | simp_all
+      | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all paths; worktree at base_commit 2c7846d992 in ./wt, left clean).

**SAME-SPEC:** every attack + control checked with swebench_unified.markers.same_spec => True, and variant_scope.unsound_evasions => [] (no new axiom/sorry/native_decide, obligation statement byte-identical). Only the impl region differs; axioms/pure/pre/post byte-identical. ctl_gold.lean is byte-identical to the frozen Solution.lean (verified by diff).

VERIFY CMD (each): `bash scripts/lean_verify.sh <f>.lean` from the repo root, run as concurrent background jobs 4 at a time. ctl_gold  EXIT=0  (positive control verifies) atk_1  EXIT=1  PREPATCH BUG re-encoded: langPrefixN 1 (pre-patch `?` matcher). rfl failed. atk_2  EXIT=1  boundary over-permissive: langPrefixN 3. atk_3  EXIT=1  PARTIAL DOMAIN: gold matcher only when path.length <= 8, else pre-patch. atk_4  EXIT=1  BOUNDARY: drops the `$`-before-single-trailing-newline anchor. atk_5  EXIT=1  CONTROL-FLOW EFFECT: allAscii guard inverted (branches NOT swapped). atk_6  EXIT=1  UNGROUNDED-ORACLE ECHO: return nonAsciiOutcome path everywhere. atk_7  EXIT=1  wrong argument to the A-reference callee: resolveVariant path, not lc. atk_8  EXIT=1  all-or-nothing grab (requires a trailing subtag to exist). atk_9  EXIT=0  A-LEG reshape on nonAsciiOutcome: guard negated AND branches swapped. atk_10 EXIT=0  A-LEG reshape on resolveVariant: (langPrefix path).bind resolveVariant. atk_11 EXIT=1  PARTIAL DOMAIN on the SEPARATOR: '@' paths keep the 1-subtag grammar. atk_12 EXIT=1  CONTROL-FLOW EFFECT: drops the leading-'/' anchor (retries on '/'::path). atk_13 EXIT=1  UNGROUNDED-ORACLE ECHO: skip extraction, hand the whole path to the callee. atk_14 EXIT=1  BOUNDARY: the two opaque oracles SWAPPED across the branches. atk_15 EXIT=1  SHARPEST graded-slice shape: wrong ONLY on '@'-separated 2-subtag paths, a region NO graded test touches (all F2P paths use '-').

Still rejected => the spec is not graded-slice-shaped. atk_16 EXIT=1  wrong only for candidates longer than 12 chars, retried under a much more aggressive tactic budget (split/simp_all/decide) in case the gold tactic rather than the statement was the obstacle. Still rejected.

AXIOMS (`#print axioms correct_langCodeFromPath` appended, same verifier): ax_ctl_gold EXIT=0, ax_atk_9 EXIT=0, ax_atk_10 EXIT=0; all three print exactly `depends on axioms: [propext]` — clean, identical to gold, no sorryAx.

MANDATORY RESOLVE RUNS (harness.run_resolve, instance django__django-15098; every diff `git apply --check`-ed clean in the base_commit worktree first):
  atk_9.diff            (UNFAITHFUL first try: separate pre-patch matcher for non-ASCII) -> completed=True resolved=True attempts=1.
  atk_10.diff           (UNFAITHFUL first try: strict=True) -> completed=True resolved=False attempts=3, patch_applied=True, F2P both failed. ADJUDICATED NOT A BREAK — not a faithful refinement (see counterexample field).
  atk_9_faithful.diff   (FAITHFUL: same two routes, same matcher, same callee/argument, control-flow reshape only) -> completed=True resolved=True attempts=1, F2P both success, P2P 0 failures.
  atk_10_faithful.diff  (FAITHFUL: bind-shaped early return; matcher and callee incl. strict untouched) -> completed=True resolved=True attempts=1, F2P both success, P2P 0 failures.
So NO impl with a closing clean-axiom proof has a faithful patch that fails to resolve.

INDEPENDENT R-LEG CHECK (fuzz_indep.py — transcribed from the LEAN SOURCE, not copied from the bundle's conformance_check.py; fresh seed 0xC0FFEE, not the pinned 15098): langPrefixN 2 vs group 1 of `^/(\w+([@-]\w+){0,2})(/|$)` and langPrefixN 1 vs the pre-patch `^/(\w+([@-]\w+)?)(/|$)`, over 177,156 EXHAUSTIVE strings (len<=5 over {a,1,_,-,@,/,\n,\r,.,NUL,space}) + 400,000 random paths over the full ASCII plane and a langtag alphabet + 45 hand boundary cases (incl. every F2P path, /en\n, /en\n\n, /en\r, /a-b-c-d, /a@b@c@d, /en--gb/, /sr-RS@latin/, //, /_/). 0 disagreements. The deep model of the CHANGED op is confirmed independently of the artifact.

REFINEMENT.MD LEG AUDIT — 4 legs, kinds {1:R, 2:R/A-reference, 3:I, 4:R/A-reference}. NO kind-3 leg; no leg is unlabelled or mis-labelled. Declared opaque set == {resolveVariant, nonAsciiOutcome}, matching the axioms region exactly; both are genuinely two-sided (occur identically on both sides of the spec equation), so the claimed 'consumes no `_prop` axiom' and G-AX=skip are correct.
  A-leg correspondence to the REAL callees (the part no mechanical gate reaches) HOLDS:
  * resolveVariant <-> get_supported_language_variant (trans_real.py:464-498): UNCHANGED by the gold patch (patch.diff touches only line 46 — confirmed); returns the candidate / a more generic variant / raises LookupError, and LookupError -> none is the documented Option modeling; `strict` legitimately pinned at its default False — I grepped django/ and tests/ and NO caller passes strict (only the def site mentions it), so the modeled slice is the one the repo actually exercises.
  * nonAsciiOutcome <-> the whole routine on paths carrying a non-ASCII code point. I probed this as the widest part of the model and it is an honest boundary, not an escape hatch: (a) it is not free — being two-sided, it pins every closing impl off-ASCII too, which attacks 5, 6 and 14 confirm by being rejected for deviating only there; (b) it is necessary — Python 3 `\w` is Unicode-aware while Lean's Char.isAlpha/isDigit are ASCII-only, so an ASCII isWord claim off-ASCII would be FALSE (mapping.md explicitly records retracting that earlier wrong justification, which is the right correction); (c) it costs no grading coverage — every F2P path and every settings.LANGUAGES code in the test patch is pure ASCII, and a scan of tests/i18n found ZERO non-ASCII URL-path literals reaching get_language_from_path.
  I also confirmed the prepatch claim structurally: langPrefixN 1 returns none on /en-latn-us/, /en-Latn-US/, /de-ch-1901/, /nan-hani-tw/ where langPrefixN 2 returns the full candidate, matching refinement.md's G-DIFF paragraph, and atk_1 (that exact impl) does not verify.

**WHY NO BREAK IS AVAILABLE:** the post-condition is a total equation whose RHS mentions no unconstrained symbol, so `correct_langCodeFromPath` forces extensional equality with the gold impl on ALL of List Char. Any deviation makes it a false forall and rfl/decide cannot close it. The only same-spec impls that verify are reshapes of gold, whose faithful patches necessarily resolve — demonstrated, not assumed, for both.

**Verdict:** SOUND (advisory). 16 admissible attacks re-run, none breaks the spec; positive control verifies with clean [propext] axioms; prepatch bug reproduced as atk_1; both candidate reshapes' faithful patches resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `ctl_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 16 same-spec attacks (all same_spec=True, unsound_evasions=[]); 14 rejected by the verifier (exit 1, `rfl` failed); the 2 that verify (atk_9, atk_10) are extensional/definitional RESHAPES of the gold impl, not wrong impls, and each one's FAITHFUL refined patch RESOLVES under the official harness (atk_9_faithful: completed=True resolved=True attempts=1; atk_10_faithful: completed=True resolved=True attempts=1). They are correct echoes, not weaknesses. Root cause of the tightness: problem_spec_langCodeFromPath is a TOTAL functional equation, result = (if allAscii path then match langPrefix path with none => none | some lc => resolveVariant lc else nonAsciiOutcome path). Both opaque symbols (resolveVariant, nonAsciiOutcome) occur IDENTICALLY on both sides, so no _prop axiom exists to consume and there is no free region anywhere in the domain: every closing impl is extensionally equal to the fully-pinned RHS, including off-ASCII. HONEST-NEGATIVE NOTE: my first patch for atk_10 (pinning get_supported_language_variant(lang_code, strict=True), atk_10.diff) did NOT resolve (completed=True resolved=False attempts=3, F2P both failed, patch_applied=True). I did NOT report that as BROKEN, because it is NOT a faithful refinement: atk_10's Lean impl applies the SAME opaque resolveVariant to the SAME argument lc as gold, and mapping.md fixes the correspondence resolveVariant lc <-> get_supported_language_variant(lc, strict=False) (strict held at its default; no caller in django/ or tests/ passes strict). strict=True has no counterpart in atk_10's impl, so the oracle rejected MY EDIT, not the spec (build_one._patch_not_a_faithful_refinement). Rebuilt faithfully (bind-shaped early return, matcher and callee untouched) it resolves.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all paths; worktree at base_commit 2c7846d992 in ./wt, left clean).

**SAME-SPEC:** every attack + control checked with swebench_unified.markers.same_spec => True, and variant_scope.unsound_evasions => [] (no new axiom/sorry/native_decide, obligation statement byte-identical). Only the impl region differs; axioms/pure/pre/post byte-identical. ctl_gold.lean is byte-identical to the frozen Solution.lean (verified by diff).

VERIFY CMD (each): `bash scripts/lean_verify.sh <f>.lean` from the repo root, run as concurrent background jobs 4 at a time. ctl_gold  EXIT=0  (positive control verifies) atk_1  EXIT=1  PREPATCH BUG re-encoded: langPrefixN 1 (pre-patch `?` matcher). rfl failed. atk_2  EXIT=1  boundary over-permissive: langPrefixN 3. atk_3  EXIT=1  PARTIAL DOMAIN: gold matcher only when path.length <= 8, else pre-patch. atk_4  EXIT=1  BOUNDARY: drops the `$`-before-single-trailing-newline anchor. atk_5  EXIT=1  CONTROL-FLOW EFFECT: allAscii guard inverted (branches NOT swapped). atk_6  EXIT=1  UNGROUNDED-ORACLE ECHO: return nonAsciiOutcome path everywhere. atk_7  EXIT=1  wrong argument to the A-reference callee: resolveVariant path, not lc. atk_8  EXIT=1  all-or-nothing grab (requires a trailing subtag to exist). atk_9  EXIT=0  A-LEG reshape on nonAsciiOutcome: guard negated AND branches swapped. atk_10 EXIT=0  A-LEG reshape on resolveVariant: (langPrefix path).bind resolveVariant. atk_11 EXIT=1  PARTIAL DOMAIN on the SEPARATOR: '@' paths keep the 1-subtag grammar. atk_12 EXIT=1  CONTROL-FLOW EFFECT: drops the leading-'/' anchor (retries on '/'::path). atk_13 EXIT=1  UNGROUNDED-ORACLE ECHO: skip extraction, hand the whole path to the callee. atk_14 EXIT=1  BOUNDARY: the two opaque oracles SWAPPED across the branches. atk_15 EXIT=1  SHARPEST graded-slice shape: wrong ONLY on '@'-separated 2-subtag paths, a region NO graded test touches (all F2P paths use '-').

Still rejected => the spec is not graded-slice-shaped. atk_16 EXIT=1  wrong only for candidates longer than 12 chars, retried under a much more aggressive tactic budget (split/simp_all/decide) in case the gold tactic rather than the statement was the obstacle. Still rejected.

AXIOMS (`#print axioms correct_langCodeFromPath` appended, same verifier): ax_ctl_gold EXIT=0, ax_atk_9 EXIT=0, ax_atk_10 EXIT=0; all three print exactly `depends on axioms: [propext]` — clean, identical to gold, no sorryAx.

MANDATORY RESOLVE RUNS (harness.run_resolve, instance django__django-15098; every diff `git apply --check`-ed clean in the base_commit worktree first):
  atk_9.diff            (UNFAITHFUL first try: separate pre-patch matcher for non-ASCII) -> completed=True resolved=True attempts=1.
  atk_10.diff           (UNFAITHFUL first try: strict=True) -> completed=True resolved=False attempts=3, patch_applied=True, F2P both failed. ADJUDICATED NOT A BREAK — not a faithful refinement (see counterexample field).
  atk_9_faithful.diff   (FAITHFUL: same two routes, same matcher, same callee/argument, control-flow reshape only) -> completed=True resolved=True attempts=1, F2P both success, P2P 0 failures.
  atk_10_faithful.diff  (FAITHFUL: bind-shaped early return; matcher and callee incl. strict untouched) -> completed=True resolved=True attempts=1, F2P both success, P2P 0 failures.
So NO impl with a closing clean-axiom proof has a faithful patch that fails to resolve.

INDEPENDENT R-LEG CHECK (fuzz_indep.py — transcribed from the LEAN SOURCE, not copied from the bundle's conformance_check.py; fresh seed 0xC0FFEE, not the pinned 15098): langPrefixN 2 vs group 1 of `^/(\w+([@-]\w+){0,2})(/|$)` and langPrefixN 1 vs the pre-patch `^/(\w+([@-]\w+)?)(/|$)`, over 177,156 EXHAUSTIVE strings (len<=5 over {a,1,_,-,@,/,\n,\r,.,NUL,space}) + 400,000 random paths over the full ASCII plane and a langtag alphabet + 45 hand boundary cases (incl. every F2P path, /en\n, /en\n\n, /en\r, /a-b-c-d, /a@b@c@d, /en--gb/, /sr-RS@latin/, //, /_/). 0 disagreements. The deep model of the CHANGED op is confirmed independently of the artifact.

REFINEMENT.MD LEG AUDIT — 4 legs, kinds {1:R, 2:R/A-reference, 3:I, 4:R/A-reference}. NO kind-3 leg; no leg is unlabelled or mis-labelled. Declared opaque set == {resolveVariant, nonAsciiOutcome}, matching the axioms region exactly; both are genuinely two-sided (occur identically on both sides of the spec equation), so the claimed 'consumes no `_prop` axiom' and G-AX=skip are correct.
  A-leg correspondence to the REAL callees (the part no mechanical gate reaches) HOLDS:
  * resolveVariant <-> get_supported_language_variant (trans_real.py:464-498): UNCHANGED by the gold patch (patch.diff touches only line 46 — confirmed); returns the candidate / a more generic variant / raises LookupError, and LookupError -> none is the documented Option modeling; `strict` legitimately pinned at its default False — I grepped django/ and tests/ and NO caller passes strict (only the def site mentions it), so the modeled slice is the one the repo actually exercises.
  * nonAsciiOutcome <-> the whole routine on paths carrying a non-ASCII code point. I probed this as the widest part of the model and it is an honest boundary, not an escape hatch: (a) it is not free — being two-sided, it pins every closing impl off-ASCII too, which attacks 5, 6 and 14 confirm by being rejected for deviating only there; (b) it is necessary — Python 3 `\w` is Unicode-aware while Lean's Char.isAlpha/isDigit are ASCII-only, so an ASCII isWord claim off-ASCII would be FALSE (mapping.md explicitly records retracting that earlier wrong justification, which is the right correction); (c) it costs no grading coverage — every F2P path and every settings.LANGUAGES code in the test patch is pure ASCII, and a scan of tests/i18n found ZERO non-ASCII URL-path literals reaching get_language_from_path.
  I also confirmed the prepatch claim structurally: langPrefixN 1 returns none on /en-latn-us/, /en-Latn-US/, /de-ch-1901/, /nan-hani-tw/ where langPrefixN 2 returns the full candidate, matching refinement.md's G-DIFF paragraph, and atk_1 (that exact impl) does not verify.

**WHY NO BREAK IS AVAILABLE:** the post-condition is a total equation whose RHS mentions no unconstrained symbol, so `correct_langCodeFromPath` forces extensional equality with the gold impl on ALL of List Char. Any deviation makes it a false forall and rfl/decide cannot close it. The only same-spec impls that verify are reshapes of gold, whose faithful patches necessarily resolve — demonstrated, not assumed, for both.

**Verdict:** SOUND (advisory). 16 admissible attacks re-run, none breaks the spec; positive control verifies with clean [propext] axioms; prepatch bug reproduced as atk_1; both candidate reshapes' faithful patches resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK LANE (spec-too-strong / drift from real repo behavior). Reference = worktree at base_commit 2c7846d992 with patch.diff APPLIED (verified: `git diff` shows exactly the one-line `?` -> `{0,2}` matcher change; imported module pattern confirmed at runtime as `^/(\w+([@-]\w+){0,2})(/|$)`). No divergence found on any input.

### Artifact integrity
- Solution.lean sha256 a5000c74b518... == meta.json G-VERIFY/G-MUT/G-PBT/G-CONF/G-AX recorded source hash; Solution_prepatch.lean f7c1f2bf91f1... == recorded G-DIFF source. Artifacts are the ones the gates judged; no stale-record issue.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean_backend) = True -> spec region byte-identical, so G-DIFF discrimination lives in the impl region only (no prose/spec edit invalidating retained attacks).
- scripts/lean_verify.sh Solution.lean -> EXIT 0. `#print axioms correct_langCodeFromPath` -> [propext] only. No sorryAx: the proof is real, not fake.

EVIDENCE 1 - deep model vs real regex, evaluated in REAL LEAN (not a hand-port). Built a Lean file reusing the FROZEN imports+axioms+pure region verbatim (head of Solution.lean split at post-conditions-start), hex-encoded 17,194 paths, `#eval`-ed `langPrefix` on each, and diffed against the real patched `language_code_prefix_re.match(p)[1]` imported from the worktree. Result: 17,194 cases, 0 mismatches. Case set = F2P inputs + ~50 hand-built anchor/terminator boundaries + exhaustive product over ['/','a','1',`'_'`,'-','@','\n','.','\r'] to len 4 + 6k uniform draws from the full ASCII plane (0-127) + 6k langtag-shaped draws.

EVIDENCE 2 - backtracking-adversarial exhaustive sweep. The one real structural risk is that `grabSubtags` is GREEDY while the `re` engine BACKTRACKS, so a shorter subtag parse might match where greedy fails. Exhaustive over alphabet ['/','a','b','-','@','\n',`'_'`,'1'] for all lengths <= 7 = 2,396,745 paths: 0 mismatches. Greedy never loses to backtracking here, because `\w` and `[@-]` are disjoint classes and the terminator alternation `(/|$)` cannot be satisfied by shortening a maximal `\w+` run (any char that would end the run early is itself a non-word char that fails `(/|$)` unless it is `/` or end). Plus ~1.7M additional random/structured ASCII draws in a separate harness: 0 mismatches.

EVIDENCE 3 - END-TO-END whole-routine spec vs real `get_language_from_path`. Transcribed the post-conditions region exactly (allAscii branch; langPrefixN 2; resolveVariant = real get_supported_language_variant with LookupError -> None) and compared against the real patched routine. 47,422 all-ASCII cases (structured langtag fuzz + full-ASCII-plane draws): 0 mismatches. Non-ASCII inputs correctly skipped (pinned only to opaque nonAsciiOutcome).

EVIDENCE 4 - F2P ground truth. Applied instance.json test_patch to the worktree; both F2P tests (test_get_language_from_path_real, test_get_supported_language_variant_null) PASS. Then reproduced the F2P's own @override_settings LANGUAGES and compared expected vs spec vs real on all 16 table rows: all three agree on every row, including the four two-trailing-subtag rows the patch exists for (/en-latn-us/, /en-Latn-US/, /de-ch-1901/, /nan-hani-tw/) and the negative /de-simple-page-test/ -> None. Additional 63,944-case fuzz under those same LANGUAGES: 0 mismatches.

EVIDENCE 5 - delta alignment (guards against the trap of condemning the patch delta itself). `langPrefixN 1` evaluated in real Lean over the same 17,194 cases == the PRE-patch regex `^/(\w+([@-]\w+)?)(/|$)` group-1 with 0 mismatches. The model's pre/post delta is 78 paths; the real regex's pre/post delta is 78 paths; the two delta SETS are identical. So the spec's strength differs from base behavior on exactly the patch's delta and nowhere else - correct spec, not drift.

EVIDENCE 6 - axiom faithfulness. resolveVariant models UNCHANGED callee get_supported_language_variant with LookupError modeled as `none`. Probed the real callee's exception surface (empty, None, 5000-char, all-hyphen, NUL, non-BMP emoji, Latin-1, 2000-char subtag): raises ONLY LookupError, never another exception type -> the total `Option` model is faithful, no hidden throw the spec would wrongly claim returns a value. Also confirmed the real `get_language_from_path` is TOTAL (0 raises over 60,000 draws incl. code points to 300), so pinning it to a total Lean function over-claims nothing. Both opaque symbols appear identically on both sides of the spec equation, so no `_prop` axiom is consumed (consistent with axioms = [propext]).

**NON-VACUITY.** Substituted the pre-patch impl (langPrefixN 1) under the frozen spec with a real (non-sorry) proof body: verification FAILS with `Tactic rfl failed ... some val is not definitionally equal to match langPrefix path`. The spec genuinely rejects the pre-patch behavior, so FAITHFUL here is not a vacuous pass.

SCOPE NOTES (checked, not defects): (a) the non-ASCII `nonAsciiOutcome` escape hatch makes the spec WEAKER, not stronger - it cannot cause a faithfulness break in this lane, and mapping.md correctly retracts the earlier bogus 'non-ASCII candidates never resolve' argument. (b) `strict` is pinned to its default False (the i18n_patterns/LocaleMiddleware path) and declared in mapping.md; the spec asserts nothing about strict=True, so it is scoped, not drifting. (c) The `['\n']` terminator clause correctly models Python's non-MULTILINE `$` matching before a single trailing newline; verified `\r` is NOT accepted, matching `re`.

PROCESS CAVEAT worth recording: two of my own intermediate harness runs reported 283 and 464 'mismatches' that were entirely a sys.path artifact - a stray Django 3.2 tree carrying the PRE-patch regex shadowed the worktree (script-dir sys.path[0], and `import django` executing before sys.path.insert). Both false alarms landed exactly on the two-trailing-subtag delta, i.e. they looked precisely like the 'condemn a correct spec on the patch delta' failure mode this lane is warned about. Confirmed the shadow by printing django.`__file__` and the live regex pattern, then re-ran with PYTHONPATH pinned: 0 mismatches. Any future run in this bundle should assert `django.__file__` startswith the worktree path before trusting a divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**Role:** leakage / gold-reconstruction, django__django-15098 (lean). NO RELAXATION IN THIS BUNDLE: no RELAXED_LEAKAGE.md exists (find -iname '*RELAX*' -> empty) and meta.json has no relaxed_leakage key / G-LEAK status is "pass" ("spec view clean"), so this is a plain leakage judgement, not an inherited disposition. No file in the bundle addresses the panel or suggests a verdict: grep -niE 'attacker|panel[- ]?3|you must submit|submit NO-LEAKAGE|the honest verdict|reviewer should|do not flag' over Solution.lean, Solution_prepatch.lean, refinement.md, mapping.md returns nothing; the only G-PANEL-3 hits in verdict.md/meta.json are prior ledger records of past runs, which is normal bookkeeping, not instruction.

### WHAT I RAN (my measurements, not the bundle's assertions):
1. Spec region byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) = True. The two bundles differ ONLY in the elided impl region (langPrefix vs langPrefixN 1) and the proof (real proof vs sorry) -- confirmed by diff: 2 hunks, both outside the spec view. So the graded spec view is edit-agnostic and cannot by itself disclose which side is gold.
2. scripts/lean_verify.sh Solution.lean -> exit 0. Axiom check: injected '#print axioms correct_langCodeFromPath' -> "depends on axioms: [propext]". No sorryAx; the proof is real.
3. Mechanical G-LEAK re-run by hand: leakage.screen(Solution.lean, lean backend, row['patch'], row['problem_statement'], test_patch=...) -> passed=True, hard_failures=[], warnings=[]. Note the two historical L3 'narration: fixed' hits recorded in verdict.md line 3227 are GONE from the current bytes (grep -c 'fixed' Solution.lean = 0); the author reworded to '(unspecified, deterministic)'. So the screen is clean on the shipped artifact, not clean-by-waiver.
4. Load-bearing check on the one clause a leakage reviewer would suspect (the "up to two trailing subtags" bound): I rebuilt the impl with langPrefixN 1 and the REAL proof -> exit 1, 'Tactic rfl failed' on both langPrefix branches. And I proved the boundary decidably in a scratch file (exit 0): langPrefixN 1 "/en-latn-us/" = none while langPrefix "/en-latn-us/" = some "en-latn-us"; same for /de-ch-1901/; langPrefixN 3 "/a-b-c-d/" = some "a-b-c-d" while langPrefix "/a-b-c-d/" = none; langPrefix "/en-gb/" = some "en-gb". So the bound is a genuine two-sided discriminator, i.e. the clause is load-bearing for faithfulness -- a faithful spec cannot omit or loosen it.

**WHY NOT LEAKAGE.** Gold edit = one line in django/utils/translation/trans_real.py:46, language_code_prefix_re: r'^/(\w+([@-]\w+)?)(/|$)' -> r'^/(\w+([@-]\w+){0,2})(/|$)'.

(a) The bound of two is derivable from the PUBLIC problem_statement alone, not from the spec. Its title is "Internationalisation didn't support language locale containing both script and region"; it names en-latn-us / en-Latn-US as the 404 cases and demands 200; and it quotes RFC 5646 verbatim: langtag = language ["-" script] ["-" region] ... -- i.e. primary subtag plus up to two trailing subtags, exactly what the spec's prose ("per RFC 5646 a tag is a language optionally followed by a script and a region ... up to two such trailing subtags are admissible") and langPrefixN 2 state. Restating the publicly mandated target behaviour is not edit disclosure. (I did NOT consult hints_text.)

(b) Nothing gold-specific is present anywhere in the spec view: no regex literal, no {0,2} or ? quantifier, no diff markers, no patched file path (trans_real.py), no patched symbol (language_code_prefix_re), and crucially no statement of the PRE-patch bound of 1 -- langPrefixN is parameterized by a neutral n and only n=2 is instantiated, so the view never says "currently one, make it two".

(c) Details that are NOT part of the edit and are pre-patch-identical are the only other implementation-flavored content: the '@' separator, `'_'` in the word class, and the '$'-before-single-trailing-newline anchor (rrest = ['\n']). Modeling them is required for a total functional equation and reveals nothing about the change.

TWO BORDERLINE PHRASES I WEIGHED AND REJECTED AS FINDINGS, for the record:
- line 72, "(the end-of-input anchor convention of the host pattern language)": discloses that the real routine matches via a pattern language with a $ anchor. It describes UNCHANGED pre-patch anchor semantics; it does not name the file, the symbol, or the changed quantifier, and prefix-matching a URL segment already implies a matcher. Not a gold-edit leak.
- line 27, resolveVariant's "This is an unchanged library routine": mild meta-narration implying the edit is not in the resolver. Already implied by the problem_statement, which reports /en-us/ working and lists en-latn-us in LANGUAGES while only the URL prefix path 404s. Not beyond public.
A solver handed this spec view still has to locate trans_real.py:46, recognise the matcher, and choose the quantifier; it learns the target grammar the issue already mandates. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

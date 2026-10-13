# P2 adversarial audit — sympy__sympy-18763

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,14 +53,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: first build the joined assignment subscript, then return
-the assembled layout with the body presented as its own delimited group. Mirrors
-the two statements of the source (compute the joined assignments; format and
-return). -/
+/-- attack impl -/
 def implementation_renderRestriction
     (inner : String) (lhs rhs : List String) : String := Id.run do
   let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
-  return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
+  return "\\left. " ++ inner ++ " \\right|_{\\substack{ "
     ++ latexSubs ++ " }}"
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,15 +53,15 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: first build the joined assignment subscript, then return
-the assembled layout with the body presented as its own delimited group. Mirrors
-the two statements of the source (compute the joined assignments; format and
-return). -/
+/-- attack impl -/
 def implementation_renderRestriction
     (inner : String) (lhs rhs : List String) : String := Id.run do
   let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
-  return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
-    ++ latexSubs ++ " }}"
+  if inner = "" then
+    return ""
+  else
+    return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
+      ++ latexSubs ++ " }}"
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: first build the joined assignment subscript, then return
-the assembled layout with the body presented as its own delimited group. Mirrors
-the two statements of the source (compute the joined assignments; format and
-return). -/
+/-- attack impl -/
 def implementation_renderRestriction
     (inner : String) (lhs rhs : List String) : String := Id.run do
-  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
+  let latexSubs := String.intercalate "\\ " (subsEntries lhs rhs)
   return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
     ++ latexSubs ++ " }}"
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,15 +53,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: first build the joined assignment subscript, then return
-the assembled layout with the body presented as its own delimited group. Mirrors
-the two statements of the source (compute the joined assignments; format and
-return). -/
+/-- attack impl -/
 def implementation_renderRestriction
     (inner : String) (lhs rhs : List String) : String := Id.run do
   let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
-  return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
+  let mut out := "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
     ++ latexSubs ++ " }}"
+  out := out ++ "!"
+  return out
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: first build the joined assignment subscript, then return
-the assembled layout with the body presented as its own delimited group. Mirrors
-the two statements of the source (compute the joined assignments; format and
-return). -/
+/-- attack impl -/
 def implementation_renderRestriction
     (inner : String) (lhs rhs : List String) : String := Id.run do
-  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
+  let latexSubs := String.intercalate subsSep ((lhs.zip rhs).map (fun p => p.2 ++ "=" ++ p.1))
   return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
     ++ latexSubs ++ " }}"
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,15 +53,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: first build the joined assignment subscript, then return
-the assembled layout with the body presented as its own delimited group. Mirrors
-the two statements of the source (compute the joined assignments; format and
-return). -/
+/-- attack impl -/
 def implementation_renderRestriction
     (inner : String) (lhs rhs : List String) : String := Id.run do
   let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
   return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
-    ++ latexSubs ++ " }}"
+    ++ latexSubs ++ " }"
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,15 +53,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: first build the joined assignment subscript, then return
-the assembled layout with the body presented as its own delimited group. Mirrors
-the two statements of the source (compute the joined assignments; format and
-return). -/
+/-- attack impl -/
 def implementation_renderRestriction
     (inner : String) (lhs rhs : List String) : String := Id.run do
-  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
-  return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
-    ++ latexSubs ++ " }}"
+  return "\\left. \\left(\\right) \\right|_{\\substack{  }}"
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Markup rendering of a bound-evaluation expression: a body together with a list
of variable-to-value assignments, displayed as the body restricted by those
assignments.

The renderer receives the already-rendered markup of the body and of each
assignment's left- and right-hand sides (these renderings are produced by a
generic recursive markup routine and are inputs here). It assembles a single
markup string consisting of:

  * the body, displayed as a self-contained delimited group, restricted by
  * the assignment list, each entry shown as `lhs=rhs` and the entries separated
    by a line break, all gathered in a stacked subscript.

The body is always presented as its own delimited group so that, when this
rendering is placed inside a larger surrounding expression, the body reads as a
single unit rather than merging with its surroundings.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The recursive
-- markup of the body and of each assignment side is produced upstream and is
-- supplied to this routine as plain string inputs (`inner`, `lhs`, `rhs`); this
-- routine only assembles those strings into the final layout, so there is no
-- `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- The rendered assignment entries: each `(l, r)` pair from the parallel
left/right rendering lists shown as `l=r`. The pairing truncates to the shorter
list, exactly as a parallel zip does. -/
def subsEntries (lhs rhs : List String) : List String :=
  (lhs.zip rhs).map (fun p => p.1 ++ "=" ++ p.2)

/-- The line-break separator between stacked assignment entries (a markup line
break: two backslashes followed by a space). -/
def subsSep : String := "\\\\ "
-- pure-end

-- post-conditions-start
/-- The assembled markup. The body `inner` is wrapped as its own delimited group
and placed as the restricted quantity; the assignment entries (`subsEntries`),
joined by the line-break separator, fill the stacked subscript. Every fragment of
the output is pinned to the inputs, so the result is fully determined. -/
def problem_spec_renderRestriction
    (inner : String) (lhs rhs : List String) (result : String) : Prop :=
  result =
    "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
      ++ String.intercalate subsSep (subsEntries lhs rhs) ++ " }}"
-- post-conditions-end

-- impl-start
/-- Imperative skeleton: first build the joined assignment subscript, then return
the assembled layout with the body presented as its own delimited group. Mirrors
the two statements of the source (compute the joined assignments; format and
return). -/
def implementation_renderRestriction
    (inner : String) (lhs rhs : List String) : String := Id.run do
  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
  return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
    ++ latexSubs ++ " }}"
-- impl-end

-- proof-start
theorem correct_renderRestriction :
    ∀ (inner : String) (lhs rhs : List String),
      problem_spec_renderRestriction inner lhs rhs
        (implementation_renderRestriction inner lhs rhs) := by
  intro inner lhs rhs
  unfold problem_spec_renderRestriction implementation_renderRestriction
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition problem_spec_renderRestriction pins `result` by a TOTAL, EXACT string equality to a fully input-grounded expression ("\left. \left(" ++ inner ++ "\right) \right|_{\substack{ " ++ intercalate subsSep (subsEntries lhs rhs) ++ " }}"). meta.json confirms axioms=[], deep_model_references=[], conf_skip=false: there is NO A-leg / deep-model attack surface. Refinement.md legs are all R (1,2: inner/lhs/rhs = R-abstracted self._print outputs) or I (3,4,5: concrete ops); no A-consumed / A-reference / kind-3 legs, consistent with the empty axioms set. R-legs are covered by G-CONF (recorded pass, 100006 samples, 0 disagreements). Because the theorem is ∀ inner lhs rhs, impl = <fixed expr>, ANY verifying impl must be pointwise-equal to gold on every input, hence extensionally identical to gold, hence resolves — verify DOES imply correct here.

Protocol executed. same_spec(Solution.lean, atk_N.lean, lean) = True for all 7 attacks and for pos_control (verified via swebench_unified.markers.same_spec). Verifications run concurrently as background jobs (batches of 4) via `bash scripts/lean_verify.sh <file>` from project root.

### RESULTS (exit codes):
- pos_control.lean (gold impl): exit 0 (verifies, no sorry). #print axioms correct_renderRestriction -> "'correct_renderRestriction' does not depend on any axioms" (clean; AXRC=0).
- atk_1 (PREPATCH BUG: body not wrapped in \left(...\right)): exit 1 (rfl mismatch: "\left. " ++ inner ++ " \right|..." vs spec's "\left. \left(" ++ inner ++ "\right) \right|..."). Prepatch reproduced.
- atk_2 (partial-domain: empty inner -> ""): exit 1.
- atk_3 (boundary: wrong separator "\ " instead of subsSep "\\ "): exit 1.
- atk_4 (control-flow-effect: mutable accumulator appends trailing "!"): exit 1.
- atk_5 (ungrounded/swapped pairing p.2 ++ "=" ++ p.1 instead of p.1 ++ "=" ++ p.2): exit 1.
- atk_6 (off-by-one suffix " }" instead of " }}"): exit 1.
- atk_7 (ungrounded-oracle echo: constant string ignoring all inputs): exit 1.

Every attack failed to verify (exit 1) with a genuine unprovable string-equality goal (confirmed by inspecting the Lean error logs — the goal is exactly the mismatch between the wrong impl's assembled string and the pinned spec expression). NO wrong impl closed with clean axioms, so there is no verifying-but-wrong impl to materialize a faithful patch for; the `patches` map is empty because no attack qualified for a resolve run. The >=5 attack requirement is satisfied (7 distinct wrong impls across partial-domain, boundary, control-flow-effect, and ungrounded-oracle-echo classes plus the prepatch bug), positive control verifies with clean axioms, and none breaks the spec. Verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Markup rendering of a bound-evaluation expression: a body together with a list
of variable-to-value assignments, displayed as the body restricted by those
assignments.

The renderer receives the already-rendered markup of the body and of each
assignment's left- and right-hand sides (these renderings are produced by a
generic recursive markup routine and are inputs here). It assembles a single
markup string consisting of:

  * the body, displayed as a self-contained delimited group, restricted by
  * the assignment list, each entry shown as `lhs=rhs` and the entries separated
    by a line break, all gathered in a stacked subscript.

The body is always presented as its own delimited group so that, when this
rendering is placed inside a larger surrounding expression, the body reads as a
single unit rather than merging with its surroundings.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The recursive
-- markup of the body and of each assignment side is produced upstream and is
-- supplied to this routine as plain string inputs (`inner`, `lhs`, `rhs`); this
-- routine only assembles those strings into the final layout, so there is no
-- `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- The rendered assignment entries: each `(l, r)` pair from the parallel
left/right rendering lists shown as `l=r`. The pairing truncates to the shorter
list, exactly as a parallel zip does. -/
def subsEntries (lhs rhs : List String) : List String :=
  (lhs.zip rhs).map (fun p => p.1 ++ "=" ++ p.2)

/-- The line-break separator between stacked assignment entries (a markup line
break: two backslashes followed by a space). -/
def subsSep : String := "\\\\ "
-- pure-end

-- post-conditions-start
/-- The assembled markup. The body `inner` is wrapped as its own delimited group
and placed as the restricted quantity; the assignment entries (`subsEntries`),
joined by the line-break separator, fill the stacked subscript. Every fragment of
the output is pinned to the inputs, so the result is fully determined. -/
def problem_spec_renderRestriction
    (inner : String) (lhs rhs : List String) (result : String) : Prop :=
  result =
    "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
      ++ String.intercalate subsSep (subsEntries lhs rhs) ++ " }}"
-- post-conditions-end

-- impl-start
/-- Imperative skeleton: first build the joined assignment subscript, then return
the assembled layout with the body presented as its own delimited group. Mirrors
the two statements of the source (compute the joined assignments; format and
return). -/
def implementation_renderRestriction
    (inner : String) (lhs rhs : List String) : String := Id.run do
  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
  return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
    ++ latexSubs ++ " }}"
-- impl-end

-- proof-start
theorem correct_renderRestriction :
    ∀ (inner : String) (lhs rhs : List String),
      problem_spec_renderRestriction inner lhs rhs
        (implementation_renderRestriction inner lhs rhs) := by
  intro inner lhs rhs
  unfold problem_spec_renderRestriction implementation_renderRestriction
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition problem_spec_renderRestriction pins `result` by a TOTAL, EXACT string equality to a fully input-grounded expression ("\left. \left(" ++ inner ++ "\right) \right|_{\substack{ " ++ intercalate subsSep (subsEntries lhs rhs) ++ " }}"). meta.json confirms axioms=[], deep_model_references=[], conf_skip=false: there is NO A-leg / deep-model attack surface. Refinement.md legs are all R (1,2: inner/lhs/rhs = R-abstracted self._print outputs) or I (3,4,5: concrete ops); no A-consumed / A-reference / kind-3 legs, consistent with the empty axioms set. R-legs are covered by G-CONF (recorded pass, 100006 samples, 0 disagreements). Because the theorem is ∀ inner lhs rhs, impl = <fixed expr>, ANY verifying impl must be pointwise-equal to gold on every input, hence extensionally identical to gold, hence resolves — verify DOES imply correct here.

Protocol executed. same_spec(Solution.lean, atk_N.lean, lean) = True for all 7 attacks and for pos_control (verified via swebench_unified.markers.same_spec). Verifications run concurrently as background jobs (batches of 4) via `bash scripts/lean_verify.sh <file>` from project root.

### RESULTS (exit codes):
- pos_control.lean (gold impl): exit 0 (verifies, no sorry). #print axioms correct_renderRestriction -> "'correct_renderRestriction' does not depend on any axioms" (clean; AXRC=0).
- atk_1 (PREPATCH BUG: body not wrapped in \left(...\right)): exit 1 (rfl mismatch: "\left. " ++ inner ++ " \right|..." vs spec's "\left. \left(" ++ inner ++ "\right) \right|..."). Prepatch reproduced.
- atk_2 (partial-domain: empty inner -> ""): exit 1.
- atk_3 (boundary: wrong separator "\ " instead of subsSep "\\ "): exit 1.
- atk_4 (control-flow-effect: mutable accumulator appends trailing "!"): exit 1.
- atk_5 (ungrounded/swapped pairing p.2 ++ "=" ++ p.1 instead of p.1 ++ "=" ++ p.2): exit 1.
- atk_6 (off-by-one suffix " }" instead of " }}"): exit 1.
- atk_7 (ungrounded-oracle echo: constant string ignoring all inputs): exit 1.

Every attack failed to verify (exit 1) with a genuine unprovable string-equality goal (confirmed by inspecting the Lean error logs — the goal is exactly the mismatch between the wrong impl's assembled string and the pinned spec expression). NO wrong impl closed with clean axioms, so there is no verifying-but-wrong impl to materialize a faithful patch for; the `patches` map is empty because no attack qualified for a resolve run. The >=5 attack requirement is satisfied (7 distinct wrong impls across partial-domain, boundary, control-flow-effect, and ungrounded-oracle-echo classes plus the prepatch bug), positive control verifies with clean axioms, and none breaks the spec. Verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for sympy__sympy-18763 lean bundle, modeled function _print_Subs (post-patch). Findings:

1. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True — spec region byte-identical to prepatch; no impl smuggled into the spec.
2. Solution.lean compiles under scripts/lean_verify.sh (exit 0, no sorry). `#print axioms correct_renderRestriction` => 'does not depend on any axioms' — proof is genuine, no sorryAx.
3. Spec models the POST-PATCH function. Real post-patch _print_Subs: latex_subs = r'\\ '.join(e[0]+'='+e[1] for e in zip(latex_old,latex_new)); return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs). Lean postcondition pins result to full string equality with the identical assembly.
4. Abstraction correctness: self._print recursion correctly R-abstracted as string inputs (inner, lhs, rhs) since the fix only re-wraps the already-rendered body — no callee contract to axiomatize. zip <-> List.zip both truncate to shorter. Separator r'\\ ' (backslash,backslash,space; 3 bytes) == Lean "\\\\ " (3 bytes). Literal fragments prefix/mid/suffix match byte-for-byte.
5. Differential test: 200,000 fuzzed inputs (varied inner tokens incl empty/backslash/brace; equal & unequal-length lhs/rhs lists incl empty) + hand-picked edge cases (empty, unequal-length, backslashes/braces, F2P case inner='- x + y' lhs=['x'] rhs=['1']) => 0 mismatches between the Lean spec's required output and an in-process replica of the real post-patch assembly.

The modeled function agrees with the real callee on every tested input; no diverging input found. Spec is neither too strong nor drifting. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: spec view (Solution.lean docstring + postcondition + refinement.md/mapping.md) vs the PUBLIC problem_statement only; hints_text is empty and out of scope.

Gold edit (patch.diff): wrap the body %s in \left(...\right) — 'r\'\left. %s \right|_{\substack{ %s }}\'' -> 'r\'\left. \left(%s\right) \right|_{\substack{ %s }}\''.

The public problem_statement ALREADY discloses the entire fix: it shows the buggy output '3 \left. - x + y \right|_{\substack{ x=1 }}' AND the exact desired parenthesized output '3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}', and states 'It would be better to be parenthesized'. Every literal fragment appearing in the Lean postcondition (\left. \left( , \right) \right|_{\substack{ , the \\ join separator, and }}) is present verbatim in that public desired-output string. The Solution.lean docstring rationale ('body presented as its own delimited group so it reads as a single unit rather than merging with its surroundings') merely restates the public issue's concern about 3* binding to only the first term.

refinement.md and mapping.md do quote the post-patch Python, but (a) they are audit-derivation artifacts, and (b) even so the only substantive content they reveal — the parenthesization — is already public. No spec-view line exposes anything beyond what problem_statement reveals.

Mechanical checks: gates in meta.json all pass (G-EQ, G-PANEL-1/2/3, G-CONF, G-LEAK); Solution.lean compiles clean with rfl proof and #print axioms reported clean. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

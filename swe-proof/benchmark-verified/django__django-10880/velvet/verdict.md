# P2 adversarial audit — django__django-10880

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch.lean`, `atk_2_leading_space.lean`, `atk_3_partial_domain.lean`, `atk_4_inverted.lean`, `atk_5_double_space.lean`, `atk_6_no_close_paren.lean`, `atk_7_loop_offbyone.lean`, `atk_9_pick_echo.lean`, `atk_12_nonterm.lean`, `atk_13_cf_effect.lean`, `atk_14_only_count.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8_oracle_echo.lean`, `atk_10_assoc_shift.lean`, `atk_11_qualifier_on_args.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
+    let qualifier : List Char := if distinct then "DISTINCT".toList else []
     let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
     return out
     -- impl-end
```

Attack 2 — `atk_2_leading_space.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
+    let qualifier : List Char := if distinct then " DISTINCT".toList else []
     let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
     return out
     -- impl-end
```

Attack 3 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,9 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
+    let qualifier : List Char :=
+      if distinct then (if expressions = [] then "DISTINCT".toList else "DISTINCT ".toList)
+      else []
     let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
     return out
     -- impl-end
```

Attack 4 — `atk_4_inverted.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
+    let qualifier : List Char := if distinct then [] else "DISTINCT ".toList
     let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
     return out
     -- impl-end
```

Attack 5 — `atk_5_double_space.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
+    let qualifier : List Char := if distinct then "DISTINCT  ".toList else []
     let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
     return out
     -- impl-end
```

Attack 6 — `atk_6_no_close_paren.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
   do
     -- impl-start
     let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let out := function ++ ['('] ++ qualifier ++ expressions
     return out
     -- impl-end
 
```

Attack 7 — `atk_7_loop_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,10 +55,18 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let full : List Char := if distinct then "DISTINCT ".toList else []
+    let mut rem : List Char := full
+    let mut acc : List Char := function ++ ['(']
+    while rem.length > 1
+      invariant acc ++ rem = function ++ ['('] ++ full
+      decreasing rem.length
+    do
+      acc := acc ++ [rem.headD ' ']
+      rem := rem.tail
+    let out := acc ++ expressions ++ [')']
     return out
     -- impl-end
 
 prove_correct aggregateAsSql by
-  loom_solve
+  loom_solve <;> try grind
```

Attack 8 — `atk_8_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,8 +55,7 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let out := renderCall function distinct expressions
     return out
     -- impl-end
 
```

Attack 9 — `atk_9_pick_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,8 +55,7 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let out :| out = renderCall function distinct expressions
     return out
     -- impl-end
 
```

Attack 10 — `atk_10_assoc_shift.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,8 +55,9 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let head : List Char :=
+      if distinct then function ++ ['('] ++ "DISTINCT ".toList else function ++ ['(']
+    let out := head ++ expressions ++ [')']
     return out
     -- impl-end
 
```

Attack 11 — `atk_11_qualifier_on_args.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,8 +55,9 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let args : List Char :=
+      if distinct then "DISTINCT ".toList ++ expressions else expressions
+    let out := function ++ ['('] ++ args ++ [')']
     return out
     -- impl-end
 
```

Attack 12 — `atk_12_nonterm.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,10 +55,16 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
+    let mut acc : List Char := function ++ ['(']
+    let mut n : Nat := 0
+    while distinct
+      invariant True
+    do
+      n := n + 1
     let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let out := acc ++ qualifier ++ expressions ++ [')']
     return out
     -- impl-end
 
 prove_correct aggregateAsSql by
-  loom_solve
+  loom_solve <;> try grind
```

Attack 13 — `atk_13_cf_effect.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,10 +55,19 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
-    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
+    let mut acc : List Char := function ++ ['(']
+    let mut k : Nat := 0
+    while k < 1
+      invariant k <= 1
+      invariant acc = function ++ ['('] ++
+        (if k = 0 then [] else (if distinct then "DISTINCT ".toList else []))
+      decreasing 1 - k
+    do
+      acc := acc ++ (if distinct then "DISTINCT".toList else [])
+      k := k + 1
+    let out := acc ++ expressions ++ [')']
     return out
     -- impl-end
 
 prove_correct aggregateAsSql by
-  loom_solve
+  loom_solve <;> try grind
```

Attack 14 — `atk_14_only_count.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,10 @@
   ensures out = renderCall function distinct expressions
   do
     -- impl-start
-    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
+    let qualifier : List Char :=
+      if distinct then
+        (if function = "COUNT".toList then "DISTINCT ".toList else "DISTINCT".toList)
+      else []
     let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
     return out
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
/- No consumed axioms. The one unchanged callee this operation invokes — the
   generic SQL function-call renderer that substitutes a function name, an
   optional leading qualifier, and the rendered argument text into the call
   template `NAME(QUALIFIER ARGS)` — is modeled DEEPLY (the `renderCall`
   concatenation in the `pure` region) and validated equal to the real callee
   by axiom_check.py (G-AX, an A-reference). Provenance: mapping.md §3. -/
-- axioms-end

-- pure-start
/- The leading qualifier text emitted before the argument list of an aggregate
   SQL call. When the aggregate is asked to deduplicate its input, the qualifier
   is the keyword `DISTINCT` FOLLOWED BY A SEPARATOR, so that it never abuts the
   argument text that follows it; otherwise no qualifier is emitted. The
   separator is what keeps `NAME(DISTINCT <args>)` a syntactically valid call
   rather than gluing the keyword onto the first argument token. -/
def distinctQualifier (distinct : Bool) : List Char :=
  if distinct then "DISTINCT ".toList else []

/- The rendered aggregate SQL call: the function name, an opening parenthesis,
   the leading qualifier, the rendered argument text, and a closing parenthesis,
   concatenated in order. This is the deep model of the generic function-call
   renderer applied to this module's call template `NAME(QUALIFIER ARGS)`
   (mapping.md §3.1, validated == the real renderer by G-AX). -/
def renderCall (function : List Char) (distinct : Bool) (expressions : List Char) :
    List Char :=
  function ++ ['('] ++ distinctQualifier distinct ++ expressions ++ [')']

@[grind] lemma distinctQualifier_true :
    distinctQualifier true = "DISTINCT ".toList := rfl
@[grind] lemma distinctQualifier_false :
    distinctQualifier false = [] := rfl
@[grind] lemma renderCall_eq (function : List Char) (distinct : Bool)
    (expressions : List Char) :
    renderCall function distinct expressions =
      function ++ ['('] ++ distinctQualifier distinct ++ expressions ++ [')'] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method aggregateAsSql (function : List Char) (distinct : Bool)
    (expressions : List Char) return (out : List Char)
  ensures out = renderCall function distinct expressions
  do
    -- impl-start
    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
    return out
    -- impl-end

prove_correct aggregateAsSql by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on velvet django__django-10880. VERDICT: SOUND. No verifying wrong impl produced a faithful refined patch that fails to resolve; verify=>correct survived every attack.

SETUP. All 14 attacks + 2 controls built by copying the frozen Solution.lean and editing ONLY the impl region (generator: mk.py / mk2.py, retained). same_spec(Solution.lean, atk_N.lean, velvet) = True for ALL 16 files (verified via swebench_unified.markers.same_spec). Positive control pos_control.lean (byte-identical to the bundle Solution.lean) VERIFIES, exit 0.

Verify cmd: bash scripts/lean_verify.sh <path> ; logs retained as <name>.log with a trailing EXIT= line. Run 4-concurrent via runbatch.sh.

### ATTACK LEDGER (exit 0 = verifies, 1 = rejected)
1 atk_1_prepatch.lean            EXIT=1  PREPATCH BUG REPRODUCED: qualifier 'DISTINCT' with NO trailing separator (the real pre-patch line, glues to args as COUNT(DISTINCTCASE...)). Rejected with unsolved goal 'ensures_1: out = renderCall ...' -- a genuine postcondition refutation, so the spec discriminates the actual behavioural change. 2 atk_2_leading_space.lean       EXIT=1  boundary/placement: separator on the LEADING side (' DISTINCT') -- same chars, wrong position. 3 atk_3_partial_domain.lean      EXIT=1  PARTIAL DOMAIN on the argument text: gold behaviour unless expressions = [], where it reverts to pre-patch. 4 atk_4_inverted.lean            EXIT=1  branch inverted (qualifier emitted iff NOT deduplicating).

5 atk_5_double_space.lean        EXIT=1  boundary: separator width off by one ('DISTINCT  '). 6 atk_6_no_close_paren.lean      EXIT=1  boundary: closing delimiter dropped. 7 atk_7_loop_offbyone.lean       EXIT=1  CONFOUNDED, do not credit: a char-copy loop stopping one char early. Its correctness control ctl_7b_loop_correct.lean (same loop, copies all chars) ALSO failed (EXIT=1, invariant goal 'acc ++ [rem.headD ' '] ++ rem.tail = ...' left open), so the rejection may be solver weakness on List.tail/headD rather than a behavioural refutation. Superseded by the clean pair 13/13b below. 8 atk_8_oracle_echo.lean         EXIT=0  VERIFIES. Ungrounded oracle echo: impl is literally 'let out := renderCall function distinct expressions'. Patch materialized + RESOLVED (see below).

9 atk_9_pick_echo.lean           EXIT=1  nondeterministic oracle echo ('let out :| out = renderCall ...'). Rejected, but for an ELABORATION reason (failed to synthesize Findable for the postcondition predicate), not a postcondition refutation -- weak evidence; counted only as 'does not verify'. 10 atk_10_assoc_shift.lean        EXIT=0  VERIFIES. Extensionally gold, but the separator rides on the function-name/open-paren side of the concatenation instead of on the qualifier. Patch materialized + RESOLVED. 11 atk_11_qualifier_on_args.lean  EXIT=0  VERIFIES. Extensionally gold, but the qualifier is prepended to the rendered ARGUMENT text rather than emitted as its own template placeholder. Patch materialized + RESOLVED.

12 atk_12_nonterm.lean            EXIT=1  non-termination on the deduplicating path. Rejected by the total-correctness guard ('Decreasing annotations are required in total correctness semantics') + a sorry'd assertion => exit 1. Confirms set_option loom.semantics.termination "total" is load-bearing; syntax-level rejection, so weak as a behavioural probe. 13 atk_13_cf_effect.lean          EXIT=1  CONTROL-FLOW-EFFECT, CLEAN PAIR (replaces #7). A loop body performs the qualifier append; wrong version appends the separator-less keyword. Rejected on the invariant goal. Its control ctl_13b_cf_correct.lean -- IDENTICAL loop machinery, appending 'DISTINCT ' -- VERIFIES (EXIT=0).

Since only the appended literal differs, #13's rejection is a real behavioural refutation through control flow, not solver weakness. 14 atk_14_only_count.lean         EXIT=1  PARTIAL DOMAIN on the function name: gold only for function = COUNT (the sole aggregate the F2P test exercises), pre-patch for every other. A spec pinned to the tested input would have admitted this; the frozen spec rejects it.

MANDATORY RESOLVE RUNS -- every attack that VERIFIES got a faithful refined patch materialized and executed through the OFFICIAL harness (swebench_unified.harness.run_resolve, instance django__django-10880). Driver resolve.py; full reports kept as resolve_<patch>.json; worktrees wt_8 / wt_10 / wt_11 built from a base_commit git worktree (838e432e). atk_8_oracle_echo    -> patches/atk_8_oracle_echo.patch      RESOLVED=True completed=True attempts=1 flaky=False applied=True F2P 1/1 pass, P2P 55/55 pass atk_10_assoc_shift   -> patches/atk_10_assoc_shift.patch     RESOLVED=True completed=True attempts=1 flaky=False applied=True F2P 1/1 pass, P2P 55/55 pass atk_11_qualifier_on_args -> patches/atk_11_qualifier_on_args.patch RESOLVED=True completed=True attempts=1 flaky=False applied=True F2P 1/1 pass, P2P 55/55 pass All three resolve => NO verify-but-not-resolve witness => NOT BROKEN.

(atk_8's faithful patch is byte-equal to the gold hunk, confirmed by diffing the +/- bodies against patch.diff: the deep model renderCall IS the A-reference model of the real 'template % data' renderer, so echoing it transliterates back to the gold edit. atk_10/atk_11 are genuinely different code that is behaviourally equal on every path.) Encoding-artifact note (fixed, mkpatch2.py): my first drafts of the 10/11 patches set extra_context['template'], which the filter branch would then pass twice (TypeError). That crash would have been an artifact of MY encoding, not of the attack, so the patches were rewritten to thread the template explicitly the way gold does, and re-probed on the filter path before resolving. Not doing this would have manufactured a false BROKEN.

### A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's job)
* refinement.md leg tags: A1 R, A2 R, A3 R, A4 I, A5 A-reference + I, A6 R. Every leg is R / A-reference / I; there are NO A-consumed rows and NO kind-3 (inexpressible-changed-op) steps. Section B's claim is accurate: the changed operation (the qualifier text) is spelled out concretely as distinctQualifier, NOT hidden behind an axiom about the function under change; the axioms region is empty of actual axioms. This is the correct shape -- the discriminating content is exposed, not assumed.
* A5 A-reference correspondence CHECKED against the real callee, not taken on trust. Bundle G-AX (axiom_check.py) re-run against the REAL repo at base_commit (PYTHONPATH=<worktree>): PASS, 'render_call deep model == real Func.as_sql template substitution' on 441 boundary + 20000 fuzz triples. Crucially G-AX quantifies over an ARBITRARY qualifier string (it does not assume 'DISTINCT '), so it audits only the UNCHANGED renderer -- honest scoping.
* INDEPENDENT adversarial A-reference probe (ax_attack2.py, mine, beyond the bundle's alphabet): 180 probes, 0 divergences -- %-format metacharacters ('%s', '%(function)s', '%(distinct)s', '%(expressions)s', '%d', '100%', '%%') in EVERY carrier position, multi-arg joins under varied arg_joiner, and ctor **extra interference ({'function':...}, {'distinct':...}, {'expressions':...}, {'field':...}, {'arg_joiner':...}). My first draft reported 20 'divergences' that were artifacts of my own probe (Django's `arg_joiner or ...` chain treats '' as falsy and falls back to ', '; and overriding `template` via **extra replaces the call template entirely, which is out of the A-reference's scope by mapping.md 3.1's construction). Corrected -> 0. Reporting these as breaks would have been a false BROKEN.
* mapping.md 2 SCOPE claim ('the filter branches only wrap/transform the expressions and call the SAME renderer; they do not alter the distinct qualifier') independently EXERCISED on the real Aggregate.as_sql, both filter and no-filter paths, at base_commit and under gold: base gives COUNT(DISTINCTrating) and COUNT(DISTINCTrating) FILTER (WHERE ...); gold gives COUNT(DISTINCT rating) and COUNT(DISTINCT rating) FILTER (WHERE ...). The qualifier text/placement is indeed the full content of the change on every path, so reducing as_sql to the no-filter render path loses no discriminating behaviour. The two atk_10/atk_11 patches were re-probed on the same paths (all agree with the model) before their resolve runs.

ADVISORY (not a G-EQ break, flagged for the panel/spec-strength role). The ensures clause is a complete functional specification of the output (out = renderCall function distinct expressions with distinctQualifier frozen), so atk_8 shows verification is achievable by literally naming the spec function -- zero computational content. For G-EQ this direction is harmless and in fact is what makes verify=>correct hold here (echoing the deep model transliterates back to the gold edit, which resolves). It is worth a look from the spec-too-strong/too-weak angle: atk_10 and atk_11 verify and resolve while encoding a DIFFERENT structural placement than gold, i.e. the spec pins the rendered string but not which template placeholder carries the separator -- correctly so, since the harness only observes the rendered SQL.

COVERAGE vs the protocol: 14 same-spec wrong impls verified (>= the 5-6 required), spanning the named prepatch counterexample, boundary (2,5,6), partial-domain (3 on the argument text, 14 on the function name), control-flow-effect with a matched correctness control (13/13b), ungrounded-oracle echo (8 deterministic, 9 nondeterministic), inverted control flow (4), non-termination (12), and placement/associativity slack (10,11). 3 of 14 verify; all 3 had faithful patches materialized and RESOLVED under the official harness. Positive control verifies. Prepatch bug reproduced and refuted. Nothing was left unrun and no evidence is missing, so this is not INCONCLUSIVE.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch.lean`, `atk_2_leading_space.lean`, `atk_3_partial_domain.lean`, `atk_4_inverted.lean`, `atk_5_double_space.lean`, `atk_6_no_close_paren.lean`, `atk_7_loop_offbyone.lean`, `atk_9_pick_echo.lean`, `atk_12_nonterm.lean`, `atk_13_cf_effect.lean`, `atk_14_only_count.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8_oracle_echo.lean`, `atk_10_assoc_shift.lean`, `atk_11_qualifier_on_args.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_leading_space.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_inverted.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_double_space.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_no_close_paren.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_loop_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_pick_echo.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_assoc_shift.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_qualifier_on_args.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_nonterm.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_cf_effect.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_only_count.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this operation invokes — the
   generic SQL function-call renderer that substitutes a function name, an
   optional leading qualifier, and the rendered argument text into the call
   template `NAME(QUALIFIER ARGS)` — is modeled DEEPLY (the `renderCall`
   concatenation in the `pure` region) and validated equal to the real callee
   by axiom_check.py (G-AX, an A-reference). Provenance: mapping.md §3. -/
-- axioms-end

-- pure-start
/- The leading qualifier text emitted before the argument list of an aggregate
   SQL call. When the aggregate is asked to deduplicate its input, the qualifier
   is the keyword `DISTINCT` FOLLOWED BY A SEPARATOR, so that it never abuts the
   argument text that follows it; otherwise no qualifier is emitted. The
   separator is what keeps `NAME(DISTINCT <args>)` a syntactically valid call
   rather than gluing the keyword onto the first argument token. -/
def distinctQualifier (distinct : Bool) : List Char :=
  if distinct then "DISTINCT ".toList else []

/- The rendered aggregate SQL call: the function name, an opening parenthesis,
   the leading qualifier, the rendered argument text, and a closing parenthesis,
   concatenated in order. This is the deep model of the generic function-call
   renderer applied to this module's call template `NAME(QUALIFIER ARGS)`
   (mapping.md §3.1, validated == the real renderer by G-AX). -/
def renderCall (function : List Char) (distinct : Bool) (expressions : List Char) :
    List Char :=
  function ++ ['('] ++ distinctQualifier distinct ++ expressions ++ [')']

@[grind] lemma distinctQualifier_true :
    distinctQualifier true = "DISTINCT ".toList := rfl
@[grind] lemma distinctQualifier_false :
    distinctQualifier false = [] := rfl
@[grind] lemma renderCall_eq (function : List Char) (distinct : Bool)
    (expressions : List Char) :
    renderCall function distinct expressions =
      function ++ ['('] ++ distinctQualifier distinct ++ expressions ++ [')'] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method aggregateAsSql (function : List Char) (distinct : Bool)
    (expressions : List Char) return (out : List Char)
  ensures out = renderCall function distinct expressions
  do
    -- impl-start
    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
    return out
    -- impl-end

prove_correct aggregateAsSql by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on velvet django__django-10880. VERDICT: SOUND. No verifying wrong impl produced a faithful refined patch that fails to resolve; verify=>correct survived every attack.

SETUP. All 14 attacks + 2 controls built by copying the frozen Solution.lean and editing ONLY the impl region (generator: mk.py / mk2.py, retained). same_spec(Solution.lean, atk_N.lean, velvet) = True for ALL 16 files (verified via swebench_unified.markers.same_spec). Positive control pos_control.lean (byte-identical to the bundle Solution.lean) VERIFIES, exit 0.

Verify cmd: bash scripts/lean_verify.sh <path> ; logs retained as <name>.log with a trailing EXIT= line. Run 4-concurrent via runbatch.sh.

### ATTACK LEDGER (exit 0 = verifies, 1 = rejected)
1 atk_1_prepatch.lean            EXIT=1  PREPATCH BUG REPRODUCED: qualifier 'DISTINCT' with NO trailing separator (the real pre-patch line, glues to args as COUNT(DISTINCTCASE...)). Rejected with unsolved goal 'ensures_1: out = renderCall ...' -- a genuine postcondition refutation, so the spec discriminates the actual behavioural change. 2 atk_2_leading_space.lean       EXIT=1  boundary/placement: separator on the LEADING side (' DISTINCT') -- same chars, wrong position. 3 atk_3_partial_domain.lean      EXIT=1  PARTIAL DOMAIN on the argument text: gold behaviour unless expressions = [], where it reverts to pre-patch. 4 atk_4_inverted.lean            EXIT=1  branch inverted (qualifier emitted iff NOT deduplicating).

5 atk_5_double_space.lean        EXIT=1  boundary: separator width off by one ('DISTINCT  '). 6 atk_6_no_close_paren.lean      EXIT=1  boundary: closing delimiter dropped. 7 atk_7_loop_offbyone.lean       EXIT=1  CONFOUNDED, do not credit: a char-copy loop stopping one char early. Its correctness control ctl_7b_loop_correct.lean (same loop, copies all chars) ALSO failed (EXIT=1, invariant goal 'acc ++ [rem.headD ' '] ++ rem.tail = ...' left open), so the rejection may be solver weakness on List.tail/headD rather than a behavioural refutation. Superseded by the clean pair 13/13b below. 8 atk_8_oracle_echo.lean         EXIT=0  VERIFIES. Ungrounded oracle echo: impl is literally 'let out := renderCall function distinct expressions'. Patch materialized + RESOLVED (see below).

9 atk_9_pick_echo.lean           EXIT=1  nondeterministic oracle echo ('let out :| out = renderCall ...'). Rejected, but for an ELABORATION reason (failed to synthesize Findable for the postcondition predicate), not a postcondition refutation -- weak evidence; counted only as 'does not verify'. 10 atk_10_assoc_shift.lean        EXIT=0  VERIFIES. Extensionally gold, but the separator rides on the function-name/open-paren side of the concatenation instead of on the qualifier. Patch materialized + RESOLVED. 11 atk_11_qualifier_on_args.lean  EXIT=0  VERIFIES. Extensionally gold, but the qualifier is prepended to the rendered ARGUMENT text rather than emitted as its own template placeholder. Patch materialized + RESOLVED.

12 atk_12_nonterm.lean            EXIT=1  non-termination on the deduplicating path. Rejected by the total-correctness guard ('Decreasing annotations are required in total correctness semantics') + a sorry'd assertion => exit 1. Confirms set_option loom.semantics.termination "total" is load-bearing; syntax-level rejection, so weak as a behavioural probe. 13 atk_13_cf_effect.lean          EXIT=1  CONTROL-FLOW-EFFECT, CLEAN PAIR (replaces #7). A loop body performs the qualifier append; wrong version appends the separator-less keyword. Rejected on the invariant goal. Its control ctl_13b_cf_correct.lean -- IDENTICAL loop machinery, appending 'DISTINCT ' -- VERIFIES (EXIT=0).

Since only the appended literal differs, #13's rejection is a real behavioural refutation through control flow, not solver weakness. 14 atk_14_only_count.lean         EXIT=1  PARTIAL DOMAIN on the function name: gold only for function = COUNT (the sole aggregate the F2P test exercises), pre-patch for every other. A spec pinned to the tested input would have admitted this; the frozen spec rejects it.

MANDATORY RESOLVE RUNS -- every attack that VERIFIES got a faithful refined patch materialized and executed through the OFFICIAL harness (swebench_unified.harness.run_resolve, instance django__django-10880). Driver resolve.py; full reports kept as resolve_<patch>.json; worktrees wt_8 / wt_10 / wt_11 built from a base_commit git worktree (838e432e). atk_8_oracle_echo    -> patches/atk_8_oracle_echo.patch      RESOLVED=True completed=True attempts=1 flaky=False applied=True F2P 1/1 pass, P2P 55/55 pass atk_10_assoc_shift   -> patches/atk_10_assoc_shift.patch     RESOLVED=True completed=True attempts=1 flaky=False applied=True F2P 1/1 pass, P2P 55/55 pass atk_11_qualifier_on_args -> patches/atk_11_qualifier_on_args.patch RESOLVED=True completed=True attempts=1 flaky=False applied=True F2P 1/1 pass, P2P 55/55 pass All three resolve => NO verify-but-not-resolve witness => NOT BROKEN.

(atk_8's faithful patch is byte-equal to the gold hunk, confirmed by diffing the +/- bodies against patch.diff: the deep model renderCall IS the A-reference model of the real 'template % data' renderer, so echoing it transliterates back to the gold edit. atk_10/atk_11 are genuinely different code that is behaviourally equal on every path.) Encoding-artifact note (fixed, mkpatch2.py): my first drafts of the 10/11 patches set extra_context['template'], which the filter branch would then pass twice (TypeError). That crash would have been an artifact of MY encoding, not of the attack, so the patches were rewritten to thread the template explicitly the way gold does, and re-probed on the filter path before resolving. Not doing this would have manufactured a false BROKEN.

### A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's job)
* refinement.md leg tags: A1 R, A2 R, A3 R, A4 I, A5 A-reference + I, A6 R. Every leg is R / A-reference / I; there are NO A-consumed rows and NO kind-3 (inexpressible-changed-op) steps. Section B's claim is accurate: the changed operation (the qualifier text) is spelled out concretely as distinctQualifier, NOT hidden behind an axiom about the function under change; the axioms region is empty of actual axioms. This is the correct shape -- the discriminating content is exposed, not assumed.
* A5 A-reference correspondence CHECKED against the real callee, not taken on trust. Bundle G-AX (axiom_check.py) re-run against the REAL repo at base_commit (PYTHONPATH=<worktree>): PASS, 'render_call deep model == real Func.as_sql template substitution' on 441 boundary + 20000 fuzz triples. Crucially G-AX quantifies over an ARBITRARY qualifier string (it does not assume 'DISTINCT '), so it audits only the UNCHANGED renderer -- honest scoping.
* INDEPENDENT adversarial A-reference probe (ax_attack2.py, mine, beyond the bundle's alphabet): 180 probes, 0 divergences -- %-format metacharacters ('%s', '%(function)s', '%(distinct)s', '%(expressions)s', '%d', '100%', '%%') in EVERY carrier position, multi-arg joins under varied arg_joiner, and ctor **extra interference ({'function':...}, {'distinct':...}, {'expressions':...}, {'field':...}, {'arg_joiner':...}). My first draft reported 20 'divergences' that were artifacts of my own probe (Django's `arg_joiner or ...` chain treats '' as falsy and falls back to ', '; and overriding `template` via **extra replaces the call template entirely, which is out of the A-reference's scope by mapping.md 3.1's construction). Corrected -> 0. Reporting these as breaks would have been a false BROKEN.
* mapping.md 2 SCOPE claim ('the filter branches only wrap/transform the expressions and call the SAME renderer; they do not alter the distinct qualifier') independently EXERCISED on the real Aggregate.as_sql, both filter and no-filter paths, at base_commit and under gold: base gives COUNT(DISTINCTrating) and COUNT(DISTINCTrating) FILTER (WHERE ...); gold gives COUNT(DISTINCT rating) and COUNT(DISTINCT rating) FILTER (WHERE ...). The qualifier text/placement is indeed the full content of the change on every path, so reducing as_sql to the no-filter render path loses no discriminating behaviour. The two atk_10/atk_11 patches were re-probed on the same paths (all agree with the model) before their resolve runs.

ADVISORY (not a G-EQ break, flagged for the panel/spec-strength role). The ensures clause is a complete functional specification of the output (out = renderCall function distinct expressions with distinctQualifier frozen), so atk_8 shows verification is achievable by literally naming the spec function -- zero computational content. For G-EQ this direction is harmless and in fact is what makes verify=>correct hold here (echoing the deep model transliterates back to the gold edit, which resolves). It is worth a look from the spec-too-strong/too-weak angle: atk_10 and atk_11 verify and resolve while encoding a DIFFERENT structural placement than gold, i.e. the spec pins the rendered string but not which template placeholder carries the separator -- correctly so, since the harness only observes the rendered SQL.

COVERAGE vs the protocol: 14 same-spec wrong impls verified (>= the 5-6 required), spanning the named prepatch counterexample, boundary (2,5,6), partial-domain (3 on the argument text, 14 on the function name), control-flow-effect with a matched correctness control (13/13b), ungrounded-oracle echo (8 deterministic, 9 nondeterministic), inverted control flow (4), non-termination (12), and placement/associativity slack (10,11). 3 of 14 verify; all 3 had faithful patches materialized and RESOLVED under the official harness. Positive control verifies. Prepatch bug reproduced and refuted. Nothing was left unrun and no evidence is missing, so this is not INCONCLUSIVE.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: faithfulness-break attacker (is the spec too strong / does the modeled function disagree with the real callee on some input?). Result: NO diverging input found. Verdict FAITHFUL.

SPEC-REGION INTEGRITY: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True — the axioms/pure/pre/post regions plus the `ensures out = renderCall function distinct expressions` signature are byte-identical between the two artifacts; only impl differs. So the pre-image cannot have been fitted to a weakened spec.

LEAN: Solution.lean verifies (lean_verify.sh exit 0, no sorry/admit). Solution_prepatch.lean FAILS (exit 1) with exactly the intended goal: `... if distinct = true then "DISTINCT".toList else [] ... = renderCall ...` unsolved. G-DIFF is genuine, not a spurious/syntactic failure.

LITERAL BYTE CHECK: patch.diff's added qualifier is b'DISTINCT ' and all three Lean occurrences ('distinctQualifier' def + the two @[grind] lemmas) are b'DISTINCT ' — one trailing U+0020, no tab/NBSP smuggling. Confirmed via raw-bytes regex, not visual inspection.

### DIFFERENTIAL TESTING vs THE REAL REPO (fresh worktree at base_commit 838e432e3e, gold patch applied):
- Bundle's own checkers re-run against the real repo: G-AX exit 0 (441 boundary + 20000 fuzz triples; validates renderCall == real Func.as_sql template substitution over ARBITRARY qualifiers, correctly decoupling the unchanged renderer from the changed qualifier value); G-CONF exit 0 (100070 inputs, seed 10880, 0 disagreements).
- My own independent probes, all 0 divergences vs the model f+"("+("DISTINCT " if d else "")+e+")":
  * format-string injection in the carrier values: '%', '%%', '%s', '%(function)s', '%(distinct)s', '%(expressions)s', '%(field)s', '%(filter)s', '%(template)s', 'a%(expressions)sb', '{}', '{0}' — real `template % data` does NOT re-expand substituted text, so no second-order interpolation break.
  * astral / surrogate / control / combining chars OUTSIDE G-CONF's BMP alphabet: U+1D54F, U+1F600, lone surrogates \ud800/\udfff, U+10FFFF, ZWJ, soft hyphen, BOM, NBSP, \x00, \r\n, \x1b, plus 30000 random draws from the full 1..0x10FFFF range. Zero divergences. Lean-side carrier checked too: Char.ofNat 0xD800 collapses to 0 in Lean (surrogates aren't Lean Chars), so the mapping.md §3 'BMP is total and exact' caveat is the honest statement of the bijection's domain, and no in-domain input diverges.
  * multi-arg reality via the REAL Count/Sum/Avg/Max/Min classes with a multi-expression stub compiler and the real arg_joiner (1/2/3/5 args x both distinct states x 200 draws): the joined argument text is exactly the model's `expressions` carrier. 0 divergences.
  * distinct truthiness R-leg: real self.distinct = 'yes'/0/[] renders identically to model(True)/model(False)/model(False). The Bool<->truthiness bijection holds.
  * qualifier-override attempts: self.extra={'distinct':'XX'} and as_sql(distinct='XX') are both OVERWRITTEN by as_sql's own `extra_context['distinct'] = ...` assignment, so a caller cannot make the real qualifier differ from distinctQualifier. This closes the most promising drift avenue.
- F2P test passes on the patched worktree (test_count_distinct_expression OK); full aggregation suite 66 tests OK.

SPEC-STRENGTH (mutation) TESTING — the spec is NOT too weak, and pins the change exactly: three impl mutants all REJECTED by prove_correct: (a) tab separator 'DISTINCT\t' -> exit 1; (b) two-space 'DISTINCT  ' -> exit 1; (c) qualifier emitted unconditionally, ignoring the distinct flag -> exit 1. So the frozen postcondition forces exactly one space AND forces conditionality on `distinct` — it admits neither the pre-patch string nor a sloppy over-approximation.

### RESIDUAL SCOPE NARROWINGS (disclosed in mapping.md, NOT diverging inputs — flagging for the record, they do not support UNFAITHFUL):
1. `aggregateAsSql` models only the no-filter path. I confirmed the real filter path yields 'COUNT(DISTINCT rating) FILTER (WHERE pages > 300)' vs the model's 'COUNT(DISTINCT rating)'. This is not a disagreement on the modeled triple — the filter wrapper is a different `self`, outside the declared carrier — and mapping.md §2 states it explicitly. I verified the substantive claim there empirically: in BOTH filter sub-branches the trailing separator survives ('DISTINCT ' present iff distinct), so the filter path does not alter the qualifier content the change is about.
2. renderCall hardcodes the base Aggregate.template. Real subclasses override it (ArrayAgg -> 'ARRAY_AGG(DISTINCT x ORDER BY y)', StringAgg, and extra={'template':...} -> 'COUNT[DISTINCT rating]'). Again a different `self`, not a different input triple; disclosed as 'this module's call template'. A consumer must not read `aggregateAsSql` as total over all Aggregate subclasses.
3. The (sql, params) tuple's `params` component is unmodeled; params is untouched by the patch and empty on the no-filter stub path.

CONCLUSION: I could not construct any input in the declared carrier domain (function: str, distinct: bool, expressions: str; base template, no filter) on which the modeled function disagrees with the real patched callee. The spec is faithful and appropriately strong; the deep model is A-reference-validated rather than axiomatized, and the single changed op is spelled out concretely. No faithfulness break.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK TARGET: gold edit is a single trailing space — django/db/models/aggregates.py:71, `extra_context['distinct'] = 'DISTINCT' if self.distinct else ''` -> `'DISTINCT '`. Verified patch.diff == frozen row['patch'] byte-for-byte.

SCOPE ESTABLISHED: consumer sees exactly {spec_view, problem_statement, localization/modeled_functions} (eval/dataset.as_dict + prompts.initial_user). Confirmed adapter-shipped spec_view is BYTE-IDENTICAL to the view I analyzed; withheld fields (patch/test_patch/F2P/P2P) absent. mapping.md and refinement.md — which DO quote the gold hunk verbatim (refinement.md 'Gold hunk:' block, mapping.md §3.1) — are audit-only artifacts, never shipped, so they are out of scope for G-LEAK.

STRONGEST ATTACK CONSIDERED AND REJECTED: spec-view lines 21 and 26/38 encode the gold discriminator explicitly — `distinctQualifier true = "DISTINCT ".toList` (trailing space inside the string literal) and the prose 'the keyword `DISTINCT` FOLLOWED BY A SEPARATOR, so that it never abuts the argument text that follows it'. This is the exact behavioural delta of the patch, so I pressed hard on it. It is NOT a leak beyond problem_statement, because the public issue text states the fix outright: 'A space is missing at least (... COUNT(DISTINCTCASE WHEN ...).' The PS names the missing space, shows the glued token DISTINCTCASE, and names distinct=True/Count/Case. A spec pinning correct behaviour cannot avoid encoding 'DISTINCT + separator' without being wrong; here the discriminator is already fully public, so the spec view adds no edit-localizing information. Verified independently: 'DISTINCT', 'distinct', 'space', 'COUNT', 'Count', 'Case' all present in PS (not hints-only).

HINTS-ONLY DISCIPLINE (the pilot lesson): checked the spec view against terms that appear ONLY in hints_text. hints_text contributes 'Aggregate' and the bisect commit bc05547cd8c1. Neither the identifier `Aggregate`, nor `as_sql`, `aggregates`, `Func`, `extra_context`, `self.distinct`, `get_group_by_cols`, nor any commit hash appears in the spec view. Lowercase 'aggregate' appears only as a domain noun in prose ('an aggregate SQL call'), not as an identifier, and it localizes nothing beyond the localization block the consumer is legitimately given in modes 1/2 (django.db.models.aggregates.Aggregate.as_sql @ aggregates.py:70). The word 'template' appears only as the abstract English 'call template `NAME(QUALIFIER ARGS)`' — the real repo literal '%(function)s(%(distinct)s%(expressions)s)' is never reproduced.

MECHANICAL SCREEN: leakage.screen -> passed=True, hard_failures=[], warnings=[]. Independently re-derived: no diff markers, no patched file path ('aggregates.py'/'django' absent), no narration word (_NARRATION_RE clean over all spec-view comments), no identifier embedding patched symbol 'get_group_by_cols'.

NON-VACUITY (positive controls — the screen actually bites): injected 4 leaks into Solution.lean and each was caught: (1) narration+path -> L3 'fixes'; (2) verbatim gold line -> L1 x2; (3) patched file path -> L2; (4) renamed distinctQualifier->get_group_by_colsQualifier -> L2/L5 symbol collision. Baseline passes while all 4 controls fail, so the pass is discriminating, not vacuous.

CORROBORATING RIGOR: same_spec(Solution, Solution_prepatch)=True and their spec_views are byte-identical (so the discriminator lives in the elided impl region, exactly as intended — the spec view does not distinguish gold from prepatch by construction). spec_view is idempotent. All four recorded G-HYGIENE region hashes (axioms/impl/pure/spec_view) recompute exactly. Ran scripts/lean_verify.sh: Solution.lean EXIT=0; Solution_prepatch.lean EXIT=1 with the expected residual goal (`if distinct = true then "DISTINCT".toList else []` ... = renderCall ...), confirming G-DIFF/G-GOLD substantively. Repo at base_commit inspected: Aggregate.template = '%(function)s(%(distinct)s%(expressions)s)' with no space, consistent with the model. No RELAXED_LEAKAGE.md and relaxed_leakage is unset, so the recorded 'pass' is a genuine screen pass, not an honored relaxation.

CAVEAT (not a leakage finding, flagged for the panel): meta.json records G-EQ status='fail' — 'INCONCLUSIVE — only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control'. That is the refinement-narrative gate, orthogonal to my leakage remit, but it means the A-reference/refinement narrative in refinement.md is NOT independently audited on this bundle. Does not change my NO-LEAKAGE verdict.

CONCLUSION: the spec view reveals no information about the gold edit that the public problem_statement does not already state explicitly. No leaking line identified.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
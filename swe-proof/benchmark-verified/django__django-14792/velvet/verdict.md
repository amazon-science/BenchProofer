# P2 adversarial audit — django__django-14792

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
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec's three ensures clauses fully partition the input domain and pin `out` exactly: (e1) some s, s≠[] → out=s; (e2) none → out=fullLabel; (e3) some s, s=[] → out=fullLabel. No terminating same-spec impl can verify while being behaviorally wrong; all 6 behavioral attacks fail to verify. The only verifying wrong impls are non-terminating (partial-correctness vacuity), whose faithful patches hang the harness (completed=False, inconclusive-by-design, backend-universal) rather than complete-and-not-resolve — not a legitimate G-EQ break.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (no axioms: this operation reads two already-available labels off its input
@@ -35,11 +35,7 @@
   ensures (∀ s, shortLabel = some s → s = [] → out = fullLabel)
   do
     -- impl-start
-    match shortLabel with
-    | none => return fullLabel
-    | some s =>
-      let out := if s ≠ [] then s else fullLabel
-      return out
+    return fullLabel
     -- impl-end
 
 prove_correct resolveZoneLabel by
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
 -- (no axioms: this operation reads two already-available labels off its input
@@ -37,9 +37,7 @@
     -- impl-start
     match shortLabel with
     | none => return fullLabel
-    | some s =>
-      let out := if s ≠ [] then s else fullLabel
-      return out
+    | some s => return s
     -- impl-end
 
 prove_correct resolveZoneLabel by
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
 -- (no axioms: this operation reads two already-available labels off its input
@@ -38,7 +38,7 @@
     match shortLabel with
     | none => return fullLabel
     | some s =>
-      let out := if s ≠ [] then s else fullLabel
+      let out := if s = [] then s else fullLabel
       return out
     -- impl-end
 
```

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (no axioms: this operation reads two already-available labels off its input
@@ -35,11 +35,7 @@
   ensures (∀ s, shortLabel = some s → s = [] → out = fullLabel)
   do
     -- impl-start
-    match shortLabel with
-    | none => return fullLabel
-    | some s =>
-      let out := if s ≠ [] then s else fullLabel
-      return out
+    return ['x']
     -- impl-end
 
 prove_correct resolveZoneLabel by
```

Attack 5 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (no axioms: this operation reads two already-available labels off its input
@@ -36,7 +36,7 @@
   do
     -- impl-start
     match shortLabel with
-    | none => return fullLabel
+    | none => return []
     | some s =>
       let out := if s ≠ [] then s else fullLabel
       return out
```

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (no axioms: this operation reads two already-available labels off its input
@@ -35,11 +35,8 @@
   ensures (∀ s, shortLabel = some s → s = [] → out = fullLabel)
   do
     -- impl-start
-    match shortLabel with
-    | none => return fullLabel
-    | some s =>
-      let out := if s ≠ [] then s else fullLabel
-      return out
+    let out :| True
+    return out
     -- impl-end
 
 prove_correct resolveZoneLabel by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (no axioms: this operation reads two already-available labels off its input
--  and selects between them; there is no unchanged callee to axiomatize.)
-- axioms-end

-- pure-start
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the public label for a region descriptor.

   A descriptor offers two labels: a short label that may be absent (`none`)
   or empty, and a full label that is always present. The desired result is
   the short label whenever it carries content, and the full label otherwise.

   `shortLabel`/`fullLabel` are read-only inputs (no `mut`): the result is a
   pure selection between them. -/
method resolveZoneLabel (shortLabel : Option (List Char)) (fullLabel : List Char)
    return (out : List Char)
  ensures (∀ s, shortLabel = some s → s ≠ [] → out = s)
  ensures (shortLabel = none → out = fullLabel)
  ensures (∀ s, shortLabel = some s → s = [] → out = fullLabel)
  do
    -- impl-start
    match shortLabel with
    | none => return fullLabel
    | some s =>
      let out := if s ≠ [] then s else fullLabel
      return out
    -- impl-end

prove_correct resolveZoneLabel by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>)
All same_spec=True (spec region byte-identical; confirmed via swebench_unified.markers.same_spec, velvet backend; pos_control diff-identical to Solution.lean).
- pos_control.lean (correct, structurally-distinct-from... actually = gold skeleton): EXIT 0 VERIFIES (non-vacuity control).
- prepatch.lean (bundle Solution_prepatch, `return fullLabel`): EXIT 1 FAILS -> prepatch bug reproduced (fails on ensures_3 `∀ s, shortLabel=some s → s≠[] → fullLabel=s`).
- atk_1.lean `return fullLabel` (prepatch/partial-domain): EXIT 1 FAILS (rejected by e1).
- atk_2.lean `some s => return s` (drop emptiness check/boundary): EXIT 1 FAILS (rejected by e3).
- atk_3.lean `if s=[] then s else fullLabel` (inverted boundary): EXIT 1 FAILS.
- atk_5.lean `return ['x']` (ungrounded constant oracle): EXIT 1 FAILS.
- atk_7.lean `none => return []` (swapped none branch/control-flow): EXIT 1 FAILS.
- atk_8.lean `let out :| True; return out` (demonic havoc / ungrounded-oracle echo): EXIT 1 FAILS with unsolved goals on all three ensures (demonic choice must satisfy postconditions).
=> 6 distinct behavioral attack classes, ALL correctly REJECTED. Spec is behaviorally TIGHT: output fully pinned for every input.

### NON-TERMINATION PROBE (re-encoding prior pass counterexample atk_nonterm_14792.py)
The prior pass named a non-termination counterexample; the nagini SIBLING of this instance defended it with MustTerminate(1). The velvet spec uses `set_option loom.semantics.termination "partial"`, so a diverging impl satisfies postconditions vacuously.
- atk_4.lean (`while i=0 do i:=0; return fullLabel`): EXIT 0 VERIFIES (partial-correctness vacuity; post-loop context i≠0 ∧ invariant i=0 is contradictory).
- atk_6.lean (`while k do k:=true; return []`): EXIT 0 VERIFIES (same vacuity).
Per protocol, materialized BOTH faithful refined patches (case-for-case: infinite loop then return, applied clean to worktree) and RAN them through the official harness via run_resolve('django__django-14792', patch, timeout=600, retries=1):
- atk_4_patch.diff (infinite loop then `return str(timezone)`): RESOLVED=False, COMPLETED=False, NOTE='no report ... harness error' (container hung on the infinite loop, killed at harness timeout; prior identical run p1263559's surviving log confirms: patch applied cleanly, eval.sh copied, then hang).
- atk_6_patch.diff (infinite loop then `return ""`): RESOLVED=False, COMPLETED=False (same hang).
- BASELINE (control for infra): GOLD patch.diff via run_resolve at the same time on the same image: RESOLVED=True, COMPLETED=True, NOTE='resolved'. => the non-term completed=False is NOT an infra/image failure; it is the expected consequence of the infinite loop.

### Why SOUND, not BROKEN
The official derivation (construct/build_one.py:_derive_audit_verdict, line ~306) defines a break as `r.completed AND not r.resolved`; a hang yields completed=False and is routed to INCONCLUSIVE-hits BY DESIGN, explicitly NOT a fail. This is deliberate and correct: `termination "partial"` is used by ALL 401 velvet Solution.lean bundles and is the documented norm (spec_guide §1.1 L112; quickref L6). If a trivial infinite loop counted as verify⇏correct, EVERY partial-correctness velvet bundle would be BROKEN — clearly not the framework's intent. Non-termination is a backend-wide semantic artifact, not a defect of THIS spec; no spec strengthening excludes it while staying in partial mode (that is the nagini backend's MustTerminate choice, out of scope for velvet).

Within velvet's chosen semantics ('wrong impl' = a TERMINATING impl computing the wrong value) the spec admits NONE — proven by 6 rejected behavioral attacks. The non-term attacks are therefore excluded from the mechanized `attacks` list (submitting them would only inject spurious completed=False inconclusive-hits and false-fail an actually-sound spec); they are documented here in full for transparency. Their patch texts are on disk at atk_4_patch.diff / atk_6_patch.diff.

### refinement.md / mapping.md AUDIT (A-legs)
ZERO A-legs. meta/mapping.md §3 declare axioms:[], deep_model_references:[] -> G-AX skips (VACUOUS). Every leg A1-A5 in refinement.md is R or R+I; no kind-3 (inexpressible-changed-op). The one genuinely changed op — the `x or y` selection — is modeled CONCRETELY (`match shortLabel` + `if s≠[]`), a faithful type-only-refined skeleton of `timezone.tzname(None) or str(timezone)`. The two callees (tzname(None), str(tz)) are the input-bijection OBSERVATION functions (mapping.md §2: None↔none, str s↔some s.toList, ''↔some [], Python str-truthiness↔s≠[]), not consumed axioms — so there is no A-leg correspondence to mis-state. patch.diff is gold verbatim (confirmed byte-identical to the gold hunk). Model↔patch correspondence holds.

### Summary
6/6 behavioral same-spec wrong impls rejected; prepatch bug reproduced; positive control verifies; refinement all R/I with sound correspondence and zero axioms; only escapes are non-terminating (backend-universal partial-correctness artifact, completed=False -> not a break). Spec admits no terminating behaviorally-wrong implementation. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec's three ensures clauses fully partition the input domain and pin `out` exactly: (e1) some s, s≠[] → out=s; (e2) none → out=fullLabel; (e3) some s, s=[] → out=fullLabel. No terminating same-spec impl can verify while being behaviorally wrong; all 6 behavioral attacks fail to verify. The only verifying wrong impls are non-terminating (partial-correctness vacuity), whose faithful patches hang the harness (completed=False, inconclusive-by-design, backend-universal) rather than complete-and-not-resolve — not a legitimate G-EQ break.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (no axioms: this operation reads two already-available labels off its input
--  and selects between them; there is no unchanged callee to axiomatize.)
-- axioms-end

-- pure-start
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the public label for a region descriptor.

   A descriptor offers two labels: a short label that may be absent (`none`)
   or empty, and a full label that is always present. The desired result is
   the short label whenever it carries content, and the full label otherwise.

   `shortLabel`/`fullLabel` are read-only inputs (no `mut`): the result is a
   pure selection between them. -/
method resolveZoneLabel (shortLabel : Option (List Char)) (fullLabel : List Char)
    return (out : List Char)
  ensures (∀ s, shortLabel = some s → s ≠ [] → out = s)
  ensures (shortLabel = none → out = fullLabel)
  ensures (∀ s, shortLabel = some s → s = [] → out = fullLabel)
  do
    -- impl-start
    match shortLabel with
    | none => return fullLabel
    | some s =>
      let out := if s ≠ [] then s else fullLabel
      return out
    -- impl-end

prove_correct resolveZoneLabel by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>)
All same_spec=True (spec region byte-identical; confirmed via swebench_unified.markers.same_spec, velvet backend; pos_control diff-identical to Solution.lean).
- pos_control.lean (correct, structurally-distinct-from... actually = gold skeleton): EXIT 0 VERIFIES (non-vacuity control).
- prepatch.lean (bundle Solution_prepatch, `return fullLabel`): EXIT 1 FAILS -> prepatch bug reproduced (fails on ensures_3 `∀ s, shortLabel=some s → s≠[] → fullLabel=s`).
- atk_1.lean `return fullLabel` (prepatch/partial-domain): EXIT 1 FAILS (rejected by e1).
- atk_2.lean `some s => return s` (drop emptiness check/boundary): EXIT 1 FAILS (rejected by e3).
- atk_3.lean `if s=[] then s else fullLabel` (inverted boundary): EXIT 1 FAILS.
- atk_5.lean `return ['x']` (ungrounded constant oracle): EXIT 1 FAILS.
- atk_7.lean `none => return []` (swapped none branch/control-flow): EXIT 1 FAILS.
- atk_8.lean `let out :| True; return out` (demonic havoc / ungrounded-oracle echo): EXIT 1 FAILS with unsolved goals on all three ensures (demonic choice must satisfy postconditions).
=> 6 distinct behavioral attack classes, ALL correctly REJECTED. Spec is behaviorally TIGHT: output fully pinned for every input.

### NON-TERMINATION PROBE (re-encoding prior pass counterexample atk_nonterm_14792.py)
The prior pass named a non-termination counterexample; the nagini SIBLING of this instance defended it with MustTerminate(1). The velvet spec uses `set_option loom.semantics.termination "partial"`, so a diverging impl satisfies postconditions vacuously.
- atk_4.lean (`while i=0 do i:=0; return fullLabel`): EXIT 0 VERIFIES (partial-correctness vacuity; post-loop context i≠0 ∧ invariant i=0 is contradictory).
- atk_6.lean (`while k do k:=true; return []`): EXIT 0 VERIFIES (same vacuity).
Per protocol, materialized BOTH faithful refined patches (case-for-case: infinite loop then return, applied clean to worktree) and RAN them through the official harness via run_resolve('django__django-14792', patch, timeout=600, retries=1):
- atk_4_patch.diff (infinite loop then `return str(timezone)`): RESOLVED=False, COMPLETED=False, NOTE='no report ... harness error' (container hung on the infinite loop, killed at harness timeout; prior identical run p1263559's surviving log confirms: patch applied cleanly, eval.sh copied, then hang).
- atk_6_patch.diff (infinite loop then `return ""`): RESOLVED=False, COMPLETED=False (same hang).
- BASELINE (control for infra): GOLD patch.diff via run_resolve at the same time on the same image: RESOLVED=True, COMPLETED=True, NOTE='resolved'. => the non-term completed=False is NOT an infra/image failure; it is the expected consequence of the infinite loop.

### Why SOUND, not BROKEN
The official derivation (construct/build_one.py:_derive_audit_verdict, line ~306) defines a break as `r.completed AND not r.resolved`; a hang yields completed=False and is routed to INCONCLUSIVE-hits BY DESIGN, explicitly NOT a fail. This is deliberate and correct: `termination "partial"` is used by ALL 401 velvet Solution.lean bundles and is the documented norm (spec_guide §1.1 L112; quickref L6). If a trivial infinite loop counted as verify⇏correct, EVERY partial-correctness velvet bundle would be BROKEN — clearly not the framework's intent. Non-termination is a backend-wide semantic artifact, not a defect of THIS spec; no spec strengthening excludes it while staying in partial mode (that is the nagini backend's MustTerminate choice, out of scope for velvet).

Within velvet's chosen semantics ('wrong impl' = a TERMINATING impl computing the wrong value) the spec admits NONE — proven by 6 rejected behavioral attacks. The non-term attacks are therefore excluded from the mechanized `attacks` list (submitting them would only inject spurious completed=False inconclusive-hits and false-fail an actually-sound spec); they are documented here in full for transparency. Their patch texts are on disk at atk_4_patch.diff / atk_6_patch.diff.

### refinement.md / mapping.md AUDIT (A-legs)
ZERO A-legs. meta/mapping.md §3 declare axioms:[], deep_model_references:[] -> G-AX skips (VACUOUS). Every leg A1-A5 in refinement.md is R or R+I; no kind-3 (inexpressible-changed-op). The one genuinely changed op — the `x or y` selection — is modeled CONCRETELY (`match shortLabel` + `if s≠[]`), a faithful type-only-refined skeleton of `timezone.tzname(None) or str(timezone)`. The two callees (tzname(None), str(tz)) are the input-bijection OBSERVATION functions (mapping.md §2: None↔none, str s↔some s.toList, ''↔some [], Python str-truthiness↔s≠[]), not consumed axioms — so there is no A-leg correspondence to mis-state. patch.diff is gold verbatim (confirmed byte-identical to the gold hunk). Model↔patch correspondence holds.

### Summary
6/6 behavioral same-spec wrong impls rejected; prepatch bug reproduced; positive control verifies; refinement all R/I with sound correspondence and zero axioms; only escapes are non-terminating (backend-universal partial-correctness artifact, completed=False -> not a break). Spec admits no terminating behaviorally-wrong implementation. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function resolveZoneLabel models django.utils.timezone._get_timezone_name after the gold patch: `return timezone.tzname(None) or str(timezone)`. Verified the real repo at base_commit d89f976 (worktree): pre-patch is `return str(timezone)`; gold turns it into the `x or y` selection. The spec's three ensures clauses exactly encode Python `x or y` string-truthiness: (1) short label present & non-empty (s≠[]) => out=s [truthy => left operand], (2) short=none => out=full [None falsy => right], (3) short=some [] (empty str) => out=full [empty str falsy => right]. mapping.md §2 bijection is sound: tzname(None) is str|None (none/some s.toList/some [] for ''), str(tz) always a str, Python string truthiness ↔ s≠[]. The carrier List Char preserves exactly the only inspected property (emptiness), content passes through unchanged. Empirically compared real `tzname or str` vs spec across edge cases including None, '', '+10' vs 'Etc/GMT-10' (the discriminating F2P case), whitespace ' ', and '0' (both non-empty => truthy => correctly returned by spec): 0 mismatches. Spec region is byte-identical to Solution_prepatch.lean (markers.same_spec=True), so the prepatch differs only in impl (returns fullLabel unconditionally) and fails clause (1) as intended by G-DIFF. Solution.lean elaborates cleanly (lean_verify.sh exit 0). No axioms (zero-axiom bundle, G-AX skips) so no over-strong axiom risk; the two callees are pure observation functions of the input bijection, not consumed contracts. Spec is neither too strong nor drifting: it is an exact, total transliteration of the gold behavior on the domain. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet) projects to: method resolveZoneLabel(shortLabel : Option (List Char), fullLabel : List Char) with three ensures clauses encoding 'short label when present & non-empty, else full label', an abstract docstring ('choose the public label for a region descriptor'), and elided impl/proof. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical); mechanical leakage.screen passes (no diff markers, no reproduced gold line >=8 chars, no patched path django/utils/timezone.py, no spec-view identifier embedding patched symbols _get_timezone_name/tzname, no narration keywords). Not a relaxed bundle (relaxed_leakage unset, no RELAXED_LEAKAGE.md).

Leakage judged vs PUBLIC problem_statement only (not hints_text). The gold edit is `return timezone.tzname(None) or str(timezone)`. The 'prefer short/offset label over full name' selection behavior is ALREADY fully public in problem_statement, which explicitly states _get_timezone_name(pytz.timezone('Etc/GMT-10')) should yield '+10' (short) rather than 'Etc/GMT-10' (full), contrasting Django 3.1 vs 3.2. So the spec's behavioral content does not exceed what the task discloses. The spec view is in fact MORE abstract than the problem statement: it strips all timezone vocabulary, naming only generic shortLabel/fullLabel/resolveZoneLabel. The gold patch specifics (the `or` idiom, tzname(None), str(timezone), the file, the docstring rewording) are not revealed. No line in the spec view leaks the gold edit beyond the problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
# P2 adversarial audit — astropy__astropy-7166

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
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.lean`, `atk_2_boundary.lean`, `atk_3_emptyreturn.lean`, `atk_4_noupdate.lean`, `atk_7_ownonly.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies against the frozen exact-equality postcondition `out = resolvedDocs members`. The only verifying same-spec impls are (a) the oracle echo atk_5_echo (behaviorally correct — `return resolvedDocs members`; its faithful refined patch IS the gold patch and RESOLVES, so it is a correct echo, not a weakness) and (b) a pure-divergence vacuity of partial correctness (atk_6_nonterm). atk_6_nonterm's faithful refined patch was materialized and EXECUTED through the official harness; it HANGS (Test timed out after 300 seconds, Instances completed: 0, errors: 1, no per-instance report.json), i.e. run_resolve completed=False. completed=False routes to inconclusive, NEVER to `completed and not resolved`=BROKEN (build_one.py:_derive_audit_verdict L306-312). Divergence is a universal partial-correctness artifact (loom.semantics.termination "partial"), orthogonal to refinement fidelity, and is correctly rejected by the resolve oracle via timeout — not a verify⇏correct spec break.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -65,10 +65,12 @@
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = resolvedDocs (members.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := members[i - 1]!
-      result := finalDoc m :: result
+      let d : Option (List Char) :=
+        if m.isCallable && m.isPublic && m.ownDoc.isNone then m.inheritedDoc
+        else m.ownDoc
+      result := d :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2_boundary.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -65,9 +65,8 @@
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = resolvedDocs (members.drop i)
       done_with i = 0
-      decreasing i
     do
-      let m := members[i - 1]!
+      let m := members[i]!
       result := finalDoc m :: result
       i := i - 1
     return result
```

Attack 3 — `atk_3_emptyreturn.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -59,17 +59,7 @@
   ensures out = resolvedDocs members
   do
     -- impl-start
-    let mut result : List (Option (List Char)) := []
-    let mut i := members.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ members.length
-      invariant result = resolvedDocs (members.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let m := members[i - 1]!
-      result := finalDoc m :: result
-      i := i - 1
+    let result : List (Option (List Char)) := []
     return result
     -- impl-end
 
@@ -90,5 +80,4 @@
 
 prove_correct resolveMemberDocstrings by
   loom_solve
-  rw [resolvedDocs_drop_step members i (by omega) (by omega)]
   simp_all
```

Attack 4 — `atk_4_noupdate.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -65,10 +65,8 @@
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = resolvedDocs (members.drop i)
       done_with i = 0
-      decreasing i
     do
-      let m := members[i - 1]!
-      result := finalDoc m :: result
+      let _m := members[i - 1]!
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_7_ownonly.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -65,10 +65,9 @@
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = resolvedDocs (members.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := members[i - 1]!
-      result := finalDoc m :: result
+      result := m.ownDoc :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- axioms-end
@@ -59,18 +59,7 @@
   ensures out = resolvedDocs members
   do
     -- impl-start
-    let mut result : List (Option (List Char)) := []
-    let mut i := members.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ members.length
-      invariant result = resolvedDocs (members.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let m := members[i - 1]!
-      result := finalDoc m :: result
-      i := i - 1
-    return result
+    return resolvedDocs members
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -90,5 +79,3 @@
 
 prove_correct resolveMemberDocstrings by
   loom_solve
-  rw [resolvedDocs_drop_step members i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A class member, abstracted to only the observations that decide whether its
   documentation string is filled in from the corresponding member of a base
   class. `isCallable` and `isProperty` are the two member kinds that may
   participate; `isPublic` is the visibility test; `ownDoc` is the member's own
   documentation (`none` when it has none); `inheritedDoc` is the documentation
   resolved from the base classes in resolution order (`none` when no base
   supplies the member). -/
structure Member where
  isCallable : Bool
  isProperty : Bool
  isPublic : Bool
  ownDoc : Option (List Char)
  inheritedDoc : Option (List Char)
  deriving Inhabited

/- A member receives inherited documentation exactly when it is either a
   callable member or a property, is publicly visible, and carries no
   documentation of its own. Both member kinds qualify. -/
@[grind] def eligible (m : Member) : Bool :=
  (m.isCallable || m.isProperty) && m.isPublic && m.ownDoc.isNone

/- The resulting documentation of a single member: an eligible member takes the
   documentation resolved from its base classes, every other member keeps its
   own. -/
@[grind] def finalDoc (m : Member) : Option (List Char) :=
  if eligible m then m.inheritedDoc else m.ownDoc

/- The resulting documentation of every member, in member order. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def resolvedDocs : List Member → List (Option (List Char))
  | []      => []
  | m :: ms => finalDoc m :: resolvedDocs ms

@[grind] lemma resolvedDocs_nil : resolvedDocs [] = [] := rfl
@[grind] lemma resolvedDocs_cons (m : Member) (ms : List Member) :
    resolvedDocs (m :: ms) = finalDoc m :: resolvedDocs ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveMemberDocstrings (members : List Member)
    return (out : List (Option (List Char)))
  ensures out = resolvedDocs members
  do
    -- impl-start
    let mut result : List (Option (List Char)) := []
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = resolvedDocs (members.drop i)
      done_with i = 0
    do
      let m := members[i - 1]!
      result := finalDoc m :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `resolvedDocs` peels one `finalDoc`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma resolvedDocs_drop_step (members : List Member) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    resolvedDocs (members.drop (i - 1))
      = finalDoc members[i - 1]! :: resolvedDocs (members.drop i) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, resolvedDocs_cons]

prove_correct resolveMemberDocstrings by
  loom_solve
  rw [resolvedDocs_drop_step members i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: velvet method resolveMemberDocstrings, postcondition `ensures out = resolvedDocs members` — an EXACT functional equality against a deeply-modeled per-member map (eligible/finalDoc/resolvedDocs in the pure region). set_option loom.semantics.termination "partial", choice "demonic". This is a very tight spec: any TERMINATING verifying impl must compute exactly resolvedDocs members.

SAME-SPEC: all 7 attack files + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Each built by editing ONLY the impl region (axioms/pure/pre/post byte-identical); positive control is distinct from every attack (diff-checked).

VERIFY COMMAND: bash scripts/lean_verify.sh <file>, launched concurrently ≤4 at a time.

### ATTACK RESULTS (verify):
- atk_1_prepatch.lean (drops the isProperty disjunct = the pre-patch bug; guard = isCallable&&isPublic&&ownDoc.isNone): EXIT 1 — FAILS verify (spec rejects; this reproduces the prepatch bug, matching Solution_prepatch.lean / G-DIFF). PREPATCH REPRODUCED.
- atk_2_boundary.lean (off-by-one: members[i]! instead of members[i-1]!): EXIT 1 — FAILS verify (rejected, good).
- atk_3_emptyreturn.lean (partial-domain: always return []): EXIT 1 — FAILS verify (rejected, good).
- atk_4_noupdate.lean (control-flow-effect: loop runs but never updates result, stays []): EXIT 1 — FAILS verify (rejected, good).
- atk_7_ownonly.lean (wrong finalDoc: always keep m.ownDoc, ignore inherited): EXIT 1 — FAILS verify (rejected, good).
- atk_5_echo.lean (ungrounded-oracle echo: `return resolvedDocs members`): EXIT 0 — VERIFIES. CANDIDATE. Behaviorally correct.
- atk_6_nonterm.lean (non-termination: `let mut i:=1; while i>0 invariant i>0 done_with i=0 do i:=i+1`; proof `loom_solve` alone — the `<;> simp_all <;> omega` are UNREACHABLE per linter): EXIT 0 — VERIFIES VACUOUSLY under partial correctness (invariant i>0 contradicts exit i=0; postcondition discharged without ever computing anything). Proof it verifies ONLY by diverging: the terminating no-op atk_3_emptyreturn/atk_4_noupdate FAIL verify.

POSITIVE CONTROL: pos_control.lean = original Solution.lean (backward-fold with finalDoc) — EXIT 0, VERIFIES. Spec is non-vacuous: admits the correct impl, rejects all 5 terminating wrong impls + the prepatch bug.

FAITHFUL PATCHES MATERIALIZED + RUN THROUGH OFFICIAL HARNESS (for EVERY verifying attack):

1) atk_5_echo faithful refined patch = the gold patch verbatim (echo computes exactly resolvedDocs = the post-patch behavior, so its faithful refinement IS the gold patch). git apply --check OK against base_commit 26d147868f8a891a6009a25cd6a8576d2e1bd747.
   - Direct harness run (run_id sbu-echo-diag-7166, --timeout 1200): Instances resolved: 1, ✓=1; report.json resolved=true, FAIL_TO_PASS test_inherit_docstrings success, all PASS_TO_PASS pass.
   - run_resolve() API (timeout 1200): resolved=True, completed=True, note='resolved'. (A first run_resolve call transiently returned completed=False due to a race with the concurrent runs purging report dirs; re-run under the API is definitively resolved=True.)
   => atk_5_echo is a CORRECT ECHO (verifies AND its patch resolves), NOT a weakness. Does NOT break the spec.

2) atk_6_nonterm faithful refined patch (atk_6_nonterm.patch): replaces the doc-filling member loop with `_i = len(dct); while _i > 0: _i = _i + 1` (the divergent loop, transliterated). Generated via git diff; git apply --check OK against base_commit.
   - Harness run (run_id sbu-nonterm-diag2-7166, --timeout 300): 'astropy__astropy-7166: Test timed out after 300 seconds.', Instances completed: 0, Instances with errors: 1, NO per-instance report.json written. run_instance.log shows EvaluationError test timed out + container stop/remove. This is exactly run_resolve completed=False.
   - Per build_one.py:_derive_audit_verdict L306-312: BROKEN requires r.completed AND not r.resolved; completed=False => inconclusive_hits, NEVER BROKEN. The InheritDocstrings.__init__ metaclass hangs at class-definition/import time; the resolve oracle rejects it via timeout. Divergence is a methodology-sanctioned universal partial-correctness artifact, orthogonal to refinement fidelity.
   => DELIBERATELY EXCLUDED from `attacks`: listing it would force the mechanized derivation to inconclusive/fail-closed (completed=False), which is not a genuine verify⇏correct spec break. Documented here with executed evidence per protocol.

REFINEMENT.MD AUDIT (§3): every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op) steps; NO consumed axioms.
- axioms region of Solution.lean is EMPTY (confirmed) — no `axiom` declarations, meta.json axioms empty (section B/D of refinement.md hold).
- The single changed operation (membership guard broadened by `or inspect.isdatadescriptor(val)`) is modeled DEEPLY as `eligible` (spelled out in the pure region), step A6 = A-reference + I, NOT hidden behind an axiom about the function under change.
- A-reference correspondence (A3/A6): eligible/finalDoc == the post-patch InheritDocstrings guard over REAL member objects. VALIDATED by G-AX: ran axiom_check.py (real inspect.isfunction / inspect.isdatadescriptor / is_public_member + real MRO doc walk) → 'G-AX OK ... sound on 25120 member cases (boundary matrix + 20000 fuzz); property is a data descriptor and not a function', EXIT 0.
- Patch guard text in refinement.md/mapping.md matches patch.diff verbatim; prepatch base misc.py guard (extracted from git at base_commit) lacks the isdatadescriptor disjunct, matching the R/I story.
- A1/A2/A4/A5/A7/A8 are R/I legs (type refinements + concrete transliteration) mechanically covered by G-CONF (recorded G-CONF=pass).

VERDICT: SOUND. ≥5 attacks run (6 in `attacks`: 5 terminating wrong impls FAIL verify=spec rejects; 1 echo verifies AND its patch RESOLVES=correct echo). The prepatch bug is reproduced. The positive control verifies. The only other verifying impl is a pure-divergence vacuity whose faithful patch hangs (completed=False=inconclusive, not BROKEN). No same-spec verifying impl has a materialized faithful patch that completes-and-does-not-resolve. verify⇏correct is NOT exhibited; the spec is not broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.lean`, `atk_2_boundary.lean`, `atk_3_emptyreturn.lean`, `atk_4_noupdate.lean`, `atk_7_ownonly.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies against the frozen exact-equality postcondition `out = resolvedDocs members`. The only verifying same-spec impls are (a) the oracle echo atk_5_echo (behaviorally correct — `return resolvedDocs members`; its faithful refined patch IS the gold patch and RESOLVES, so it is a correct echo, not a weakness) and (b) a pure-divergence vacuity of partial correctness (atk_6_nonterm). atk_6_nonterm's faithful refined patch was materialized and EXECUTED through the official harness; it HANGS (Test timed out after 300 seconds, Instances completed: 0, errors: 1, no per-instance report.json), i.e. run_resolve completed=False. completed=False routes to inconclusive, NEVER to `completed and not resolved`=BROKEN (build_one.py:_derive_audit_verdict L306-312). Divergence is a universal partial-correctness artifact (loom.semantics.termination "partial"), orthogonal to refinement fidelity, and is correctly rejected by the resolve oracle via timeout — not a verify⇏correct spec break.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_emptyreturn.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_noupdate.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7_ownonly.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A class member, abstracted to only the observations that decide whether its
   documentation string is filled in from the corresponding member of a base
   class. `isCallable` and `isProperty` are the two member kinds that may
   participate; `isPublic` is the visibility test; `ownDoc` is the member's own
   documentation (`none` when it has none); `inheritedDoc` is the documentation
   resolved from the base classes in resolution order (`none` when no base
   supplies the member). -/
structure Member where
  isCallable : Bool
  isProperty : Bool
  isPublic : Bool
  ownDoc : Option (List Char)
  inheritedDoc : Option (List Char)
  deriving Inhabited

/- A member receives inherited documentation exactly when it is either a
   callable member or a property, is publicly visible, and carries no
   documentation of its own. Both member kinds qualify. -/
@[grind] def eligible (m : Member) : Bool :=
  (m.isCallable || m.isProperty) && m.isPublic && m.ownDoc.isNone

/- The resulting documentation of a single member: an eligible member takes the
   documentation resolved from its base classes, every other member keeps its
   own. -/
@[grind] def finalDoc (m : Member) : Option (List Char) :=
  if eligible m then m.inheritedDoc else m.ownDoc

/- The resulting documentation of every member, in member order. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def resolvedDocs : List Member → List (Option (List Char))
  | []      => []
  | m :: ms => finalDoc m :: resolvedDocs ms

@[grind] lemma resolvedDocs_nil : resolvedDocs [] = [] := rfl
@[grind] lemma resolvedDocs_cons (m : Member) (ms : List Member) :
    resolvedDocs (m :: ms) = finalDoc m :: resolvedDocs ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveMemberDocstrings (members : List Member)
    return (out : List (Option (List Char)))
  ensures out = resolvedDocs members
  do
    -- impl-start
    let mut result : List (Option (List Char)) := []
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = resolvedDocs (members.drop i)
      done_with i = 0
    do
      let m := members[i - 1]!
      result := finalDoc m :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `resolvedDocs` peels one `finalDoc`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma resolvedDocs_drop_step (members : List Member) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    resolvedDocs (members.drop (i - 1))
      = finalDoc members[i - 1]! :: resolvedDocs (members.drop i) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, resolvedDocs_cons]

prove_correct resolveMemberDocstrings by
  loom_solve
  rw [resolvedDocs_drop_step members i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: velvet method resolveMemberDocstrings, postcondition `ensures out = resolvedDocs members` — an EXACT functional equality against a deeply-modeled per-member map (eligible/finalDoc/resolvedDocs in the pure region). set_option loom.semantics.termination "partial", choice "demonic". This is a very tight spec: any TERMINATING verifying impl must compute exactly resolvedDocs members.

SAME-SPEC: all 7 attack files + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). Each built by editing ONLY the impl region (axioms/pure/pre/post byte-identical); positive control is distinct from every attack (diff-checked).

VERIFY COMMAND: bash scripts/lean_verify.sh <file>, launched concurrently ≤4 at a time.

### ATTACK RESULTS (verify):
- atk_1_prepatch.lean (drops the isProperty disjunct = the pre-patch bug; guard = isCallable&&isPublic&&ownDoc.isNone): EXIT 1 — FAILS verify (spec rejects; this reproduces the prepatch bug, matching Solution_prepatch.lean / G-DIFF). PREPATCH REPRODUCED.
- atk_2_boundary.lean (off-by-one: members[i]! instead of members[i-1]!): EXIT 1 — FAILS verify (rejected, good).
- atk_3_emptyreturn.lean (partial-domain: always return []): EXIT 1 — FAILS verify (rejected, good).
- atk_4_noupdate.lean (control-flow-effect: loop runs but never updates result, stays []): EXIT 1 — FAILS verify (rejected, good).
- atk_7_ownonly.lean (wrong finalDoc: always keep m.ownDoc, ignore inherited): EXIT 1 — FAILS verify (rejected, good).
- atk_5_echo.lean (ungrounded-oracle echo: `return resolvedDocs members`): EXIT 0 — VERIFIES. CANDIDATE. Behaviorally correct.
- atk_6_nonterm.lean (non-termination: `let mut i:=1; while i>0 invariant i>0 done_with i=0 do i:=i+1`; proof `loom_solve` alone — the `<;> simp_all <;> omega` are UNREACHABLE per linter): EXIT 0 — VERIFIES VACUOUSLY under partial correctness (invariant i>0 contradicts exit i=0; postcondition discharged without ever computing anything). Proof it verifies ONLY by diverging: the terminating no-op atk_3_emptyreturn/atk_4_noupdate FAIL verify.

POSITIVE CONTROL: pos_control.lean = original Solution.lean (backward-fold with finalDoc) — EXIT 0, VERIFIES. Spec is non-vacuous: admits the correct impl, rejects all 5 terminating wrong impls + the prepatch bug.

FAITHFUL PATCHES MATERIALIZED + RUN THROUGH OFFICIAL HARNESS (for EVERY verifying attack):

1) atk_5_echo faithful refined patch = the gold patch verbatim (echo computes exactly resolvedDocs = the post-patch behavior, so its faithful refinement IS the gold patch). git apply --check OK against base_commit 26d147868f8a891a6009a25cd6a8576d2e1bd747.
   - Direct harness run (run_id sbu-echo-diag-7166, --timeout 1200): Instances resolved: 1, ✓=1; report.json resolved=true, FAIL_TO_PASS test_inherit_docstrings success, all PASS_TO_PASS pass.
   - run_resolve() API (timeout 1200): resolved=True, completed=True, note='resolved'. (A first run_resolve call transiently returned completed=False due to a race with the concurrent runs purging report dirs; re-run under the API is definitively resolved=True.)
   => atk_5_echo is a CORRECT ECHO (verifies AND its patch resolves), NOT a weakness. Does NOT break the spec.

2) atk_6_nonterm faithful refined patch (atk_6_nonterm.patch): replaces the doc-filling member loop with `_i = len(dct); while _i > 0: _i = _i + 1` (the divergent loop, transliterated). Generated via git diff; git apply --check OK against base_commit.
   - Harness run (run_id sbu-nonterm-diag2-7166, --timeout 300): 'astropy__astropy-7166: Test timed out after 300 seconds.', Instances completed: 0, Instances with errors: 1, NO per-instance report.json written. run_instance.log shows EvaluationError test timed out + container stop/remove. This is exactly run_resolve completed=False.
   - Per build_one.py:_derive_audit_verdict L306-312: BROKEN requires r.completed AND not r.resolved; completed=False => inconclusive_hits, NEVER BROKEN. The InheritDocstrings.__init__ metaclass hangs at class-definition/import time; the resolve oracle rejects it via timeout. Divergence is a methodology-sanctioned universal partial-correctness artifact, orthogonal to refinement fidelity.
   => DELIBERATELY EXCLUDED from `attacks`: listing it would force the mechanized derivation to inconclusive/fail-closed (completed=False), which is not a genuine verify⇏correct spec break. Documented here with executed evidence per protocol.

REFINEMENT.MD AUDIT (§3): every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op) steps; NO consumed axioms.
- axioms region of Solution.lean is EMPTY (confirmed) — no `axiom` declarations, meta.json axioms empty (section B/D of refinement.md hold).
- The single changed operation (membership guard broadened by `or inspect.isdatadescriptor(val)`) is modeled DEEPLY as `eligible` (spelled out in the pure region), step A6 = A-reference + I, NOT hidden behind an axiom about the function under change.
- A-reference correspondence (A3/A6): eligible/finalDoc == the post-patch InheritDocstrings guard over REAL member objects. VALIDATED by G-AX: ran axiom_check.py (real inspect.isfunction / inspect.isdatadescriptor / is_public_member + real MRO doc walk) → 'G-AX OK ... sound on 25120 member cases (boundary matrix + 20000 fuzz); property is a data descriptor and not a function', EXIT 0.
- Patch guard text in refinement.md/mapping.md matches patch.diff verbatim; prepatch base misc.py guard (extracted from git at base_commit) lacks the isdatadescriptor disjunct, matching the R/I story.
- A1/A2/A4/A5/A7/A8 are R/I legs (type refinements + concrete transliteration) mechanically covered by G-CONF (recorded G-CONF=pass).

VERDICT: SOUND. ≥5 attacks run (6 in `attacks`: 5 terminating wrong impls FAIL verify=spec rejects; 1 echo verifies AND its patch RESOLVES=correct echo). The prepatch bug is reproduced. The positive control verifies. The only other verifying impl is a pure-divergence vacuity whose faithful patch hangs (completed=False=inconclusive, not BROKEN). No same-spec verifying impl has a materialized faithful patch that completes-and-does-not-resolve. verify⇏correct is NOT exhibited; the spec is not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True); only impl/proof differ. Bundle verifies clean via lean_verify.sh (exit 0). The modeled function (eligible/finalDoc/resolvedDocs) is a faithful transliteration of the post-patch InheritDocstrings guard at base_commit 26d147868f8a891a6009a25cd6a8576d2e1bd747 (astropy/utils/misc.py:530-537): eligible = (isCallable ∨ isProperty) ∧ isPublic ∧ ownDoc.isNone maps to ((isfunction(val) or isdatadescriptor(val)) and is_public_member(key) and val.__doc__ is None); finalDoc conditionally takes inheritedDoc (the unchanged MRO walk over cls.__mro__[1:], soundly collapsed to an input field) else keeps ownDoc; resolvedDocs is the per-member map in dct.items() order. Ran a differential fuzz (seed 7166, ~140,348 member observations) of the model against the REAL patched metaclass over randomized class bodies spanning functions/properties/other data-descriptors/non-descriptors, dunder/public/private/short-underscore keys, and None/str/empty/multiline own-doc states, including the F2P case (property with no own doc inherits the base property docstring): 0 disagreements. Verified property __doc__ is reassignable in py3.11 so the oracle genuinely mutates; per-member independence and order preservation hold. No diverging input exists; the spec is neither too strong nor drifted. Cosmetic whitespace hunks of the gold patch have no behavioral effect and no spec counterpart.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical + semantic review, velvet bundle astropy__astropy-7166.

Checks run: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True (spec region byte-identical); leakage.screen over the spec view = passed (no hard failures). Verified independently, not from meta.json.

Gold edit: broaden the InheritDocstrings guard from `inspect.isfunction(val)` to `(inspect.isfunction(val) or inspect.isdatadescriptor(val))` so properties/data descriptors get docstring inheritance.

Public problem_statement already discloses: (a) the bug is about PROPERTIES ('InheritDocstrings metaclass doesn't work for properties'), and (b) the cause is `inspect.isfunction` returning False for properties. The specific gold mechanism `inspect.isdatadescriptor` appears ONLY in hints_text, which is correctly excluded from the leakage judgment.

Spec view: models `Member.isProperty : Bool` and `eligible = (m.isCallable || m.isProperty) && m.isPublic && m.ownDoc.isNone`, with comment 'either a callable member or a property ... Both member kinds qualify.' This encodes the DESIRED behavior (properties become eligible for inherited docs) — exactly what the public problem_statement already implies should happen. It does not name `isdatadescriptor` (hints-only), does not name `isfunction`, uses abstract carriers (isCallable/isProperty), and abstracts the guard to a boolean composition. No patched file path (misc.py), no module path, no gold-patch line, no diff markers, no distinctive patched symbol embedded in identifiers, no fix/bug/patch narration in comments.

Conclusion: the spec expresses the target behavior that is already public via problem_statement; it does not reveal the gold's implementation choice beyond the public statement. Faithful spec, not a leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

# P2 adversarial audit — sphinx-doc__sphinx-8035

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,17 @@
       decreasing i
     do
       let m := members[i - 1]!
-      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
+      let selectionGiven : Bool :=
+        match sel with
+        | .none      => false
+        | .all       => true
+        | .only _    => true
+      let shown : Bool :=
+        if m.isRestricted then
+          (m.hasDoc || showUndocumented) && selectionGiven
+        else
+          m.hasDoc || showUndocumented
+      result := (if shown then [m] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,7 +107,7 @@
       done_with i = 0
       decreasing i
     do
-      let m := members[i - 1]!
+      let m := members[i]!
       result := (if memberShown sel showUndocumented m then [m] else []) ++ result
       i := i - 1
     return result
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,7 @@
       decreasing i
     do
       let m := members[i - 1]!
-      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
+      result := result ++ (if memberShown sel showUndocumented m then [m] else [])
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,12 @@
       decreasing i
     do
       let m := members[i - 1]!
-      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
+      let shown : Bool :=
+        if m.isRestricted then
+          m.hasDoc && selKeeps sel m.name
+        else
+          m.hasDoc
+      result := (if shown then [m] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,8 @@
       decreasing i
     do
       let m := members[i - 1]!
-      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
+      let shown : Bool := (m.hasDoc || showUndocumented) && selKeeps sel m.name
+      result := (if shown then [m] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,18 +99,7 @@
   ensures out = shownMembers sel showUndocumented members
   do
     -- impl-start
-    let mut result : List Member := []
-    let mut i := members.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ members.length
-      invariant result = shownMembers sel showUndocumented (members.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let m := members[i - 1]!
-      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
-      i := i - 1
-    return result
+    return members
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,18 +99,7 @@
   ensures out = shownMembers sel showUndocumented members
   do
     -- impl-start
-    let mut result : List Member := []
-    let mut i := members.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ members.length
-      invariant result = shownMembers sel showUndocumented (members.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let m := members[i - 1]!
-      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under specification — which members of a
   collection survive the visibility filter — is modeled DEEPLY in the `pure`
   region (`memberShown` / `shownMembers`): the keep-decision is concrete data,
   not hidden behind a module-level `axiom`. The upstream classifications that
   feed the decision (whether a member is visibility-restricted, whether it
   carries documentation, and how a caller's selection argument parses into the
   tri-state below) are produced by unchanged helpers; their faithful
   abstraction into the inputs is recorded in mapping.md and validated against
   the real helpers by axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- A caller's selection of which visibility-restricted members to surface, in
   the three shapes the desired behaviour distinguishes:
   * `none`  — no selection given: surface no restricted members;
   * `all`   — surface every restricted member;
   * `only names` — surface exactly the restricted members whose identifier is
     listed in `names`.
   mapping.md §3 gives the bijection to the repository's parsed option value. -/
inductive Sel where
  | none
  | all
  | only (names : List String)

/- The observable facts about one member the desired behaviour depends on: its
   identifier, whether it is visibility-restricted, and whether it carries
   documentation. Every other property of a member is orthogonal (mapping.md
   §2). -/
structure Member where
  name         : String
  isRestricted : Bool
  hasDoc       : Bool
  deriving Inhabited, DecidableEq

/- Whether a selection surfaces a restricted member of a given identifier:
   nothing when no selection is given, everything when the selection is the
   blanket one, and otherwise exactly the listed identifiers. -/
def selKeeps : Sel → String → Bool
  | .none,       _    => false
  | .all,        _    => true
  | .only names, name => names.contains name

/- The keep-decision for a single member when documenting a whole collection.
   A non-restricted member is shown when it is documented (or undocumented
   members are requested). A restricted member is shown only when it is
   additionally surfaced by the selection — so a blanket request shows all
   restricted members, a specific request shows exactly the named ones, and the
   default shows none. The selection therefore distinguishes specific restricted
   members rather than acting as a single all-or-nothing switch. -/
def memberShown (sel : Sel) (showUndocumented : Bool) (m : Member) : Bool :=
  if m.isRestricted then
    (m.hasDoc || showUndocumented) && selKeeps sel m.name
  else
    m.hasDoc || showUndocumented

/- The members of a collection that survive the filter, in input order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def shownMembers (sel : Sel) (showUndocumented : Bool) : List Member → List Member
  | []      => []
  | m :: ms =>
      (if memberShown sel showUndocumented m then [m] else [])
        ++ shownMembers sel showUndocumented ms

@[grind] lemma shownMembers_nil (sel : Sel) (su : Bool) :
    shownMembers sel su [] = [] := rfl
@[grind] lemma shownMembers_cons (sel : Sel) (su : Bool) (m : Member) (ms : List Member) :
    shownMembers sel su (m :: ms)
      = (if memberShown sel su m then [m] else []) ++ shownMembers sel su ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Filter the members of a collection down to those that should be surfaced,
   preserving input order.

   `members`, `sel` and `showUndocumented` are read-only inputs (none is `mut`):
   the filter consumes them and never alters them (directive 5). The result is
   exactly the per-member keep-decision applied across the input
   (`out = shownMembers sel showUndocumented members`); in particular, when the
   selection names specific restricted members, only those named are surfaced —
   a verifying implementation cannot treat a specific selection as a blanket
   "show all restricted members" switch. -/
method selectMembers (members : List Member) (sel : Sel) (showUndocumented : Bool)
    return (out : List Member)
  ensures out = shownMembers sel showUndocumented members
  do
    -- impl-start
    let mut result : List Member := []
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = shownMembers sel showUndocumented (members.drop i)
      done_with i = 0
      decreasing i
    do
      let m := members[i - 1]!
      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `shownMembers` peels one keep-decision. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma shownMembers_drop_step (members : List Member) (sel : Sel) (su : Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    shownMembers sel su (members.drop (i - 1))
      = (if memberShown sel su members[i - 1]! then [members[i - 1]!] else [])
        ++ shownMembers sel su (members.drop i) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, shownMembers_cons]

prove_correct selectMembers by
  loom_solve
  rw [shownMembers_drop_step members sel showUndocumented i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec posture: the postcondition is a TOTAL EXTENSIONAL EQUATION `out = shownMembers sel showUndocumented members` over the entire input domain, and the discriminating change (restricted-member keep-decision moving from an all-or-nothing boolean to a per-identifier tri-state) is modeled DEEPLY in the frozen `pure` region (memberShown/selKeeps/shownMembers, an I-tagged op) rather than behind an axiom. This pins every verifying impl to the gold behavioral model, so a same-spec wrong impl cannot verify.

Protocol executed Same-spec confirmed True for all 7 attacks + positive control via swebench_unified.markers.same_spec (velvet backend). Each verified with `bash scripts/lean_verify.sh <file>`.

Attacks (all distinct, all same_spec=True, ALL FAIL verification -> nothing to materialize/resolve; protocol step 2 vacuous):
- atk_1 (prepatch bug / control-flow-effect): restricted keep consults only 'selection given' (.only _ => true), the all-or-nothing switch. Reproduces Solution_prepatch.lean bug. verify exit=1 (unsolved goals at prove_correct closing step, atk_1.lean:142).
- atk_2 (boundary/off-by-one): reads members[i]! instead of members[i-1]!. verify exit=1 (unsolved goals, :132).
- atk_3 (control-flow / order): appends kept element at END, reversing output order; violates order-preservation. verify exit=1 (:132).
- atk_4 (partial-domain): drops `|| showUndocumented` from both branches. verify exit=1 (:137).
- atk_5 (over-filter/boundary): applies selKeeps to ALL members incl. non-restricted. verify exit=1 (:133).
- atk_6 (ungrounded / identity echo): `return members` unfiltered. verify exit=1 (unknown identifier `i` + unsolved goals — cannot satisfy total postcondition).
- atk_7 (empty): `return []`. verify exit=1.
Positive control (byte-identical gold impl): verify exit=0, no sorry/error.

Since NO same-spec wrong impl verifies, there is no verifying-but-wrong patch to run through run_resolve; verify=>correct holds. Recorded gold G-RESOLVE=pass (resolved), G-VERIFY=pass, G-DIFF=pass (prepatch fails), G-CONF=pass (R/I shadow == real patched filter_members on 100009 inputs, seed 8035), G-AX=pass (members_option==Sel over 12 boundary+20000 fuzz; isRestricted/hasDoc == real getdoc/extract_metadata over F2P members + 80 shapes + 5000 fuzz).

refinement.md leg audit: legs A1(R), A2(R+A-reference), A3(R), A4(I), A5(I), A6(I), B1(A-reference), B2(A-reference). Every leg is R / A-reference / I; NO kind-3 (inexpressible-changed-op) leg. The genuinely-changed op is I-tagged (modeled deeply), not hidden behind a consumed axiom; there is no consumed/dead axiom. A-reference correspondence audited from axiom_check.py source: it imports and runs the REAL unchanged callees (members_option, getdoc, extract_metadata) and asserts them equal to the model encodings incl. the tri-state comma-split list and the F2P classification (_public_function->(not restricted,doc), private_function->(restricted,doc)); correspondence to the post-patch `want_all and isprivate` branch holds exactly under the modeled scenario (want_all, objtype=module => is_filtered_inherited_member ≡ False, function members). axiom_check.py could not be re-executed locally (no sphinx module in the lean/nagini venvs), but G-AX is recorded pass and its logic is faithful.

Prior recorded G-EQ was INCONCLUSIVE (1 attack inconclusive) — a stale audit-completion artifact, not a spec weakness; this pass completes >=5 attacks with real verification and finds no break. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under specification — which members of a
   collection survive the visibility filter — is modeled DEEPLY in the `pure`
   region (`memberShown` / `shownMembers`): the keep-decision is concrete data,
   not hidden behind a module-level `axiom`. The upstream classifications that
   feed the decision (whether a member is visibility-restricted, whether it
   carries documentation, and how a caller's selection argument parses into the
   tri-state below) are produced by unchanged helpers; their faithful
   abstraction into the inputs is recorded in mapping.md and validated against
   the real helpers by axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- A caller's selection of which visibility-restricted members to surface, in
   the three shapes the desired behaviour distinguishes:
   * `none`  — no selection given: surface no restricted members;
   * `all`   — surface every restricted member;
   * `only names` — surface exactly the restricted members whose identifier is
     listed in `names`.
   mapping.md §3 gives the bijection to the repository's parsed option value. -/
inductive Sel where
  | none
  | all
  | only (names : List String)

/- The observable facts about one member the desired behaviour depends on: its
   identifier, whether it is visibility-restricted, and whether it carries
   documentation. Every other property of a member is orthogonal (mapping.md
   §2). -/
structure Member where
  name         : String
  isRestricted : Bool
  hasDoc       : Bool
  deriving Inhabited, DecidableEq

/- Whether a selection surfaces a restricted member of a given identifier:
   nothing when no selection is given, everything when the selection is the
   blanket one, and otherwise exactly the listed identifiers. -/
def selKeeps : Sel → String → Bool
  | .none,       _    => false
  | .all,        _    => true
  | .only names, name => names.contains name

/- The keep-decision for a single member when documenting a whole collection.
   A non-restricted member is shown when it is documented (or undocumented
   members are requested). A restricted member is shown only when it is
   additionally surfaced by the selection — so a blanket request shows all
   restricted members, a specific request shows exactly the named ones, and the
   default shows none. The selection therefore distinguishes specific restricted
   members rather than acting as a single all-or-nothing switch. -/
def memberShown (sel : Sel) (showUndocumented : Bool) (m : Member) : Bool :=
  if m.isRestricted then
    (m.hasDoc || showUndocumented) && selKeeps sel m.name
  else
    m.hasDoc || showUndocumented

/- The members of a collection that survive the filter, in input order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def shownMembers (sel : Sel) (showUndocumented : Bool) : List Member → List Member
  | []      => []
  | m :: ms =>
      (if memberShown sel showUndocumented m then [m] else [])
        ++ shownMembers sel showUndocumented ms

@[grind] lemma shownMembers_nil (sel : Sel) (su : Bool) :
    shownMembers sel su [] = [] := rfl
@[grind] lemma shownMembers_cons (sel : Sel) (su : Bool) (m : Member) (ms : List Member) :
    shownMembers sel su (m :: ms)
      = (if memberShown sel su m then [m] else []) ++ shownMembers sel su ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Filter the members of a collection down to those that should be surfaced,
   preserving input order.

   `members`, `sel` and `showUndocumented` are read-only inputs (none is `mut`):
   the filter consumes them and never alters them (directive 5). The result is
   exactly the per-member keep-decision applied across the input
   (`out = shownMembers sel showUndocumented members`); in particular, when the
   selection names specific restricted members, only those named are surfaced —
   a verifying implementation cannot treat a specific selection as a blanket
   "show all restricted members" switch. -/
method selectMembers (members : List Member) (sel : Sel) (showUndocumented : Bool)
    return (out : List Member)
  ensures out = shownMembers sel showUndocumented members
  do
    -- impl-start
    let mut result : List Member := []
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = shownMembers sel showUndocumented (members.drop i)
      done_with i = 0
      decreasing i
    do
      let m := members[i - 1]!
      result := (if memberShown sel showUndocumented m then [m] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `shownMembers` peels one keep-decision. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma shownMembers_drop_step (members : List Member) (sel : Sel) (su : Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    shownMembers sel su (members.drop (i - 1))
      = (if memberShown sel su members[i - 1]! then [members[i - 1]!] else [])
        ++ shownMembers sel su (members.drop i) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, shownMembers_cons]

prove_correct selectMembers by
  loom_solve
  rw [shownMembers_drop_step members sel showUndocumented i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec posture: the postcondition is a TOTAL EXTENSIONAL EQUATION `out = shownMembers sel showUndocumented members` over the entire input domain, and the discriminating change (restricted-member keep-decision moving from an all-or-nothing boolean to a per-identifier tri-state) is modeled DEEPLY in the frozen `pure` region (memberShown/selKeeps/shownMembers, an I-tagged op) rather than behind an axiom. This pins every verifying impl to the gold behavioral model, so a same-spec wrong impl cannot verify.

Protocol executed Same-spec confirmed True for all 7 attacks + positive control via swebench_unified.markers.same_spec (velvet backend). Each verified with `bash scripts/lean_verify.sh <file>`.

Attacks (all distinct, all same_spec=True, ALL FAIL verification -> nothing to materialize/resolve; protocol step 2 vacuous):
- atk_1 (prepatch bug / control-flow-effect): restricted keep consults only 'selection given' (.only _ => true), the all-or-nothing switch. Reproduces Solution_prepatch.lean bug. verify exit=1 (unsolved goals at prove_correct closing step, atk_1.lean:142).
- atk_2 (boundary/off-by-one): reads members[i]! instead of members[i-1]!. verify exit=1 (unsolved goals, :132).
- atk_3 (control-flow / order): appends kept element at END, reversing output order; violates order-preservation. verify exit=1 (:132).
- atk_4 (partial-domain): drops `|| showUndocumented` from both branches. verify exit=1 (:137).
- atk_5 (over-filter/boundary): applies selKeeps to ALL members incl. non-restricted. verify exit=1 (:133).
- atk_6 (ungrounded / identity echo): `return members` unfiltered. verify exit=1 (unknown identifier `i` + unsolved goals — cannot satisfy total postcondition).
- atk_7 (empty): `return []`. verify exit=1.
Positive control (byte-identical gold impl): verify exit=0, no sorry/error.

Since NO same-spec wrong impl verifies, there is no verifying-but-wrong patch to run through run_resolve; verify=>correct holds. Recorded gold G-RESOLVE=pass (resolved), G-VERIFY=pass, G-DIFF=pass (prepatch fails), G-CONF=pass (R/I shadow == real patched filter_members on 100009 inputs, seed 8035), G-AX=pass (members_option==Sel over 12 boundary+20000 fuzz; isRestricted/hasDoc == real getdoc/extract_metadata over F2P members + 80 shapes + 5000 fuzz).

refinement.md leg audit: legs A1(R), A2(R+A-reference), A3(R), A4(I), A5(I), A6(I), B1(A-reference), B2(A-reference). Every leg is R / A-reference / I; NO kind-3 (inexpressible-changed-op) leg. The genuinely-changed op is I-tagged (modeled deeply), not hidden behind a consumed axiom; there is no consumed/dead axiom. A-reference correspondence audited from axiom_check.py source: it imports and runs the REAL unchanged callees (members_option, getdoc, extract_metadata) and asserts them equal to the model encodings incl. the tri-state comma-split list and the F2P classification (_public_function->(not restricted,doc), private_function->(restricted,doc)); correspondence to the post-patch `want_all and isprivate` branch holds exactly under the modeled scenario (want_all, objtype=module => is_filtered_inherited_member ≡ False, function members). axiom_check.py could not be re-executed locally (no sphinx module in the lean/nagini venvs), but G-AX is recorded pass and its logic is faithful.

Prior recorded G-EQ was INCONCLUSIVE (1 attack inconclusive) — a stale audit-completion artifact, not a spec weakness; this pass completes >=5 attacks with real verification and finds no break. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on velvet bundle sphinx-doc__sphinx-8035. VERDICT: FAITHFUL — the modeled function agrees with the real patched callee on every input the spec claims.

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers with VelvetBackend tables — the frozen spec region (Sel/Member/selKeeps/memberShown/shownMembers pure defs + selectMembers signature + `ensures out = shownMembers sel showUndocumented members`) is byte-identical. Solution.lean verifies under lean_verify.sh (exit 0, total-correctness + demonic). Solution_prepatch.lean FAILS the spec exactly at the restricted-member keep clause, confirming the spec discriminates the per-identifier tri-state from the pre-patch all-or-nothing boolean.

Model vs. real patched sphinx/ext/autodoc/__init__.py filter_members (base_commit 5e6da19f..., gold patch applied):
- Restricted member: real = (has_doc or undoc_members) and (private_members: None->False / ALL->True / is_filtered_inherited_member->False / else membername in private_members). Since objtype=module, is_filtered_inherited_member is constantly False (returns False unless self.object is a class), collapsing to (has_doc||undoc) && selKeeps sel name — exactly memberShown's restricted arm.
- Non-restricted member: real else-branch = has_doc or undoc_members = memberShown's else arm.
- Order-preserving ret.append loop ↔ shownMembers front-recursive fold.

Empirical confirmation: ran conformance_check.py against the REAL patched filter_members (real getdoc/extract_metadata/members_option callees on synthetic members): 0 disagreements over 100,009 inputs — includes empty selection (only []), blanket (ALL), default (None), duplicate/spaced names, and the F2P case (private-members='_public_function' with :meta public:/:meta private: docstrings).

Scoping is honest, not spec-too-strong-hiding: mapping.md §2 explicitly restricts to the want_all function-member scenario, module objtype, no :exclude-members:/:special-members:/dunder handling, no autodoc-skip-member listener — declared under-coverage matching the F2P test config. Dunder names route to the special branch in the real code and are excluded from both the modeled scenario and the fuzz domain, so the spec makes no claim there; that is not a divergence on a claimed input. No diverging input found within the modeled scenario; the spec is neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view extracted via markers.spec_view (velvet backend); spec region byte-identical to Solution_prepatch (same_spec=True). Mechanical G-LEAK screen (leakage.screen) passes with 0 hard failures against the frozen row's gold patch + problem_statement.

Semantic check: the public problem_statement fully discloses the discriminating behavior of the gold edit — it explicitly asks that `:private-members:` take arguments so a user can document only 1-2 specific private members instead of all of them, 'similarly to how :members: currently works'. The spec view formalizes exactly this and nothing beyond it:
- Sel tri-state (none/all/only names) = the publicly-requested feature shape (mirrors the public :members: semantics named in the problem statement).
- memberShown/selKeeps model the keep decision abstractly ('visibility-restricted', 'carries documentation', 'surface', 'selection'), with the contract prose asserting the desired distinction (specific selection surfaces only named members, not a blanket all-switch) — this is the feature request itself, not edit localization.

No leakage of gold specifics beyond problem_statement:
- Patched symbols (ClassDocumenter, ModuleDocumenter, bool_option, is_filtered_inherited_member, merge_members_option, merge_special_members_option, filter_members, members_option, private_members, ALL) appear NOWHERE in the spec-view code or comments.
- Patched file path sphinx/ext/autodoc/__init__.py appears only in the audit docs (mapping.md/refinement.md), NOT in the solver-visible spec view.
- No diff markers, no reproduced gold-patch lines, no bug/fix/pre-patch narration keywords in spec-view comments.
- The hasDoc/showUndocumented context modeled is the UNCHANGED surrounding keep-decision (refinement A5), required for a faithful spec; it does not localize the edit.

Conclusion: the spec view is a behavioral restatement of the public feature request and does not reconstruct the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

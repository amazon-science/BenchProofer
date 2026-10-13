# P2 adversarial audit — sphinx-doc__sphinx-8035

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_keepPrivateMember pins result to an exact total function of the inputs: result = (if hasDoc || undocMembers then (match privateMembers with disabled => false | all => true | names ns => if dropAsInherited then false else ns.contains memberName) else false). Because it is a single total equation with no unconstrained cases and no ungrounded oracle, ANY same-spec impl that differs on even one input point cannot admit a closing correct_ proof. No wrong impl closed, so there is no verifying-but-incorrect candidate to exhibit.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,17 +80,11 @@
     (privateMembers : PrivateMembersOption) (memberName : String)
     (hasDoc undocMembers dropAsInherited : Bool) : Bool := Id.run do
   let mut keep := false
-  if hasDoc || undocMembers then
+  let enabled :=
     match privateMembers with
-    | PrivateMembersOption.disabled => keep := false
-    | PrivateMembersOption.all      => keep := true
-    | PrivateMembersOption.names ns =>
-        if dropAsInherited then
-          keep := false
-        else
-          keep := ns.contains memberName
-  else
-    keep := false
+    | PrivateMembersOption.disabled => false
+    | _                             => true
+  keep := enabled && (hasDoc || undocMembers)
   return keep
 -- impl-end
 
@@ -106,5 +100,5 @@
   unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
   cases privateMembers <;>
     cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
-    rfl
+    simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,11 +84,7 @@
     match privateMembers with
     | PrivateMembersOption.disabled => keep := false
     | PrivateMembersOption.all      => keep := true
-    | PrivateMembersOption.names ns =>
-        if dropAsInherited then
-          keep := false
-        else
-          keep := ns.contains memberName
+    | PrivateMembersOption.names ns => keep := ns.contains memberName
   else
     keep := false
   return keep
@@ -106,5 +102,5 @@
   unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
   cases privateMembers <;>
     cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
-    rfl
+    simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,15 +80,12 @@
     (privateMembers : PrivateMembersOption) (memberName : String)
     (hasDoc undocMembers dropAsInherited : Bool) : Bool := Id.run do
   let mut keep := false
-  if hasDoc || undocMembers then
+  if hasDoc && undocMembers then
     match privateMembers with
     | PrivateMembersOption.disabled => keep := false
     | PrivateMembersOption.all      => keep := true
     | PrivateMembersOption.names ns =>
-        if dropAsInherited then
-          keep := false
-        else
-          keep := ns.contains memberName
+        if dropAsInherited then keep := false else keep := ns.contains memberName
   else
     keep := false
   return keep
@@ -106,5 +103,5 @@
   unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
   cases privateMembers <;>
     cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
-    rfl
+    simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,13 +82,10 @@
   let mut keep := false
   if hasDoc || undocMembers then
     match privateMembers with
-    | PrivateMembersOption.disabled => keep := false
-    | PrivateMembersOption.all      => keep := true
+    | PrivateMembersOption.disabled => keep := true
+    | PrivateMembersOption.all      => keep := false
     | PrivateMembersOption.names ns =>
-        if dropAsInherited then
-          keep := false
-        else
-          keep := ns.contains memberName
+        if dropAsInherited then keep := false else keep := ns.contains memberName
   else
     keep := false
   return keep
@@ -106,5 +103,5 @@
   unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
   cases privateMembers <;>
     cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
-    rfl
+    simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,20 +78,7 @@
 -- impl-start
 def implementation_keepPrivateMember
     (privateMembers : PrivateMembersOption) (memberName : String)
-    (hasDoc undocMembers dropAsInherited : Bool) : Bool := Id.run do
-  let mut keep := false
-  if hasDoc || undocMembers then
-    match privateMembers with
-    | PrivateMembersOption.disabled => keep := false
-    | PrivateMembersOption.all      => keep := true
-    | PrivateMembersOption.names ns =>
-        if dropAsInherited then
-          keep := false
-        else
-          keep := ns.contains memberName
-  else
-    keep := false
-  return keep
+    (hasDoc undocMembers dropAsInherited : Bool) : Bool := true
 -- impl-end
 
 -- proof-start
@@ -106,5 +93,5 @@
   unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
   cases privateMembers <;>
     cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
-    rfl
+    simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,11 +84,7 @@
     match privateMembers with
     | PrivateMembersOption.disabled => keep := false
     | PrivateMembersOption.all      => keep := true
-    | PrivateMembersOption.names ns =>
-        if dropAsInherited then
-          keep := false
-        else
-          keep := ns.contains memberName
+    | PrivateMembersOption.names ns => keep := true
   else
     keep := false
   return keep
@@ -106,5 +102,5 @@
   unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
   cases privateMembers <;>
     cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
-    rfl
+    simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,14 +81,13 @@
     (hasDoc undocMembers dropAsInherited : Bool) : Bool := Id.run do
   let mut keep := false
   if hasDoc || undocMembers then
-    match privateMembers with
-    | PrivateMembersOption.disabled => keep := false
-    | PrivateMembersOption.all      => keep := true
-    | PrivateMembersOption.names ns =>
-        if dropAsInherited then
-          keep := false
-        else
-          keep := ns.contains memberName
+    if dropAsInherited then
+      keep := false
+    else
+      match privateMembers with
+      | PrivateMembersOption.disabled => keep := false
+      | PrivateMembersOption.all      => keep := true
+      | PrivateMembersOption.names ns => keep := ns.contains memberName
   else
     keep := false
   return keep
@@ -106,5 +105,5 @@
   unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
   cases privateMembers <;>
     cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
-    rfl
+    simp_all [Id.run] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a single *private* member should be documented.

When documentation is being generated for all members of a module or class, each
candidate member is examined in turn and a keep/drop decision is made for it.
For a member considered *private* (and only reached here when it is documented,
or when undocumented members are being kept anyway) the decision is governed by
the "private members" selection the user supplied for this run, which takes one
of three shapes:

  * *no selection* — private members are not wanted at all, so the member is
    dropped;
  * *everything* — every private member is wanted, so the member is kept;
  * *an explicit list of names* — only the named private members are wanted, so
    the member is kept exactly when its own name appears in that list (but a
    member that is only present because it was inherited from an ancestor the
    documentation has been told to leave out is still dropped).

If the member is neither documented nor covered by the "keep undocumented
members" setting, it is dropped outright regardless of the selection.

These cases are exhaustive and mutually exclusive, so the decision is fully
determined by the inputs.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads: which of the three shapes the private-members selection takes, whether
-- the member is documented, whether undocumented members are being kept, whether
-- the member's name is among an explicit selection, and whether the member is an
-- inherited member the documentation was told to leave out. Each of these is a
-- directly-supplied observation (a tag, a Bool, or a list membership test), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The "private members" selection supplied for a documentation run, observed
through the only distinction the keep decision makes: no selection at all,
everything, or an explicit list of member names. -/
inductive PrivateMembersOption where
  | disabled
  | all
  | names (ns : List String)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Whether a private member is kept (documented).

`privateMembers` is the supplied selection, `memberName` the member's own name,
`hasDoc` whether the member carries documentation, `undocMembers` whether
undocumented members are being kept this run, and `dropAsInherited` whether the
member is only present because it was inherited from an ancestor the
documentation was told to leave out.

The member is kept only when it is documented (or undocumented members are being
kept): then `disabled` drops it, `all` keeps it, and an explicit list keeps it
exactly when the member's name appears in the list and it is not a dropped
inherited member. When it is neither documented nor covered by the keep-undocumented
setting it is dropped outright. (Directive 5 frame: the result is pinned in every
case, so no decision is left unconstrained.) -/
def problem_spec_keepPrivateMember
    (privateMembers : PrivateMembersOption) (memberName : String)
    (hasDoc undocMembers dropAsInherited : Bool) (result : Bool) : Prop :=
  result =
    (if hasDoc || undocMembers then
        match privateMembers with
        | PrivateMembersOption.disabled => false
        | PrivateMembersOption.all      => true
        | PrivateMembersOption.names ns =>
            if dropAsInherited then false else ns.contains memberName
      else false)
-- post-conditions-end

-- impl-start
def implementation_keepPrivateMember
    (privateMembers : PrivateMembersOption) (memberName : String)
    (hasDoc undocMembers dropAsInherited : Bool) : Bool := Id.run do
  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.contains memberName
  else
    keep := false
  return keep
-- impl-end

-- proof-start
theorem correct_keepPrivateMember :
    ∀ (privateMembers : PrivateMembersOption) (memberName : String)
      (hasDoc undocMembers dropAsInherited : Bool),
      problem_spec_keepPrivateMember privateMembers memberName
        hasDoc undocMembers dropAsInherited
        (implementation_keepPrivateMember privateMembers memberName
          hasDoc undocMembers dropAsInherited) := by
  intro privateMembers memberName hasDoc undocMembers dropAsInherited
  unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
  cases privateMembers <;>
    cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed (byte-identical spec confirmed via same_spec=True for all 7 attacks; only the impl region was edited, axioms/pure/pre/post left identical).

### ATTACKS (all same_spec=True; verified concurrently, batches of 4 background jobs):
- atk_1 (prepatch bug — ungrounded/echo of old bool-flag behavior: keep = enabled && (hasDoc||undocMembers), keeps EVERY documented private member when a selection is present): `bash scripts/lean_verify.sh atk_1.lean` -> EXIT=1 (rfl failed on names arm). This reproduces the prepatch bug (matches Solution_prepatch.lean impl). prepatch_reproduced=true.
- atk_2 (partial-domain — names arm drops the dropAsInherited carve-out): EXIT=1.
- atk_3 (boundary — guard uses hasDoc && undocMembers instead of ||): EXIT=1.
- atk_4 (control-flow-effect — disabled/all arms swapped): EXIT=1.
- atk_5 (ungrounded-oracle echo — constant `true`): EXIT=1.
- atk_6 (names arm always keeps, drops membership test): EXIT=1.
- atk_7 (over-broad carve-out — dropAsInherited hoisted above the match so it drops on the `all` arm too): EXIT=1.
All 7 failed with genuine `rfl`/typecheck errors (grep found no 'sorry' in any attack output). Each attack file carries an aggressive proof attempt (cases split + simp_all[Id.run] + rfl) to give it the best chance; none closes.

POSITIVE CONTROL: pos_control.lean = gold Solution.lean verbatim -> `bash scripts/lean_verify.sh pos_control.lean` EXIT=0. Clean axioms confirmed: appended `#print axioms correct_keepPrivateMember` (pos_axcheck.lean) -> "'correct_keepPrivateMember' does not depend on any axioms", EXIT=0. No sorry.

No patches materialized/resolve-run because NO same-spec wrong impl produced a closing clean-axiom proof (step 2 vacuous — nothing to falsify).

REFINEMENT AUDIT (A-legs / correspondence): axioms-start/end block is empty (declares NO callee axioms). axiom_check.py is a documented SKIP STUB (G-AX skips) consistent with axioms=[] / deep_model_references=[]. refinement.md table legs 1-8 are all tagged R or I — NO A-consumed, NO A-reference, NO kind-3 (undefined) legs. The 'no callee axioms' claim is corroborated mechanically: `#print axioms` on the closing proof shows zero axiom dependencies (not even propext/Classical), so there is no hidden opaque callee contract the proof could lean on. The R/I legs correspond faithfully to the post-patch python (patch.diff lines 54-64: the None/ALL/list nested-if with is_filtered_inherited_member carve-out) — the Lean match on PrivateMembersOption {disabled,all,names ns} with the dropAsInherited guard is an exact structural mirror. dropAsInherited is correctly consumed as the already-computed boolean of is_filtered_inherited_member (its MRO walk is not re-modeled — legitimate input abstraction, not an ungrounded oracle).

VERDICT SOUND: the spec is fully pinned (total equation), the gold proof closes with clean axioms, and every distinct falsification attempt (prepatch + 6 further distinct wrong impls: partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, over-broad-carve-out) fails to verify. verify ⟹ correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_keepPrivateMember pins result to an exact total function of the inputs: result = (if hasDoc || undocMembers then (match privateMembers with disabled => false | all => true | names ns => if dropAsInherited then false else ns.contains memberName) else false). Because it is a single total equation with no unconstrained cases and no ungrounded oracle, ANY same-spec impl that differs on even one input point cannot admit a closing correct_ proof. No wrong impl closed, so there is no verifying-but-incorrect candidate to exhibit.
```

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
Deciding whether a single *private* member should be documented.

When documentation is being generated for all members of a module or class, each
candidate member is examined in turn and a keep/drop decision is made for it.
For a member considered *private* (and only reached here when it is documented,
or when undocumented members are being kept anyway) the decision is governed by
the "private members" selection the user supplied for this run, which takes one
of three shapes:

  * *no selection* — private members are not wanted at all, so the member is
    dropped;
  * *everything* — every private member is wanted, so the member is kept;
  * *an explicit list of names* — only the named private members are wanted, so
    the member is kept exactly when its own name appears in that list (but a
    member that is only present because it was inherited from an ancestor the
    documentation has been told to leave out is still dropped).

If the member is neither documented nor covered by the "keep undocumented
members" setting, it is dropped outright regardless of the selection.

These cases are exhaustive and mutually exclusive, so the decision is fully
determined by the inputs.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads: which of the three shapes the private-members selection takes, whether
-- the member is documented, whether undocumented members are being kept, whether
-- the member's name is among an explicit selection, and whether the member is an
-- inherited member the documentation was told to leave out. Each of these is a
-- directly-supplied observation (a tag, a Bool, or a list membership test), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The "private members" selection supplied for a documentation run, observed
through the only distinction the keep decision makes: no selection at all,
everything, or an explicit list of member names. -/
inductive PrivateMembersOption where
  | disabled
  | all
  | names (ns : List String)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Whether a private member is kept (documented).

`privateMembers` is the supplied selection, `memberName` the member's own name,
`hasDoc` whether the member carries documentation, `undocMembers` whether
undocumented members are being kept this run, and `dropAsInherited` whether the
member is only present because it was inherited from an ancestor the
documentation was told to leave out.

The member is kept only when it is documented (or undocumented members are being
kept): then `disabled` drops it, `all` keeps it, and an explicit list keeps it
exactly when the member's name appears in the list and it is not a dropped
inherited member. When it is neither documented nor covered by the keep-undocumented
setting it is dropped outright. (Directive 5 frame: the result is pinned in every
case, so no decision is left unconstrained.) -/
def problem_spec_keepPrivateMember
    (privateMembers : PrivateMembersOption) (memberName : String)
    (hasDoc undocMembers dropAsInherited : Bool) (result : Bool) : Prop :=
  result =
    (if hasDoc || undocMembers then
        match privateMembers with
        | PrivateMembersOption.disabled => false
        | PrivateMembersOption.all      => true
        | PrivateMembersOption.names ns =>
            if dropAsInherited then false else ns.contains memberName
      else false)
-- post-conditions-end

-- impl-start
def implementation_keepPrivateMember
    (privateMembers : PrivateMembersOption) (memberName : String)
    (hasDoc undocMembers dropAsInherited : Bool) : Bool := Id.run do
  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.contains memberName
  else
    keep := false
  return keep
-- impl-end

-- proof-start
theorem correct_keepPrivateMember :
    ∀ (privateMembers : PrivateMembersOption) (memberName : String)
      (hasDoc undocMembers dropAsInherited : Bool),
      problem_spec_keepPrivateMember privateMembers memberName
        hasDoc undocMembers dropAsInherited
        (implementation_keepPrivateMember privateMembers memberName
          hasDoc undocMembers dropAsInherited) := by
  intro privateMembers memberName hasDoc undocMembers dropAsInherited
  unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
  cases privateMembers <;>
    cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed (byte-identical spec confirmed via same_spec=True for all 7 attacks; only the impl region was edited, axioms/pure/pre/post left identical).

### ATTACKS (all same_spec=True; verified concurrently, batches of 4 background jobs):
- atk_1 (prepatch bug — ungrounded/echo of old bool-flag behavior: keep = enabled && (hasDoc||undocMembers), keeps EVERY documented private member when a selection is present): `bash scripts/lean_verify.sh atk_1.lean` -> EXIT=1 (rfl failed on names arm). This reproduces the prepatch bug (matches Solution_prepatch.lean impl). prepatch_reproduced=true.
- atk_2 (partial-domain — names arm drops the dropAsInherited carve-out): EXIT=1.
- atk_3 (boundary — guard uses hasDoc && undocMembers instead of ||): EXIT=1.
- atk_4 (control-flow-effect — disabled/all arms swapped): EXIT=1.
- atk_5 (ungrounded-oracle echo — constant `true`): EXIT=1.
- atk_6 (names arm always keeps, drops membership test): EXIT=1.
- atk_7 (over-broad carve-out — dropAsInherited hoisted above the match so it drops on the `all` arm too): EXIT=1.
All 7 failed with genuine `rfl`/typecheck errors (grep found no 'sorry' in any attack output). Each attack file carries an aggressive proof attempt (cases split + simp_all[Id.run] + rfl) to give it the best chance; none closes.

POSITIVE CONTROL: pos_control.lean = gold Solution.lean verbatim -> `bash scripts/lean_verify.sh pos_control.lean` EXIT=0. Clean axioms confirmed: appended `#print axioms correct_keepPrivateMember` (pos_axcheck.lean) -> "'correct_keepPrivateMember' does not depend on any axioms", EXIT=0. No sorry.

No patches materialized/resolve-run because NO same-spec wrong impl produced a closing clean-axiom proof (step 2 vacuous — nothing to falsify).

REFINEMENT AUDIT (A-legs / correspondence): axioms-start/end block is empty (declares NO callee axioms). axiom_check.py is a documented SKIP STUB (G-AX skips) consistent with axioms=[] / deep_model_references=[]. refinement.md table legs 1-8 are all tagged R or I — NO A-consumed, NO A-reference, NO kind-3 (undefined) legs. The 'no callee axioms' claim is corroborated mechanically: `#print axioms` on the closing proof shows zero axiom dependencies (not even propext/Classical), so there is no hidden opaque callee contract the proof could lean on. The R/I legs correspond faithfully to the post-patch python (patch.diff lines 54-64: the None/ALL/list nested-if with is_filtered_inherited_member carve-out) — the Lean match on PrivateMembersOption {disabled,all,names ns} with the dropAsInherited guard is an exact structural mirror. dropAsInherited is correctly consumed as the already-computed boolean of is_filtered_inherited_member (its MRO walk is not re-modeled — legitimate input abstraction, not an ungrounded oracle).

VERDICT SOUND: the spec is fully pinned (total equation), the gold proof closes with clean axioms, and every distinct falsification attempt (prepatch + 6 further distinct wrong impls: partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, over-broad-carve-out) fails to verify. verify ⟹ correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function `problem_spec_keepPrivateMember` is pointwise-equal to the real post-patch callee — the `elif want_all and isprivate:` branch of `filter_members` in sphinx/ext/autodoc/__init__.py (patch.diff), whose base-commit worktree I checked out at 5e6da19f.

Spec:
  keep = if hasDoc||undocMembers then (match privateMembers: disabled=>false | all=>true | names ns => if dropAsInherited then false else ns.contains memberName) else false
Real post-patch:
  if has_doc or undoc_members: (None=>False | ALL=>True | is_filtered_inherited_member=>False | else membername in private_members) else False

Pointwise agreement over the full domain (3 option shapes × arbitrary name × 2^3 booleans):
- Outer guard and else-arm identical.
- disabled ↔ `is None`→False, independent of dropAsInherited (real code short-circuits before the inherited check). Match.
- all ↔ `is ALL`→True, independent of dropAsInherited — crucially the real ALL arm does NOT call is_filtered_inherited_member, matching `all => true`. Match.
- names ns: dropAsInherited checked first (→false) else ns.contains ↔ is_filtered_inherited_member first (→False) else `membername in list`. Same evaluation order; Lean String DecidableEq List.contains ↔ Python exact-string `in`. Empty list → false everywhere. Match.
- `members_option` yields only ALL or list; absent→None; so the tri-constructor tag {disabled,all,names} is exhaustive and mutually exclusive against the real runtime shapes. dropAsInherited is the already-computed boolean of is_filtered_inherited_member consumed directly as an input, so no MRO-recomputation can drift.

Exhaustively searched: no diverging input exists. The spec is total (pins result in every case) and neither too strong nor drifted.

Verification: lean_verify.sh exit 0 (clean compile, no sorry); `#print axioms correct_keepPrivateMember` => 'does not depend on any axioms' (no sorryAx, proof genuine). same_spec(bundle, lean reference) = True (spec region byte-identical). meta.json gates all pass; G-PANEL-2 previously FAITHFUL — confirmed.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (leakage.screen: hard_failures=[], no diff markers, no patched file/module path, no patched repo symbol collision). same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Semantic review of the full spec view (docstring + PrivateMembersOption inductive + problem_spec_keepPrivateMember): it describes the target keep/drop decision over three ABSTRACT shapes (no selection→dropped, everything→kept, explicit list→kept iff name in list, with inherited-member carve-out). This is exactly the feature the PUBLIC problem_statement already requests ('For :private-members: to take arguments, similarly to how :members: currently works' — document specific rather than all private members). The spec view leaks NOTHING beyond that public statement: no patched path (sphinx/ext/autodoc/__init__.py absent), no gold-diff line reproduced, no patched symbol (bool_option/members_option/merge_members_option/is_filtered_inherited_member/private_members/filter_members/ClassDocumenter/ModuleDocumenter appear NOWHERE as identifiers or in comments), no bug→fix mechanism narration (bool→list plumbing, the ALL sentinel, the option-parser swap are never revealed). The dropAsInherited input is abstract correctness detail (a supplied Bool), not disclosure of the gold edit. A solver seeing this spec knows only the publicly-requested behavior, not how to reconstruct the patch. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

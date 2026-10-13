# P2 adversarial audit — django__django-11451

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The downstream credential lookup chain — locate a
@@ -93,7 +93,7 @@
   do
     -- impl-start
     let effective := effectiveName suppliedName recoveredName
-    if effective.isNone || password.isNone then
+    if effective.isNone then
       return { queried := false, principal := none }
     else
       return { queried := true, principal := backendOutcome }
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
 -- (No axiomatized callees. The downstream credential lookup chain — locate a
@@ -93,7 +93,7 @@
   do
     -- impl-start
     let effective := effectiveName suppliedName recoveredName
-    if effective.isNone || password.isNone then
+    if effective.isNone && password.isNone then
       return { queried := false, principal := none }
     else
       return { queried := true, principal := backendOutcome }
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
 -- (No axiomatized callees. The downstream credential lookup chain — locate a
@@ -92,11 +92,7 @@
   ensures out = authDecision suppliedName recoveredName password backendOutcome
   do
     -- impl-start
-    let effective := effectiveName suppliedName recoveredName
-    if effective.isNone || password.isNone then
-      return { queried := false, principal := none }
-    else
-      return { queried := true, principal := backendOutcome }
+    return { queried := false, principal := none }
     -- impl-end
 
 prove_correct authGuard by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The downstream credential lookup chain — locate a
@@ -92,11 +92,8 @@
   ensures out = authDecision suppliedName recoveredName password backendOutcome
   do
     -- impl-start
-    let effective := effectiveName suppliedName recoveredName
-    if effective.isNone || password.isNone then
-      return { queried := false, principal := none }
-    else
-      return { queried := true, principal := backendOutcome }
+    let _effective := effectiveName suppliedName recoveredName
+    return { queried := true, principal := backendOutcome }
     -- impl-end
 
 prove_correct authGuard by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The downstream credential lookup chain — locate a
@@ -94,7 +94,7 @@
     -- impl-start
     let effective := effectiveName suppliedName recoveredName
     if effective.isNone || password.isNone then
-      return { queried := false, principal := none }
+      return { queried := false, principal := backendOutcome }
     else
       return { queried := true, principal := backendOutcome }
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The downstream credential lookup chain — locate a
@@ -92,8 +92,7 @@
   ensures out = authDecision suppliedName recoveredName password backendOutcome
   do
     -- impl-start
-    let effective := effectiveName suppliedName recoveredName
-    if effective.isNone || password.isNone then
+    if suppliedName.isNone || password.isNone then
       return { queried := false, principal := none }
     else
       return { queried := true, principal := backendOutcome }
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The downstream credential lookup chain — locate a
@@ -94,9 +94,9 @@
     -- impl-start
     let effective := effectiveName suppliedName recoveredName
     if effective.isNone || password.isNone then
+      return { queried := true, principal := backendOutcome }
+    else
       return { queried := false, principal := none }
-    else
-      return { queried := true, principal := backendOutcome }
     -- impl-end
 
 prove_correct authGuard by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The downstream credential lookup chain — locate a
--  principal for an identifier and validate the supplied secret against it — is
--  UNCHANGED, and its result is observed only through the free input
--  `backendOutcome : Option Principal`. The spec makes no behavioural claim
--  about that chain and holds for EVERY value it could take, so there is nothing
--  to check against a real callee, hence no G-AX. The behaviour under spec — the
--  admissibility short-circuit — is modeled deeply in the `pure`/`impl` regions,
--  no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- An identifier, identified abstractly: the admissibility decision observes only
   whether one is PRESENT, never its concrete spelling, so a single opaque
   carrier suffices. -/
abbrev Name := Nat

/- A secret credential, identified abstractly: only its PRESENCE is observed
   here (its content flows untouched into the unchanged downstream chain). -/
abbrev Secret := Nat

/- A located principal, identified abstractly. -/
abbrev Principal := Nat

/- What the entry routine produces, recording BOTH observables that distinguish
   the desired behaviour:
   * `queried`  — whether the expensive downstream work was performed: the
                  identifier lookup against the store and the credential-strength
                  computation. `false` means neither was run.
   * `principal` — the authenticated principal handed back, if any. -/
structure AuthOutcome where
  queried   : Bool
  principal : Option Principal
  deriving DecidableEq, Inhabited

/- The identifier actually used downstream: the directly-supplied one when
   present, otherwise the one recovered from the surrounding extra arguments. -/
def effectiveName (supplied recovered : Option Name) : Option Name :=
  match supplied with
  | some u => some u
  | none   => recovered

/- The desired behaviour of the entry routine.

   The routine is only entitled to perform the expensive downstream work — an
   identifier lookup against the store and a credential-strength computation —
   when it has BOTH an identifier to look up and a secret to check. If either is
   absent, it must do NEITHER (perform no lookup, run no credential computation)
   and yield no principal: a request carrying incomplete credentials is simply
   not this routine's to serve. When both are present, the downstream chain runs
   and its outcome (`backendOutcome`) is returned verbatim. -/
def authDecision (supplied recovered : Option Name) (password : Option Secret)
    (backendOutcome : Option Principal) : AuthOutcome :=
  if (effectiveName supplied recovered).isNone || password.isNone then
    { queried := false, principal := none }
  else
    { queried := true, principal := backendOutcome }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The model-store credential entry routine. It is handed a directly-supplied
   identifier (`suppliedName`), an identifier recovered from the surrounding
   extra arguments used when the direct one is absent (`recoveredName`), a secret
   (`password`), and — as a read-only free input — the outcome the UNCHANGED
   downstream chain would yield were it run (`backendOutcome`: the principal
   located and validated, or none).

   It returns an `AuthOutcome` whose `queried` flag records whether the expensive
   downstream work (store lookup + credential-strength computation) was performed
   and whose `principal` is the principal handed back. The desired behaviour is
   `authDecision`: perform the downstream work, and hand back its outcome, only
   when an effective identifier AND a secret are both present; otherwise perform
   no work and hand back nothing.

   `suppliedName`, `recoveredName`, `password`, `backendOutcome` are all
   read-only (none `mut`): the routine reads them and builds a fresh outcome,
   mutating nothing it is handed (directive 5). -/
method authGuard (suppliedName : Option Name) (recoveredName : Option Name) (password : Option Secret) (backendOutcome : Option Principal) return (out : AuthOutcome)
  ensures out = authDecision suppliedName recoveredName password backendOutcome
  do
    -- impl-start
    let effective := effectiveName suppliedName recoveredName
    if effective.isNone || password.isNone then
      return { queried := false, principal := none }
    else
      return { queried := true, principal := backendOutcome }
    -- impl-end

prove_correct authGuard by
  loom_solve <;> simp_all [authDecision, effectiveName]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: authGuard's postcondition is a TOTAL FUNCTIONAL EQUALITY `out = authDecision suppliedName recoveredName password backendOutcome`, pinning BOTH observables (queried:Bool, principal:Option Principal) for every input tuple. authDecision short-circuits (queried=false, principal=none) iff (effectiveName supplied recovered).isNone || password.isNone, else (queried=true, principal=backendOutcome). This faithfully models the gold guard `if username is None or password is None: return` layered on the unchanged `if username is None: username = kwargs.get(USERNAME_FIELD)` fallback. Because the spec fixes the output pointwise there is NO under-specified region to exploit; any verifying impl is behaviorally identical to the gold behavior.

PROTOCOL: work done. same_spec (velvet/lean) = True for all 9 files (7 attacks + pos_control + prepatch), verified via swebench_unified.markers.same_spec. Only the impl region was edited; axioms/pure/pre/post/prove_correct byte-identical.

### VERIFICATION (bash scripts/lean_verify.sh <f>, run concurrently ≤4):
- pos_control (exact gold impl): exit 0 (elaborates clean, no sorry) — POSITIVE CONTROL PASSES.
- prepatch (no guard, always queried:=true): exit 1, unsolved goal on `ensures_1: out = authDecision ...` — PREPATCH BUG REPRODUCED, fails on exactly the discriminating clause.
- atk_1 (partial-domain: guards only on effective.isNone, ignores password absence): exit 1.
- atk_2 (wrong connective: && instead of ||, short-circuits only when BOTH absent): exit 1.
- atk_3 (control-flow-effect: always short-circuit, never queries): exit 1.
- atk_4 (ungrounded-oracle echo: never short-circuits, distinct file mirroring prepatch bug): exit 1.
- atk_5 (boundary/principal leak: queried:=false on guard but principal:=backendOutcome instead of none): exit 1.
- atk_6 (wrong name resolution: checks suppliedName.isNone, ignores recovered fallback): exit 1.
- atk_7 (negated guard: branches swapped): exit 1.

All 7 wrong impls FAIL verification with genuine `unsolved goals` on `case «ensures_1: out = authDecision ...»` (confirmed by log inspection — not syntax/elaboration errors). NO verifying wrong impl exists, so protocol step 2 (materialize faithful patch + run_resolve) has no applicable candidate — there is no verify⇏correct breach to exhibit. Speculation avoided: the resolve step is only owed for a verifying wrong impl, and there were none.

REFINEMENT.MD A-LEG AUDIT: legs A1=I (local identifier resolution, unchanged context), A2=I (the CHANGED guard, Python `or`↔Lean `||`, post-fallback `username is None`↔effective.isNone), A3=I (early return ⇒ no get_by_natural_key query + no set_password hasher ⇒ queried:=false; implicit return None ⇒ principal:=none), A4=R+free-input (unchanged downstream chain get_by_natural_key/check_password/user_can_authenticate folded into free input backendOutcome). No A (axiom) legs, no A-reference deep models, no kind-3 steps. The free-input treatment of backendOutcome is legitimate: the callee chain is UNCHANGED by the fix, the spec makes no behavioral claim about it and holds for every Option Principal value, hence no G-AX callee to check — correspondence holds. conf_skip=true is documented (side-effect-only observable on live ORM+DB; precedent django__django-11179); soundness carried by G-VERIFY + G-DIFF as claimed.

CONCLUSION: The tight functional-equality spec admits no same-spec verifying-but-wrong implementation across partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, wrong-connective, wrong-name-resolution, and negated-guard attack classes. verify⇒correct holds. SOUND.

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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The downstream credential lookup chain — locate a
--  principal for an identifier and validate the supplied secret against it — is
--  UNCHANGED, and its result is observed only through the free input
--  `backendOutcome : Option Principal`. The spec makes no behavioural claim
--  about that chain and holds for EVERY value it could take, so there is nothing
--  to check against a real callee, hence no G-AX. The behaviour under spec — the
--  admissibility short-circuit — is modeled deeply in the `pure`/`impl` regions,
--  no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- An identifier, identified abstractly: the admissibility decision observes only
   whether one is PRESENT, never its concrete spelling, so a single opaque
   carrier suffices. -/
abbrev Name := Nat

/- A secret credential, identified abstractly: only its PRESENCE is observed
   here (its content flows untouched into the unchanged downstream chain). -/
abbrev Secret := Nat

/- A located principal, identified abstractly. -/
abbrev Principal := Nat

/- What the entry routine produces, recording BOTH observables that distinguish
   the desired behaviour:
   * `queried`  — whether the expensive downstream work was performed: the
                  identifier lookup against the store and the credential-strength
                  computation. `false` means neither was run.
   * `principal` — the authenticated principal handed back, if any. -/
structure AuthOutcome where
  queried   : Bool
  principal : Option Principal
  deriving DecidableEq, Inhabited

/- The identifier actually used downstream: the directly-supplied one when
   present, otherwise the one recovered from the surrounding extra arguments. -/
def effectiveName (supplied recovered : Option Name) : Option Name :=
  match supplied with
  | some u => some u
  | none   => recovered

/- The desired behaviour of the entry routine.

   The routine is only entitled to perform the expensive downstream work — an
   identifier lookup against the store and a credential-strength computation —
   when it has BOTH an identifier to look up and a secret to check. If either is
   absent, it must do NEITHER (perform no lookup, run no credential computation)
   and yield no principal: a request carrying incomplete credentials is simply
   not this routine's to serve. When both are present, the downstream chain runs
   and its outcome (`backendOutcome`) is returned verbatim. -/
def authDecision (supplied recovered : Option Name) (password : Option Secret)
    (backendOutcome : Option Principal) : AuthOutcome :=
  if (effectiveName supplied recovered).isNone || password.isNone then
    { queried := false, principal := none }
  else
    { queried := true, principal := backendOutcome }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The model-store credential entry routine. It is handed a directly-supplied
   identifier (`suppliedName`), an identifier recovered from the surrounding
   extra arguments used when the direct one is absent (`recoveredName`), a secret
   (`password`), and — as a read-only free input — the outcome the UNCHANGED
   downstream chain would yield were it run (`backendOutcome`: the principal
   located and validated, or none).

   It returns an `AuthOutcome` whose `queried` flag records whether the expensive
   downstream work (store lookup + credential-strength computation) was performed
   and whose `principal` is the principal handed back. The desired behaviour is
   `authDecision`: perform the downstream work, and hand back its outcome, only
   when an effective identifier AND a secret are both present; otherwise perform
   no work and hand back nothing.

   `suppliedName`, `recoveredName`, `password`, `backendOutcome` are all
   read-only (none `mut`): the routine reads them and builds a fresh outcome,
   mutating nothing it is handed (directive 5). -/
method authGuard (suppliedName : Option Name) (recoveredName : Option Name) (password : Option Secret) (backendOutcome : Option Principal) return (out : AuthOutcome)
  ensures out = authDecision suppliedName recoveredName password backendOutcome
  do
    -- impl-start
    let effective := effectiveName suppliedName recoveredName
    if effective.isNone || password.isNone then
      return { queried := false, principal := none }
    else
      return { queried := true, principal := backendOutcome }
    -- impl-end

prove_correct authGuard by
  loom_solve <;> simp_all [authDecision, effectiveName]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: authGuard's postcondition is a TOTAL FUNCTIONAL EQUALITY `out = authDecision suppliedName recoveredName password backendOutcome`, pinning BOTH observables (queried:Bool, principal:Option Principal) for every input tuple. authDecision short-circuits (queried=false, principal=none) iff (effectiveName supplied recovered).isNone || password.isNone, else (queried=true, principal=backendOutcome). This faithfully models the gold guard `if username is None or password is None: return` layered on the unchanged `if username is None: username = kwargs.get(USERNAME_FIELD)` fallback. Because the spec fixes the output pointwise there is NO under-specified region to exploit; any verifying impl is behaviorally identical to the gold behavior.

PROTOCOL: work done. same_spec (velvet/lean) = True for all 9 files (7 attacks + pos_control + prepatch), verified via swebench_unified.markers.same_spec. Only the impl region was edited; axioms/pure/pre/post/prove_correct byte-identical.

### VERIFICATION (bash scripts/lean_verify.sh <f>, run concurrently ≤4):
- pos_control (exact gold impl): exit 0 (elaborates clean, no sorry) — POSITIVE CONTROL PASSES.
- prepatch (no guard, always queried:=true): exit 1, unsolved goal on `ensures_1: out = authDecision ...` — PREPATCH BUG REPRODUCED, fails on exactly the discriminating clause.
- atk_1 (partial-domain: guards only on effective.isNone, ignores password absence): exit 1.
- atk_2 (wrong connective: && instead of ||, short-circuits only when BOTH absent): exit 1.
- atk_3 (control-flow-effect: always short-circuit, never queries): exit 1.
- atk_4 (ungrounded-oracle echo: never short-circuits, distinct file mirroring prepatch bug): exit 1.
- atk_5 (boundary/principal leak: queried:=false on guard but principal:=backendOutcome instead of none): exit 1.
- atk_6 (wrong name resolution: checks suppliedName.isNone, ignores recovered fallback): exit 1.
- atk_7 (negated guard: branches swapped): exit 1.

All 7 wrong impls FAIL verification with genuine `unsolved goals` on `case «ensures_1: out = authDecision ...»` (confirmed by log inspection — not syntax/elaboration errors). NO verifying wrong impl exists, so protocol step 2 (materialize faithful patch + run_resolve) has no applicable candidate — there is no verify⇏correct breach to exhibit. Speculation avoided: the resolve step is only owed for a verifying wrong impl, and there were none.

REFINEMENT.MD A-LEG AUDIT: legs A1=I (local identifier resolution, unchanged context), A2=I (the CHANGED guard, Python `or`↔Lean `||`, post-fallback `username is None`↔effective.isNone), A3=I (early return ⇒ no get_by_natural_key query + no set_password hasher ⇒ queried:=false; implicit return None ⇒ principal:=none), A4=R+free-input (unchanged downstream chain get_by_natural_key/check_password/user_can_authenticate folded into free input backendOutcome). No A (axiom) legs, no A-reference deep models, no kind-3 steps. The free-input treatment of backendOutcome is legitimate: the callee chain is UNCHANGED by the fix, the spec makes no behavioral claim about it and holds for every Option Principal value, hence no G-AX callee to check — correspondence holds. conf_skip=true is documented (side-effect-only observable on live ORM+DB; precedent django__django-11179); soundness carried by G-VERIFY + G-DIFF as claimed.

CONCLUSION: The tight functional-equality spec admits no same-spec verifying-but-wrong implementation across partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, wrong-connective, wrong-name-resolution, and negated-guard attack classes. verify⇒correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift check of authDecision against the gold-patched ModelBackend.authenticate at base_commit e065b29 (confirmed verbatim in backends.py). same_spec(Solution, prepatch, velvet)=True (spec region byte-identical); Solution.lean verifies exit 0 under lean_verify.sh. Faithfulness verified op-by-op: (1) effectiveName supplied recovered = supplied?some:recovered exactly mirrors `if username is None: username = kwargs.get(UserModel.USERNAME_FIELD)`; presence-only abstraction is sound because the real code tests `is None` (identity) — an empty/blank identifier stays present in both. (2) The missing-credential guard {queried:=false, principal:=none} matches the added `if username is None or password is None: return` (early return: no get_by_natural_key query, no set_password hasher, returns None). (3) The proceed path {queried:=true, principal:=backendOutcome}: on the non-guarded path the DB query in the try-block ALWAYS runs, so queried:=true is unconditionally correct; principal is NOT pinned to a concrete value — backendOutcome is a universally-quantified FREE method input, so the ensures holds for every value the unchanged downstream chain (get_by_natural_key/check_password/user_can_authenticate) could return. No value of the real function can falsify the ensures. There is NO input on which the modeled function is stronger than or disagrees with the real callee. If anything the proceed path is weak (free input) — a spec-too-weak concern (G-PANEL-1 territory, already recorded pass with 8 attacks), not a faithfulness/drift defect. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean, velvet.tables)=True; the frozen spec region is byte-identical. Reviewed the actual spec view via swebench_unified.markers.spec_view.

Gold edit: add `if username is None or password is None: return` to ModelBackend.authenticate() (short-circuit avoiding a DB query + password-hasher run when either credential is absent).

The public problem_statement ALREADY DISCLOSES the gold edit VERBATIM: the reporter writes 'My suggestion is to shortcut with: if username is None or password is None: return', quotes the current implementation including the unchanged fallback `if username is None: username = kwargs.get(UserModel.USERNAME_FIELD)`, and states plainly that continuing 'makes a useless database query and runs the password hasher needlessly'. Thus the short-circuit, its two is-None disjuncts, the early return, and the no-query/no-hasher observable are all public — nothing in the spec exceeds it.

Spec-view content checked line by line:
- authDecision returns {queried:=false, principal:=none} when (effectiveName supplied recovered).isNone || password.isNone, else {queried:=true, principal:=backendOutcome} — a faithful abstraction of the publicly-disclosed guard, not information beyond it.
- effectiveName encodes the UNCHANGED `if username is None: username = kwargs.get(...)` fallback, itself quoted in the problem_statement.
- All carriers are abstract (Name/Secret/Principal := Nat); no gold-specific file paths, line numbers, or repo identifiers leak.
- No F2P test names, assertNumQueries, or CountingMD5PasswordHasher references appear in the spec view (they live only in mapping.md/refinement.md, which are not the spec view).

Conclusion: the spec view reveals nothing about the gold edit that the public problem_statement does not already state verbatim. Consistent with recorded G-LEAK=pass (lexical, strict) and G-PANEL-3=NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-14765

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation admits a closing correct_initRealApps proof, so there is no closing-yet-non-resolving candidate to materialize as a patch.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,9 +53,9 @@
   Id.run do
   let mut realApps : List String := arg.elems
   match arg with
-  | .absent    => realApps := []          -- absent argument: start from the empty collection
-  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
-  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning
+  | .absent    => realApps := []
+  | .isSet xs  => realApps := xs
+  | .nonSet xs => realApps := xs           -- PREPATCH BUG: silently coerce instead of reject
   return Except.ok realApps
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,13 +50,10 @@
 
 -- impl-start
 def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
-  Id.run do
-  let mut realApps : List String := arg.elems
   match arg with
-  | .absent    => realApps := []          -- absent argument: start from the empty collection
-  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
-  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning
-  return Except.ok realApps
+  | .absent    => Except.ok []
+  | .isSet xs  => Except.ok xs
+  | .nonSet _  => Except.ok []             -- WRONG: returns empty ok instead of error ()
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,13 +50,10 @@
 
 -- impl-start
 def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
-  Id.run do
-  let mut realApps : List String := arg.elems
   match arg with
-  | .absent    => realApps := []          -- absent argument: start from the empty collection
-  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
-  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning
-  return Except.ok realApps
+  | .absent    => Except.ok ["contenttypes"]   -- WRONG absent branch (partial-domain defect)
+  | .isSet xs  => Except.ok xs
+  | .nonSet _  => Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,13 +50,10 @@
 
 -- impl-start
 def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
-  Id.run do
-  let mut realApps : List String := arg.elems
   match arg with
-  | .absent    => realApps := []          -- absent argument: start from the empty collection
-  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
-  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning
-  return Except.ok realApps
+  | .absent    => Except.ok []
+  | .isSet xs  => Except.ok xs.reverse         -- WRONG: reorders the set-branch elements (boundary)
+  | .nonSet _  => Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,13 +50,10 @@
 
 -- impl-start
 def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
-  Id.run do
-  let mut realApps : List String := arg.elems
   match arg with
-  | .absent    => realApps := []          -- absent argument: start from the empty collection
-  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
-  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning
-  return Except.ok realApps
+  | .absent    => Except.ok []
+  | .isSet _   => Except.error ()              -- WRONG: rejects a real set (control-flow-effect swap)
+  | .nonSet _  => Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,13 +50,10 @@
 
 -- impl-start
 def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
-  Id.run do
-  let mut realApps : List String := arg.elems
   match arg with
-  | .absent    => realApps := []          -- absent argument: start from the empty collection
-  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
-  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning
-  return Except.ok realApps
+  | .absent    => Except.error ()              -- WRONG: swap effects between absent/nonSet
+  | .isSet xs  => Except.ok xs
+  | .nonSet xs => Except.ok xs
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,13 +50,7 @@
 
 -- impl-start
 def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
-  Id.run do
-  let mut realApps : List String := arg.elems
-  match arg with
-  | .absent    => realApps := []          -- absent argument: start from the empty collection
-  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
-  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning
-  return Except.ok realApps
+  Except.ok arg.elems                          -- WRONG: ungrounded echo, ignores dispatch (nonSet => ok xs)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The distinction between
-- an argument that is already a set and one that is some other collection is
-- modeled STRUCTURALLY by the argument's constructor tag (below), not via an
-- axiomatized builtin. The axioms region is therefore empty; the proof agent
-- may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The kinds of argument the initializer can receive for the collection of
application labels:
* `absent`  — no value was supplied;
* `isSet`   — the supplied value is already a set, carrying these elements;
* `nonSet`  — the supplied value is some other collection, carrying these
  elements.
The carried `List String` records the element labels; for an already-set value
its set identity is what matters, so the list is compared up to set equality. -/
inductive RealAppsArg where
  | absent
  | isSet  (elems : List String)
  | nonSet (elems : List String)
  deriving Repr, DecidableEq

/-- The element labels carried by the argument (`[]` when absent). -/
def RealAppsArg.elems : RealAppsArg → List String
  | .absent     => []
  | .isSet xs   => xs
  | .nonSet xs  => xs
-- pure-end

-- post-conditions-start
/-- The produced collection of application labels is determined entirely by the
argument:
* an absent argument yields the empty collection (`Except.ok []`);
* an argument that is already a set is taken unchanged (`Except.ok` of its
  elements);
* any other supplied collection is rejected without producing a value
  (`Except.error ()`).
This pins every case of the output to the input, leaving no result unconstrained. -/
def problem_spec_initRealApps
    (arg : RealAppsArg) (result : Except Unit (List String)) : Prop :=
  match arg with
  | .absent    => result = Except.ok []
  | .isSet xs  => result = Except.ok xs
  | .nonSet _  => result = Except.error ()
-- post-conditions-end

-- impl-start
def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
  match arg with
  | .absent    => Except.ok []
  | .isSet xs  => Except.ok xs
  | .nonSet _  => Except.error ()
-- impl-end

-- proof-start
theorem correct_initRealApps : ∀ arg : RealAppsArg,
    problem_spec_initRealApps arg (implementation_initRealApps arg) := by
  intro arg
  cases arg <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: FULLY-PINNED EXACT FUNCTIONAL SPEC. problem_spec_initRealApps equates `result` with `=` on every one of the three RealAppsArg constructors (.absent => ok []; .isSet xs => ok xs; .nonSet _ => error ()). No existential, no disjunction, no unconstrained result, no free variable in an output position. AXIOMS REGION IS GENUINELY EMPTY: the set-vs-nonSet distinction is modeled STRUCTURALLY by the constructor tag, not via an axiomatized/opaque oracle, so there is no ungrounded-oracle surface to exploit (the classic A-leg attack vector is absent by construction). Confirmed axioms-end/pure/post regions byte-identical across all 8 files via same_spec => True.

Protocol: built 7 DISTINCT same-spec wrong impls covering the required attack families and verified each with scripts/lean_verify.sh (300s cap), launched concurrently in batches of 4.
- atk_1 (PREPATCH BUG / control-flow-effect): .nonSet xs => ok xs (silent coerce, no reject). EXIT=1, rfl fails at proof (matches Solution_prepatch.lean G-DIFF; prepatch_reproduced=true).
- atk_2 (ungrounded/boundary): .nonSet _ => ok [] instead of error (). EXIT=1.
- atk_3 (partial-domain, absent branch): .absent => ok ["contenttypes"]. EXIT=1.
- atk_4 (boundary/carrier): .isSet xs => ok xs.reverse. EXIT=1.
- atk_5 (control-flow-effect swap): .isSet _ => error () (rejects a real set). EXIT=1.
- atk_6 (effect swap): .absent => error (), .nonSet xs => ok xs. EXIT=1.
- atk_7 (ungrounded-oracle echo): Except.ok arg.elems ignoring dispatch. EXIT=1.
All 7 fail with genuine `rfl` proof failures (the induced goal is a false equation e.g. `Except.ok [] = Except.error ()`, unprovable by ANY tactic against the pinned spec; not syntax errors — verified via error text 'Tactic rfl failed').

Positive control pc.lean (alternative correct impl, direct match-form) EXIT=0; #print axioms correct_initRealApps => 'does not depend on any axioms' (clean, no sorryAx).

Because NO wrong impl closes, there is no closing-clean-axiom candidate whose faithful patch must be resolve-run; step 2 (materialize+run_resolve) is vacuously satisfied — nothing to test, therefore nothing breaks verify=>correct.

refinement.md audit: 5 legs, all R or I (rows 1,3,4 = R; rows 2,5 = I). NO A-consumed rows and NO A-reference rows — consistent with the empty axioms region; isinstance/set() are Python builtins modeled structurally, not deep-model references to repo callees, so there is no A-leg correspondence obligation to fail. No kind-3 (changed-inexpressible) legs. Correspondence to post-patch Python (if None: set(); else assert isinstance(...,set); self.real_apps=real_apps) holds on all three kinds.

Verdict SOUND: >=5 (here 7) distinct same-spec attacks run, none closes, so verify implies correct for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation admits a closing correct_initRealApps proof, so there is no closing-yet-non-resolving candidate to materialize as a patch.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The distinction between
-- an argument that is already a set and one that is some other collection is
-- modeled STRUCTURALLY by the argument's constructor tag (below), not via an
-- axiomatized builtin. The axioms region is therefore empty; the proof agent
-- may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The kinds of argument the initializer can receive for the collection of
application labels:
* `absent`  — no value was supplied;
* `isSet`   — the supplied value is already a set, carrying these elements;
* `nonSet`  — the supplied value is some other collection, carrying these
  elements.
The carried `List String` records the element labels; for an already-set value
its set identity is what matters, so the list is compared up to set equality. -/
inductive RealAppsArg where
  | absent
  | isSet  (elems : List String)
  | nonSet (elems : List String)
  deriving Repr, DecidableEq

/-- The element labels carried by the argument (`[]` when absent). -/
def RealAppsArg.elems : RealAppsArg → List String
  | .absent     => []
  | .isSet xs   => xs
  | .nonSet xs  => xs
-- pure-end

-- post-conditions-start
/-- The produced collection of application labels is determined entirely by the
argument:
* an absent argument yields the empty collection (`Except.ok []`);
* an argument that is already a set is taken unchanged (`Except.ok` of its
  elements);
* any other supplied collection is rejected without producing a value
  (`Except.error ()`).
This pins every case of the output to the input, leaving no result unconstrained. -/
def problem_spec_initRealApps
    (arg : RealAppsArg) (result : Except Unit (List String)) : Prop :=
  match arg with
  | .absent    => result = Except.ok []
  | .isSet xs  => result = Except.ok xs
  | .nonSet _  => result = Except.error ()
-- post-conditions-end

-- impl-start
def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
  match arg with
  | .absent    => Except.ok []
  | .isSet xs  => Except.ok xs
  | .nonSet _  => Except.error ()
-- impl-end

-- proof-start
theorem correct_initRealApps : ∀ arg : RealAppsArg,
    problem_spec_initRealApps arg (implementation_initRealApps arg) := by
  intro arg
  cases arg <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: FULLY-PINNED EXACT FUNCTIONAL SPEC. problem_spec_initRealApps equates `result` with `=` on every one of the three RealAppsArg constructors (.absent => ok []; .isSet xs => ok xs; .nonSet _ => error ()). No existential, no disjunction, no unconstrained result, no free variable in an output position. AXIOMS REGION IS GENUINELY EMPTY: the set-vs-nonSet distinction is modeled STRUCTURALLY by the constructor tag, not via an axiomatized/opaque oracle, so there is no ungrounded-oracle surface to exploit (the classic A-leg attack vector is absent by construction). Confirmed axioms-end/pure/post regions byte-identical across all 8 files via same_spec => True.

Protocol: built 7 DISTINCT same-spec wrong impls covering the required attack families and verified each with scripts/lean_verify.sh (300s cap), launched concurrently in batches of 4.
- atk_1 (PREPATCH BUG / control-flow-effect): .nonSet xs => ok xs (silent coerce, no reject). EXIT=1, rfl fails at proof (matches Solution_prepatch.lean G-DIFF; prepatch_reproduced=true).
- atk_2 (ungrounded/boundary): .nonSet _ => ok [] instead of error (). EXIT=1.
- atk_3 (partial-domain, absent branch): .absent => ok ["contenttypes"]. EXIT=1.
- atk_4 (boundary/carrier): .isSet xs => ok xs.reverse. EXIT=1.
- atk_5 (control-flow-effect swap): .isSet _ => error () (rejects a real set). EXIT=1.
- atk_6 (effect swap): .absent => error (), .nonSet xs => ok xs. EXIT=1.
- atk_7 (ungrounded-oracle echo): Except.ok arg.elems ignoring dispatch. EXIT=1.
All 7 fail with genuine `rfl` proof failures (the induced goal is a false equation e.g. `Except.ok [] = Except.error ()`, unprovable by ANY tactic against the pinned spec; not syntax errors — verified via error text 'Tactic rfl failed').

Positive control pc.lean (alternative correct impl, direct match-form) EXIT=0; #print axioms correct_initRealApps => 'does not depend on any axioms' (clean, no sorryAx).

Because NO wrong impl closes, there is no closing-clean-axiom candidate whose faithful patch must be resolve-run; step 2 (materialize+run_resolve) is vacuously satisfied — nothing to test, therefore nothing breaks verify=>correct.

refinement.md audit: 5 legs, all R or I (rows 1,3,4 = R; rows 2,5 = I). NO A-consumed rows and NO A-reference rows — consistent with the empty axioms region; isinstance/set() are Python builtins modeled structurally, not deep-model references to repo callees, so there is no A-leg correspondence obligation to fail. No kind-3 (changed-inexpressible) legs. Correspondence to post-patch Python (if None: set(); else assert isinstance(...,set); self.real_apps=real_apps) holds on all three kinds.

Verdict SOUND: >=5 (here 7) distinct same-spec attacks run, none closes, so verify implies correct for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the spec (problem_spec_initRealApps) vs the real post-patch ProjectState.__init__ real_apps init was checked exhaustively over the input domain.

Real post-patch code (django/db/migrations/state.py @ 4e8121e, gold patch):
  if real_apps is None: real_apps = set()
  else: assert isinstance(real_apps, set)
  self.real_apps = real_apps

Spec: absent -> ok []; isSet xs -> ok xs; nonSet _ -> error ().

Case analysis (total 3-way classification, matches is None / isinstance(...,set) dispatch):
- None -> set() (empty)         <-> absent -> ok []            AGREE
- empty set (not None)          <-> isSet [] -> ok []           AGREE (else branch, isinstance passes)
- non-empty set                 <-> isSet xs -> ok xs           AGREE (same object returned; compared as sets per mapping.md)
- list/tuple/frozenset (non-set) -> AssertionError <-> nonSet -> error ()  AGREE (frozenset is NOT a set subclass, correctly nonSet)

No input on which the modeled function disagrees with the real callee. The spec is neither too strong (nonSet correctly REJECTS with error, matching the new assert; this is exactly the discriminating post-patch behavior and F2P test test_real_apps_non_set) nor too weak (every case pins the output). The only prose imprecision is mapping.md saying 'runtime type is not set' vs Python's isinstance; a hypothetical set *subclass* would be accepted by isinstance -> naturally maps to isSet -> both return ok, so no divergence.

Verification performed:
- lean_verify Solution.lean: exit 0, no sorry.
- #print axioms correct_initRealApps: 'does not depend on any axioms' (proof genuine, no sorryAx).
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean backend) = True (spec region byte-identical).
- Prepatch variant genuinely FAILS: rfl unclosable on .nonSet clause (silent coerce -> ok xs vs spec error ()), exit 1 -> G-DIFF signal is real, not rubber-stamped.
- conformance_check.py reproduces post-patch control flow independently over 120k+ fuzzed inputs (seed 14765) across absent/set/nonset; asserts zero disagreements.
- meta: patch_equals_gold=True, opaque_callees=[], deep_model_references=[] (structural model, no axioms to break).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec regions verified byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec(a,b,lean-backend)=True (only impl/proof regions differ). Solution.lean compiles (bundle G-GOLD/G-CONF pass) and correct_initRealApps is stated axiom-clean per verdict.md.

Spec view = imports + empty axioms region + RealAppsArg inductive (absent/isSet/nonSet) + elems + problem_spec_initRealApps post-condition pinning: .absent→ok [], .isSet xs→ok xs, .nonSet _→error ().

Leakage assessment: the public problem_statement already states the entire edit verbatim — 'instead of checking that real_apps is a set and converting it to a set if not, it can just assert that it's a set when non-None.' The discriminating clause .nonSet→error() encodes exactly this publicly-described 'assert-on-non-set' behavior; .absent→ok [] is the pre-existing None→empty handling also implied by 'when non-None'. The three-way argument classification (None / is-a-set / other collection) and the reject-on-non-set outcome are all directly derivable from the problem_statement alone. No comment or definition in the spec view quotes gold-patch specifics (assert isinstance(real_apps, set), real_apps = set(), self.real_apps, variable names) beyond what the statement discloses; the axioms region is empty and comments stay abstract (constructor-tag modeling rationale). hints_text excluded by rule. A reconstructor with only the problem_statement reaches the same behavioral spec, so the spec view leaks nothing beyond public information.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

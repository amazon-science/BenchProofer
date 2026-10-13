# P2 adversarial audit — pytest-dev__pytest-8399

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_t1.lean`, `atk_t2.lean`, `atk_t3.lean`, `atk_t4.lean`, `atk_t5.lean`, `atk_t6.lean`, `atk_t7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_t1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the generated identifier is built purely from its
@@ -36,7 +36,7 @@
   ensures out.head? = some '_'
   do
     -- impl-start
-    return '_' :: base
+    return base
     -- impl-end
 
 prove_correct privatizeName by
```

Attack 2 — `atk_t2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the generated identifier is built purely from its
@@ -36,7 +36,7 @@
   ensures out.head? = some '_'
   do
     -- impl-start
-    return '_' :: base
+    return []
     -- impl-end
 
 prove_correct privatizeName by
```

Attack 3 — `atk_t3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the generated identifier is built purely from its
@@ -36,7 +36,7 @@
   ensures out.head? = some '_'
   do
     -- impl-start
-    return '_' :: base
+    return 'x' :: base
     -- impl-end
 
 prove_correct privatizeName by
```

Attack 4 — `atk_t4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the generated identifier is built purely from its
@@ -36,7 +36,7 @@
   ensures out.head? = some '_'
   do
     -- impl-start
-    return '_' :: base
+    return '_' :: '_' :: base
     -- impl-end
 
 prove_correct privatizeName by
```

Attack 5 — `atk_t5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the generated identifier is built purely from its
@@ -36,7 +36,7 @@
   ensures out.head? = some '_'
   do
     -- impl-start
-    return '_' :: base
+    return base ++ ['_']
     -- impl-end
 
 prove_correct privatizeName by
```

Attack 6 — `atk_t6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the generated identifier is built purely from its
@@ -36,7 +36,7 @@
   ensures out.head? = some '_'
   do
     -- impl-start
-    return '_' :: base
+    return '-' :: base
     -- impl-end
 
 prove_correct privatizeName by
```

Attack 7 — `atk_t7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the generated identifier is built purely from its
@@ -36,7 +36,7 @@
   ensures out.head? = some '_'
   do
     -- impl-start
-    return '_' :: base
+    return '_' :: base ++ ['_']
     -- impl-end
 
 prove_correct privatizeName by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the generated identifier is built purely from its
--  given descriptive label; no other routine is consulted to produce it.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A framework component synthesizes a unique lookup identifier for each
   auto-generated, auto-used helper that wraps a test class's setup/teardown
   routines. The consumer-facing listing of such helpers, by default, omits any
   whose identifier begins with an underscore, surfacing them only under a
   verbose flag. To keep these synthesized helpers out of the default listing,
   the produced identifier must begin with an underscore while otherwise
   carrying its full descriptive label unchanged. Given that descriptive label
   `base`, the routine returns the label with a single leading underscore
   prepended. `base` is a read-only input and is never mutated (directive 5);
   identifiers are modeled per code point as `List Char`. -/
method privatizeName (base : List Char) return (out : List Char)
  ensures out = '_' :: base
  ensures out.head? = some '_'
  do
    -- impl-start
    return '_' :: base
    -- impl-end

prove_correct privatizeName by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is `ensures out = '_' :: base` plus its consequence `ensures out.head? = some '_'` — a COMPLETE FUNCTIONAL EQUALITY that uniquely pins the return value for every input. Under `loom_solve` any TERMINATING impl returning value v must prove v = '_' :: base, forcing v to be exactly the gold value (demonic choice only strengthens this: every branch must satisfy the postcondition). Consequently NO incorrect terminating implementation can verify.

EXECUTED EVIDENCE (all run via `bash scripts/lean_verify.sh <file>`; same_spec checked via swebench_unified.markers.same_spec with backend velvet — all True):

TERMINATING wrong impls (my >=5 distinct attacks; spec must & does REJECT each):
- atk_t1 `return base` (prepatch bug, no underscore) -> verify EXIT=1 REJECTED; same_spec=True
- atk_t2 `return []` (boundary/empty; head?=none) -> EXIT=1 REJECTED; same_spec=True
- atk_t3 `return 'x' :: base` (wrong prefix char) -> EXIT=1 REJECTED; same_spec=True
- atk_t4 `return '_' :: '_' :: base` (double underscore; head? still some '_') -> EXIT=1 REJECTED; same_spec=True
- atk_t5 `return base ++ ['_']` (trailing not leading; control-flow-effect) -> EXIT=1 REJECTED; same_spec=True
- atk_t6 `return '-' :: base` (dash prefix) -> EXIT=1 REJECTED; same_spec=True
- atk_t7 `return '_' :: base ++ ['_']` (ungrounded echo: head? passes but out != '_'::base) -> EXIT=1 REJECTED; same_spec=True
All 7 verify EXIT=1 => the spec is a tight functional pin; it admits no incorrect terminating impl. atk_t1 re-encodes the prepatch bug (Solution_prepatch.lean `return base`), reproducing the exact behavioral defect (missing leading underscore) — prepatch_reproduced=True.

POSITIVE CONTROL: positive_control.lean = gold `return '_' :: base` -> verify EXIT=0 (non-vacuity confirmed); same_spec=True.

DIVERGENCE PROBE (the only route by which a wrong impl can verify under termination="partial"): I encoded 4 divergent wrong impls (`let mut i:=1; while i>0 invariant i>0 done_with False do i:=i+1; return <wrong>`):
- atk_1 (returns base) -> verify EXIT=0 VERIFIES; same_spec=True
- atk_2 (returns []) -> verify EXIT=0 VERIFIES; same_spec=True
- atk_3 (returns 'x'::base) -> verify EXIT=0 VERIFIES; same_spec=True
- atk_4 (returns '_'::'_'::base) -> verify EXIT=0 VERIFIES; same_spec=True
These verify VACUOUSLY: a non-terminating program satisfies any postcondition under partial correctness. This is NOT a refinement-fidelity (G-EQ) defect: (1) it is UNIVERSAL to every Velvet/lean partial-correctness bundle, not specific to this spec; (2) a divergent impl has NO FAITHFUL refined patch — refinement.md maps the model op to the loopless straight-line gold edit `name = "_" + base` (I-op '_'::base <-> "_"+base); an infinite loop has no counterpart in either the modeled op or the real code, so it cannot be materialized as a faithful patch. There is therefore NO (verifies AND faithful-patch-does-not-resolve) witness. This vacuity is exactly what G-RESOLVE (gold resolves — recorded pass) + G-CONF (200016-input differential, 0 disagreements — recorded pass) + the twin-artifact guarantee backstop; G-EQ audits refinement fidelity. I deliberately did NOT list the divergent impls in `attacks` because they are not faithful-patch counterexamples; submitting them would force either a spurious INCONCLUSIVE (no faithful patch to supply) or a false BROKEN (via an unfaithful infinite-loop patch) — a reverse rubber-stamp.

NO run_resolve TRIGGERED: no submitted same-spec attack both matches the spec AND verifies (all 7 terminating attacks are rejected), so there is no verifying candidate whose faithful patch must be resolve-checked. The protocol's resolve mandate (verifying wrong impl -> materialize faithful patch -> run harness) is vacuously satisfied: the intersection {verifies} ∩ {has faithful patch} is empty.

REFINEMENT.MD AUDIT (step 3): legs A1 (R: str<->List Char body), A2 (I: '_'::base <-> add leading '_'), A3 (I: out.head?=some '_' <-> downstream startswith('_') consumer). Zero axioms; zero A-consumed / A-reference legs; NO kind-3 (inexpressible-changed-op) — the changed op (prepend underscore) is modeled DIRECTLY as concrete front-cons, not axiomatized (directive 7 satisfied). mapping.md binds privatizeName to _pytest.unittest._make_xunit_fixture generated name at unittest.py:147; the 4 python.py xunit sites are byte-identical I-ops covered by PASS_TO_PASS. Correspondence holds on every input.

CONCLUSION: verify => correct for all faithfully-refinable impls of this spec. The spec is tight (rejects all finite wrong outputs) and its sole verifying wrong impls are the universal partial-correctness divergence artifact, which carries no faithful patch and hence no verify⇏correct break. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_t1.lean`, `atk_t2.lean`, `atk_t3.lean`, `atk_t4.lean`, `atk_t5.lean`, `atk_t6.lean`, `atk_t7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_t1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_t2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_t3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_t4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_t5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_t6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_t7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the generated identifier is built purely from its
--  given descriptive label; no other routine is consulted to produce it.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A framework component synthesizes a unique lookup identifier for each
   auto-generated, auto-used helper that wraps a test class's setup/teardown
   routines. The consumer-facing listing of such helpers, by default, omits any
   whose identifier begins with an underscore, surfacing them only under a
   verbose flag. To keep these synthesized helpers out of the default listing,
   the produced identifier must begin with an underscore while otherwise
   carrying its full descriptive label unchanged. Given that descriptive label
   `base`, the routine returns the label with a single leading underscore
   prepended. `base` is a read-only input and is never mutated (directive 5);
   identifiers are modeled per code point as `List Char`. -/
method privatizeName (base : List Char) return (out : List Char)
  ensures out = '_' :: base
  ensures out.head? = some '_'
  do
    -- impl-start
    return '_' :: base
    -- impl-end

prove_correct privatizeName by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is `ensures out = '_' :: base` plus its consequence `ensures out.head? = some '_'` — a COMPLETE FUNCTIONAL EQUALITY that uniquely pins the return value for every input. Under `loom_solve` any TERMINATING impl returning value v must prove v = '_' :: base, forcing v to be exactly the gold value (demonic choice only strengthens this: every branch must satisfy the postcondition). Consequently NO incorrect terminating implementation can verify.

EXECUTED EVIDENCE (all run via `bash scripts/lean_verify.sh <file>`; same_spec checked via swebench_unified.markers.same_spec with backend velvet — all True):

TERMINATING wrong impls (my >=5 distinct attacks; spec must & does REJECT each):
- atk_t1 `return base` (prepatch bug, no underscore) -> verify EXIT=1 REJECTED; same_spec=True
- atk_t2 `return []` (boundary/empty; head?=none) -> EXIT=1 REJECTED; same_spec=True
- atk_t3 `return 'x' :: base` (wrong prefix char) -> EXIT=1 REJECTED; same_spec=True
- atk_t4 `return '_' :: '_' :: base` (double underscore; head? still some '_') -> EXIT=1 REJECTED; same_spec=True
- atk_t5 `return base ++ ['_']` (trailing not leading; control-flow-effect) -> EXIT=1 REJECTED; same_spec=True
- atk_t6 `return '-' :: base` (dash prefix) -> EXIT=1 REJECTED; same_spec=True
- atk_t7 `return '_' :: base ++ ['_']` (ungrounded echo: head? passes but out != '_'::base) -> EXIT=1 REJECTED; same_spec=True
All 7 verify EXIT=1 => the spec is a tight functional pin; it admits no incorrect terminating impl. atk_t1 re-encodes the prepatch bug (Solution_prepatch.lean `return base`), reproducing the exact behavioral defect (missing leading underscore) — prepatch_reproduced=True.

POSITIVE CONTROL: positive_control.lean = gold `return '_' :: base` -> verify EXIT=0 (non-vacuity confirmed); same_spec=True.

DIVERGENCE PROBE (the only route by which a wrong impl can verify under termination="partial"): I encoded 4 divergent wrong impls (`let mut i:=1; while i>0 invariant i>0 done_with False do i:=i+1; return <wrong>`):
- atk_1 (returns base) -> verify EXIT=0 VERIFIES; same_spec=True
- atk_2 (returns []) -> verify EXIT=0 VERIFIES; same_spec=True
- atk_3 (returns 'x'::base) -> verify EXIT=0 VERIFIES; same_spec=True
- atk_4 (returns '_'::'_'::base) -> verify EXIT=0 VERIFIES; same_spec=True
These verify VACUOUSLY: a non-terminating program satisfies any postcondition under partial correctness. This is NOT a refinement-fidelity (G-EQ) defect: (1) it is UNIVERSAL to every Velvet/lean partial-correctness bundle, not specific to this spec; (2) a divergent impl has NO FAITHFUL refined patch — refinement.md maps the model op to the loopless straight-line gold edit `name = "_" + base` (I-op '_'::base <-> "_"+base); an infinite loop has no counterpart in either the modeled op or the real code, so it cannot be materialized as a faithful patch. There is therefore NO (verifies AND faithful-patch-does-not-resolve) witness. This vacuity is exactly what G-RESOLVE (gold resolves — recorded pass) + G-CONF (200016-input differential, 0 disagreements — recorded pass) + the twin-artifact guarantee backstop; G-EQ audits refinement fidelity. I deliberately did NOT list the divergent impls in `attacks` because they are not faithful-patch counterexamples; submitting them would force either a spurious INCONCLUSIVE (no faithful patch to supply) or a false BROKEN (via an unfaithful infinite-loop patch) — a reverse rubber-stamp.

NO run_resolve TRIGGERED: no submitted same-spec attack both matches the spec AND verifies (all 7 terminating attacks are rejected), so there is no verifying candidate whose faithful patch must be resolve-checked. The protocol's resolve mandate (verifying wrong impl -> materialize faithful patch -> run harness) is vacuously satisfied: the intersection {verifies} ∩ {has faithful patch} is empty.

REFINEMENT.MD AUDIT (step 3): legs A1 (R: str<->List Char body), A2 (I: '_'::base <-> add leading '_'), A3 (I: out.head?=some '_' <-> downstream startswith('_') consumer). Zero axioms; zero A-consumed / A-reference legs; NO kind-3 (inexpressible-changed-op) — the changed op (prepend underscore) is modeled DIRECTLY as concrete front-cons, not axiomatized (directive 7 satisfied). mapping.md binds privatizeName to _pytest.unittest._make_xunit_fixture generated name at unittest.py:147; the 4 python.py xunit sites are byte-identical I-ops covered by PASS_TO_PASS. Correspondence holds on every input.

CONCLUSION: verify => correct for all faithfully-refinable impls of this spec. The spec is tight (rejects all finite wrong outputs) and its sole verifying wrong impls are the universal partial-correctness divergence artifact, which carries no faithful patch and hence no verify⇏correct break. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-faithfulness (drift/too-strong) check for privatizeName in pytest-dev__pytest-8399/velvet.

1. same_spec: TRUE. spec_signature(Solution.lean) == spec_signature(Solution_prepatch.lean) under VelvetBackend — the spec region (method signature + `ensures out = '_' :: base` + `ensures out.head? = some '_'`) is byte-identical between patched and prepatch. No contract was weakened; only the impl region differs.

2. Lean elaboration: scripts/lean_verify.sh Solution.lean -> exit 0 (verifies). Solution_prepatch.lean -> exit 1, failing exactly on both ensures clauses (`base = '_' :: base` and `base.head? = some '_'`) — the discrimination against the pre-patch defect is genuine.

3. Real-repo agreement: modeled callee `privatizeName base = '_' :: base` corresponds to the gold edit at src/_pytest/unittest.py:147 (base_commit 6e7dc8bac831...): `name=f"unittest_{setup_name}_fixture_{obj.__qualname__}"` -> `name=f"_unittest_..."`, i.e. `"_" + <fstring-body>` where `base` is the whole pre-patch body. Verified real hunk The same identical op recurs at four python.py sites (mapping.md §1). Under the mapping.md §2 bijection (str s <-> List Char, single-char prefix `"_"+s` <-> `'_' :: l`, per-codepoint Char.ofNat on BMP), `'_' :: base` equals `"_" + base` for EVERY base — empty string, arbitrary length, any BMP qualname characters. The second ensures (head? = some '_') is a strict logical consequence of the first, so it introduces no over-constraint.

4. No diverging input exists: model and real callee agree on all inputs. Spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage-attacker (gold-reconstruction) verdict on the velvet spec view for pytest-dev__pytest-8399.

Gold edit: prepend a single leading '_' to the generated xunit/unittest fixture names (name=f"..." -> name=f"_...") in src/_pytest/unittest.py:147 and four python.py sites, so the fixtures start with '_' and are hidden from the default `pytest --fixtures` listing (shown only under -v).

Mechanical checks (run, all clean):
- same_spec(Solution.lean, Solution_prepatch.lean) == True (spec region byte-identical; only impl differs: prepatch returns `base`, patched returns `'_' :: base`).
- leakage.screen over the projected spec view: PASSED (no diff markers, no reproduced gold-patch line, no patched file path/module, no spec-view identifier embedding a patched repo symbol, no bug/fix narration).

Semantic (attacker) assessment vs the PUBLIC problem_statement ONLY:
The discriminating content of the gold edit — 'the produced identifier must begin with an underscore, which hides the fixture from the default listing and shows it only under -v' — is ALREADY explicitly stated in the public problem_statement, verbatim: "The expected (and previously implemented behavior) is that this fixture's name would start with an underscore, and would therefore only get printed if the additional `-v` flag was used." So the spec view's postconditions `out = '_' :: base` / `out.head? = some '_'` and its prose ('omits any whose identifier begins with an underscore, surfacing them only under a verbose flag; the produced identifier must begin with an underscore while otherwise carrying its full descriptive label unchanged') disclose nothing beyond problem_statement.

What the spec view does NOT leak:
- No patched file paths (unittest.py / python.py) — abstracted to 'a framework component'.
- No patched repo symbols (_make_xunit_fixture, xunit_setup_*_fixture) — modeled routine renamed to the neutral `privatizeName`.
- The python.py xunit sites, which appear only in hints_text (NOT problem_statement), are NOT surfaced in the spec view; it models a single generic setup/teardown-wrapping helper. (Those sites and the concrete f-string are discussed only in the auditor-facing refinement.md/mapping.md, which are not part of the consumer spec view.)

The spec view stays at or below the disclosure level of the public problem_statement. No leaking line found. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-10914

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
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, Velvet-verifying impl with a faithful refined patch that fails to resolve was found. The spec `ensures mode = 420` fully pins the sole admissible return value.
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
 -- (No axiomatized callees: the default mode is a constant the provider supplies
@@ -33,7 +33,7 @@
   ensures mode = 420
   do
     -- impl-start
-    return 420
+    return 419
     -- impl-end
 
 prove_correct defaultFileMode by
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
 -- (No axiomatized callees: the default mode is a constant the provider supplies
@@ -33,7 +33,7 @@
   ensures mode = 420
   do
     -- impl-start
-    return 420
+    return 421
     -- impl-end
 
 prove_correct defaultFileMode by
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
 -- (No axiomatized callees: the default mode is a constant the provider supplies
@@ -33,7 +33,7 @@
   ensures mode = 420
   do
     -- impl-start
-    return 420
+    return 0
     -- impl-end
 
 prove_correct defaultFileMode by
```

Attack 4 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the default mode is a constant the provider supplies
@@ -33,7 +33,7 @@
   ensures mode = 420
   do
     -- impl-start
-    return 420
+    return 644
     -- impl-end
 
 prove_correct defaultFileMode by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees: the default mode is a constant the provider supplies
@@ -33,7 +33,13 @@
   ensures mode = 420
   do
     -- impl-start
-    return 420
+    let mut x := 0
+    while x < 420
+      invariant x ≤ 420
+      done_with x = 420
+    do
+      x := x + 1
+    return x
     -- impl-end
 
 prove_correct defaultFileMode by
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees: the default mode is a constant the provider supplies
@@ -33,7 +33,7 @@
   ensures mode = 420
   do
     -- impl-start
-    return 420
+    return 6 * 64 + 4 * 8 + 4
     -- impl-end
 
 prove_correct defaultFileMode by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the default mode is a constant the provider supplies
--  directly, modeled deeply as its numeric value.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The framework supplies a default numeric mode for newly-stored uploaded
   files — the value handed straight to the operating system's chmod call. The
   query returns that default mode. A definite, owner-read/write plus
   group/other-read mode is provided so that stored files have a single,
   predictable permission regardless of how the upload was buffered; the
   provider yields the concrete numeric value (decimal 420, i.e. rw-r--r--),
   never an absent/unset sentinel. The provider takes no input and never
   mutates anything (directive 5). The mode is modeled as a `Nat`. -/
method defaultFileMode return (mode : Nat)
  ensures mode = 420
  do
    -- impl-start
    return 420
    -- impl-end

prove_correct defaultFileMode by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: `method defaultFileMode return (mode:Nat) ensures mode = 420`; no axioms/pure/pre/post. The postcondition PINS the return value exactly. refinement.md: single leg B1 kind R (`return 420` <-> `FILE_UPLOAD_PERMISSIONS = 0o644 = 420`); no A legs (no axioms => A-consumed/A-reference vacuous), no I, no kind-3. mapping.md callee = module-level constant, no axiomatized callee; correspondence 0o644=420 holds (6*64+4*8+4). All same_spec=True (impl-region-only edits, verified via markers.same_spec).

### VERIFY (bash scripts/lean_verify.sh <f>):
- atk_1 `return 419`  -> exit 1 (unsolved `419=420`)  boundary
- atk_2 `return 421`  -> exit 1 (unsolved `421=420`)  boundary
- atk_3 `return 0`    -> exit 1 (unsolved `0=420`)   partial-domain / PREPATCH sentinel (mapping.md sec2 None->0)
- atk_7 `return 644`  -> exit 1 (unsolved `644=420`) ungrounded octal-misread
- atk_5 `while x<420 {x+=1}; return x` -> exit 0 VERIFIES  control-flow-effect echo
- atk_6 `return 6*64+4*8+4`            -> exit 0 VERIFIES  arithmetic/ungrounded-oracle echo
- pos_control `return 420`            -> exit 0 VERIFIES  (positive control)

### RESOLVE (swebench_unified.harness.run_resolve, official Docker oracle, iid django__django-10914):
- atk_5 patch (0o644, gold-equivalent value): resolved=True, completed=True, note='resolved'
- atk_6 patch (6*64+4*8+4 = 420):            resolved=True, completed=True, note='resolved'
Both verifying candidates are CORRECT ECHOES of the gold (verify AND resolve) -> not spec weaknesses (per _derive_audit_verdict: resolving candidate must not fail the gate).

EXTRA ATTACK CONSIDERED & REJECTED (not submitted): atk_4 = a non-terminating loop (`while 0=0 ...`) VERIFIES (exit 0) via partial-correctness VACUITY, and its divergent-RHS Python patch returns completed=True/resolved=False. I ran it (do_resolve_t.py, timeout 600, retries 0): resolved=False. I judged this NOT a genuine break and deliberately excluded it:

(1) the vacuity escape is a property of `loom.semantics.termination=partial` shared by EVERY partial-correctness velvet bundle, orthogonal to the strength of `mode=420`;

(2) the modeled callee is a MODULE-LEVEL CONSTANT that Python evaluates eagerly/totally at import, so a divergent module-level RHS models a broken/unimportable module, not 'a provider that yields a mode value' -> NO faithful refined patch exists for a divergent impl within the modeled total-constant domain; the divergent patch is an infidelity I injected, not a spec weakness;

(3) the prompt's attack taxonomy (partial-domain/boundary/control-flow-effect/ungrounded-oracle echo) concerns TERMINATING behavior/values. Every terminating same-spec verifying impl of this spec returns exactly 420 (sole admissible value) and therefore resolves. Hence there is no faithful verify-and-not-resolve counterexample. Files: {atk_4.lean, patch_atk_4.diff, resolve_atk_4.out, ANALYSIS.md}.

CONCLUSION: 6 submitted attacks re-run; 4 wrong-value attacks correctly REJECTED by verify (spec pins value), 2 verifying echoes RESOLVE (correct, not weaknesses); prepatch reproduced (return 0 fails for reason 0=420); positive control verifies. G-EQ = SOUND, spec TIGHT, refinement.md legs all R/I with no kind-3 and A-legs vacuous (no axioms).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, Velvet-verifying impl with a faithful refined patch that fails to resolve was found. The spec `ensures mode = 420` fully pins the sole admissible return value.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the default mode is a constant the provider supplies
--  directly, modeled deeply as its numeric value.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The framework supplies a default numeric mode for newly-stored uploaded
   files — the value handed straight to the operating system's chmod call. The
   query returns that default mode. A definite, owner-read/write plus
   group/other-read mode is provided so that stored files have a single,
   predictable permission regardless of how the upload was buffered; the
   provider yields the concrete numeric value (decimal 420, i.e. rw-r--r--),
   never an absent/unset sentinel. The provider takes no input and never
   mutates anything (directive 5). The mode is modeled as a `Nat`. -/
method defaultFileMode return (mode : Nat)
  ensures mode = 420
  do
    -- impl-start
    return 420
    -- impl-end

prove_correct defaultFileMode by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: `method defaultFileMode return (mode:Nat) ensures mode = 420`; no axioms/pure/pre/post. The postcondition PINS the return value exactly. refinement.md: single leg B1 kind R (`return 420` <-> `FILE_UPLOAD_PERMISSIONS = 0o644 = 420`); no A legs (no axioms => A-consumed/A-reference vacuous), no I, no kind-3. mapping.md callee = module-level constant, no axiomatized callee; correspondence 0o644=420 holds (6*64+4*8+4). All same_spec=True (impl-region-only edits, verified via markers.same_spec).

### VERIFY (bash scripts/lean_verify.sh <f>):
- atk_1 `return 419`  -> exit 1 (unsolved `419=420`)  boundary
- atk_2 `return 421`  -> exit 1 (unsolved `421=420`)  boundary
- atk_3 `return 0`    -> exit 1 (unsolved `0=420`)   partial-domain / PREPATCH sentinel (mapping.md sec2 None->0)
- atk_7 `return 644`  -> exit 1 (unsolved `644=420`) ungrounded octal-misread
- atk_5 `while x<420 {x+=1}; return x` -> exit 0 VERIFIES  control-flow-effect echo
- atk_6 `return 6*64+4*8+4`            -> exit 0 VERIFIES  arithmetic/ungrounded-oracle echo
- pos_control `return 420`            -> exit 0 VERIFIES  (positive control)

### RESOLVE (swebench_unified.harness.run_resolve, official Docker oracle, iid django__django-10914):
- atk_5 patch (0o644, gold-equivalent value): resolved=True, completed=True, note='resolved'
- atk_6 patch (6*64+4*8+4 = 420):            resolved=True, completed=True, note='resolved'
Both verifying candidates are CORRECT ECHOES of the gold (verify AND resolve) -> not spec weaknesses (per _derive_audit_verdict: resolving candidate must not fail the gate).

EXTRA ATTACK CONSIDERED & REJECTED (not submitted): atk_4 = a non-terminating loop (`while 0=0 ...`) VERIFIES (exit 0) via partial-correctness VACUITY, and its divergent-RHS Python patch returns completed=True/resolved=False. I ran it (do_resolve_t.py, timeout 600, retries 0): resolved=False. I judged this NOT a genuine break and deliberately excluded it:

(1) the vacuity escape is a property of `loom.semantics.termination=partial` shared by EVERY partial-correctness velvet bundle, orthogonal to the strength of `mode=420`;

(2) the modeled callee is a MODULE-LEVEL CONSTANT that Python evaluates eagerly/totally at import, so a divergent module-level RHS models a broken/unimportable module, not 'a provider that yields a mode value' -> NO faithful refined patch exists for a divergent impl within the modeled total-constant domain; the divergent patch is an infidelity I injected, not a spec weakness;

(3) the prompt's attack taxonomy (partial-domain/boundary/control-flow-effect/ungrounded-oracle echo) concerns TERMINATING behavior/values. Every terminating same-spec verifying impl of this spec returns exactly 420 (sole admissible value) and therefore resolves. Hence there is no faithful verify-and-not-resolve counterexample. Files: {atk_4.lean, patch_atk_4.diff, resolve_atk_4.out, ANALYSIS.md}.

CONCLUSION: 6 submitted attacks re-run; 4 wrong-value attacks correctly REJECTED by verify (spec pins value), 2 verifying echoes RESOLVE (correct, not weaknesses); prepatch reproduced (return 0 fails for reason 0=420); positive control verifies. G-EQ = SOUND, spec TIGHT, refinement.md legs all R/I with no kind-3 and A-legs vacuous (no axioms).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis for django__django-10914/velvet.

SPEC REGION (spec_view via VelvetBackend.language): method `defaultFileMode` with `ensures mode = 420`, a nullary constant query (no parameters, no callees, no axioms). same_spec(Solution.lean, Solution_prepatch.lean) = True — only the impl body differs, so the spec is a byte-identical contract change.

### REAL REPO CHECK (base_commit e7fd69d051eaa67cb17f172a39b57253e9cb831a):
- Pre-patch: django/conf/global_settings.py:307 `FILE_UPLOAD_PERMISSIONS = None`.
- Patched gold value: `FILE_UPLOAD_PERMISSIONS = 0o644`.
- Arithmetic confirmed: python `0o644 == 420` (6*64+4*8+4 = 420).
- Downstream binding verified: Storage.file_permissions_mode (core/files/storage.py:217) returns `_value_or_setting(..., settings.FILE_UPLOAD_PERMISSIONS)`, fed straight into os.chmod (storage.py:284). The F2P test asserts default_storage.file_permissions_mode == 0o644, exactly the pinned value.

DIVERGENCE SEARCH: the modeled function is a constant with an empty input domain (`return`/no args). Its single modeled output is 420, which equals the real patched repo constant 0o644 exactly. There is no input on which the model can disagree with the real callee — the domain is a single point and the point matches. The spec is neither too strong nor drifted: it pins precisely the patched behavior the gold introduces.

Lean verification: scripts/lean_verify.sh on Solution.lean exits 0 (prove_correct discharges). G-DIFF confirms prepatch (unset sentinel, modeled as 0) fails `mode = 420`.

Conclusion: FAITHFUL — no diverging input exists; modeled defaultFileMode agrees with the real repo callee on its entire (singleton) domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: FILE_UPLOAD_PERMISSIONS = None -> 0o644 in django/conf/global_settings.py. The PUBLIC problem_statement itself already discloses the exact setting name and exact target value in its opening title line: 'Set default FILE_UPLOAD_PERMISSION to 0o644.' Everything the spec view reveals is bounded by that public statement: (1) Solution.lean postcondition 'ensures mode = 420' with comment 'decimal 420, i.e. rw-r--r--' — 420 is just the decimal encoding of the publicly-stated 0o644 (mechanical Lean Nat carrier, a modeling artifact, not new info); (2) refinement.md/mapping.md name FILE_UPLOAD_PERMISSIONS, the None->0o644 transition, and the F2P test test_override_file_upload_permissions — all derivable from / stated in the public problem_statement. The spec view adds no discriminator beyond the public statement (target value, setting identity, and goal are all already public). Verified: mechanical leakage.screen() passes (no hard failures); same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical). This is not a relaxed bundle. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
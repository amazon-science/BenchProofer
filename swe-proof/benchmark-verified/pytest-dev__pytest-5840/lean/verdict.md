# P2 adversarial audit — pytest-dev__pytest-5840

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
None. The spec is a TOTAL EXACT-EQUALITY obligation: problem_spec_cacheKey resolved result := (result = resolved), so the proof goal is ∀ resolved, implementation_cacheKey resolved = resolved. That closes ONLY for functions extensionally equal to the identity — i.e. exactly the correct case-preserving fix (Path(str(p)).resolve() used verbatim). Every wrong impl differs from id on some input and fails rfl, so no verifying wrong impl exists and there is nothing to resolve-run (step 2 vacuously satisfied).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,8 @@
 
 -- impl-start
 def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
-  -- The cache key is the resolved path used as-is, preserving its letter case.
-  let key := resolved
+  -- PRE-PATCH (buggy): fold to lower case (normcase on case-insensitive FS)
+  let key := resolved.map Char.toLower
   return key
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,10 @@
 
 -- impl-start
 def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
-  -- The cache key is the resolved path used as-is, preserving its letter case.
-  let key := resolved
-  return key
+  -- partial-domain: correct only on the empty path, else drops everything
+  match resolved with
+  | [] => return []
+  | _  => return []
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,8 @@
 
 -- impl-start
 def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
-  -- The cache key is the resolved path used as-is, preserving its letter case.
-  let key := resolved
+  -- boundary: drop the first character of the path
+  let key := resolved.drop 1
   return key
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,11 @@
 
 -- impl-start
 def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
-  -- The cache key is the resolved path used as-is, preserving its letter case.
-  let key := resolved
-  return key
+  -- control-flow-effect: fold to UPPER case instead of preserving case
+  let mut acc : List Char := []
+  for c in resolved do
+    acc := acc ++ [c.toUpper]
+  return acc
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,8 @@
 
 -- impl-start
 def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
-  -- The cache key is the resolved path used as-is, preserving its letter case.
-  let key := resolved
+  -- ungrounded normalization: append a trailing separator sentinel
+  let key := resolved ++ ['/']
   return key
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,8 +47,8 @@
 
 -- impl-start
 def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
-  -- The cache key is the resolved path used as-is, preserving its letter case.
-  let key := resolved
+  -- plausible-but-wrong: collapse adjacent duplicate separators/chars
+  let key := resolved.eraseDups
   return key
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,8 @@
 
 -- impl-start
 def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
-  -- The cache key is the resolved path used as-is, preserving its letter case.
-  let key := resolved
-  return key
+  -- ungrounded oracle echo: ignore input, return a fixed canonical constant
+  return "conftest.py".toList
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deriving the de-duplication key for the canonical path of a loaded configuration
hook file.

A test runner caches a loaded hook module under a key derived from the file's
canonical (fully resolved, absolute) path, so the same file encountered by two
different routes is only loaded once. The key is computed by a single
transformation of the already-resolved path.

The transformation must PRESERVE the original letter case of the resolved path:
the key is the resolved path verbatim. It must NOT fold the path to lower case.
On case-insensitive (but case-preserving) file systems, folding the path to lower
case produces a key that no longer matches the path's true on-disk casing, which
in turn breaks deriving the module's qualified name from the path (the reported
failure: a path that "was converted to lower case", yielding an import error for
a package whose name contains upper-case characters).

The modeled value here is exactly that key-derivation step: given the canonical
resolved path (a sequence of characters), produce the cache key. The desired
behavior is the identity on the path — every character, including its letter
case, is retained.
-/

-- axioms-start
-- No unchanged callee contributes a property the proof consumes. The path
-- canonicalization (resolving symlinks / making absolute) happens before the
-- modeled step and is taken as the already-resolved input `resolved`; the only
-- modeled behavior is how the cache key is derived from that resolved path. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No shared helper is needed: the key derivation is the identity on the resolved
-- path, and the spec pins the result to the input directly.
-- pure-end

-- post-conditions-start
/-- The cache key for a loaded hook file is exactly its canonical resolved path,
character-for-character — the original letter case of the path is preserved, not
folded. -/
def problem_spec_cacheKey (resolved : List Char) (result : List Char) : Prop :=
  result = resolved
-- post-conditions-end

-- impl-start
def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
  let key := resolved
  return key
-- impl-end

-- proof-start
theorem correct_cacheKey :
    ∀ (resolved : List Char),
      problem_spec_cacheKey resolved (implementation_cacheKey resolved) := by
  intro resolved
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: pytest-dev__pytest-5840 lean. Spec: problem_spec_cacheKey (resolved result : List Char) : Prop := result = resolved. Impl: identity on resolved (case-preserving cache key). Proof: rfl, CLEAN axioms.

SAME_SPEC: all 7 attacks + positive control return same_spec==True (spec_view collapses BOTH impl and proof regions to placeholders; lines 1-47 header kept byte-identical, verified diff HEADER IDENTICAL). Axioms region is comment-only/empty (grep for axiom/opaque -> NONE).

POSITIVE CONTROL pos_control.lean (identity impl): cmd `bash scripts/lean_verify.sh <f>` -> EXIT 0. #print axioms correct_cacheKey -> "'correct_cacheKey' does not depend on any axioms" (clean).

### ATTACKS (cmd for each: `bash scripts/lean_verify.sh <path>`; run concurrently in 2 batches of 4):
- atk_1.lean PREPATCH BUG (normcase lower-case fold, resolved.map Char.toLower): EXIT 1, rfl failed (LHS `resolved` not defeq `implementation_cacheKey resolved`). Prepatch bug reproduced.
- atk_2.lean PARTIAL-DOMAIN (identity only on [], else []): EXIT 1, rfl failed.
- atk_3.lean BOUNDARY/off-by-one (resolved.drop 1): EXIT 1, rfl failed.
- atk_4.lean CONTROL-FLOW-EFFECT (for-loop upper-case fold c.toUpper): EXIT 1, rfl failed.
- atk_5.lean (append trailing '/' sentinel, ungrounded normalization): EXIT 1, rfl failed.
- atk_6.lean (eraseDups collapse duplicates, plausible-but-wrong canonicalize): EXIT 1, rfl failed.
- atk_7.lean UNGROUNDED-ORACLE ECHO (ignore input, return fixed "conftest.py".toList): EXIT 1, rfl failed.

All 7 wrong impls FAIL to close with genuine rfl mismatches; none closes with clean axioms, so per protocol step 2 no faithful patch needed materialization/resolve (vacuous). RESOLVE runs: N/A (no verifying wrong impl).

REFINEMENT.MD LEG AUDIT: empty axioms region (no A-consumed/A-reference legs). 3 legs: (1) resolved:List Char input = R (path canonicalization unchanged by patch, factored to input); (2) let key:=resolved = I (deep model of the changed op = identity, case preserved; matches post-patch key=Path(str(conftestpath)).resolve() used verbatim); (3) return key = R (key indexes _conftestpath2mod). All legs R/I, NO kind-3, no A-legs to check callee correspondence for. mapping.md type bijection (str code-point <-> Char; normcase <-> Char.toLower prepatch-only) is faithful; prepatch leg (atk_1) is the correct discriminator and fails as required.

VERDICT SOUND: >=5 (7) distinct same-spec attacks run, prepatch reproduced, positive control verifies clean, and the total exact-equality spec admits no verifying wrong impl (verify => correct holds).

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
None. The spec is a TOTAL EXACT-EQUALITY obligation: problem_spec_cacheKey resolved result := (result = resolved), so the proof goal is ∀ resolved, implementation_cacheKey resolved = resolved. That closes ONLY for functions extensionally equal to the identity — i.e. exactly the correct case-preserving fix (Path(str(p)).resolve() used verbatim). Every wrong impl differs from id on some input and fails rfl, so no verifying wrong impl exists and there is nothing to resolve-run (step 2 vacuously satisfied).
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
Deriving the de-duplication key for the canonical path of a loaded configuration
hook file.

A test runner caches a loaded hook module under a key derived from the file's
canonical (fully resolved, absolute) path, so the same file encountered by two
different routes is only loaded once. The key is computed by a single
transformation of the already-resolved path.

The transformation must PRESERVE the original letter case of the resolved path:
the key is the resolved path verbatim. It must NOT fold the path to lower case.
On case-insensitive (but case-preserving) file systems, folding the path to lower
case produces a key that no longer matches the path's true on-disk casing, which
in turn breaks deriving the module's qualified name from the path (the reported
failure: a path that "was converted to lower case", yielding an import error for
a package whose name contains upper-case characters).

The modeled value here is exactly that key-derivation step: given the canonical
resolved path (a sequence of characters), produce the cache key. The desired
behavior is the identity on the path — every character, including its letter
case, is retained.
-/

-- axioms-start
-- No unchanged callee contributes a property the proof consumes. The path
-- canonicalization (resolving symlinks / making absolute) happens before the
-- modeled step and is taken as the already-resolved input `resolved`; the only
-- modeled behavior is how the cache key is derived from that resolved path. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No shared helper is needed: the key derivation is the identity on the resolved
-- path, and the spec pins the result to the input directly.
-- pure-end

-- post-conditions-start
/-- The cache key for a loaded hook file is exactly its canonical resolved path,
character-for-character — the original letter case of the path is preserved, not
folded. -/
def problem_spec_cacheKey (resolved : List Char) (result : List Char) : Prop :=
  result = resolved
-- post-conditions-end

-- impl-start
def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
  let key := resolved
  return key
-- impl-end

-- proof-start
theorem correct_cacheKey :
    ∀ (resolved : List Char),
      problem_spec_cacheKey resolved (implementation_cacheKey resolved) := by
  intro resolved
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: pytest-dev__pytest-5840 lean. Spec: problem_spec_cacheKey (resolved result : List Char) : Prop := result = resolved. Impl: identity on resolved (case-preserving cache key). Proof: rfl, CLEAN axioms.

SAME_SPEC: all 7 attacks + positive control return same_spec==True (spec_view collapses BOTH impl and proof regions to placeholders; lines 1-47 header kept byte-identical, verified diff HEADER IDENTICAL). Axioms region is comment-only/empty (grep for axiom/opaque -> NONE).

POSITIVE CONTROL pos_control.lean (identity impl): cmd `bash scripts/lean_verify.sh <f>` -> EXIT 0. #print axioms correct_cacheKey -> "'correct_cacheKey' does not depend on any axioms" (clean).

### ATTACKS (cmd for each: `bash scripts/lean_verify.sh <path>`; run concurrently in 2 batches of 4):
- atk_1.lean PREPATCH BUG (normcase lower-case fold, resolved.map Char.toLower): EXIT 1, rfl failed (LHS `resolved` not defeq `implementation_cacheKey resolved`). Prepatch bug reproduced.
- atk_2.lean PARTIAL-DOMAIN (identity only on [], else []): EXIT 1, rfl failed.
- atk_3.lean BOUNDARY/off-by-one (resolved.drop 1): EXIT 1, rfl failed.
- atk_4.lean CONTROL-FLOW-EFFECT (for-loop upper-case fold c.toUpper): EXIT 1, rfl failed.
- atk_5.lean (append trailing '/' sentinel, ungrounded normalization): EXIT 1, rfl failed.
- atk_6.lean (eraseDups collapse duplicates, plausible-but-wrong canonicalize): EXIT 1, rfl failed.
- atk_7.lean UNGROUNDED-ORACLE ECHO (ignore input, return fixed "conftest.py".toList): EXIT 1, rfl failed.

All 7 wrong impls FAIL to close with genuine rfl mismatches; none closes with clean axioms, so per protocol step 2 no faithful patch needed materialization/resolve (vacuous). RESOLVE runs: N/A (no verifying wrong impl).

REFINEMENT.MD LEG AUDIT: empty axioms region (no A-consumed/A-reference legs). 3 legs: (1) resolved:List Char input = R (path canonicalization unchanged by patch, factored to input); (2) let key:=resolved = I (deep model of the changed op = identity, case preserved; matches post-patch key=Path(str(conftestpath)).resolve() used verbatim); (3) return key = R (key indexes _conftestpath2mod). All legs R/I, NO kind-3, no A-legs to check callee correspondence for. mapping.md type bijection (str code-point <-> Char; normcase <-> Char.toLower prepatch-only) is faithful; prepatch leg (atk_1) is the correct discriminator and fails as required.

VERDICT SOUND: >=5 (7) distinct same-spec attacks run, prepatch reproduced, positive control verifies clean, and the total exact-equality spec admits no verifying wrong impl (verify => correct holds).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on pytest-dev__pytest-5840 lean bundle. Verified: (1) same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with LeanBackend — spec region byte-identical (problem_spec_cacheKey resolved result := result = resolved). (2) Solution.lean compiles under lean_verify.sh (exit 0); #print axioms correct_cacheKey => 'does not depend on any axioms' (genuine rfl proof, no sorryAx). (3) Modeling boundary is sound & faithful: the patch changes _importconftest's cache-key derivation from unique_path(conftestpath) [= type(path)(normcase(str(path.realpath()))), which lower-cases on case-insensitive FS] to key = Path(str(conftestpath)).resolve() [canonicalizes WITHOUT case-folding]. The auditor factors out the path canonicalization — UNCHANGED by the patch (both realpath() pre and Path.resolve() post canonicalize) — as the already-resolved input `resolved`, and models ONLY the changed behavior (case preservation vs. folding). The post-patch modeled function = identity on `resolved` (case preserved), which agrees with the real callee `Path(str(p)).resolve()` on an already-canonicalized path (idempotent, case-preserving) for every input. No input exists where the identity model overclaims vs. the real case-preserving key derivation, so the spec is not too strong / does not drift. (4) Spec is non-vacuous: the prepatch leg (resolved.map Char.toLower, modeling normcase) violates result=resolved on any upper-case path, so the spec correctly discriminates the fix from the bug — matching FAIL_TO_PASS tests (test_conftest_uppercase, test_setinitial_conftest_subdirs). No diverging input; verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no diff markers, no gold-patch line reproduced, no patched file/module path (config/__init__.py, pathlib.py), no patched symbol (unique_path, normcase, resolve) echoed in a spec-view identifier or comment, no narration keywords. Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True).

Semantic gold-reconstruction check: the spec view discloses that the cache key must PRESERVE letter case / must NOT fold to lower case (postcondition result = resolved, the identity), and that lower-casing breaks the module's qualified name for an upper-case package. This is the direct logical inverse of what the PUBLIC problem_statement already reveals: '5.1.2 ImportError while loading conftest (windows import folder casing issues)', 'the path was converted to lower case', and 'ModuleNotFoundError: No module named 'python'' (a lowercased path segment). The desired behavior (preserve case) is derivable from the public bug report alone.

Crucially, the spec view abstracts the actual gold edit: the canonicalization callee is factored out as the already-resolved input 'resolved' and the transformation is described generically as 'a single transformation of the already-resolved path' — it does NOT name unique_path/normcase/Path().resolve(), the patched files, or any diff line. It leaks no implementation-level edit detail beyond the publicly-disclosed casing symptom. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

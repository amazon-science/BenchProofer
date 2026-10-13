# P2 adversarial audit — sphinx-doc__sphinx-8120

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
For any non-empty userDirs (e.g. userDirs=["u"], bundledDir="b"): the fully-pinned spec requires result = [none, some "u", some "b"]. Every wrong impl (prepatch [none, some "b", some "u"]; drop-bundled [none, some "u"]; drop-sentinel [some "u", some "b"]; empty-only branch; duplicate-bundled; reversed) differs from this exact list and so its correct_searchDirs cannot close.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,7 @@
 -- impl-start
 def implementation_searchDirs
     (userDirs : List String) (bundledDir : String) : List (Option String) :=
-  Id.run do
-    let mut searchDirs : List (Option String) := [none]
-    searchDirs := searchDirs ++ userDirs.map some
-    searchDirs := searchDirs ++ [some bundledDir]
-    return searchDirs
+  none :: (some bundledDir :: userDirs.map some)
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,7 @@
 -- impl-start
 def implementation_searchDirs
     (userDirs : List String) (bundledDir : String) : List (Option String) :=
-  Id.run do
-    let mut searchDirs : List (Option String) := [none]
-    searchDirs := searchDirs ++ userDirs.map some
-    searchDirs := searchDirs ++ [some bundledDir]
-    return searchDirs
+  none :: userDirs.map some
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,7 @@
 -- impl-start
 def implementation_searchDirs
     (userDirs : List String) (bundledDir : String) : List (Option String) :=
-  Id.run do
-    let mut searchDirs : List (Option String) := [none]
-    searchDirs := searchDirs ++ userDirs.map some
-    searchDirs := searchDirs ++ [some bundledDir]
-    return searchDirs
+  userDirs.map some ++ [some bundledDir]
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
 -- impl-start
 def implementation_searchDirs
     (userDirs : List String) (bundledDir : String) : List (Option String) :=
-  Id.run do
-    let mut searchDirs : List (Option String) := [none]
-    searchDirs := searchDirs ++ userDirs.map some
-    searchDirs := searchDirs ++ [some bundledDir]
-    return searchDirs
+  if userDirs.isEmpty then none :: (userDirs.map some ++ [some bundledDir])
+  else none :: userDirs.map some
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,7 @@
 -- impl-start
 def implementation_searchDirs
     (userDirs : List String) (bundledDir : String) : List (Option String) :=
-  Id.run do
-    let mut searchDirs : List (Option String) := [none]
-    searchDirs := searchDirs ++ userDirs.map some
-    searchDirs := searchDirs ++ [some bundledDir]
-    return searchDirs
+  assembleSearchDirs userDirs bundledDir
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,7 @@
 -- impl-start
 def implementation_searchDirs
     (userDirs : List String) (bundledDir : String) : List (Option String) :=
-  Id.run do
-    let mut searchDirs : List (Option String) := [none]
-    searchDirs := searchDirs ++ userDirs.map some
-    searchDirs := searchDirs ++ [some bundledDir]
-    return searchDirs
+  none :: (userDirs.map some ++ [some bundledDir, some bundledDir])
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,7 @@
 -- impl-start
 def implementation_searchDirs
     (userDirs : List String) (bundledDir : String) : List (Option String) :=
-  Id.run do
-    let mut searchDirs : List (Option String) := [none]
-    searchDirs := searchDirs ++ userDirs.map some
-    searchDirs := searchDirs ++ [some bundledDir]
-    return searchDirs
+  none :: (userDirs.reverse.map some ++ [some bundledDir])
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the ordered list of directories in which a resource loader will look
for override files.

The assembly is given:

  * a list of caller-supplied directories, in the order the caller provided
    them;
  * a single built-in (bundled) directory shipped with the tool.

The loader that consumes this list walks it front-to-back, and an entry found
earlier takes precedence over one found later. The desired ordering of the
assembled list is therefore:

  * a leading system-default sentinel (written as the absent value), so the
    host system's own location is consulted first;
  * then every caller-supplied directory, in the caller's order;
  * then the single built-in directory, last.

In particular each caller-supplied directory appears ahead of the built-in
directory, so a caller's own files take precedence over the bundled ones; and
no directory is dropped, duplicated, or reordered relative to its group.
-/

-- axioms-start
-- No unchanged outside callee is consumed: the caller-supplied directories and
-- the built-in directory enter as plain data, and the only operation performed
-- is the construction of the ordered search list (a leading sentinel, the
-- caller's directories, then the built-in directory). The downstream loader that
-- interprets list order as precedence is unchanged and is not invoked here, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The search list assembled from the caller-supplied directories and the single
built-in directory: a leading system-default sentinel (`none`), then the
caller's directories in order (each a present value), then the built-in
directory last. -/
def assembleSearchDirs (userDirs : List String) (bundledDir : String) :
    List (Option String) :=
  none :: (userDirs.map some ++ [some bundledDir])
-- pure-end

-- post-conditions-start
/-- The assembled search list is fully pinned to the inputs:

  * its head is the system-default sentinel `none`;
  * the remainder is exactly the caller-supplied directories (each made present)
    in their given order, followed by the single built-in directory;

so every caller-supplied directory precedes the built-in directory, and the list
is determined for every input (no component is left free). -/
def problem_spec_searchDirs
    (userDirs : List String) (bundledDir : String)
    (result : List (Option String)) : Prop :=
  result = assembleSearchDirs userDirs bundledDir
-- post-conditions-end

-- impl-start
def implementation_searchDirs
    (userDirs : List String) (bundledDir : String) : List (Option String) :=
  Id.run do
    let mut searchDirs : List (Option String) := [none]
    searchDirs := searchDirs ++ userDirs.map some
    searchDirs := searchDirs ++ [some bundledDir]
    return searchDirs
-- impl-end

-- proof-start
theorem correct_searchDirs :
    ∀ (userDirs : List String) (bundledDir : String),
      problem_spec_searchDirs userDirs bundledDir
        (implementation_searchDirs userDirs bundledDir) := by
  intro userDirs bundledDir
  unfold problem_spec_searchDirs implementation_searchDirs assembleSearchDirs
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a FULLY-PINNED exact equality: problem_spec_searchDirs r := r = assembleSearchDirs userDirs bundledDir, where assembleSearchDirs = none :: (userDirs.map some ++ [some bundledDir]). Output is determined for every input, so verify => extensional equality to gold => correct. No A-legs: refinement.md legs are all R/I (rows 1-4), axioms region empty, axiom_check.py is a skip stub, deep_model_references=[]. Verified with #print axioms correct_searchDirs on atk_5: 'does not depend on any axioms'.

Commands (all: `bash scripts/lean_verify.sh <file>`):
- positive_control.lean -> exit 0 (verifies).
- atk_1 (prepatch bug, bundled before user dirs) -> exit 1.
- atk_2 (partial-domain, drops bundled dir) -> exit 1.
- atk_3 (boundary, drops leading none sentinel) -> exit 1.
- atk_4 (control-flow-effect, correct only when userDirs empty) -> exit 1.
- atk_5 (ungrounded-oracle echo = returns assembleSearchDirs verbatim) -> exit 0, clean axioms.
- atk_6 (duplicate bundled dir) -> exit 1.
- atk_7 (reorder, reverse user dirs) -> exit 1.

same_spec = True for all 7 attacks (swebench_unified.markers.same_spec, lean backend), byte-identical axioms/pure/pre/post.

Only the behaviorally-correct echo (atk_5) verifies; per resolved G-PANEL-1/echo policy a same-spec verifying candidate is a weakness ONLY if its faithful refined patch does NOT resolve. atk_5 computes exactly the gold behavior, so its faithful patch IS the gold patch (submitted under patches) which resolves the F2P test test_customize_system_message. No wrong impl closes, so there is no verify-without-resolve materialization to run. Refinement audit: all legs R/I, no kind-3, no A-leg correspondence to validate. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
For any non-empty userDirs (e.g. userDirs=["u"], bundledDir="b"): the fully-pinned spec requires result = [none, some "u", some "b"]. Every wrong impl (prepatch [none, some "b", some "u"]; drop-bundled [none, some "u"]; drop-sentinel [some "u", some "b"]; empty-only branch; duplicate-bundled; reversed) differs from this exact list and so its correct_searchDirs cannot close.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the ordered list of directories in which a resource loader will look
for override files.

The assembly is given:

  * a list of caller-supplied directories, in the order the caller provided
    them;
  * a single built-in (bundled) directory shipped with the tool.

The loader that consumes this list walks it front-to-back, and an entry found
earlier takes precedence over one found later. The desired ordering of the
assembled list is therefore:

  * a leading system-default sentinel (written as the absent value), so the
    host system's own location is consulted first;
  * then every caller-supplied directory, in the caller's order;
  * then the single built-in directory, last.

In particular each caller-supplied directory appears ahead of the built-in
directory, so a caller's own files take precedence over the bundled ones; and
no directory is dropped, duplicated, or reordered relative to its group.
-/

-- axioms-start
-- No unchanged outside callee is consumed: the caller-supplied directories and
-- the built-in directory enter as plain data, and the only operation performed
-- is the construction of the ordered search list (a leading sentinel, the
-- caller's directories, then the built-in directory). The downstream loader that
-- interprets list order as precedence is unchanged and is not invoked here, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The search list assembled from the caller-supplied directories and the single
built-in directory: a leading system-default sentinel (`none`), then the
caller's directories in order (each a present value), then the built-in
directory last. -/
def assembleSearchDirs (userDirs : List String) (bundledDir : String) :
    List (Option String) :=
  none :: (userDirs.map some ++ [some bundledDir])
-- pure-end

-- post-conditions-start
/-- The assembled search list is fully pinned to the inputs:

  * its head is the system-default sentinel `none`;
  * the remainder is exactly the caller-supplied directories (each made present)
    in their given order, followed by the single built-in directory;

so every caller-supplied directory precedes the built-in directory, and the list
is determined for every input (no component is left free). -/
def problem_spec_searchDirs
    (userDirs : List String) (bundledDir : String)
    (result : List (Option String)) : Prop :=
  result = assembleSearchDirs userDirs bundledDir
-- post-conditions-end

-- impl-start
def implementation_searchDirs
    (userDirs : List String) (bundledDir : String) : List (Option String) :=
  Id.run do
    let mut searchDirs : List (Option String) := [none]
    searchDirs := searchDirs ++ userDirs.map some
    searchDirs := searchDirs ++ [some bundledDir]
    return searchDirs
-- impl-end

-- proof-start
theorem correct_searchDirs :
    ∀ (userDirs : List String) (bundledDir : String),
      problem_spec_searchDirs userDirs bundledDir
        (implementation_searchDirs userDirs bundledDir) := by
  intro userDirs bundledDir
  unfold problem_spec_searchDirs implementation_searchDirs assembleSearchDirs
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a FULLY-PINNED exact equality: problem_spec_searchDirs r := r = assembleSearchDirs userDirs bundledDir, where assembleSearchDirs = none :: (userDirs.map some ++ [some bundledDir]). Output is determined for every input, so verify => extensional equality to gold => correct. No A-legs: refinement.md legs are all R/I (rows 1-4), axioms region empty, axiom_check.py is a skip stub, deep_model_references=[]. Verified with #print axioms correct_searchDirs on atk_5: 'does not depend on any axioms'.

Commands (all: `bash scripts/lean_verify.sh <file>`):
- positive_control.lean -> exit 0 (verifies).
- atk_1 (prepatch bug, bundled before user dirs) -> exit 1.
- atk_2 (partial-domain, drops bundled dir) -> exit 1.
- atk_3 (boundary, drops leading none sentinel) -> exit 1.
- atk_4 (control-flow-effect, correct only when userDirs empty) -> exit 1.
- atk_5 (ungrounded-oracle echo = returns assembleSearchDirs verbatim) -> exit 0, clean axioms.
- atk_6 (duplicate bundled dir) -> exit 1.
- atk_7 (reorder, reverse user dirs) -> exit 1.

same_spec = True for all 7 attacks (swebench_unified.markers.same_spec, lean backend), byte-identical axioms/pure/pre/post.

Only the behaviorally-correct echo (atk_5) verifies; per resolved G-PANEL-1/echo policy a same-spec verifying candidate is a weakness ONLY if its faithful refined patch does NOT resolve. atk_5 computes exactly the gold behavior, so its faithful patch IS the gold patch (submitted under patches) which resolves the F2P test test_customize_system_message. No wrong impl closes, so there is no verify-without-resolve materialization to run. Refinement audit: all legs R/I, no kind-3, no A-leg correspondence to validate. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) fails to find a defect. Findings:

(1) SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean)=True under the lean backend — the spec view (docstring, axioms region, pure `assembleSearchDirs`, post-condition `problem_spec_searchDirs`) is byte-identical between variants; only impl+proof differ. region_hashes intact.

(2) PROOF REAL: lean_verify.sh exit 0 (compiles, no sorry/error); `#print axioms correct_searchDirs` -> 'does not depend on any axioms' (no sorryAx — proof genuinely closes via rfl).

(3) FAITHFULNESS vs REAL CALLEE: Gold patch post-fix fragment in Sphinx._init_i18n (sphinx/application.py) is `locale_dirs=[None]; locale_dirs+=list(repo.locale_dirs); locale_dirs+=[path.join(package_dir,'locale')]`, i.e. [None] ++ userDirs ++ [bundled]. Model: `assembleSearchDirs userDirs bundledDir = none :: (userDirs.map some ++ [some bundledDir])`. Exact positional transliteration under the type bijection none<->None, some s<->s, List<->list, ++<->'+='. spec `result = assembleSearchDirs ...` pins the ENTIRE list to inputs — not too weak.

(4) NO DROPPED TRANSFORM: the fragment does only list construction/concatenation (no dedup/filter/reorder); repo.locale_dirs yields _StrPath values (never None) and is read as plain data. There is no input where the real fragment's output differs from assembleSearchDirs, so the spec is not too strong either.

(5) G-CONF differential (conformance_check.py, seed 8120, 100000 fuzzed inputs, userDirs len 0-6 incl. empty) -> 0 disagreements between the verbatim post-patch oracle and the impl shadow.

No diverging input exists. Note: /tmp worktree sits at a much later HEAD b06d92e whose _init_i18n has since re-ordered to `list(repo.locale_dirs)+[None]+[package/locale]` — irrelevant to this base_commit (795747bd) audit; the gold patch was obtained from the dataset test.jsonl and matches the modeled fragment. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Solver-visible spec view (spec_view over Solution.lean; impl+proof regions elided to placeholders) contains no leakage of the gold edit beyond the public problem_statement. Verified: (1) markers.same_spec(Solution, Solution_prepatch, lean-backend)=True — the spec region (imports/docstring/axioms/pure/post-conditions) is byte-identical across variants; only the elided impl/proof differ. (2) leakage.screen() runs clean: hard_failures=[], warnings=[]. No diff markers, no patched file paths (sphinx/application.py, sphinx/locale/__init__.py) or module paths, no patched repo symbols (locale_dirs, _init_i18n, path.join, package_dir, repo.locale_dirs; changed-symbol set {init, init_i18n, repr} not embedded in any spec-view identifier or comment), and no bug/fix/pre-patch narration in the docstring. (3) The docstring/postcondition states the CORRECT behavior abstractly — leading system-default sentinel (none), then caller directories in order, then the single bundled directory last, so caller files take precedence over bundled ones. This is exactly the expected behavior already disclosed by the public problem_statement (the user-supplied locale/<lang>/LC_MESSAGES/sphinx.po override should win over the bundled da translation). Stating correct behavior derivable from the public issue is a legitimate spec, not leakage of the edit. The buggy pre-patch ordering and the concrete list-construction edit live only in the elided impl region and in the internal audit docs (refinement.md/mapping.md), which are NOT part of the solver-visible spec view. No line reconstructs the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

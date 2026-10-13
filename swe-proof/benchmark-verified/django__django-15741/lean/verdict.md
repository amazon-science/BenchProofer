# P2 adversarial audit — django__django-15741

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,8 +64,9 @@
 -- impl-start
 def implementation_localizedFormat
     (name : FmtName) (lang : String) : Option String := Id.run do
-  let key := realizeName name
-  return some (lookupFormat key lang)
+  match directName name with
+  | some key => return some (lookupFormat key lang)
+  | none     => return none
 -- impl-end
 
 -- proof-start
@@ -74,5 +75,11 @@
       problem_spec_localizedFormat name lang
         (implementation_localizedFormat name lang) := by
   intro name lang
-  rfl
+  cases name <;>
+    simp only [problem_spec_localizedFormat, implementation_localizedFormat,
+      realizeName, directName, Id.run, bind, pure] <;>
+    first
+    | rfl
+    | (try decide)
+    | (try simp_all)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
 def implementation_localizedFormat
     (name : FmtName) (lang : String) : Option String := Id.run do
   let key := realizeName name
-  return some (lookupFormat key lang)
+  return some (lookupFormat lang key)
 -- impl-end
 
 -- proof-start
@@ -74,5 +74,11 @@
       problem_spec_localizedFormat name lang
         (implementation_localizedFormat name lang) := by
   intro name lang
-  rfl
+  cases name <;>
+    simp only [problem_spec_localizedFormat, implementation_localizedFormat,
+      realizeName, directName, Id.run, bind, pure] <;>
+    first
+    | rfl
+    | (try decide)
+    | (try simp_all)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,8 +64,7 @@
 -- impl-start
 def implementation_localizedFormat
     (name : FmtName) (lang : String) : Option String := Id.run do
-  let key := realizeName name
-  return some (lookupFormat key lang)
+  return some (lookupFormat "" lang)
 -- impl-end
 
 -- proof-start
@@ -74,5 +73,11 @@
       problem_spec_localizedFormat name lang
         (implementation_localizedFormat name lang) := by
   intro name lang
-  rfl
+  cases name <;>
+    simp only [problem_spec_localizedFormat, implementation_localizedFormat,
+      realizeName, directName, Id.run, bind, pure] <;>
+    first
+    | rfl
+    | (try decide)
+    | (try simp_all)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,8 +64,7 @@
 -- impl-start
 def implementation_localizedFormat
     (name : FmtName) (lang : String) : Option String := Id.run do
-  let key := realizeName name
-  return some (lookupFormat key lang)
+  return none
 -- impl-end
 
 -- proof-start
@@ -74,5 +73,11 @@
       problem_spec_localizedFormat name lang
         (implementation_localizedFormat name lang) := by
   intro name lang
-  rfl
+  cases name <;>
+    simp only [problem_spec_localizedFormat, implementation_localizedFormat,
+      realizeName, directName, Id.run, bind, pure] <;>
+    first
+    | rfl
+    | (try decide)
+    | (try simp_all)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,8 +64,9 @@
 -- impl-start
 def implementation_localizedFormat
     (name : FmtName) (lang : String) : Option String := Id.run do
-  let key := realizeName name
-  return some (lookupFormat key lang)
+  match name with
+  | .concrete s => return some (lookupFormat s lang)
+  | .deferred _ => return some (lookupFormat "" lang)
 -- impl-end
 
 -- proof-start
@@ -74,5 +75,11 @@
       problem_spec_localizedFormat name lang
         (implementation_localizedFormat name lang) := by
   intro name lang
-  rfl
+  cases name <;>
+    simp only [problem_spec_localizedFormat, implementation_localizedFormat,
+      realizeName, directName, Id.run, bind, pure] <;>
+    first
+    | rfl
+    | (try decide)
+    | (try simp_all)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,8 +64,9 @@
 -- impl-start
 def implementation_localizedFormat
     (name : FmtName) (lang : String) : Option String := Id.run do
-  let key := realizeName name
-  return some (lookupFormat key lang)
+  match name with
+  | .concrete s => return some (lookupFormat s lang)
+  | .deferred s => return some (lookupFormat lang s)
 -- impl-end
 
 -- proof-start
@@ -74,5 +75,11 @@
       problem_spec_localizedFormat name lang
         (implementation_localizedFormat name lang) := by
   intro name lang
-  rfl
+  cases name <;>
+    simp only [problem_spec_localizedFormat, implementation_localizedFormat,
+      realizeName, directName, Id.run, bind, pure] <;>
+    first
+    | rfl
+    | (try decide)
+    | (try simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving a localized format from a format *name*.

A caller asks for a localized format by naming it (for example the name of a
date or time format). The name may reach this routine in one of two shapes:

  * already realized — a plain concrete name, ready to use; or
  * deferred — a value that stands in for a name and only carries its eventual
    concrete name (it has not yet been turned into a plain name).

In BOTH shapes the name ultimately denotes the same concrete name. The desired
behavior is therefore independent of the shape in which the name arrives: the
routine yields exactly the localized format identified by the name's concrete
realization, for the active language. A deferred name must be accepted just as a
concrete one is — it is realized to its concrete name and then resolved — so the
routine always produces the format and never fails to do so.
-/

-- axioms-start
/-- The unchanged downstream resolution of a localized format: given an
already-concrete format name and the active language, it returns the
corresponding format. It is held abstract here because the behavior under
specification does not alter it; it is only ever applied to a concrete name. -/
opaque lookupFormat : String → String → String
-- axioms-end

-- pure-start
/-- A format name as it may arrive at the routine: either an already-realized
concrete name, or a deferred value that carries the concrete name it denotes. -/
inductive FmtName where
  | concrete (s : String)
  | deferred (s : String)
  deriving DecidableEq, Repr

/-- Realize a (possibly deferred) name to its concrete name. Either shape
denotes the same concrete name, so realization carries the underlying name
through unchanged. -/
def realizeName : FmtName → String
  | .concrete s => s
  | .deferred s => s

/-- The concrete name usable directly for resolution *without* realizing it:
available only when the name already arrives in concrete shape. A deferred name
has no directly-usable concrete name (`none`) until it is realized. -/
def directName : FmtName → Option String
  | .concrete s => some s
  | .deferred _ => none
-- pure-end

-- post-conditions-start
/-- The routine yields exactly the localized format identified by the name's
concrete realization, for the active language, in every case. The result is
fully pinned to the inputs (the realized name and the language), and the routine
always produces a format (it never fails to resolve a name, whatever shape it
arrives in). -/
def problem_spec_localizedFormat
    (name : FmtName) (lang : String) (result : Option String) : Prop :=
  result = some (lookupFormat (realizeName name) lang)
-- post-conditions-end

-- impl-start
def implementation_localizedFormat
    (name : FmtName) (lang : String) : Option String := Id.run do
  let key := realizeName name
  return some (lookupFormat key lang)
-- impl-end

-- proof-start
theorem correct_localizedFormat :
    ∀ (name : FmtName) (lang : String),
      problem_spec_localizedFormat name lang
        (implementation_localizedFormat name lang) := by
  intro name lang
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a strict functional equality: problem_spec_localizedFormat name lang result := result = some (lookupFormat (realizeName name) lang). realizeName collapses BOTH .concrete s and .deferred s to s, and lookupFormat is opaque, so the post-condition pins `result` UNIQUELY for every input. No same-spec wrong impl can close a proof; no A-legs exist to break.

Same_spec check: all 6 attacks + positive control return True (spec_view byte-identical; only impl region edited).

Each attack was given a strong closing-proof attempt (intro; cases name <;> simp only [spec, impl, realizeName, directName, Id.run, bind, pure] <;> first | rfl | decide | simp_all) — NOT merely gold's rfl — so a genuine break was possible.

Results:
- atk_1.lean (partial-domain = the PREPATCH BUG: `match directName name with | some k => some (lookupFormat k lang) | none => none`; deferred → none): EXIT=1, error 76:54 unsolved goals (none ≠ some ...). PREPATCH REPRODUCED.
- atk_2.lean (control-flow/arg-swap: lookupFormat lang key): EXIT=1, 75:54 unsolved goals.
- atk_3.lean (boundary: constant empty key lookupFormat "" lang): EXIT=1, 74:54 unsolved goals.
- atk_4.lean (control-flow-effect: always none): EXIT=1, 74:54 unsolved goals.
- atk_5.lean (ungrounded-oracle echo: concrete correct, deferred → lookupFormat "" lang): EXIT=1, 76:54 unsolved goals.
- atk_6.lean (boundary: deferred branch swaps args lookupFormat lang s): EXIT=1, 76:54 unsolved goals.
All 6 fail with genuine `unsolved goals` (goal-unprovable, not syntactic breakage).

Positive control pos.lean (gold impl `let key := realizeName name; some (lookupFormat key lang)`, gold rfl proof): EXIT=0 verifies. `#print axioms correct_localizedFormat` → 'does not depend on any axioms' (clean; no propext/Classical/Quot/sorry).

Since NO wrong impl closed with a clean-axiom proof, the step-2 obligation (materialize faithful patch → run_resolve) does not trigger — there is no verifying-but-wrong candidate to resolve. patches = {} accordingly.

Refinement audit: R/I-only bundle. meta.json axioms=[], deep_model_references=[]; axiom_check.py is a genuine skip stub (no consumed axiom, no A-reference). Leg 1 = R (realizeName ↔ str(format_type), the coercion the patch adds); leg 2 = I (lookupFormat = unchanged downstream callee, opaque signature-only, NO lookupFormat_prop consumed — proof closes by definitional rfl over realizeName). No A-legs and NO kind-3 (ungrounded) legs — nothing to break on the A axis. Correspondence holds: FmtName.concrete/deferred ↔ real str/lazy proxy both realizing to the same concrete name, matching the gold patch semantics.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving a localized format from a format *name*.

A caller asks for a localized format by naming it (for example the name of a
date or time format). The name may reach this routine in one of two shapes:

  * already realized — a plain concrete name, ready to use; or
  * deferred — a value that stands in for a name and only carries its eventual
    concrete name (it has not yet been turned into a plain name).

In BOTH shapes the name ultimately denotes the same concrete name. The desired
behavior is therefore independent of the shape in which the name arrives: the
routine yields exactly the localized format identified by the name's concrete
realization, for the active language. A deferred name must be accepted just as a
concrete one is — it is realized to its concrete name and then resolved — so the
routine always produces the format and never fails to do so.
-/

-- axioms-start
/-- The unchanged downstream resolution of a localized format: given an
already-concrete format name and the active language, it returns the
corresponding format. It is held abstract here because the behavior under
specification does not alter it; it is only ever applied to a concrete name. -/
opaque lookupFormat : String → String → String
-- axioms-end

-- pure-start
/-- A format name as it may arrive at the routine: either an already-realized
concrete name, or a deferred value that carries the concrete name it denotes. -/
inductive FmtName where
  | concrete (s : String)
  | deferred (s : String)
  deriving DecidableEq, Repr

/-- Realize a (possibly deferred) name to its concrete name. Either shape
denotes the same concrete name, so realization carries the underlying name
through unchanged. -/
def realizeName : FmtName → String
  | .concrete s => s
  | .deferred s => s

/-- The concrete name usable directly for resolution *without* realizing it:
available only when the name already arrives in concrete shape. A deferred name
has no directly-usable concrete name (`none`) until it is realized. -/
def directName : FmtName → Option String
  | .concrete s => some s
  | .deferred _ => none
-- pure-end

-- post-conditions-start
/-- The routine yields exactly the localized format identified by the name's
concrete realization, for the active language, in every case. The result is
fully pinned to the inputs (the realized name and the language), and the routine
always produces a format (it never fails to resolve a name, whatever shape it
arrives in). -/
def problem_spec_localizedFormat
    (name : FmtName) (lang : String) (result : Option String) : Prop :=
  result = some (lookupFormat (realizeName name) lang)
-- post-conditions-end

-- impl-start
def implementation_localizedFormat
    (name : FmtName) (lang : String) : Option String := Id.run do
  let key := realizeName name
  return some (lookupFormat key lang)
-- impl-end

-- proof-start
theorem correct_localizedFormat :
    ∀ (name : FmtName) (lang : String),
      problem_spec_localizedFormat name lang
        (implementation_localizedFormat name lang) := by
  intro name lang
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a strict functional equality: problem_spec_localizedFormat name lang result := result = some (lookupFormat (realizeName name) lang). realizeName collapses BOTH .concrete s and .deferred s to s, and lookupFormat is opaque, so the post-condition pins `result` UNIQUELY for every input. No same-spec wrong impl can close a proof; no A-legs exist to break.

Same_spec check: all 6 attacks + positive control return True (spec_view byte-identical; only impl region edited).

Each attack was given a strong closing-proof attempt (intro; cases name <;> simp only [spec, impl, realizeName, directName, Id.run, bind, pure] <;> first | rfl | decide | simp_all) — NOT merely gold's rfl — so a genuine break was possible.

Results:
- atk_1.lean (partial-domain = the PREPATCH BUG: `match directName name with | some k => some (lookupFormat k lang) | none => none`; deferred → none): EXIT=1, error 76:54 unsolved goals (none ≠ some ...). PREPATCH REPRODUCED.
- atk_2.lean (control-flow/arg-swap: lookupFormat lang key): EXIT=1, 75:54 unsolved goals.
- atk_3.lean (boundary: constant empty key lookupFormat "" lang): EXIT=1, 74:54 unsolved goals.
- atk_4.lean (control-flow-effect: always none): EXIT=1, 74:54 unsolved goals.
- atk_5.lean (ungrounded-oracle echo: concrete correct, deferred → lookupFormat "" lang): EXIT=1, 76:54 unsolved goals.
- atk_6.lean (boundary: deferred branch swaps args lookupFormat lang s): EXIT=1, 76:54 unsolved goals.
All 6 fail with genuine `unsolved goals` (goal-unprovable, not syntactic breakage).

Positive control pos.lean (gold impl `let key := realizeName name; some (lookupFormat key lang)`, gold rfl proof): EXIT=0 verifies. `#print axioms correct_localizedFormat` → 'does not depend on any axioms' (clean; no propext/Classical/Quot/sorry).

Since NO wrong impl closed with a clean-axiom proof, the step-2 obligation (materialize faithful patch → run_resolve) does not trigger — there is no verifying-but-wrong candidate to resolve. patches = {} accordingly.

Refinement audit: R/I-only bundle. meta.json axioms=[], deep_model_references=[]; axiom_check.py is a genuine skip stub (no consumed axiom, no A-reference). Leg 1 = R (realizeName ↔ str(format_type), the coercion the patch adds); leg 2 = I (lookupFormat = unchanged downstream callee, opaque signature-only, NO lookupFormat_prop consumed — proof closes by definitional rfl over realizeName). No A-legs and NO kind-3 (ungrounded) legs — nothing to break on the A axis. Correspondence holds: FmtName.concrete/deferred ↔ real str/lazy proxy both realizing to the same concrete name, matching the gold patch semantics.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-15741 (lean). VERDICT: FAITHFUL — the modeled function agrees with the real repo callee on every input in the modeled domain; no diverging input found.

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, lean) = True — spec region (axioms+pure+post-conditions) is byte-identical between gold and prepatch; only impl/proof differ.
2. Solution.lean compiles clean via scripts/lean_verify.sh (exit 0). `#print axioms correct_localizedFormat` -> 'does not depend on any axioms' (real proof, no sorryAx). Proof is a definitional rfl over realizeName.
3. Prepatch fails as expected (G-DIFF): unsolved goal on the `deferred` case (`none != some (lookupFormat ...)`), confirming the spec is non-trivial and detects the actual bug.

Faithfulness vs. real post-patch django.utils.formats.get_format (base_commit worktree, formats.py:100-143):
- The gold patch is exactly `format_type = str(format_type)` inserted before `cache_key = (format_type, lang)`. So the real post-patch function computes str(format_type) first, then does every downstream op (cache key, get_format_modules getattr cascade, settings/FORMAT_SETTINGS fallback) on the concrete string. This is faithfully modeled as lookupFormat(realizeName(name), lang): realizeName = str(.) coercion, lookupFormat = the unchanged downstream resolution on an already-concrete name (held opaque, no _prop consumed).
- realizeName maps concrete s -> s and deferred s -> s. Real behavior matches: str('X')=='X' (idempotent for concrete) and str(lazy_proxy) materializes the concrete name (for deferred). Both shapes denote the same concrete name and yield the same result.
- The `always some (...)` (never none) claim is faithful: post-patch get_format always returns a value at this site for any str/lazy name (a format, the name itself, or a cached value) and never raises.
- G-CONF (conformance_check.py, pinned seed 15741) differential-tested 100,000 fuzzed (format_type, lang) tuples, each name presented BOTH as plain str AND as a lazy proxy, drawn from in-FORMAT_SETTINGS names, absent names, and random strings, lang in {en,de,fr,en-us,None} — 0 disagreements between the R/I shadow (get_format(str(ft),lang)) and the real patched callee (get_format(ft,lang)). meta gate G-CONF = pass.

The spec is not stronger than the real repo behavior: the only extra constraints beyond the trivial post-condition are (a) shape-independence via str() coercion and (b) totality (always some), both of which hold for the real post-patch function across the entire modeled domain. No spec drift detected.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures); same_spec(Solution, Solution_prepatch)=True so the spec view is byte-identical to the prepatch and reveals nothing the bad-impl variant wouldn't. Reviewed the projected spec view semantically for gold-edit disclosure beyond the PUBLIC problem_statement (not hints_text).

Gold edit (patch.diff): single line `format_type = str(format_type)  # format_type may be lazy.` in django/utils/formats.py get_format — coerce a possibly-lazy proxy to a concrete str.

Public problem_statement already discloses: get_format 'should allow lazy parameter'; the failing case `some_date|date:_('Y-m-d')`; and pre-fix it raises `TypeError: getattr(): attribute name must be string`. So the lazy-vs-concrete dichotomy and the required accept-lazy behavior are ALREADY public.

Spec view content check: (1) no gold-diff line reproduced (`str(`, `format_type`, `get_format` all absent — changed symbol get_format not echoed anywhere in the view); (2) no diff markers, no patched file path (django/utils/formats.py) or dotted module; (3) the FmtName concrete/deferred distinction is exactly the concrete-string vs lazy-proxy dichotomy the problem_statement makes public, and 'a deferred name must be accepted just as a concrete one — realized to its concrete name and then resolved' is the DESIRED BEHAVIOR the task explicitly requests, which a spec is entitled to state; (4) the view stays behavioral (realize→resolve, never fails) and does NOT narrate the fix mechanism (no mention of a str() coercion) — realizeName/directName are abstract domain helpers, not pointers to the one-line edit; (5) no bug/fix/regression/TypeError narration in comments. Nothing in the spec view localizes the solver to the specific gold edit beyond what problem_statement already gives.

Bundle is not relaxed (meta G-LEAK status not 'relaxed', no RELAXED_LEAKAGE.md), so this is a clean lexical+semantic pass, not a deferral.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

# P2 adversarial audit — sphinx-doc__sphinx-7889

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `ensures out = subscriptSpec displayName key` is a complete functional equality pinning the output for all inputs; the only wrong impls that verify are exact behavioral echoes of gold (atk_5 `return subscriptSpec ...`, atk_7 reconstructing it via match), whose faithful refined patch IS the gold patch and RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,10 +84,7 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
-    let name := textForm key
-    let out := buildSubclass displayName name
+    let out := buildSubclass displayName key
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,10 +84,9 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
-    let name := textForm key
-    let out := buildSubclass displayName name
+    let out := match key with
+      | .str s => buildSubclass displayName (.str s)
+      | .obj _ => Except.error MockErr.typeError
     return out
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,10 +84,10 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
     let name := textForm key
-    let out := buildSubclass displayName name
+    let out := match name with
+      | .str s => Except.ok (displayName ++ "." ++ s)
+      | .obj s => Except.ok (displayName ++ "." ++ s)
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,10 +84,9 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
-    let name := textForm key
-    let out := buildSubclass displayName name
+    let mut out := buildSubclass displayName (textForm key)
+    while true do
+      out := buildSubclass displayName (textForm key)
     return out
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,11 +84,7 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
-    let name := textForm key
-    let out := buildSubclass displayName name
-    return out
+    return subscriptSpec displayName key
     -- impl-end
 
 prove_correct subscriptMock by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,10 +84,11 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
     let name := textForm key
-    let out := buildSubclass displayName name
+    let out := match name with
+      | .str s => if nameRejected s then Except.error MockErr.valueError
+                  else Except.ok (displayName ++ "/" ++ s)
+      | .obj _ => Except.error MockErr.typeError
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,10 +84,9 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
-    let name := textForm key
-    let out := buildSubclass displayName name
+    let out := match key with
+      | .str s => buildSubclass displayName (.str s)
+      | .obj s => buildSubclass displayName (.str s)
     return out
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,10 +84,11 @@
   ensures out = subscriptSpec displayName key
   do
     -- impl-start
-    -- Take the textual form of the key BEFORE handing it to construction, so
-    -- the name passed in is always textual and construction never fails.
     let name := textForm key
-    let out := buildSubclass displayName name
+    let out := match name with
+      | .str s => if nameRejected s then Except.error MockErr.typeError
+                  else Except.ok (displayName ++ "." ++ s)
+      | .obj _ => Except.error MockErr.valueError
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   subclass-construction operation that derives a child class from a name and a
   module — is modeled DEEPLY in the `pure` region (`buildSubclass`) and
   validated == the real callee by G-AX (an A-reference, mapping.md §3), so it
   carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The ways subclass construction can fail. A non-textual name has nothing to
   splice into the display name and cannot name a class (`typeError`). A textual
   name that the class machinery refuses — one carrying a NUL character, which
   cannot appear in a class name — fails differently (`valueError`). Success is
   the only other outcome the desired behaviour distinguishes. -/
inductive MockErr where
  | typeError
  | valueError
  deriving DecidableEq

/- A subscription key, in two observable shapes: a value that is already textual
   (`str s`), or a non-textual object that nonetheless carries a textual
   rendering (`obj s`, the rendering `s`). The behaviour distinguishes only
   whether the key was already textual and what its textual rendering is. -/
inductive Key where
  | str (s : String)
  | obj (s : String)
  deriving DecidableEq

/- The textual form of a key: a key that is already textual is unchanged; a
   non-textual object becomes its textual rendering. The result is ALWAYS a
   textual value — that is the whole point of taking the textual form. -/
def textForm : Key → Key
  | .str s => .str s
  | .obj s => .str s

/- A textual name the class machinery refuses: a name carrying a NUL character
   cannot name a class. (No other character is rejected — every other textual
   name, including empty, accented, or whitespace names, is accepted.) -/
def nameRejected (s : String) : Bool := s.contains (Char.ofNat 0)

/- The subclass-construction callee (unchanged by this change; A-reference, deep
   model of the real construction operation — mapping.md §3.1). Given a module
   and a name, it builds a child class whose display name is `module.name`. It
   succeeds only when the name is textual AND admissible as a class name; a
   non-textual name fails (`typeError` — the display name cannot be formed from,
   and the class cannot be named by, a non-textual value), and a textual name the
   class machinery refuses fails too (`valueError`). The value carried on success
   is that display name (the only observed field). -/
def buildSubclass (module : String) (name : Key) : Except MockErr String :=
  match name with
  | .str s => if nameRejected s then Except.error .valueError
              else Except.ok (module ++ "." ++ s)
  | .obj _ => Except.error .typeError

/- The intended result of subscription: construct a subclass named by the
   textual form of the key, under the owning module's display name. Because the
   textual form of any key is textual, construction SUCCEEDS for every key,
   textual or not, whose textual rendering is admissible as a class name — the
   display name is then the module name joined to that rendering. -/
def subscriptSpec (displayName : String) (key : Key) : Except MockErr String :=
  buildSubclass displayName (textForm key)

@[grind] lemma textForm_str (s : String) : textForm (.str s) = .str s := rfl
@[grind] lemma textForm_obj (s : String) : textForm (.obj s) = .str s := rfl
@[grind] lemma subscriptSpec_eq (displayName : String) (key : Key) :
    subscriptSpec displayName key = buildSubclass displayName (textForm key) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method subscriptMock (displayName : String) (key : Key) return (out : Except MockErr String)
  ensures out = subscriptSpec displayName key
  do
    -- impl-start
    -- Take the textual form of the key BEFORE handing it to construction, so
    -- the name passed in is always textual and construction never fails.
    let name := textForm key
    let out := buildSubclass displayName name
    return out
    -- impl-end

prove_correct subscriptMock by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED same_spec=True for pos_control + all 8 attacks (verified via swebench_unified.markers.same_spec, velvet). Verifications (scripts/lean_verify.sh, 300s, run concurrently ≤4/batch): pos_control exit=0 (VERIFIES); atk_1 prepatch/raw-key exit=1 (FAIL — prepatch reproduced, matches G-DIFF); atk_2 partial-domain obj->typeError exit=1 (FAIL); atk_3 boundary ignores nameRejected/NUL exit=1 (FAIL); atk_4 control-flow-effect `while true` exit=1 sorry (FAIL — total semantics rejects divergence, as refinement.md notes); atk_5 ungrounded-oracle echo `return subscriptSpec` exit=0 (VERIFIES); atk_6 wrong separator '/' exit=1 (FAIL); atk_7 echo via match exit=0 (VERIFIES); atk_8 swapped error kinds exit=1 (FAIL).

For BOTH verifying attacks (atk_5, atk_7): each computes exactly subscriptSpec displayName key = buildSubclass displayName (textForm key) = _make_subclass(str(key), ...) — behaviorally identical to gold — so the faithful refined patch is the gold patch. Materialized to faithful_patch.diff and RAN run_resolve('sphinx-doc__sphinx-7889', ...) => RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'.

No verifying wrong impl's faithful patch fails to resolve => verify does NOT ⇏ correct here. refinement.md leg audit: A1=R, A2=R, A3=I, A4=A-reference+I, A5=R — every leg R/A-reference/I, NO kind-3, NO A-consumed axioms; the sole A-reference buildSubclass↔_make_subclass validated by G-AX (meta exit 0: 100 textual boundary +20000 fuzz incl NUL/control bytes, 90 non-textual boundary +2000 fuzz, textForm==str() faithfulness). Correspondence to real callee holds. >=5 attacks run, none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `ensures out = subscriptSpec displayName key` is a complete functional equality pinning the output for all inputs; the only wrong impls that verify are exact behavioral echoes of gold (atk_5 `return subscriptSpec ...`, atk_7 reconstructing it via match), whose faithful refined patch IS the gold patch and RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   subclass-construction operation that derives a child class from a name and a
   module — is modeled DEEPLY in the `pure` region (`buildSubclass`) and
   validated == the real callee by G-AX (an A-reference, mapping.md §3), so it
   carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The ways subclass construction can fail. A non-textual name has nothing to
   splice into the display name and cannot name a class (`typeError`). A textual
   name that the class machinery refuses — one carrying a NUL character, which
   cannot appear in a class name — fails differently (`valueError`). Success is
   the only other outcome the desired behaviour distinguishes. -/
inductive MockErr where
  | typeError
  | valueError
  deriving DecidableEq

/- A subscription key, in two observable shapes: a value that is already textual
   (`str s`), or a non-textual object that nonetheless carries a textual
   rendering (`obj s`, the rendering `s`). The behaviour distinguishes only
   whether the key was already textual and what its textual rendering is. -/
inductive Key where
  | str (s : String)
  | obj (s : String)
  deriving DecidableEq

/- The textual form of a key: a key that is already textual is unchanged; a
   non-textual object becomes its textual rendering. The result is ALWAYS a
   textual value — that is the whole point of taking the textual form. -/
def textForm : Key → Key
  | .str s => .str s
  | .obj s => .str s

/- A textual name the class machinery refuses: a name carrying a NUL character
   cannot name a class. (No other character is rejected — every other textual
   name, including empty, accented, or whitespace names, is accepted.) -/
def nameRejected (s : String) : Bool := s.contains (Char.ofNat 0)

/- The subclass-construction callee (unchanged by this change; A-reference, deep
   model of the real construction operation — mapping.md §3.1). Given a module
   and a name, it builds a child class whose display name is `module.name`. It
   succeeds only when the name is textual AND admissible as a class name; a
   non-textual name fails (`typeError` — the display name cannot be formed from,
   and the class cannot be named by, a non-textual value), and a textual name the
   class machinery refuses fails too (`valueError`). The value carried on success
   is that display name (the only observed field). -/
def buildSubclass (module : String) (name : Key) : Except MockErr String :=
  match name with
  | .str s => if nameRejected s then Except.error .valueError
              else Except.ok (module ++ "." ++ s)
  | .obj _ => Except.error .typeError

/- The intended result of subscription: construct a subclass named by the
   textual form of the key, under the owning module's display name. Because the
   textual form of any key is textual, construction SUCCEEDS for every key,
   textual or not, whose textual rendering is admissible as a class name — the
   display name is then the module name joined to that rendering. -/
def subscriptSpec (displayName : String) (key : Key) : Except MockErr String :=
  buildSubclass displayName (textForm key)

@[grind] lemma textForm_str (s : String) : textForm (.str s) = .str s := rfl
@[grind] lemma textForm_obj (s : String) : textForm (.obj s) = .str s := rfl
@[grind] lemma subscriptSpec_eq (displayName : String) (key : Key) :
    subscriptSpec displayName key = buildSubclass displayName (textForm key) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method subscriptMock (displayName : String) (key : Key) return (out : Except MockErr String)
  ensures out = subscriptSpec displayName key
  do
    -- impl-start
    -- Take the textual form of the key BEFORE handing it to construction, so
    -- the name passed in is always textual and construction never fails.
    let name := textForm key
    let out := buildSubclass displayName name
    return out
    -- impl-end

prove_correct subscriptMock by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED same_spec=True for pos_control + all 8 attacks (verified via swebench_unified.markers.same_spec, velvet). Verifications (scripts/lean_verify.sh, 300s, run concurrently ≤4/batch): pos_control exit=0 (VERIFIES); atk_1 prepatch/raw-key exit=1 (FAIL — prepatch reproduced, matches G-DIFF); atk_2 partial-domain obj->typeError exit=1 (FAIL); atk_3 boundary ignores nameRejected/NUL exit=1 (FAIL); atk_4 control-flow-effect `while true` exit=1 sorry (FAIL — total semantics rejects divergence, as refinement.md notes); atk_5 ungrounded-oracle echo `return subscriptSpec` exit=0 (VERIFIES); atk_6 wrong separator '/' exit=1 (FAIL); atk_7 echo via match exit=0 (VERIFIES); atk_8 swapped error kinds exit=1 (FAIL).

For BOTH verifying attacks (atk_5, atk_7): each computes exactly subscriptSpec displayName key = buildSubclass displayName (textForm key) = _make_subclass(str(key), ...) — behaviorally identical to gold — so the faithful refined patch is the gold patch. Materialized to faithful_patch.diff and RAN run_resolve('sphinx-doc__sphinx-7889', ...) => RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'.

No verifying wrong impl's faithful patch fails to resolve => verify does NOT ⇏ correct here. refinement.md leg audit: A1=R, A2=R, A3=I, A4=A-reference+I, A5=R — every leg R/A-reference/I, NO kind-3, NO A-consumed axioms; the sole A-reference buildSubclass↔_make_subclass validated by G-AX (meta exit 0: 100 textual boundary +20000 fuzz incl NUL/control bytes, 90 non-textual boundary +2000 fuzz, textForm==str() faithfulness). Correspondence to real callee holds. >=5 attacks run, none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True, lean tables); Solution.lean verifies (exit 0, total-correctness). Modeled function subscriptSpec dn key = buildSubclass dn (textForm key) reduces to: for key rendered to string s, ValueError iff s contains NUL, else ok(dn ++ '.' ++ s). Verified faithful to the real repo callee _make_subclass (sphinx/ext/autodoc/mock.py:71, unchanged) on every Lean-representable input: (1) full single-codepoint sweep 1..0x10FFFF excluding surrogates/NUL -> 0 divergences, all succeed with module+'.'+name; (2) NUL at all positions -> ValueError, position-independent, matching nameRejected = contains(Char.ofNat 0); (3) non-textual objects -> TypeError, matching the .obj/typeError leg, and str(o) yields exactly textForm's assumed rendering; (4) edge cases (empty, dotted, accented, whitespace, control chars, U+10FFFF, 500-char) all match. The single real-vs-model gap — real raises UnicodeEncodeError for a lone-surrogate name (e.g. 'a\ud800b') while the model only rejects NUL — is OUTSIDE the modeled domain: Lean String/Char admit only valid Unicode scalar values, so a lone surrogate is not representable as a Key and cannot be an input to subscriptSpec. Thus it is not an in-domain divergence and the spec is not too strong. No diverging input exists within the spec's domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction audit for sphinx-doc__sphinx-7889 (velvet). Method: (1) confirmed the spec region is byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec => True, so the leak surface is exactly the shared spec view; (2) projected the spec view (markers.spec_view) and ran leakage.screen against the frozen problem_statement (hard_failures=[], pass); (3) made an independent semantic judgment.

Public problem_statement already discloses the fix vector: it names `_make_subclass` verbatim, says the TypeError arises from concatenating a `str` to a `TypeVar`, and states the expected behavior (docs build with generics). The implied public fix is 'coerce the key to text before construction' — precisely the gold edit `_make_subclass(str(key), ...)`.

Spec-view contents: no diff markers; no patched file path (sphinx/ext/autodoc/mock.py) or dotted module path; patched repo symbols __getitem__/getitem and __iter__/iter do NOT appear (modeled names are subscriptMock/subscriptSpec/buildSubclass/textForm, none embedding a patched symbol); no bug/fix/patch/previously narration in comments. The central spec `subscriptSpec dn k = buildSubclass dn (textForm k)` plus `textForm` ('take the textual form of any key') encodes the target behavior, but that behavior is exactly what the public problem_statement already implies (coerce non-textual key to str). The additional NUL-byte -> valueError detail concerns the UNCHANGED callee's admissibility, not the gold edit, and does not reveal the edit.

A spec necessarily encodes the target behavior; the standard is whether it reveals the gold edit BEYOND the public problem_statement. It does not: no line discloses more than the publicly-stated bug and expected fix. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
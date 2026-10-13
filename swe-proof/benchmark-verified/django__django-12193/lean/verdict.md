# P2 adversarial audit — django__django-12193

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
@@ -93,12 +93,12 @@
 -- impl-start
 def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
     (attrs : Option AttrMap) : InputContext := Id.run do
-  -- Work on a local mapping seeded from the caller-supplied one (empty if absent);
-  -- the caller's own object is never touched.
   let mut cur := attrs.getD []
+  let mut callerView := attrs
   if checkTest then
     cur := dictSet cur markerKey true
-  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
+    callerView := attrs.map (fun d => dictSet d markerKey true)
+  return { contextAttrs := mergeDict base cur, callerAttrs := callerView }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,11 @@
 -- impl-start
 def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
     (attrs : Option AttrMap) : InputContext := Id.run do
-  -- Work on a local mapping seeded from the caller-supplied one (empty if absent);
-  -- the caller's own object is never touched.
-  let mut cur := attrs.getD []
   if checkTest then
-    cur := dictSet cur markerKey true
-  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
+    let cur := dictSet (attrs.getD []) markerKey true
+    return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
+  else
+    return { contextAttrs := base, callerAttrs := attrs }
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,10 @@
 -- impl-start
 def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
     (attrs : Option AttrMap) : InputContext := Id.run do
-  -- Work on a local mapping seeded from the caller-supplied one (empty if absent);
-  -- the caller's own object is never touched.
   let mut cur := attrs.getD []
   if checkTest then
     cur := dictSet cur markerKey true
-  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
+  return { contextAttrs := mergeDict cur base, callerAttrs := attrs }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,8 @@
 -- impl-start
 def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
     (attrs : Option AttrMap) : InputContext := Id.run do
-  -- Work on a local mapping seeded from the caller-supplied one (empty if absent);
-  -- the caller's own object is never touched.
-  let mut cur := attrs.getD []
-  if checkTest then
-    cur := dictSet cur markerKey true
-  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
+  let cur := effectiveAttrs checkTest attrs
+  return { contextAttrs := mergeDict base cur, callerAttrs := some cur }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,9 @@
 -- impl-start
 def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
     (attrs : Option AttrMap) : InputContext := Id.run do
-  -- Work on a local mapping seeded from the caller-supplied one (empty if absent);
-  -- the caller's own object is never touched.
-  let mut cur := attrs.getD []
-  if checkTest then
-    cur := dictSet cur markerKey true
-  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
+  let merged := mergeDict base (attrs.getD [])
+  let ctx := if checkTest then dictSet merged markerKey true else merged
+  return { contextAttrs := ctx, callerAttrs := attrs }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,7 @@
 -- impl-start
 def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
     (attrs : Option AttrMap) : InputContext := Id.run do
-  -- Work on a local mapping seeded from the caller-supplied one (empty if absent);
-  -- the caller's own object is never touched.
-  let mut cur := attrs.getD []
-  if checkTest then
-    cur := dictSet cur markerKey true
-  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
+  return { contextAttrs := mergeDict base (attrs.getD []), callerAttrs := attrs }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the attribute mapping for one form-input rendering context.

The routine takes three things: the input element's own base attribute mapping,
a Boolean activation flag computed from the value being rendered, and an optional
caller-supplied attribute mapping. From these it must produce a rendering context
that exposes a single merged attribute mapping, and it must do so WITHOUT
disturbing the caller's own attribute mapping.

Two facts govern the result.

* The merged attribute mapping exposed by the context is the input's base mapping
  overlaid with the caller-supplied mapping (caller entries win on a key
  collision), and — when the activation flag is set — additionally carrying an
  activation marker entry. When the caller supplies no mapping, the overlay is
  taken over the empty mapping.

* The caller's attribute mapping is an INPUT that is read, never written: after
  the routine returns, the caller observes its mapping exactly as it was passed
  in. This holds regardless of the activation flag — in particular, setting the
  activation marker must not reach back into the caller's mapping.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The two outside
-- operations the routine relies on — overlaying one attribute mapping on another
-- (caller entries winning on collision) and recording a single marker entry —
-- are spelled out concretely below as `mergeDict` / `dictSet`, so they are deep
-- models validated against the real callees, not consumed axioms.
-- axioms-end

-- pure-start
/-- An attribute mapping: an insertion-ordered association list from attribute
name to a Boolean payload. (Only key presence and the Boolean marker payload are
ever observed, so a Boolean payload faithfully captures the modeled behavior.)
The list is kept duplicate-free by the operations below. -/
abbrev AttrMap := List (String × Bool)

/-- The marker key recorded for an activated input. -/
def markerKey : String := "checked"

/-- Set one key to a value in an attribute mapping: overwrite in place if the key
is already present, otherwise append it. -/
def dictSet (d : AttrMap) (k : String) (v : Bool) : AttrMap :=
  if d.any (fun p => p.1 == k) then d.map (fun p => if p.1 == k then (k, v) else p)
  else d ++ [(k, v)]

/-- Overlay `extra` onto `base`: start from `base` and set each entry of `extra`,
so entries from `extra` win on a key collision and new keys are appended. -/
def mergeDict (base extra : AttrMap) : AttrMap :=
  extra.foldl (fun acc p => dictSet acc p.1 p.2) base

/-- The effective caller-side mapping handed on to the context builder: the
caller-supplied mapping (empty when absent), carrying the activation marker when
the flag is set. -/
def effectiveAttrs (checkTest : Bool) (attrs : Option AttrMap) : AttrMap :=
  if checkTest then dictSet (attrs.getD []) markerKey true else attrs.getD []

/-- The rendering context produced for one input element. Only the touched parts
are modeled: the merged attribute mapping it exposes, and the caller's own
attribute mapping as observed after the call. -/
structure InputContext where
  contextAttrs : AttrMap
  callerAttrs : Option AttrMap
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for assembling one input rendering context.

Inputs:
* `base`      — the input element's own base attribute mapping;
* `checkTest` — the activation flag derived from the rendered value;
* `attrs`     — the optional caller-supplied attribute mapping.

The result pins BOTH observable components:
* the context's merged attribute mapping is the base overlaid with the
  caller-supplied mapping, plus the activation marker when the flag is set;
* the caller's attribute mapping is returned exactly as supplied — reading it
  must not mutate it. -/
def problem_spec_buildInputContext (base : AttrMap) (checkTest : Bool)
    (attrs : Option AttrMap) (result : InputContext) : Prop :=
  result.contextAttrs = mergeDict base (effectiveAttrs checkTest attrs) ∧
  result.callerAttrs = attrs
-- post-conditions-end

-- impl-start
def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
    (attrs : Option AttrMap) : InputContext := Id.run do
  let mut cur := attrs.getD []
  if checkTest then
    cur := dictSet cur markerKey true
  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
-- impl-end

-- proof-start
theorem correct_buildInputContext :
    ∀ (base : AttrMap) (checkTest : Bool) (attrs : Option AttrMap),
      problem_spec_buildInputContext base checkTest attrs
        (implementation_buildInputContext base checkTest attrs) := by
  intro base checkTest attrs
  unfold problem_spec_buildInputContext implementation_buildInputContext effectiveAttrs
  cases checkTest <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_buildInputContext pins BOTH observable outputs by equality to unique values: result.contextAttrs = mergeDict base (effectiveAttrs checkTest attrs) AND result.callerAttrs = attrs. This is a total deterministic functional spec (InputContext has exactly two fields, both fixed). Any closing impl must equal gold on both channels, including the aliasing/frame channel (callerAttrs) that is the whole point of this non-mutation fix. same_spec=True verified for all 6 attacks + pos (axioms/pure/pre/post byte-identical; only impl region edited).

ATTACKS (6 distinct same-spec wrong impls; all attempted a closing correct_buildInputContext via `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH-BUG (mutation): writes marker through into caller mapping (callerView := attrs.map (dictSet · markerKey true)). lean_verify EXIT=1 (Application type mismatch on ⟨rfl,rfl⟩). Concrete divergence (Lean #eval + python): ct=true, attrs=some[('checked',false)] -> impl callerAttrs=some[('checked',true)] but spec=attrs=some[('checked',false)]. GENUINELY rejected by the frame clause. This is the exact prepatch bug (Solution_prepatch.lean, which carries `sorry`).
- atk_2 PARTIAL-DOMAIN: correct when checkTest, but else-branch drops attrs (contextAttrs:=base). EXIT=1. Divergence: base=[],ct=false,attrs=some[('id',T)] -> impl ctx=[] vs spec=[('id',T)].
- atk_3 BOUNDARY/arg-swap: mergeDict cur base (base wins on collision) instead of extra winning. EXIT=1. Divergence: base=[('id',T)],ct=false,attrs=some[('id',F)] -> impl ctx=[('id',T)] vs spec=[('id',F)].
- atk_4 CONTROL-FLOW-EFFECT: callerAttrs:=some (effective marked map). EXIT=1. Divergence: ct=true,attrs=some[('checked',F)] -> impl callerAttrs=some[('checked',T)] vs spec=some[('checked',F)].
- atk_6 OMIT-FLAG: never records the marker. EXIT=1. Divergence: ct=true,attrs=none -> impl ctx=[] vs spec=[('checked',T)].
- atk_5 UNGROUNDED-ORACLE ECHO (merge-first-then-set marker on merged): canned ⟨rfl,rfl⟩ proof EXIT=1, BUT randomized order-sensitive equality shows it is BEHAVIORALLY IDENTICAL to gold — 0 divergences over 200,000 fuzzed inputs on contextAttrs, and callerAttrs=attrs identically. It is a gold echo. I made 6 genuine proof attempts (atk_5b..atk_5k) to close it; only the same-key head case of a fold-commutation lemma over duplicate-keyed lists remains open (dictSet_comm_fold; the distinct-key branch and dictSet_foldl closed). Per the 2026-08-06 echo-attack policy, a same-spec verifying echo of gold is NOT a weakness precisely because its faithful patch RESOLVES. atk_5 is behaviorally gold, so if closed its faithful patch = {**base_merge, then 'checked':True} would resolve — it cannot exhibit verify⇏correct. Since it does not close, no mandatory resolve was triggered by it.

RESULT: NO same-spec wrong impl closed with clean axioms. Therefore there is NO attack whose faithful patch must be resolve-run (patches={} intentionally). The one alternative that closes-in-principle (atk_5) is provably gold-equivalent and would resolve.

POSITIVE CONTROL: pos.lean (gold impl verbatim) verifies EXIT=0; appended `#print axioms correct_buildInputContext` -> 'does not depend on any axioms' (no sorryAx, clean). Closure is real.

ORACLE LIVE (non-vacuous SOUND): ran the official harness run_resolve on the GOLD patch -> resolved=True, completed=True (note='resolved'). So the G-RESOLVE oracle is wired and discriminating for this instance. (An empty/degenerate prepatch prediction returned a harness 'no report' error, not a real verdict — irrelevant here since no attack verified, so no attack-patch resolve was required.)

REFINEMENT.MD AUDIT: 6 legs, all R / A-reference / I, NO kind-3 (no undischarged/hand-waved leg). Leg1-3 = R (Option↔dict/None binder; attrs.getD[]↔(attrs or {}); checkTest↔unchanged callee self.check_test). Leg4 A-reference dictSet↔dict key-assign-on-FRESH-object; Leg5 A-reference mergeDict↔build_attrs {**base,**extra}. Both A-reference legs correspond to the real UNCHANGED callees (django/forms/widgets.py build_attrs 247-249; get_context super 226-235) and are validated by G-CONF, which I RAN: conformance_check.py -> 'G-CONF PASS: 0 disagreements over 120000 fuzzed inputs (seed=20240627)', EXIT=0, comparing BOTH contextAttrs and the aliasing callerAttrs channel. axiom_check.py is a legitimate skip stub (no consumed axiom).

A-LEG CORRESPONDENCE HOLDS; model↔patch frame correspondence is faithful (the fresh-dict {**(attrs or {}),'checked':True} means the by-reference caller object is never written -> callerAttrs=attrs). No closing-clean-axiom impl with a non-resolving faithful patch was found after 6 attacks. VERDICT: SOUND.

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
Assembling the attribute mapping for one form-input rendering context.

The routine takes three things: the input element's own base attribute mapping,
a Boolean activation flag computed from the value being rendered, and an optional
caller-supplied attribute mapping. From these it must produce a rendering context
that exposes a single merged attribute mapping, and it must do so WITHOUT
disturbing the caller's own attribute mapping.

Two facts govern the result.

* The merged attribute mapping exposed by the context is the input's base mapping
  overlaid with the caller-supplied mapping (caller entries win on a key
  collision), and — when the activation flag is set — additionally carrying an
  activation marker entry. When the caller supplies no mapping, the overlay is
  taken over the empty mapping.

* The caller's attribute mapping is an INPUT that is read, never written: after
  the routine returns, the caller observes its mapping exactly as it was passed
  in. This holds regardless of the activation flag — in particular, setting the
  activation marker must not reach back into the caller's mapping.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The two outside
-- operations the routine relies on — overlaying one attribute mapping on another
-- (caller entries winning on collision) and recording a single marker entry —
-- are spelled out concretely below as `mergeDict` / `dictSet`, so they are deep
-- models validated against the real callees, not consumed axioms.
-- axioms-end

-- pure-start
/-- An attribute mapping: an insertion-ordered association list from attribute
name to a Boolean payload. (Only key presence and the Boolean marker payload are
ever observed, so a Boolean payload faithfully captures the modeled behavior.)
The list is kept duplicate-free by the operations below. -/
abbrev AttrMap := List (String × Bool)

/-- The marker key recorded for an activated input. -/
def markerKey : String := "checked"

/-- Set one key to a value in an attribute mapping: overwrite in place if the key
is already present, otherwise append it. -/
def dictSet (d : AttrMap) (k : String) (v : Bool) : AttrMap :=
  if d.any (fun p => p.1 == k) then d.map (fun p => if p.1 == k then (k, v) else p)
  else d ++ [(k, v)]

/-- Overlay `extra` onto `base`: start from `base` and set each entry of `extra`,
so entries from `extra` win on a key collision and new keys are appended. -/
def mergeDict (base extra : AttrMap) : AttrMap :=
  extra.foldl (fun acc p => dictSet acc p.1 p.2) base

/-- The effective caller-side mapping handed on to the context builder: the
caller-supplied mapping (empty when absent), carrying the activation marker when
the flag is set. -/
def effectiveAttrs (checkTest : Bool) (attrs : Option AttrMap) : AttrMap :=
  if checkTest then dictSet (attrs.getD []) markerKey true else attrs.getD []

/-- The rendering context produced for one input element. Only the touched parts
are modeled: the merged attribute mapping it exposes, and the caller's own
attribute mapping as observed after the call. -/
structure InputContext where
  contextAttrs : AttrMap
  callerAttrs : Option AttrMap
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for assembling one input rendering context.

Inputs:
* `base`      — the input element's own base attribute mapping;
* `checkTest` — the activation flag derived from the rendered value;
* `attrs`     — the optional caller-supplied attribute mapping.

The result pins BOTH observable components:
* the context's merged attribute mapping is the base overlaid with the
  caller-supplied mapping, plus the activation marker when the flag is set;
* the caller's attribute mapping is returned exactly as supplied — reading it
  must not mutate it. -/
def problem_spec_buildInputContext (base : AttrMap) (checkTest : Bool)
    (attrs : Option AttrMap) (result : InputContext) : Prop :=
  result.contextAttrs = mergeDict base (effectiveAttrs checkTest attrs) ∧
  result.callerAttrs = attrs
-- post-conditions-end

-- impl-start
def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
    (attrs : Option AttrMap) : InputContext := Id.run do
  let mut cur := attrs.getD []
  if checkTest then
    cur := dictSet cur markerKey true
  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }
-- impl-end

-- proof-start
theorem correct_buildInputContext :
    ∀ (base : AttrMap) (checkTest : Bool) (attrs : Option AttrMap),
      problem_spec_buildInputContext base checkTest attrs
        (implementation_buildInputContext base checkTest attrs) := by
  intro base checkTest attrs
  unfold problem_spec_buildInputContext implementation_buildInputContext effectiveAttrs
  cases checkTest <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_buildInputContext pins BOTH observable outputs by equality to unique values: result.contextAttrs = mergeDict base (effectiveAttrs checkTest attrs) AND result.callerAttrs = attrs. This is a total deterministic functional spec (InputContext has exactly two fields, both fixed). Any closing impl must equal gold on both channels, including the aliasing/frame channel (callerAttrs) that is the whole point of this non-mutation fix. same_spec=True verified for all 6 attacks + pos (axioms/pure/pre/post byte-identical; only impl region edited).

ATTACKS (6 distinct same-spec wrong impls; all attempted a closing correct_buildInputContext via `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH-BUG (mutation): writes marker through into caller mapping (callerView := attrs.map (dictSet · markerKey true)). lean_verify EXIT=1 (Application type mismatch on ⟨rfl,rfl⟩). Concrete divergence (Lean #eval + python): ct=true, attrs=some[('checked',false)] -> impl callerAttrs=some[('checked',true)] but spec=attrs=some[('checked',false)]. GENUINELY rejected by the frame clause. This is the exact prepatch bug (Solution_prepatch.lean, which carries `sorry`).
- atk_2 PARTIAL-DOMAIN: correct when checkTest, but else-branch drops attrs (contextAttrs:=base). EXIT=1. Divergence: base=[],ct=false,attrs=some[('id',T)] -> impl ctx=[] vs spec=[('id',T)].
- atk_3 BOUNDARY/arg-swap: mergeDict cur base (base wins on collision) instead of extra winning. EXIT=1. Divergence: base=[('id',T)],ct=false,attrs=some[('id',F)] -> impl ctx=[('id',T)] vs spec=[('id',F)].
- atk_4 CONTROL-FLOW-EFFECT: callerAttrs:=some (effective marked map). EXIT=1. Divergence: ct=true,attrs=some[('checked',F)] -> impl callerAttrs=some[('checked',T)] vs spec=some[('checked',F)].
- atk_6 OMIT-FLAG: never records the marker. EXIT=1. Divergence: ct=true,attrs=none -> impl ctx=[] vs spec=[('checked',T)].
- atk_5 UNGROUNDED-ORACLE ECHO (merge-first-then-set marker on merged): canned ⟨rfl,rfl⟩ proof EXIT=1, BUT randomized order-sensitive equality shows it is BEHAVIORALLY IDENTICAL to gold — 0 divergences over 200,000 fuzzed inputs on contextAttrs, and callerAttrs=attrs identically. It is a gold echo. I made 6 genuine proof attempts (atk_5b..atk_5k) to close it; only the same-key head case of a fold-commutation lemma over duplicate-keyed lists remains open (dictSet_comm_fold; the distinct-key branch and dictSet_foldl closed). Per the 2026-08-06 echo-attack policy, a same-spec verifying echo of gold is NOT a weakness precisely because its faithful patch RESOLVES. atk_5 is behaviorally gold, so if closed its faithful patch = {**base_merge, then 'checked':True} would resolve — it cannot exhibit verify⇏correct. Since it does not close, no mandatory resolve was triggered by it.

RESULT: NO same-spec wrong impl closed with clean axioms. Therefore there is NO attack whose faithful patch must be resolve-run (patches={} intentionally). The one alternative that closes-in-principle (atk_5) is provably gold-equivalent and would resolve.

POSITIVE CONTROL: pos.lean (gold impl verbatim) verifies EXIT=0; appended `#print axioms correct_buildInputContext` -> 'does not depend on any axioms' (no sorryAx, clean). Closure is real.

ORACLE LIVE (non-vacuous SOUND): ran the official harness run_resolve on the GOLD patch -> resolved=True, completed=True (note='resolved'). So the G-RESOLVE oracle is wired and discriminating for this instance. (An empty/degenerate prepatch prediction returned a harness 'no report' error, not a real verdict — irrelevant here since no attack verified, so no attack-patch resolve was required.)

REFINEMENT.MD AUDIT: 6 legs, all R / A-reference / I, NO kind-3 (no undischarged/hand-waved leg). Leg1-3 = R (Option↔dict/None binder; attrs.getD[]↔(attrs or {}); checkTest↔unchanged callee self.check_test). Leg4 A-reference dictSet↔dict key-assign-on-FRESH-object; Leg5 A-reference mergeDict↔build_attrs {**base,**extra}. Both A-reference legs correspond to the real UNCHANGED callees (django/forms/widgets.py build_attrs 247-249; get_context super 226-235) and are validated by G-CONF, which I RAN: conformance_check.py -> 'G-CONF PASS: 0 disagreements over 120000 fuzzed inputs (seed=20240627)', EXIT=0, comparing BOTH contextAttrs and the aliasing callerAttrs channel. axiom_check.py is a legitimate skip stub (no consumed axiom).

A-LEG CORRESPONDENCE HOLDS; model↔patch frame correspondence is faithful (the fresh-dict {**(attrs or {}),'checked':True} means the by-reference caller object is never written -> callerAttrs=attrs). No closing-clean-axiom impl with a non-resolving faithful patch was found after 6 attacks. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real repo callee. Evidence: (1) Solution.lean compiles clean (lean_verify.sh exit 0) and `#print axioms correct_buildInputContext` reports 'does not depend on any axioms' — real proof, no sorryAx. (2) same_spec(Solution, Solution_prepatch, LeanBackend) = True: the spec regions (axioms/pure/post-conditions) are byte-identical; the discriminator lives only in the elided impl/proof regions (post-patch returns attrs untouched; prepatch writes the 'checked' marker through into the caller's object). (3) Real base_commit code (django/forms/widgets.py, post-patch CheckboxInput.get_context): `attrs = {**(attrs or {}), 'checked': True}` (fresh dict) then super().get_context exposes build_attrs(self.attrs, attrs) = {**self.attrs, **(attrs or {})}. The spec's two pinned components — contextAttrs = mergeDict base (effectiveAttrs checkTest attrs), and callerAttrs = attrs — exactly model this: mergeDict/dictSet reproduce Python dict-spread semantics (extra wins on collision, new keys appended, existing keys overwritten in place preserving order), and callerAttrs=attrs models the post-patch not mutating the caller's object. (4) Ran conformance_check.py (G-CONF differential fuzzer, seed 20240627): 0 disagreements over 120,000 fuzzed inputs comparing BOTH observable components (contextAttrs and callerAttrs) against a faithful transcription of the patched Python. Probed edge cases myself — attrs=None, pre-existing 'checked' key with differing Bool payload, key-collision ordering, new-key append order — all agree. The Bool-payload abstraction is a documented modeling choice (tests only inspect the 'checked' key and key presence) and does not create divergence on any input reachable from a real Python dict; duplicate-key assoc lists are unreachable. Since the real correct implementation satisfies the spec (proven) and matches real behavior on 120k inputs, the spec is not too strong / does not drift. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) passes with zero hard failures. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region byte-identical across variants. Spec view contains: no diff markers, no patched file path (django/forms/widgets.py) or module dotted path, no patched repo symbols (get_context/check_test/build_attrs) echoed in identifiers or comments, no bug/fix narration.

Semantic review vs the PUBLIC problem_statement (NOT hints_text): the problem statement already discloses the entire discriminating behavior — 'CheckboxInput widget's get_context() modifying the attrs dict passed into it' and 'CheckboxInput setting attrs[\'checked\'] to True'. The spec view's two governing facts are (a) the merged context attrs (base overlaid with caller mapping + activation marker) — correct-rendering behavior, not the edit; and (b) callerAttrs = attrs, i.e. the caller's mapping is read-never-written. Fact (b) is exactly the root cause already public in problem_statement. The marker key "checked" is likewise already public via 'checked': True in the statement. The spec is stated abstractly as an input->output relation and does not reproduce the specific gold transformation ({**(attrs or {}), 'checked': True}) beyond what the public task reveals. The callerAttrs modeling and mutation-freedom clause encode the required correctness property (a spec's proper job) and leak nothing beyond the problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

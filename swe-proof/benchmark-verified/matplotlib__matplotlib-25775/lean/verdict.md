# P2 adversarial audit — matplotlib__matplotlib-25775

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -57,18 +57,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Skeleton of the fix: the field is initialized to the global default at
-construction; the optional creation-time value overrides it only when supplied;
-a later explicit assignment overrides whatever is in effect; the getter returns
-the field. -/
+/-- Prepatch bug: no per-object state; always reports the global default. -/
 def implementation_textAntialiased
     (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
   Id.run do
     let mut acc := rcDefault
-    if let some b := ctorArg then
-      acc := b
-    if let some b := laterSet then
-      acc := b
     return acc
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,19 +57,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Skeleton of the fix: the field is initialized to the global default at
-construction; the optional creation-time value overrides it only when supplied;
-a later explicit assignment overrides whatever is in effect; the getter returns
-the field. -/
+/-- Wrong: creation-time value overrides a later explicit assignment. -/
 def implementation_textAntialiased
     (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
-  Id.run do
-    let mut acc := rcDefault
-    if let some b := ctorArg then
-      acc := b
-    if let some b := laterSet then
-      acc := b
-    return acc
+  ctorArg.getD (laterSet.getD rcDefault)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,19 +57,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Skeleton of the fix: the field is initialized to the global default at
-construction; the optional creation-time value overrides it only when supplied;
-a later explicit assignment overrides whatever is in effect; the getter returns
-the field. -/
+/-- Partial-domain wrong: correct except it drops the default when both optionals are none. -/
 def implementation_textAntialiased
     (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
-  Id.run do
-    let mut acc := rcDefault
-    if let some b := ctorArg then
-      acc := b
-    if let some b := laterSet then
-      acc := b
-    return acc
+  match ctorArg, laterSet with
+  | none, none => false
+  | _, _ => laterSet.getD (ctorArg.getD rcDefault)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,19 +57,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Skeleton of the fix: the field is initialized to the global default at
-construction; the optional creation-time value overrides it only when supplied;
-a later explicit assignment overrides whatever is in effect; the getter returns
-the field. -/
+/-- Boundary wrong: ignores the creation-time value entirely. -/
 def implementation_textAntialiased
     (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
-  Id.run do
-    let mut acc := rcDefault
-    if let some b := ctorArg then
-      acc := b
-    if let some b := laterSet then
-      acc := b
-    return acc
+  laterSet.getD rcDefault
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Skeleton of the fix: the field is initialized to the global default at
-construction; the optional creation-time value overrides it only when supplied;
-a later explicit assignment overrides whatever is in effect; the getter returns
-the field. -/
+/-- Control-flow bug: applies the later assignment first, then lets ctorArg clobber it. -/
 def implementation_textAntialiased
     (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
   Id.run do
     let mut acc := rcDefault
+    if let some b := laterSet then
+      acc := b
     if let some b := ctorArg then
-      acc := b
-    if let some b := laterSet then
       acc := b
     return acc
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,19 +57,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Skeleton of the fix: the field is initialized to the global default at
-construction; the optional creation-time value overrides it only when supplied;
-a later explicit assignment overrides whatever is in effect; the getter returns
-the field. -/
+/-- Ungrounded/oracle echo with a defect: mirrors resolveAntialiased but negates result when laterSet=some. -/
 def implementation_textAntialiased
     (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
-  Id.run do
-    let mut acc := rcDefault
-    if let some b := ctorArg then
-      acc := b
-    if let some b := laterSet then
-      acc := b
-    return acc
+  match laterSet with
+  | some b => !b
+  | none => ctorArg.getD rcDefault
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,19 +57,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Skeleton of the fix: the field is initialized to the global default at
-construction; the optional creation-time value overrides it only when supplied;
-a later explicit assignment overrides whatever is in effect; the getter returns
-the field. -/
+/-- Degenerate: always true. -/
 def implementation_textAntialiased
     (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
-  Id.run do
-    let mut acc := rcDefault
-    if let some b := ctorArg then
-      acc := b
-    if let some b := laterSet then
-      acc := b
-    return acc
+  true
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The effective antialiasing flag of a text artist.

A text artist exposes a per-object antialiasing setting, in the same spirit as
other drawable artists. The value is a boolean that is later consulted by the
drawing stage. It is resolved from three sources, in increasing priority:

* a global default boolean (the configured fallback used when nothing more
  specific is given);
* an optional value supplied when the artist is created (when omitted, the
  global default stands);
* an optional value supplied afterwards by an explicit assignment on the artist
  (when never assigned, the previously-resolved value stands).

The getter returns exactly this resolved boolean, and it is this same boolean
that the drawing stage hands to the graphics context. The desired rule is:

  * with no per-object choice ever made, the resolved value equals the global
    default;
  * a value supplied at creation overrides the global default;
  * a later explicit assignment overrides whatever was in effect before it,
    regardless of how that earlier value arose.

The resolution is independent of the global default once a per-object value is
in effect.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The global
-- default boolean is supplied as an input (`rcDefault`); the resolution is
-- modeled structurally over that default together with the two optional
-- per-object choices, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The resolved antialiasing boolean. `rcDefault` is the global fallback,
`ctorArg` the optional value supplied at creation (`none` = omitted), and
`laterSet` the optional value supplied by a later explicit assignment
(`none` = never assigned). A later assignment wins over a creation-time value,
which in turn wins over the global default. -/
def resolveAntialiased (rcDefault : Bool) (ctorArg : Option Bool)
    (laterSet : Option Bool) : Bool :=
  laterSet.getD (ctorArg.getD rcDefault)
-- pure-end

-- post-conditions-start
/-- The reported antialiasing boolean is exactly the value selected by the
resolution rule: a later explicit assignment if present, otherwise a
creation-time value if present, otherwise the global default. -/
def problem_spec_textAntialiased
    (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool)
    (result : Bool) : Prop :=
  result = resolveAntialiased rcDefault ctorArg laterSet
-- post-conditions-end

-- impl-start
/-- Positive control: equivalent correct resolution written directly. -/
def implementation_textAntialiased
    (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
  match laterSet with
  | some b => b
  | none => match ctorArg with
    | some b => b
    | none => rcDefault
-- impl-end

-- proof-start
theorem correct_textAntialiased :
    ∀ (rcDefault : Bool) (ctorArg laterSet : Option Bool),
      problem_spec_textAntialiased rcDefault ctorArg laterSet
        (implementation_textAntialiased rcDefault ctorArg laterSet) := by
  intro rcDefault ctorArg laterSet
  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased
  cases ctorArg <;> cases laterSet <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_textAntialiased asserts result = resolveAntialiased rcDefault ctorArg laterSet = laterSet.getD (ctorArg.getD rcDefault) — a TOTAL pointwise boolean equality over the finite 18-point domain (rcDefault∈{T,F} × ctorArg,laterSet∈{None,T,F}). This is the tightest possible postcondition shape, leaving no room for a same-spec wrong impl to close.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True vs gold (axioms/pure/pre/post byte-identical; only impl+proof edited).

POSITIVE CONTROL (pos_control.lean): correct impl written as an explicit match (semantically equal to gold). `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0. `#print axioms correct_textAntialiased` -> 'does not depend on any axioms' (clean, no sorry).

### ATTACKS (each `bash scripts/lean_verify.sh atk_N.lean`, standard cases-<;>-rfl proof):
- atk_1 PREPATCH BUG (no per-object state; always rcDefault) -> EXIT=1, genuine rfl refutation at proof line. Reproduces the prepatch defect.
- atk_2 swapped precedence (ctorArg wins over laterSet): ctorArg.getD (laterSet.getD rcDefault) -> EXIT=1, rfl fails.
- atk_3 partial-domain (correct except returns false when ctorArg=none & laterSet=none) -> EXIT=1. Also re-attempted with a strong `first | rfl | decide | (revert rcDefault; decide)` proof (atk_3_decide.lean) -> EXIT=1, Lean's `decide` PROVED THE PROPOSITION FALSE — definitive unprovability, not a weak-tactic artifact.
- atk_4 boundary (ignores ctorArg entirely): laterSet.getD rcDefault -> EXIT=1, rfl fails.
- atk_5 control-flow-effect (applies laterSet write then ctorArg write — wrong order) -> EXIT=1, rfl fails.
- atk_6 ungrounded-oracle echo (mirrors resolveAntialiased but negates result when laterSet=some) -> EXIT=1, rfl fails.
- atk_7 degenerate constant true -> EXIT=1, rfl fails.

No wrong impl closes with clean axioms, so protocol step 2 (materialize+resolve faithful patch) is vacuous — there is no closing clean-axiom wrong impl to falsify. patches={} accordingly.

REFINEMENT AUDIT (refinement.md): 4 legs, ALL tagged R (type refinement); zero A-consumed, zero A-reference, zero kind-3, zero I-only-with-gaps. axioms region declares NOTHING (no opaque/axiom callee) — the A-legs the reviewer focuses on are absent by construction because the resolution is fully structural over the three inputs. Model↔patch correspondence verified against patch.diff: leg1 acc:=rcDefault ↔ __init__ self._antialiased = rcParams['text.antialiased']; leg2 ctorArg ↔ antialiased kwarg via _reset_visual_defaults `if antialiased is not None: set_antialiased(antialiased)`; leg3 laterSet ↔ post-construction set_antialiased(b) storing verbatim; leg4 return acc ↔ get_antialiased()/gc.set_antialiased. Priority laterSet>ctorArg>rcDefault matches the patch's write ordering. Option Bool↔bool|None sentinel bijection sound.

VERDICT: SOUND. 7 distinct wrong impls (prepatch + 6 further) all fail to verify; positive control verifies clean; refinement legs all R with faithful patch correspondence and no axiom surface to exploit. verify⇒correct holds.

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
import Mathlib
-- imports-end

/-!
The effective antialiasing flag of a text artist.

A text artist exposes a per-object antialiasing setting, in the same spirit as
other drawable artists. The value is a boolean that is later consulted by the
drawing stage. It is resolved from three sources, in increasing priority:

* a global default boolean (the configured fallback used when nothing more
  specific is given);
* an optional value supplied when the artist is created (when omitted, the
  global default stands);
* an optional value supplied afterwards by an explicit assignment on the artist
  (when never assigned, the previously-resolved value stands).

The getter returns exactly this resolved boolean, and it is this same boolean
that the drawing stage hands to the graphics context. The desired rule is:

  * with no per-object choice ever made, the resolved value equals the global
    default;
  * a value supplied at creation overrides the global default;
  * a later explicit assignment overrides whatever was in effect before it,
    regardless of how that earlier value arose.

The resolution is independent of the global default once a per-object value is
in effect.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The global
-- default boolean is supplied as an input (`rcDefault`); the resolution is
-- modeled structurally over that default together with the two optional
-- per-object choices, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The resolved antialiasing boolean. `rcDefault` is the global fallback,
`ctorArg` the optional value supplied at creation (`none` = omitted), and
`laterSet` the optional value supplied by a later explicit assignment
(`none` = never assigned). A later assignment wins over a creation-time value,
which in turn wins over the global default. -/
def resolveAntialiased (rcDefault : Bool) (ctorArg : Option Bool)
    (laterSet : Option Bool) : Bool :=
  laterSet.getD (ctorArg.getD rcDefault)
-- pure-end

-- post-conditions-start
/-- The reported antialiasing boolean is exactly the value selected by the
resolution rule: a later explicit assignment if present, otherwise a
creation-time value if present, otherwise the global default. -/
def problem_spec_textAntialiased
    (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool)
    (result : Bool) : Prop :=
  result = resolveAntialiased rcDefault ctorArg laterSet
-- post-conditions-end

-- impl-start
/-- Positive control: equivalent correct resolution written directly. -/
def implementation_textAntialiased
    (rcDefault : Bool) (ctorArg : Option Bool) (laterSet : Option Bool) : Bool :=
  match laterSet with
  | some b => b
  | none => match ctorArg with
    | some b => b
    | none => rcDefault
-- impl-end

-- proof-start
theorem correct_textAntialiased :
    ∀ (rcDefault : Bool) (ctorArg laterSet : Option Bool),
      problem_spec_textAntialiased rcDefault ctorArg laterSet
        (implementation_textAntialiased rcDefault ctorArg laterSet) := by
  intro rcDefault ctorArg laterSet
  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased
  cases ctorArg <;> cases laterSet <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: problem_spec_textAntialiased asserts result = resolveAntialiased rcDefault ctorArg laterSet = laterSet.getD (ctorArg.getD rcDefault) — a TOTAL pointwise boolean equality over the finite 18-point domain (rcDefault∈{T,F} × ctorArg,laterSet∈{None,T,F}). This is the tightest possible postcondition shape, leaving no room for a same-spec wrong impl to close.

SAME-SPEC: all 7 attacks + pos_control return same_spec=True vs gold (axioms/pure/pre/post byte-identical; only impl+proof edited).

POSITIVE CONTROL (pos_control.lean): correct impl written as an explicit match (semantically equal to gold). `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0. `#print axioms correct_textAntialiased` -> 'does not depend on any axioms' (clean, no sorry).

### ATTACKS (each `bash scripts/lean_verify.sh atk_N.lean`, standard cases-<;>-rfl proof):
- atk_1 PREPATCH BUG (no per-object state; always rcDefault) -> EXIT=1, genuine rfl refutation at proof line. Reproduces the prepatch defect.
- atk_2 swapped precedence (ctorArg wins over laterSet): ctorArg.getD (laterSet.getD rcDefault) -> EXIT=1, rfl fails.
- atk_3 partial-domain (correct except returns false when ctorArg=none & laterSet=none) -> EXIT=1. Also re-attempted with a strong `first | rfl | decide | (revert rcDefault; decide)` proof (atk_3_decide.lean) -> EXIT=1, Lean's `decide` PROVED THE PROPOSITION FALSE — definitive unprovability, not a weak-tactic artifact.
- atk_4 boundary (ignores ctorArg entirely): laterSet.getD rcDefault -> EXIT=1, rfl fails.
- atk_5 control-flow-effect (applies laterSet write then ctorArg write — wrong order) -> EXIT=1, rfl fails.
- atk_6 ungrounded-oracle echo (mirrors resolveAntialiased but negates result when laterSet=some) -> EXIT=1, rfl fails.
- atk_7 degenerate constant true -> EXIT=1, rfl fails.

No wrong impl closes with clean axioms, so protocol step 2 (materialize+resolve faithful patch) is vacuous — there is no closing clean-axiom wrong impl to falsify. patches={} accordingly.

REFINEMENT AUDIT (refinement.md): 4 legs, ALL tagged R (type refinement); zero A-consumed, zero A-reference, zero kind-3, zero I-only-with-gaps. axioms region declares NOTHING (no opaque/axiom callee) — the A-legs the reviewer focuses on are absent by construction because the resolution is fully structural over the three inputs. Model↔patch correspondence verified against patch.diff: leg1 acc:=rcDefault ↔ __init__ self._antialiased = rcParams['text.antialiased']; leg2 ctorArg ↔ antialiased kwarg via _reset_visual_defaults `if antialiased is not None: set_antialiased(antialiased)`; leg3 laterSet ↔ post-construction set_antialiased(b) storing verbatim; leg4 return acc ↔ get_antialiased()/gc.set_antialiased. Priority laterSet>ctorArg>rcDefault matches the patch's write ordering. Option Bool↔bool|None sentinel bijection sound.

VERDICT: SOUND. 7 distinct wrong impls (prepatch + 6 further) all fail to verify; positive control verifies clean; refinement legs all R with faithful patch correspondence and no axiom surface to exploit. verify⇒correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on matplotlib__matplotlib-25775 lean bundle. Modeled function: resolveAntialiased(rcDefault, ctorArg, laterSet) = laterSet.getD (ctorArg.getD rcDefault), reported via problem_spec_textAntialiased result = resolveAntialiased ... .

Checks performed:
1. Lean compiles: scripts/lean_verify.sh Solution.lean -> exit 0 (no sorry).
2. Axioms clean: `#print axioms correct_textAntialiased` -> 'does not depend on any axioms' (genuine proof, no sorryAx).
3. Spec-region byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) -> True; spec_view stable, only impl/proof differ (prepatch impl regresses to always-rcDefault, consistent with the base repo having no per-object antialiasing).
4. Faithfulness vs REAL patched repo (text.py): Text.__init__ seeds self._antialiased = rcParams['text.antialiased']; `if antialiased is not None: self.set_antialiased(antialiased)`; set_antialiased stores verbatim; get_antialiased returns it. This maps exactly onto the Lean resolution (default < ctor < later-set precedence).
5. Differential test against the patched source: exhaustive 18/18 combinations (rcDefault in {T,F} x ctorArg in {None,T,F} x laterSet in {None,T,F}) all match; the shipped conformance_check.py run under PYTHONPATH=patched matplotlib reports {status: ok, checked: 120018, disagreements: []} (>=1e5 fuzz + exhaustive).

No diverging input found. The Bool/Option Bool domain is a legitimate scoping to the F2P-observed boolean values (tests assert `_antialiased is True/False`), not a strengthening that contradicts the real callee on any in-domain input. Spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec=True); impl and proof regions are fully elided in the spec view. The spec view describes only an abstract behavioral contract: an antialiasing boolean resolved from three sources by priority (global default `rcDefault` < optional creation-time value `ctorArg` < optional later assignment `laterSet`; later wins), the getter returns it, and it reaches the graphics context at draw time. Lean identifiers (resolveAntialiased, problem_spec_textAntialiased, rcDefault, ctorArg, laterSet, result) are abstract and disclose no gold-patch specifics. The public problem_statement already reveals more concrete detail than the spec: it names add get/set_antialiased on Text objects, Annotations, use in the drawing stage, and routing through the GraphicsContext replacing rcParams['text.antialiased']. NONE of the gold-edit implementation specifics leak — no Python symbols (set_antialiased/get_antialiased/_antialiased/gc.get_antialiased()), no `antialiased=None` ctor kwarg, no _reset_visual_defaults, no file/line locations, no backend_agg/backend_cairo edits, no update_from propagation. The priority-ordering / creation-time tier is a legitimate abstract behavioral requirement (a spec's proper job), not a reconstruction of the gold code, and it is worded generically rather than quoting the patch. G-LEAK lexical screen recorded failures=[] , consistent with this reading. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

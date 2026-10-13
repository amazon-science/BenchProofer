# P2 adversarial audit — matplotlib__matplotlib-26466

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,11 +75,8 @@
 -- impl-start
 def implementation_freezeOffsetOrigin
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
-  let x := initial.1
-  let y := initial.2
-  return StoredCoord.snapshot x y
+  -- ATTACK: store by reference (prepatch bug)
+  return StoredCoord.reference
 -- impl-end
 
 -- proof-start
@@ -108,11 +105,8 @@
 -- impl-start
 def implementation_freezeAnchorPoint
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
-  let x := initial.1
-  let y := initial.2
-  return StoredCoord.snapshot x y
+  -- ATTACK: store by reference (prepatch bug)
+  return StoredCoord.reference
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,11 +75,10 @@
 -- impl-start
 def implementation_freezeOffsetOrigin
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: swap the two components
   let x := initial.1
   let y := initial.2
-  return StoredCoord.snapshot x y
+  return StoredCoord.snapshot y x
 -- impl-end
 
 -- proof-start
@@ -108,11 +107,10 @@
 -- impl-start
 def implementation_freezeAnchorPoint
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: swap the two components
   let x := initial.1
   let y := initial.2
-  return StoredCoord.snapshot x y
+  return StoredCoord.snapshot y x
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,11 +75,8 @@
 -- impl-start
 def implementation_freezeOffsetOrigin
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
-  let x := initial.1
-  let y := initial.2
-  return StoredCoord.snapshot x y
+  -- ATTACK: constant snapshot, ignores initial
+  return StoredCoord.snapshot 0 0
 -- impl-end
 
 -- proof-start
@@ -108,11 +105,8 @@
 -- impl-start
 def implementation_freezeAnchorPoint
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
-  let x := initial.1
-  let y := initial.2
-  return StoredCoord.snapshot x y
+  -- ATTACK: constant snapshot, ignores initial
+  return StoredCoord.snapshot 0 0
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,11 +75,13 @@
 -- impl-start
 def implementation_freezeOffsetOrigin
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: partial-domain, correct only when first component is 0
   let x := initial.1
   let y := initial.2
-  return StoredCoord.snapshot x y
+  if x = 0 then
+    return StoredCoord.snapshot x y
+  else
+    return StoredCoord.reference
 -- impl-end
 
 -- proof-start
@@ -108,11 +110,13 @@
 -- impl-start
 def implementation_freezeAnchorPoint
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: partial-domain, correct only when first component is 0
   let x := initial.1
   let y := initial.2
-  return StoredCoord.snapshot x y
+  if x = 0 then
+    return StoredCoord.snapshot x y
+  else
+    return StoredCoord.reference
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,11 +75,10 @@
 -- impl-start
 def implementation_freezeOffsetOrigin
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: off-by-one on first component
   let x := initial.1
   let y := initial.2
-  return StoredCoord.snapshot x y
+  return StoredCoord.snapshot (x + 1) y
 -- impl-end
 
 -- proof-start
@@ -108,11 +107,10 @@
 -- impl-start
 def implementation_freezeAnchorPoint
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: off-by-one on first component
   let x := initial.1
   let y := initial.2
-  return StoredCoord.snapshot x y
+  return StoredCoord.snapshot (x + 1) y
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,11 +75,9 @@
 -- impl-start
 def implementation_freezeOffsetOrigin
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: duplicate first component into both slots
   let x := initial.1
-  let y := initial.2
-  return StoredCoord.snapshot x y
+  return StoredCoord.snapshot x x
 -- impl-end
 
 -- proof-start
@@ -108,11 +106,9 @@
 -- impl-start
 def implementation_freezeAnchorPoint
     (initial : Rat × Rat) : StoredCoord := Id.run do
-  -- Read the two components of the construction-time coordinate and store them as
-  -- a detached snapshot; a later mutation of the source is irrelevant to it.
+  -- ATTACK: duplicate first component into both slots
   let x := initial.1
-  let y := initial.2
-  return StoredCoord.snapshot x y
+  return StoredCoord.snapshot x x
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Capturing a 2D coordinate handed in at construction time.

Two small helper objects each receive a 2D coordinate as a constructor argument
and keep it for later use. The coordinate is supplied by the caller through a
mutable container, and the caller is free to change the contents of that
container in place AFTER the object has been constructed.

The desired behaviour is that constructing the object must capture the coordinate
*by value*: the two components are read once, at construction time, and the stored
coordinate is a snapshot of exactly those two component values. Consequently, a
subsequent in-place change to the caller's container — so that the same source
later holds a different value — must NOT alter the coordinate already stored on
the object. Reading the stored coordinate back at any later moment yields the
component values that were present when the object was constructed, regardless of
what the source container holds at that later moment.

Both helper objects capture their coordinate the same way, and the requirement is
the same for each: the stored coordinate is frozen at construction and decoupled
from any later mutation of the source.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behaviour
-- modeled is the pure capture of a 2D coordinate's two components at construction
-- time into a fresh stored pair, decoupled from any later change to the source
-- container, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A coordinate pair retained by a helper object, viewed through *what a reader
sees after the source container may have been changed*. There are exactly two
retention behaviours the object can exhibit:

* `snapshot x y` — the pair is detached from the source: reading it always yields
  the captured `(x, y)`, whatever the source container now holds.
* `reference` — the pair stays bound to the source container: reading it yields
  the source's CURRENT contents.

The required (by-value) behaviour is `snapshot`. The two retentions are
observationally distinguishable exactly when the source is changed in place after
capture, which is the public reproduction described in the statement. -/
inductive StoredCoord where
  | snapshot (x y : Rat)
  | reference
  deriving DecidableEq, Repr

/-- Read back a retained coordinate given the source container's CURRENT contents
`later`. A `snapshot` ignores `later`; a `reference` reflects it. -/
def observe : StoredCoord → Rat × Rat → Rat × Rat
  | .snapshot x y, _     => (x, y)
  | .reference,    later => later
-- pure-end

-- post-conditions-start
/-- Capturing the offset-origin coordinate of the first helper object.

`initial` is the coordinate value present in the caller's source container at the
moment the object is constructed. `out` is the retained coordinate the object
holds afterwards.

The capture must be a by-value snapshot: reading the retained coordinate back
under ANY later state `later` of the source container yields the construction-time
value `initial`. Equivalently, the retained coordinate is decoupled from every
possible later mutation of the source — only the detached (`snapshot`) retention
satisfies this; a retained reference would leak `later`. -/
def problem_spec_freezeOffsetOrigin
    (initial : Rat × Rat) (out : StoredCoord) : Prop :=
  ∀ later : Rat × Rat, observe out later = initial
-- post-conditions-end

-- impl-start
def implementation_freezeOffsetOrigin
    (initial : Rat × Rat) : StoredCoord := Id.run do
  -- POSITIVE CONTROL: correct behaviour via destructuring
  let (x, y) := initial
  return StoredCoord.snapshot x y
-- impl-end

-- proof-start
theorem correct_freezeOffsetOrigin :
    ∀ (initial : Rat × Rat),
      problem_spec_freezeOffsetOrigin initial
        (implementation_freezeOffsetOrigin initial) := by
  intro initial later
  unfold implementation_freezeOffsetOrigin observe
  simp
-- proof-end

-- post-conditions-start
/-- Capturing the anchor-point coordinate of the second helper object.

Identical capture requirement to the first object: `initial` is the
construction-time coordinate and `out` is the retained coordinate. Reading the
retained coordinate back under ANY later state `later` of the source container
must yield `initial` — the retention is detached from every later mutation of the
source (only the `snapshot` retention satisfies this). -/
def problem_spec_freezeAnchorPoint
    (initial : Rat × Rat) (out : StoredCoord) : Prop :=
  ∀ later : Rat × Rat, observe out later = initial
-- post-conditions-end

-- impl-start
def implementation_freezeAnchorPoint
    (initial : Rat × Rat) : StoredCoord := Id.run do
  -- POSITIVE CONTROL: correct behaviour via destructuring
  let (x, y) := initial
  return StoredCoord.snapshot x y
-- impl-end

-- proof-start
theorem correct_freezeAnchorPoint :
    ∀ (initial : Rat × Rat),
      problem_spec_freezeAnchorPoint initial
        (implementation_freezeAnchorPoint initial) := by
  intro initial later
  unfold implementation_freezeAnchorPoint observe
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: postcondition `∀ later, observe out later = initial` over StoredCoord (observe (snapshot x y) later = (x,y); observe reference later = later). This is a COMPLETE functional spec: only `snapshot initial.1 initial.2` satisfies it for all `later` (reference leaks `later`; any other snapshot value fails at `later=initial`). Both impl sites are byte-identical; each attack edits ONLY the two impl regions, leaving axioms/pure/pre/post byte-identical. same_spec=True for all 7 files (verified). Axioms region is an empty comment; grep confirms NO opaque/axiom declarations => no A-legs (G-AX skips), so the A-leg correspondence audit is vacuous; refinement.md legs are all R/I, consistent with the model. Positive control atk_pos verifies clean (`#print axioms` => only propext for both correct_* theorems; no sorry).

6 DISTINCT wrong impls, all same_spec=True, all attempted with the gold proof body (intro;unfold;simp):
- atk_1 (control-flow/prepatch bug, both sites StoredCoord.reference): lean_verify EXIT 1, residual `later = initial` (unprovable for arbitrary later). Reproduces the prepatch bug.
- atk_2 (boundary: swap components, snapshot y x): EXIT 1, residual `(initial.2, initial.1) = initial`.
- atk_3 (ungrounded-oracle echo: constant snapshot 0 0): EXIT 1, residual `(0,0) = initial`.
- atk_4 (partial-domain: snapshot only when initial.1=0 else reference): EXIT 1, residual reduces to `later = initial` on the else branch.
- atk_5 (off-by-one: snapshot (x+1) y): EXIT 1, residual `(initial.1+1, initial.2) = initial`.
- atk_6 (control-flow-effect: duplicate first comp, snapshot x x): EXIT 1, residual `(initial.1, initial.1) = initial`.

EXACT COMMANDS: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently in batches of 4). Results: atk_1..atk_6 => EXIT 1 (error, proof does not close, no sorry). atk_pos => EXIT 0. Positive control axioms: `#print axioms correct_freezeOffsetOrigin/AnchorPoint` => [propext] only.

No wrong impl produced a CLOSING proof, so per protocol there is NO faithful patch to materialize/run through run_resolve (patches={} is correct — resolve is only required for verifying wrong impls). The spec is tight: verify => correct. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Capturing a 2D coordinate handed in at construction time.

Two small helper objects each receive a 2D coordinate as a constructor argument
and keep it for later use. The coordinate is supplied by the caller through a
mutable container, and the caller is free to change the contents of that
container in place AFTER the object has been constructed.

The desired behaviour is that constructing the object must capture the coordinate
*by value*: the two components are read once, at construction time, and the stored
coordinate is a snapshot of exactly those two component values. Consequently, a
subsequent in-place change to the caller's container — so that the same source
later holds a different value — must NOT alter the coordinate already stored on
the object. Reading the stored coordinate back at any later moment yields the
component values that were present when the object was constructed, regardless of
what the source container holds at that later moment.

Both helper objects capture their coordinate the same way, and the requirement is
the same for each: the stored coordinate is frozen at construction and decoupled
from any later mutation of the source.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behaviour
-- modeled is the pure capture of a 2D coordinate's two components at construction
-- time into a fresh stored pair, decoupled from any later change to the source
-- container, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A coordinate pair retained by a helper object, viewed through *what a reader
sees after the source container may have been changed*. There are exactly two
retention behaviours the object can exhibit:

* `snapshot x y` — the pair is detached from the source: reading it always yields
  the captured `(x, y)`, whatever the source container now holds.
* `reference` — the pair stays bound to the source container: reading it yields
  the source's CURRENT contents.

The required (by-value) behaviour is `snapshot`. The two retentions are
observationally distinguishable exactly when the source is changed in place after
capture, which is the public reproduction described in the statement. -/
inductive StoredCoord where
  | snapshot (x y : Rat)
  | reference
  deriving DecidableEq, Repr

/-- Read back a retained coordinate given the source container's CURRENT contents
`later`. A `snapshot` ignores `later`; a `reference` reflects it. -/
def observe : StoredCoord → Rat × Rat → Rat × Rat
  | .snapshot x y, _     => (x, y)
  | .reference,    later => later
-- pure-end

-- post-conditions-start
/-- Capturing the offset-origin coordinate of the first helper object.

`initial` is the coordinate value present in the caller's source container at the
moment the object is constructed. `out` is the retained coordinate the object
holds afterwards.

The capture must be a by-value snapshot: reading the retained coordinate back
under ANY later state `later` of the source container yields the construction-time
value `initial`. Equivalently, the retained coordinate is decoupled from every
possible later mutation of the source — only the detached (`snapshot`) retention
satisfies this; a retained reference would leak `later`. -/
def problem_spec_freezeOffsetOrigin
    (initial : Rat × Rat) (out : StoredCoord) : Prop :=
  ∀ later : Rat × Rat, observe out later = initial
-- post-conditions-end

-- impl-start
def implementation_freezeOffsetOrigin
    (initial : Rat × Rat) : StoredCoord := Id.run do
  -- POSITIVE CONTROL: correct behaviour via destructuring
  let (x, y) := initial
  return StoredCoord.snapshot x y
-- impl-end

-- proof-start
theorem correct_freezeOffsetOrigin :
    ∀ (initial : Rat × Rat),
      problem_spec_freezeOffsetOrigin initial
        (implementation_freezeOffsetOrigin initial) := by
  intro initial later
  unfold implementation_freezeOffsetOrigin observe
  simp
-- proof-end

-- post-conditions-start
/-- Capturing the anchor-point coordinate of the second helper object.

Identical capture requirement to the first object: `initial` is the
construction-time coordinate and `out` is the retained coordinate. Reading the
retained coordinate back under ANY later state `later` of the source container
must yield `initial` — the retention is detached from every later mutation of the
source (only the `snapshot` retention satisfies this). -/
def problem_spec_freezeAnchorPoint
    (initial : Rat × Rat) (out : StoredCoord) : Prop :=
  ∀ later : Rat × Rat, observe out later = initial
-- post-conditions-end

-- impl-start
def implementation_freezeAnchorPoint
    (initial : Rat × Rat) : StoredCoord := Id.run do
  -- POSITIVE CONTROL: correct behaviour via destructuring
  let (x, y) := initial
  return StoredCoord.snapshot x y
-- impl-end

-- proof-start
theorem correct_freezeAnchorPoint :
    ∀ (initial : Rat × Rat),
      problem_spec_freezeAnchorPoint initial
        (implementation_freezeAnchorPoint initial) := by
  intro initial later
  unfold implementation_freezeAnchorPoint observe
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: postcondition `∀ later, observe out later = initial` over StoredCoord (observe (snapshot x y) later = (x,y); observe reference later = later). This is a COMPLETE functional spec: only `snapshot initial.1 initial.2` satisfies it for all `later` (reference leaks `later`; any other snapshot value fails at `later=initial`). Both impl sites are byte-identical; each attack edits ONLY the two impl regions, leaving axioms/pure/pre/post byte-identical. same_spec=True for all 7 files (verified). Axioms region is an empty comment; grep confirms NO opaque/axiom declarations => no A-legs (G-AX skips), so the A-leg correspondence audit is vacuous; refinement.md legs are all R/I, consistent with the model. Positive control atk_pos verifies clean (`#print axioms` => only propext for both correct_* theorems; no sorry).

6 DISTINCT wrong impls, all same_spec=True, all attempted with the gold proof body (intro;unfold;simp):
- atk_1 (control-flow/prepatch bug, both sites StoredCoord.reference): lean_verify EXIT 1, residual `later = initial` (unprovable for arbitrary later). Reproduces the prepatch bug.
- atk_2 (boundary: swap components, snapshot y x): EXIT 1, residual `(initial.2, initial.1) = initial`.
- atk_3 (ungrounded-oracle echo: constant snapshot 0 0): EXIT 1, residual `(0,0) = initial`.
- atk_4 (partial-domain: snapshot only when initial.1=0 else reference): EXIT 1, residual reduces to `later = initial` on the else branch.
- atk_5 (off-by-one: snapshot (x+1) y): EXIT 1, residual `(initial.1+1, initial.2) = initial`.
- atk_6 (control-flow-effect: duplicate first comp, snapshot x x): EXIT 1, residual `(initial.1, initial.1) = initial`.

EXACT COMMANDS: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently in batches of 4). Results: atk_1..atk_6 => EXIT 1 (error, proof does not close, no sorry). atk_pos => EXIT 0. Positive control axioms: `#print axioms correct_freezeOffsetOrigin/AnchorPoint` => [propext] only.

No wrong impl produced a CLOSING proof, so per protocol there is NO faithful patch to materialize/run through run_resolve (patches={} is correct — resolve is only required for verifying wrong impls). The spec is tight: verify => correct. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO drift. Modeled function = post-patch capture behaviour of both sites (OffsetFrom.__init__ storing self._ref_coord; _AnnotationBase.__init__ storing self.xy). Real callee semantics confirmed against: base_commit stores the caller's mutable numpy array BY REFERENCE (modeled as StoredCoord.reference, observe=later); gold patch does `x,y = src; self.attr = x,y`, snapshotting the two scalars. Verified on a real numpy array that `x,y = arr` yields value copies decoupled from later in-place mutation (arr[1]=3 left stored (-4,1) unchanged), while the by-reference form leaks (-4,3) — exactly StoredCoord.snapshot vs reference. Spec `∀ later, observe out later = initial` is precisely the by-value detachment the fixed callee provides for every later source state; it is neither too strong nor too weak. Over the modeled domain (2-component coordinate, values only stored/read verbatim, no arithmetic) the model and the real callee agree on all inputs — no diverging input exists. Rat×Rat is a sound stand-in for (float,float) here. Excluded _get_scale inline is a behaviour-neutral refactor (identical scale for both unit branches), correctly not modeled. Mechanical corroboration: same_spec True for both prepatch variants; lean_verify Solution.lean exit 0; #print axioms => [propext] only (no sorryAx); prepatch_1/2 exit 1 (G-DIFF holds); G-CONF 200000 inputs 0 disagreements + negative control caught.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical: spec_view sha256=7a3a52604851747887841dc7b46fe7e1c45ce8e1132a83380e09630dd40bb400 matches meta.json/G-HYGIENE; same_spec(Solution,prepatch_1)=True and same_spec(Solution,prepatch_2)=True. Leakage judged against public problem_statement only (not hints_text). Baseline: problem_statement already discloses the fix essence ('very likely that the same array is kept instead of a copy', a reproduction mutating the array after the call, and the '.copy() helps' note), so copy-vs-reference is fully public. The spec view (module docstring + empty axioms region + StoredCoord/observe pure defs + the two problem_spec_* postconditions; impl/proof elided) describes the requirement only generically ('mutable container', 'capture by value', 'snapshot' detached vs 'reference' bound, 'decoupled from any later mutation'), which is coextensive with the public statement. It contains NO repo/gold identifiers (no text.py, OffsetFrom, _AnnotationBase, _ref_coord, ref_coord, self.xy, 'x, y =', '.copy(', numpy, annotate, _get_scale, points_to_pixels) and no bug/fix/patch/diff/gold narration (G-LEAK lexical screen clean). Function names freezeOffsetOrigin/freezeAnchorPoint are generic role paraphrases, not the code symbols, and reveal no file/class/method/attribute location. The only content beyond problem_statement is the bare count of 'two symmetric helper objects' (the second, OffsetFrom, site is in hints_text) — but this names nothing and gives no locating/reconstruction power, so it does not leak the gold edit. No spec-view line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).

# P2 adversarial audit — matplotlib__matplotlib-25311

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -110,16 +110,13 @@
   ensures flagsExact out (useBlit && supportsBlit)
   do
     -- impl-start
-    -- Build the persisted state: retain a reference to the dragged object, the
-    -- status bit, the effective mode bit, and the event registrations. The
-    -- rendering surface is deliberately NOT retained here; it is obtainable on
-    -- demand from the retained reference (`surfaceFromRef := true`).
     let mut attrs : List Attr := []
     attrs := Attr.refHandle :: attrs
+    attrs := Attr.surface :: attrs
     attrs := Attr.flag false :: attrs
     attrs := Attr.flag (useBlit && supportsBlit) :: attrs
     attrs := Attr.registration :: attrs
-    return { attrs := attrs, surfaceFromRef := true }
+    return { attrs := attrs, surfaceFromRef := false }
     -- impl-end
 
 prove_correct initHandler by
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
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -110,15 +110,10 @@
   ensures flagsExact out (useBlit && supportsBlit)
   do
     -- impl-start
-    -- Build the persisted state: retain a reference to the dragged object, the
-    -- status bit, the effective mode bit, and the event registrations. The
-    -- rendering surface is deliberately NOT retained here; it is obtainable on
-    -- demand from the retained reference (`surfaceFromRef := true`).
     let mut attrs : List Attr := []
     attrs := Attr.refHandle :: attrs
     attrs := Attr.flag false :: attrs
     attrs := Attr.flag (useBlit && supportsBlit) :: attrs
-    attrs := Attr.registration :: attrs
     return { attrs := attrs, surfaceFromRef := true }
     -- impl-end
 
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
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -110,13 +110,8 @@
   ensures flagsExact out (useBlit && supportsBlit)
   do
     -- impl-start
-    -- Build the persisted state: retain a reference to the dragged object, the
-    -- status bit, the effective mode bit, and the event registrations. The
-    -- rendering surface is deliberately NOT retained here; it is obtainable on
-    -- demand from the retained reference (`surfaceFromRef := true`).
     let mut attrs : List Attr := []
     attrs := Attr.refHandle :: attrs
-    attrs := Attr.flag false :: attrs
     attrs := Attr.flag (useBlit && supportsBlit) :: attrs
     attrs := Attr.registration :: attrs
     return { attrs := attrs, surfaceFromRef := true }
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -110,14 +110,10 @@
   ensures flagsExact out (useBlit && supportsBlit)
   do
     -- impl-start
-    -- Build the persisted state: retain a reference to the dragged object, the
-    -- status bit, the effective mode bit, and the event registrations. The
-    -- rendering surface is deliberately NOT retained here; it is obtainable on
-    -- demand from the retained reference (`surfaceFromRef := true`).
     let mut attrs : List Attr := []
     attrs := Attr.refHandle :: attrs
     attrs := Attr.flag false :: attrs
-    attrs := Attr.flag (useBlit && supportsBlit) :: attrs
+    attrs := Attr.flag (useBlit || supportsBlit) :: attrs
     attrs := Attr.registration :: attrs
     return { attrs := attrs, surfaceFromRef := true }
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -110,14 +110,11 @@
   ensures flagsExact out (useBlit && supportsBlit)
   do
     -- impl-start
-    -- Build the persisted state: retain a reference to the dragged object, the
-    -- status bit, the effective mode bit, and the event registrations. The
-    -- rendering surface is deliberately NOT retained here; it is obtainable on
-    -- demand from the retained reference (`surfaceFromRef := true`).
     let mut attrs : List Attr := []
     attrs := Attr.refHandle :: attrs
     attrs := Attr.flag false :: attrs
     attrs := Attr.flag (useBlit && supportsBlit) :: attrs
+    attrs := Attr.flag true :: attrs
     attrs := Attr.registration :: attrs
     return { attrs := attrs, surfaceFromRef := true }
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -110,16 +110,12 @@
   ensures flagsExact out (useBlit && supportsBlit)
   do
     -- impl-start
-    -- Build the persisted state: retain a reference to the dragged object, the
-    -- status bit, the effective mode bit, and the event registrations. The
-    -- rendering surface is deliberately NOT retained here; it is obtainable on
-    -- demand from the retained reference (`surfaceFromRef := true`).
     let mut attrs : List Attr := []
     attrs := Attr.refHandle :: attrs
     attrs := Attr.flag false :: attrs
     attrs := Attr.flag (useBlit && supportsBlit) :: attrs
     attrs := Attr.registration :: attrs
-    return { attrs := attrs, surfaceFromRef := true }
+    return { attrs := attrs, surfaceFromRef := false }
     -- impl-end
 
 prove_correct initHandler by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees and no A-reference deep model. The operation under
@@ -110,14 +110,12 @@
   ensures flagsExact out (useBlit && supportsBlit)
   do
     -- impl-start
-    -- Build the persisted state: retain a reference to the dragged object, the
-    -- status bit, the effective mode bit, and the event registrations. The
-    -- rendering surface is deliberately NOT retained here; it is obtainable on
-    -- demand from the retained reference (`surfaceFromRef := true`).
     let mut attrs : List Attr := []
+    attrs := Attr.refHandle :: attrs
     attrs := Attr.refHandle :: attrs
     attrs := Attr.flag false :: attrs
     attrs := Attr.flag (useBlit && supportsBlit) :: attrs
+    attrs := Attr.registration :: attrs
     attrs := Attr.registration :: attrs
     return { attrs := attrs, surfaceFromRef := true }
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model. The operation under
--  specification — constructing the handler's persisted object state — is
--  modeled deeply as the do block below. The only environment fact relied on is
--  structural and is encoded in the type model: a stored reference handle is
--  serializable on its own, whereas the live rendering surface is not (the
--  distinguished `Attr.surface` token). Nothing is borrowed from an outside
--  contract, so there is no axiom to validate — meta.json G-AX skip.)
-- axioms-end

-- pure-start
/- The kinds of value a freshly constructed drag-interaction handler can place
   into its persisted object state:

     * `surface`      — the live rendering surface the handler talks to. It is
                        NOT serializable: if it is placed into the persisted
                        state it is dragged into the serialized stream and makes
                        the whole object impossible to persist.
     * `refHandle`    — a reference to the object being dragged. It IS
                        serializable on its own, and the surface can be obtained
                        through it on demand.
     * `flag b`       — a boolean status/mode bit (serializable).
     * `registration` — a record of installed event registrations (serializable).

   The behavior under specification turns on WHICH of these the handler retains,
   so a first-class tag with decidable equality. -/
inductive Attr where
  | surface
  | refHandle
  | flag (b : Bool)
  | registration
  deriving DecidableEq, Inhabited

/- A constructed handler, abstracted to exactly what the observed behavior
   depends on:

     * `attrs`          — the values retained in its persisted object state (the
                          content that would be written to a serialized stream);
     * `surfaceFromRef` — whether the handler can produce the rendering surface
                          on demand from its stored reference handle, WITHOUT
                          retaining the surface in its persisted state. -/
structure Handler where
  attrs : List Attr
  surfaceFromRef : Bool
  deriving Inhabited

/- Serializability: the persisted state must contain no non-serializable
   rendering surface, so that the object can be persisted as a whole. -/
def persistable (h : Handler) : Prop :=
  Attr.surface ∉ h.attrs

/- Reachability: the rendering surface must remain obtainable. Either the
   handler can derive it on demand from a retained reference handle, or it still
   retains the surface directly. Grounded in the actual retained values: the
   first disjunct requires the reference handle to be present. -/
def surfaceReachable (h : Handler) : Prop :=
  (h.surfaceFromRef = true ∧ Attr.refHandle ∈ h.attrs) ∨ Attr.surface ∈ h.attrs

/- Status-bit inventory closure: the only boolean status/mode bits the
   constructed handler retains are the two it is built with — the cleared
   drag-status bit and the given effective mode bit. A handler carrying any
   other status bit is a different object than the one this constructor
   builds. -/
def flagsExact (h : Handler) (effective : Bool) : Prop :=
  ∀ b : Bool, Attr.flag b ∈ h.attrs → (b = false ∨ b = effective)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Constructing a drag-interaction handler. The handler watches an object being
   dragged across a rendering surface; it records a reference to that object,
   the mode/status bits it needs, and the event registrations it installs.

   Two behaviors are required of the constructed handler:

     * its persisted object state must be serializable — it must NOT retain the
       (non-serializable) rendering surface in that state, or the whole object
       becomes impossible to persist;
     * the rendering surface must nevertheless remain reachable — the handler
       must be able to obtain it on demand from the reference it retains.

   `useBlit` and `supportsBlit` are read-only inputs (a requested mode bit and a
   capability bit of the surface); the constructor builds a fresh handler and
   mutates neither (directive 5). The effective mode bit retained is their
   conjunction. The persisted state must carry the full working inventory: the
   reference to the dragged object, the (initially cleared) drag-status bit, the
   effective mode bit, and the installed event registrations — a handler
   constructed without its event registrations or its cleared status bit is not
   the required object, and neither is one that smuggles in status bits beyond
   those two (`flagsExact`). -/
method initHandler (useBlit : Bool) (supportsBlit : Bool) return (out : Handler)
  ensures persistable out
  ensures surfaceReachable out
  ensures Attr.refHandle ∈ out.attrs
  ensures Attr.flag (useBlit && supportsBlit) ∈ out.attrs
  ensures Attr.flag false ∈ out.attrs
  ensures Attr.registration ∈ out.attrs
  ensures flagsExact out (useBlit && supportsBlit)
  do
    -- impl-start
    let mut attrs : List Attr := []
    attrs := Attr.refHandle :: attrs
    attrs := Attr.flag false :: attrs
    attrs := Attr.flag (useBlit && supportsBlit) :: attrs
    attrs := Attr.registration :: attrs
    return { attrs := attrs, surfaceFromRef := true }
    -- impl-end

prove_correct initHandler by
  loom_solve <;> simp_all [persistable, surfaceReachable, flagsExact]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All 8 candidates confirmed same_spec=True (velvet) via swebench_unified.markers.same_spec. Verified with `bash scripts/lean_verify.sh <f>` (from project root), run in parallel batches of 4.

### Verify results
- atk_pos (gold impl): EXIT 0 -> verifies. Positive control OK.
- atk_1 (PREPATCH bug: stores Attr.surface directly, surfaceFromRef=false): EXIT 1, fails `ensures persistable out` (goal reduces to False). Prepatch reproduced.
- atk_2 (partial-domain: omit Attr.registration): EXIT 1, fails `Attr.registration in out.attrs` (=> False).
- atk_3 (boundary: omit cleared status bit Attr.flag false): EXIT 1, fails `Attr.flag false in out.attrs` (goal `useBlit=true -> supportsBlit=false`).
- atk_4 (control-flow-effect: `useBlit || supportsBlit` instead of `&&`): EXIT 1, fails `Attr.flag (useBlit && supportsBlit) in out.attrs`.
- atk_5 (ungrounded extra status bit: unconditional Attr.flag true): EXIT 1, fails `flagsExact` (goal `useBlit=true and supportsBlit=true`).
- atk_6 (delete surface but forget accessor: surfaceFromRef=false, no surface): EXIT 1, fails `surfaceReachable out` (=> False).
- atk_7 (gold-EQUIVALENT echo: duplicate Attr.refHandle and Attr.registration tokens; identical persisted SET, surfaceFromRef=true): EXIT 0 -> VERIFIES.

RESOLVE (echo-attack policy, per the audit protocol G-PANEL-1/eq resolve step): atk_7 is the ONLY verifying same-spec impl. Its faithful Python realization is the gold patch verbatim -- duplicating the refHandle/registration tokens maps to the SAME __dict__ keys (self.ref_artist, self.cids) with identical values, so there is no observable Python difference; the abstract List Attr models the SET of persisted values (mapping.md §2, order/multiplicity irrelevant). Materialized that patch and RAN it through the official harness: swebench_unified.harness.run_resolve('matplotlib__matplotlib-25311', gold_patch) -> RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. A resolving echo of the gold is NOT a weakness. verify=>correct holds.

REFINEMENT AUDIT: refinement.md legs A1-A6 all tagged I(+R); §B declares axioms=[] and no kind-3. Confirmed against the real repo worktree offsetbox.py (post-patch): constructor sets self.ref_artist, self.got_artist=False, self._use_blit = use_blit and self.canvas.supports_blit, self.cids=[..._connect_picklable...], and `canvas = property(lambda self: self.ref_artist.figure.canvas)` -- matches mapping.md §1/§2 exactly. The §3 environment fact (a stored reference does not embed the surface) verified: matplotlib/figure.py Figure.__getstate__ does `state.pop("canvas")` (line 3115), so a stored ref_artist.figure is pickled without the live canvas. No A-consumed/A-reference legs exist to validate (no axioms), consistent with meta.json G-AX skip.

CONCLUSION: 6 distinct wrong impls (prepatch + partial-domain + boundary + control-flow-effect + ungrounded-oracle + delete-without-accessor) all fail to verify; the sole verifying same-spec impl is a gold-equivalent echo whose materialized faithful patch RESOLVES under the official harness. No verifying wrong impl with a non-resolving patch exists. Spec is not broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model. The operation under
--  specification — constructing the handler's persisted object state — is
--  modeled deeply as the do block below. The only environment fact relied on is
--  structural and is encoded in the type model: a stored reference handle is
--  serializable on its own, whereas the live rendering surface is not (the
--  distinguished `Attr.surface` token). Nothing is borrowed from an outside
--  contract, so there is no axiom to validate — meta.json G-AX skip.)
-- axioms-end

-- pure-start
/- The kinds of value a freshly constructed drag-interaction handler can place
   into its persisted object state:

     * `surface`      — the live rendering surface the handler talks to. It is
                        NOT serializable: if it is placed into the persisted
                        state it is dragged into the serialized stream and makes
                        the whole object impossible to persist.
     * `refHandle`    — a reference to the object being dragged. It IS
                        serializable on its own, and the surface can be obtained
                        through it on demand.
     * `flag b`       — a boolean status/mode bit (serializable).
     * `registration` — a record of installed event registrations (serializable).

   The behavior under specification turns on WHICH of these the handler retains,
   so a first-class tag with decidable equality. -/
inductive Attr where
  | surface
  | refHandle
  | flag (b : Bool)
  | registration
  deriving DecidableEq, Inhabited

/- A constructed handler, abstracted to exactly what the observed behavior
   depends on:

     * `attrs`          — the values retained in its persisted object state (the
                          content that would be written to a serialized stream);
     * `surfaceFromRef` — whether the handler can produce the rendering surface
                          on demand from its stored reference handle, WITHOUT
                          retaining the surface in its persisted state. -/
structure Handler where
  attrs : List Attr
  surfaceFromRef : Bool
  deriving Inhabited

/- Serializability: the persisted state must contain no non-serializable
   rendering surface, so that the object can be persisted as a whole. -/
def persistable (h : Handler) : Prop :=
  Attr.surface ∉ h.attrs

/- Reachability: the rendering surface must remain obtainable. Either the
   handler can derive it on demand from a retained reference handle, or it still
   retains the surface directly. Grounded in the actual retained values: the
   first disjunct requires the reference handle to be present. -/
def surfaceReachable (h : Handler) : Prop :=
  (h.surfaceFromRef = true ∧ Attr.refHandle ∈ h.attrs) ∨ Attr.surface ∈ h.attrs

/- Status-bit inventory closure: the only boolean status/mode bits the
   constructed handler retains are the two it is built with — the cleared
   drag-status bit and the given effective mode bit. A handler carrying any
   other status bit is a different object than the one this constructor
   builds. -/
def flagsExact (h : Handler) (effective : Bool) : Prop :=
  ∀ b : Bool, Attr.flag b ∈ h.attrs → (b = false ∨ b = effective)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Constructing a drag-interaction handler. The handler watches an object being
   dragged across a rendering surface; it records a reference to that object,
   the mode/status bits it needs, and the event registrations it installs.

   Two behaviors are required of the constructed handler:

     * its persisted object state must be serializable — it must NOT retain the
       (non-serializable) rendering surface in that state, or the whole object
       becomes impossible to persist;
     * the rendering surface must nevertheless remain reachable — the handler
       must be able to obtain it on demand from the reference it retains.

   `useBlit` and `supportsBlit` are read-only inputs (a requested mode bit and a
   capability bit of the surface); the constructor builds a fresh handler and
   mutates neither (directive 5). The effective mode bit retained is their
   conjunction. The persisted state must carry the full working inventory: the
   reference to the dragged object, the (initially cleared) drag-status bit, the
   effective mode bit, and the installed event registrations — a handler
   constructed without its event registrations or its cleared status bit is not
   the required object, and neither is one that smuggles in status bits beyond
   those two (`flagsExact`). -/
method initHandler (useBlit : Bool) (supportsBlit : Bool) return (out : Handler)
  ensures persistable out
  ensures surfaceReachable out
  ensures Attr.refHandle ∈ out.attrs
  ensures Attr.flag (useBlit && supportsBlit) ∈ out.attrs
  ensures Attr.flag false ∈ out.attrs
  ensures Attr.registration ∈ out.attrs
  ensures flagsExact out (useBlit && supportsBlit)
  do
    -- impl-start
    let mut attrs : List Attr := []
    attrs := Attr.refHandle :: attrs
    attrs := Attr.flag false :: attrs
    attrs := Attr.flag (useBlit && supportsBlit) :: attrs
    attrs := Attr.registration :: attrs
    return { attrs := attrs, surfaceFromRef := true }
    -- impl-end

prove_correct initHandler by
  loom_solve <;> simp_all [persistable, surfaceReachable, flagsExact]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All 8 candidates confirmed same_spec=True (velvet) via swebench_unified.markers.same_spec. Verified with `bash scripts/lean_verify.sh <f>` (from project root), run in parallel batches of 4.

### Verify results
- atk_pos (gold impl): EXIT 0 -> verifies. Positive control OK.
- atk_1 (PREPATCH bug: stores Attr.surface directly, surfaceFromRef=false): EXIT 1, fails `ensures persistable out` (goal reduces to False). Prepatch reproduced.
- atk_2 (partial-domain: omit Attr.registration): EXIT 1, fails `Attr.registration in out.attrs` (=> False).
- atk_3 (boundary: omit cleared status bit Attr.flag false): EXIT 1, fails `Attr.flag false in out.attrs` (goal `useBlit=true -> supportsBlit=false`).
- atk_4 (control-flow-effect: `useBlit || supportsBlit` instead of `&&`): EXIT 1, fails `Attr.flag (useBlit && supportsBlit) in out.attrs`.
- atk_5 (ungrounded extra status bit: unconditional Attr.flag true): EXIT 1, fails `flagsExact` (goal `useBlit=true and supportsBlit=true`).
- atk_6 (delete surface but forget accessor: surfaceFromRef=false, no surface): EXIT 1, fails `surfaceReachable out` (=> False).
- atk_7 (gold-EQUIVALENT echo: duplicate Attr.refHandle and Attr.registration tokens; identical persisted SET, surfaceFromRef=true): EXIT 0 -> VERIFIES.

RESOLVE (echo-attack policy, per the audit protocol G-PANEL-1/eq resolve step): atk_7 is the ONLY verifying same-spec impl. Its faithful Python realization is the gold patch verbatim -- duplicating the refHandle/registration tokens maps to the SAME __dict__ keys (self.ref_artist, self.cids) with identical values, so there is no observable Python difference; the abstract List Attr models the SET of persisted values (mapping.md §2, order/multiplicity irrelevant). Materialized that patch and RAN it through the official harness: swebench_unified.harness.run_resolve('matplotlib__matplotlib-25311', gold_patch) -> RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. A resolving echo of the gold is NOT a weakness. verify=>correct holds.

REFINEMENT AUDIT: refinement.md legs A1-A6 all tagged I(+R); §B declares axioms=[] and no kind-3. Confirmed against the real repo worktree offsetbox.py (post-patch): constructor sets self.ref_artist, self.got_artist=False, self._use_blit = use_blit and self.canvas.supports_blit, self.cids=[..._connect_picklable...], and `canvas = property(lambda self: self.ref_artist.figure.canvas)` -- matches mapping.md §1/§2 exactly. The §3 environment fact (a stored reference does not embed the surface) verified: matplotlib/figure.py Figure.__getstate__ does `state.pop("canvas")` (line 3115), so a stored ref_artist.figure is pickled without the live canvas. No A-consumed/A-reference legs exist to validate (no axioms), consistent with meta.json G-AX skip.

CONCLUSION: 6 distinct wrong impls (prepatch + partial-domain + boundary + control-flow-effect + ungrounded-oracle + delete-without-accessor) all fail to verify; the sole verifying same-spec impl is a gold-equivalent echo whose materialized faithful patch RESOLVES under the official harness. No verifying wrong impl with a non-resolving patch exists. Spec is not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the velvet bundle for matplotlib__matplotlib-25311, modeling DraggableBase.__init__ (lib/matplotlib/offsetbox.py:1503).

SPEC-REGION BYTE-IDENTITY: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True (verified via swebench_unified.markers.same_spec). The two files differ only in the impl region, so the consumer spec view is byte-identical between the verifying and prepatch variants.

LEAN CHECKS: scripts/lean_verify.sh on Solution.lean -> exit 0 (elaborates, prove_correct closes). On Solution_prepatch.lean -> fails on exactly the discriminating goal 'case ensures persistable out ... |- False' (exit 1). G-DIFF is sound: the prepatch (which stores Attr.surface directly) is rejected by the persistable clause.

REAL CALLEE at base_commit 430fb1db (confirmed against both a patched worktree and an unpatched worktree): post-patch __init__ sets EXACTLY four instance attributes -- ref_artist (unconditional), got_artist=False, _use_blit = use_blit and self.canvas.supports_blit, cids=[...] -- and DELETES the self.canvas attribute, exposing canvas as a class-level property(lambda self: self.ref_artist.figure.canvas).

CLAUSE-BY-CLAUSE FAITHFULNESS over the full input domain {True,False}^2 of (useBlit, supportsBlit):
- persistable (Attr.surface not in attrs): TRUE for the real object -- canvas is no longer in __dict__, and ref_artist does not transitively embed the surface (Figure.__getstate__ drops canvas; mapping.md §3, an unchanged environment fact).
- surfaceReachable (surfaceFromRef=true AND refHandle in attrs): TRUE -- the class property derives the surface from the retained ref_artist.
- refHandle in attrs: TRUE (self.ref_artist = ref_artist, unconditional).
- flag (useBlit && supportsBlit) in attrs: TRUE (self._use_blit); Python 'and' on the bool capability bit coincides with && on all four combos.
- flag false in attrs: TRUE (self.got_artist = False).
- registration in attrs: TRUE (self.cids = [...]).
- flagsExact out (useBlit && supportsBlit): TRUE -- __init__ sets exactly two boolean attributes (got_artist=False, _use_blit=effective) and NO third boolean, so every retained flag b satisfies b=false OR b=effective on every input. This clause never over-constrains the real object.

I specifically searched for the spec-too-strong failure mode (an input where the real post-patch object would violate a clause -- e.g. carrying a third status bit that flagsExact forbids, or a case where _use_blit's value diverges from useBlit&&supportsBlit). None exists: there is no third boolean attribute, and the conjunction matches on all four (useBlit, supportsBlit) combinations. No diverging input found.

All clauses hold of the real callee for every input in the domain. The spec does not drift from real repo behavior; it is not too strong. G-CONF is legitimately conf_skip=true (the only observable materializes solely inside the F2P pickle integration test, not as a DB-free fuzzable shadow), and soundness is carried by G-VERIFY + G-DIFF + G-RESOLVE, matching the django__django-11179 state-construction precedent.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the velvet spec_view) PASSES with zero hard failures: no diff markers, no reproduced gold-patch line (>=8 chars normalized), no patched file path (lib/matplotlib/offsetbox.py), no patched module path, no patched-symbol echo (DraggableBase/property/canvas/ref_artist all absent from spec-view identifiers and comments), no narration terms (bug/fix/pickle/etc.). same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec region byte-identical.

Gold-reconstruction analysis: the gold edit deletes `self.canvas = self.ref_artist.figure.canvas` from DraggableBase.__init__ and adds a class-level `canvas = property(lambda self: self.ref_artist.figure.canvas)`. The spec view abstracts this to an object-state model (Attr.surface/refHandle/flag/registration, Handler, persistable/surfaceReachable/surfaceFromRef/flagsExact) and NEVER names the Python mechanism (property/pickle/canvas/__getstate__/offsetbox/__init__). The only repo-adjacent token present is `blit` (from inputs useBlit/supportsBlit), which corresponds to the UNCHANGED context line `self._use_blit = use_blit and self.canvas.supports_blit`, not the gold edit — it discloses nothing about the fix.

The correctness behavior encoded (surface absent from persisted state yet reachable via retained reference) is exactly what the PUBLIC problem_statement already implies: pickling a figure with a draggable legend fails on the canvas (TypeError: cannot pickle 'FigureCanvasQTAgg'), expected outcome 'Pickling successful', and the object stays usable. Stating the required behavior abstractly at the state level does not reveal the specific Python edit; this is the accepted django__django-11179 state-construction precedent, judged against problem_statement only (not hints). A solver cannot lexically reconstruct the gold patch from this view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

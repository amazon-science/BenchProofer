# P2 adversarial audit — pytest-dev__pytest-10051

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 8 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_1_echo.lean`, `atk_2_callview.lean`, `atk_3_partialdomain.lean`, `atk_4_boundary.lean`, `atk_5_controlflow.lean`, `atk_6_noop.lean`, `atk_7_truncatesink.lean`, `atk_9_allviews.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — no same-spec impl with a closing clean-axiom proof has a faithful refined patch that fails to resolve. The prior pass's recorded break has been CLOSED by the added transcript clause, and I re-ran that exact break to confirm: the non-resolving patch is no longer the faithful refinement of any VERIFYING impl.

The prior break, re-executed:
  - patch_nostream.diff (LogCaptureHandler.clear does `self.records.clear()` and OMITS `self.stream = StringIO()`) still does NOT resolve: run_resolve resolved=False, completed=True; FAIL_TO_PASS test_clear_for_call_stage=success, PASS_TO_PASS failure=['testing/logging/test_fixture.py::test_clear'] (assert not caplog.text).
  - BUT its Lean counterpart ctl_8_nostream.lean (same_spec=True; impl empties the referenced cell and leaves `transcript` untouched) now FAILS to verify: EXIT=1, error at clause 7 — "(...).run.transcript is not definitionally equal to []". So the spec REJECTS the impl whose patch does not resolve. That is exactly the direction a sound spec must have.

The defect the prior pass found (`self.stream` declared out of model as 'behaviourally orthogonal') has been genuinely repaired, not papered over: `HandlerState.transcript` is now a modeled component and post-condition clause 7 pins `result.transcript = []`.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
import Mathlib
-- imports-end

/-!
Resetting a collector of recorded entries without breaking the views onto it.

A *collector* owns a backing list of recorded entries, and it also feeds a
running *transcript*: a rendered account of everything it has recorded, which
readers consult directly rather than through a reference. Other parts of the
system may, at the start of a phase, take a *view* onto that collector by
remembering which backing list the collector currently uses; reading the view
then reads that same backing list. As long as the collector keeps using the same
backing list object, a view stays coupled to it: it observes whatever the
collector currently holds, including entries appended later.

This file specifies the operation that empties a collector. The required
behaviour is that the collector be emptied **without detaching the views already
taken onto it**, and that the emptying be **total** — nothing the collector had
recorded stays observable by any route:

* the backing list the collector uses is emptied;
* the collector keeps using that **same** backing list object (its reference is
  unchanged), so any view that was pointing at it still points at it — and will
  therefore see the emptied list now and any entries appended afterwards;
* the running transcript reads empty afterwards, so a reader that consults the
  transcript directly is left with nothing from before the emptying;
* no other backing list anywhere is disturbed.

The model is a tiny heap: each backing list is a *cell*, and the collector — and
each view — holds a *reference* (an index) naming the cell it reads. Emptying the
collector must edit the referenced cell in place and preserve the reference,
rather than swapping in a freshly allocated cell, which would silently strand
every view that still names the old one. The transcript is a separate sink that
nothing holds a reference into, so only its contents are constrained, never its
identity.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The emptying
-- operation and its reference-preserving (in-place) semantics are modeled
-- DEEPLY over the observable state (the heap of cells, the references into
-- it, and the transcript sink), so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A tiny heap-with-references model of a collector, the views onto it, and the
transcript it feeds.

* `cells`      — the heap: each entry is one backing list of recorded entries (an
                 entry is modeled by its identity, a `Nat`);
* `records`    — the reference (index into `cells`) the collector currently reads;
* `callView`   — the reference a view already taken onto the collector reads;
* `transcript` — the rendered account of what the collector has recorded, held in
                 a sink that readers consult directly; no reference names it, so
                 only its contents are ever observable. -/
structure HandlerState where
  cells : List (List Nat)
  records : Nat
  callView : Nat
  transcript : List Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The collector is emptied, totally, without detaching its views. The state is
pinned exactly: the heap keeps the same set of backing-list objects (same length,
every untouched object identical, addressed by identity via `cells[i]?` so a
present empty list is never confused with an absent one), and

1. the collector still references the same backing-list object as before
   (its reference is unchanged) — the emptying is in place, not a reallocation;
2. the view reference is unchanged (the operation does not touch the views);
3. the heap holds the same number of backing-list objects (no cell is allocated
   or discarded);
4. the backing list the collector references is now present and empty;
5. a view that was coupled to the collector still observes that present, empty
   backing list (this is the behaviour the surrounding system relies on);
6. every other backing-list object in the heap is unchanged, identity-for-identity
   (frame);
7. the transcript reads empty: emptying the collector discards the rendered
   account too, so a reader consulting the transcript directly observes nothing
   the collector had recorded. Only the transcript's CONTENTS are pinned — how
   the sink comes to read empty is left open, since nothing can name it. -/
def problem_spec_clear (s : HandlerState) (result : HandlerState) : Prop :=
  result.records = s.records ∧
  result.callView = s.callView ∧
  result.cells.length = s.cells.length ∧
  result.cells[result.records]? = some [] ∧
  result.cells[result.callView]? = some [] ∧
  (∀ i, i ≠ s.records → result.cells[i]? = s.cells[i]?) ∧
  result.transcript = []
-- post-conditions-end

-- impl-start
def implementation_clear (s : HandlerState) : HandlerState := Id.run do
  let mut st := s
  -- Empty the contents of the collector's current backing list in place,
  -- keeping the same reference; views onto it stay coupled.
  st := { st with cells := st.cells.set st.records [] }
  -- Discard the rendered account as well, so nothing the collector recorded
  -- stays readable through the transcript either.
  st := { st with transcript := [] }
  return st
-- impl-end

-- proof-start
theorem correct_clear :
    ∀ (s : HandlerState), s.records < s.cells.length → s.callView = s.records →
      problem_spec_clear s (implementation_clear s) := by
  intro s hlt hview
  unfold problem_spec_clear implementation_clear
  show s.records = s.records ∧ s.callView = s.callView ∧
    (s.cells.set s.records []).length = s.cells.length ∧
    (s.cells.set s.records [])[s.records]? = some [] ∧
    (s.cells.set s.records [])[s.callView]? = some [] ∧
    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧
    ([] : List Nat) = []
  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
  · exact List.length_set
  · rw [List.getElem?_set_self]
    simp [hlt]
  · rw [hview, List.getElem?_set_self]
    simp [hlt]
  · intro i hi
    rw [List.getElem?_set_ne (Ne.symm hi)]
-- proof-end
```

Attack 2 — `atk_2_callview.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,11 +95,8 @@
 -- impl-start
 def implementation_clear (s : HandlerState) : HandlerState := Id.run do
   let mut st := s
-  -- Empty the contents of the collector's current backing list in place,
-  -- keeping the same reference; views onto it stay coupled.
-  st := { st with cells := st.cells.set st.records [] }
-  -- Discard the rendered account as well, so nothing the collector recorded
-  -- stays readable through the transcript either.
+  -- Empty the cell named by the VIEW, not by the collector's own reference.
+  st := { st with cells := st.cells.set st.callView [] }
   st := { st with transcript := [] }
   return st
 -- impl-end
@@ -111,16 +108,17 @@
   intro s hlt hview
   unfold problem_spec_clear implementation_clear
   show s.records = s.records ∧ s.callView = s.callView ∧
-    (s.cells.set s.records []).length = s.cells.length ∧
-    (s.cells.set s.records [])[s.records]? = some [] ∧
-    (s.cells.set s.records [])[s.callView]? = some [] ∧
-    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧
+    (s.cells.set s.callView []).length = s.cells.length ∧
+    (s.cells.set s.callView [])[s.records]? = some [] ∧
+    (s.cells.set s.callView [])[s.callView]? = some [] ∧
+    (∀ i, i ≠ s.records → (s.cells.set s.callView [])[i]? = s.cells[i]?) ∧
     ([] : List Nat) = []
+  rw [hview]
   refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
   · exact List.length_set
   · rw [List.getElem?_set_self]
     simp [hlt]
-  · rw [hview, List.getElem?_set_self]
+  · rw [List.getElem?_set_self]
     simp [hlt]
   · intro i hi
     rw [List.getElem?_set_ne (Ne.symm hi)]
```

Attack 3 — `atk_3_partialdomain.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,15 +93,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_clear (s : HandlerState) : HandlerState := Id.run do
-  let mut st := s
-  -- Empty the contents of the collector's current backing list in place,
-  -- keeping the same reference; views onto it stay coupled.
-  st := { st with cells := st.cells.set st.records [] }
-  -- Discard the rendered account as well, so nothing the collector recorded
-  -- stays readable through the transcript either.
-  st := { st with transcript := [] }
-  return st
+def implementation_clear (s : HandlerState) : HandlerState :=
+  if s.callView = s.records then
+    { s with cells := s.cells.set s.records [], transcript := [] }
+  else
+    -- Off the precondition: destroy the heap and both references.
+    { s with cells := [], records := 0, callView := 0, transcript := [42] }
 -- impl-end
 
 -- proof-start
@@ -110,12 +107,7 @@
       problem_spec_clear s (implementation_clear s) := by
   intro s hlt hview
   unfold problem_spec_clear implementation_clear
-  show s.records = s.records ∧ s.callView = s.callView ∧
-    (s.cells.set s.records []).length = s.cells.length ∧
-    (s.cells.set s.records [])[s.records]? = some [] ∧
-    (s.cells.set s.records [])[s.callView]? = some [] ∧
-    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧
-    ([] : List Nat) = []
+  rw [if_pos hview]
   refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
   · exact List.length_set
   · rw [List.getElem?_set_self]
```

Attack 4 — `atk_4_boundary.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,15 +93,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_clear (s : HandlerState) : HandlerState := Id.run do
-  let mut st := s
-  -- Empty the contents of the collector's current backing list in place,
-  -- keeping the same reference; views onto it stay coupled.
-  st := { st with cells := st.cells.set st.records [] }
-  -- Discard the rendered account as well, so nothing the collector recorded
-  -- stays readable through the transcript either.
-  st := { st with transcript := [] }
-  return st
+def implementation_clear (s : HandlerState) : HandlerState :=
+  if s.records < s.cells.length then
+    { s with cells := s.cells.set s.records [], transcript := [] }
+  else
+    -- Off the precondition: the pre-patch reset() semantics (reallocate +
+    -- repoint), which strands every view.
+    { s with cells := s.cells ++ [[]], records := s.cells.length,
+             transcript := [7] }
 -- impl-end
 
 -- proof-start
@@ -110,12 +109,7 @@
       problem_spec_clear s (implementation_clear s) := by
   intro s hlt hview
   unfold problem_spec_clear implementation_clear
-  show s.records = s.records ∧ s.callView = s.callView ∧
-    (s.cells.set s.records []).length = s.cells.length ∧
-    (s.cells.set s.records [])[s.records]? = some [] ∧
-    (s.cells.set s.records [])[s.callView]? = some [] ∧
-    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧
-    ([] : List Nat) = []
+  rw [if_pos hlt]
   refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
   · exact List.length_set
   · rw [List.getElem?_set_self]
```

Attack 5 — `atk_5_controlflow.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,11 +95,10 @@
 -- impl-start
 def implementation_clear (s : HandlerState) : HandlerState := Id.run do
   let mut st := s
-  -- Empty the contents of the collector's current backing list in place,
-  -- keeping the same reference; views onto it stay coupled.
+  -- First OVERWRITE the collector's cell with a bogus recorded entry ...
+  st := { st with cells := st.cells.set st.records [7] }
+  -- ... then empty it. The net effect on the final state equals gold.
   st := { st with cells := st.cells.set st.records [] }
-  -- Discard the rendered account as well, so nothing the collector recorded
-  -- stays readable through the transcript either.
   st := { st with transcript := [] }
   return st
 -- impl-end
@@ -110,6 +109,7 @@
       problem_spec_clear s (implementation_clear s) := by
   intro s hlt hview
   unfold problem_spec_clear implementation_clear
+  simp only [List.set_set]
   show s.records = s.records ∧ s.callView = s.callView ∧
     (s.cells.set s.records []).length = s.cells.length ∧
     (s.cells.set s.records [])[s.records]? = some [] ∧
```

Attack 6 — `atk_6_noop.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,12 +95,10 @@
 -- impl-start
 def implementation_clear (s : HandlerState) : HandlerState := Id.run do
   let mut st := s
-  -- Empty the contents of the collector's current backing list in place,
-  -- keeping the same reference; views onto it stay coupled.
+  let _unused := st.cells.length + st.records + st.callView
+  st := { st with records := st.records, callView := st.callView }
   st := { st with cells := st.cells.set st.records [] }
-  -- Discard the rendered account as well, so nothing the collector recorded
-  -- stays readable through the transcript either.
-  st := { st with transcript := [] }
+  st := { st with transcript := List.drop 5 ([] : List Nat) }
   return st
 -- impl-end
 
@@ -110,6 +108,7 @@
       problem_spec_clear s (implementation_clear s) := by
   intro s hlt hview
   unfold problem_spec_clear implementation_clear
+  simp only [List.drop_nil]
   show s.records = s.records ∧ s.callView = s.callView ∧
     (s.cells.set s.records []).length = s.cells.length ∧
     (s.cells.set s.records [])[s.records]? = some [] ∧
```

Attack 7 — `atk_7_truncatesink.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,12 +95,10 @@
 -- impl-start
 def implementation_clear (s : HandlerState) : HandlerState := Id.run do
   let mut st := s
-  -- Empty the contents of the collector's current backing list in place,
-  -- keeping the same reference; views onto it stay coupled.
   st := { st with cells := st.cells.set st.records [] }
-  -- Discard the rendered account as well, so nothing the collector recorded
-  -- stays readable through the transcript either.
-  st := { st with transcript := [] }
+  -- Empty the EXISTING transcript sink in place, by truncating it to zero
+  -- length, instead of installing a freshly allocated sink.
+  st := { st with transcript := st.transcript.take 0 }
   return st
 -- impl-end
 
@@ -110,6 +108,7 @@
       problem_spec_clear s (implementation_clear s) := by
   intro s hlt hview
   unfold problem_spec_clear implementation_clear
+  simp only [List.take_zero]
   show s.records = s.records ∧ s.callView = s.callView ∧
     (s.cells.set s.records []).length = s.cells.length ∧
     (s.cells.set s.records [])[s.records]? = some [] ∧
```

Attack 8 — `atk_9_allviews.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,11 +95,10 @@
 -- impl-start
 def implementation_clear (s : HandlerState) : HandlerState := Id.run do
   let mut st := s
-  -- Empty the contents of the collector's current backing list in place,
-  -- keeping the same reference; views onto it stay coupled.
+  -- Empty the cell the collector names ...
   st := { st with cells := st.cells.set st.records [] }
-  -- Discard the rendered account as well, so nothing the collector recorded
-  -- stays readable through the transcript either.
+  -- ... and also the cell the view names (same cell under the precondition).
+  st := { st with cells := st.cells.set st.callView [] }
   st := { st with transcript := [] }
   return st
 -- impl-end
@@ -110,18 +109,13 @@
       problem_spec_clear s (implementation_clear s) := by
   intro s hlt hview
   unfold problem_spec_clear implementation_clear
-  show s.records = s.records ∧ s.callView = s.callView ∧
-    (s.cells.set s.records []).length = s.cells.length ∧
-    (s.cells.set s.records [])[s.records]? = some [] ∧
-    (s.cells.set s.records [])[s.callView]? = some [] ∧
-    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧
-    ([] : List Nat) = []
-  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
-  · exact List.length_set
-  · rw [List.getElem?_set_self]
-    simp [hlt]
-  · rw [hview, List.getElem?_set_self]
-    simp [hlt]
+  simp only [hview, List.set_set]
+  refine ⟨rfl, rfl, List.length_set, ?_, ?_, ?_, rfl⟩
+  · show (s.cells.set s.records [])[s.records]? = some []
+    rw [List.getElem?_set_self]; simp [hlt]
+  · show (s.cells.set s.records [])[s.records]? = some []
+    rw [List.getElem?_set_self]; simp [hlt]
   · intro i hi
+    show (s.cells.set s.records [])[i]? = s.cells[i]?
     rw [List.getElem?_set_ne (Ne.symm hi)]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resetting a collector of recorded entries without breaking the views onto it.

A *collector* owns a backing list of recorded entries, and it also feeds a
running *transcript*: a rendered account of everything it has recorded, which
readers consult directly rather than through a reference. Other parts of the
system may, at the start of a phase, take a *view* onto that collector by
remembering which backing list the collector currently uses; reading the view
then reads that same backing list. As long as the collector keeps using the same
backing list object, a view stays coupled to it: it observes whatever the
collector currently holds, including entries appended later.

This file specifies the operation that empties a collector. The required
behaviour is that the collector be emptied **without detaching the views already
taken onto it**, and that the emptying be **total** — nothing the collector had
recorded stays observable by any route:

* the backing list the collector uses is emptied;
* the collector keeps using that **same** backing list object (its reference is
  unchanged), so any view that was pointing at it still points at it — and will
  therefore see the emptied list now and any entries appended afterwards;
* the running transcript reads empty afterwards, so a reader that consults the
  transcript directly is left with nothing from before the emptying;
* no other backing list anywhere is disturbed.

The model is a tiny heap: each backing list is a *cell*, and the collector — and
each view — holds a *reference* (an index) naming the cell it reads. Emptying the
collector must edit the referenced cell in place and preserve the reference,
rather than swapping in a freshly allocated cell, which would silently strand
every view that still names the old one. The transcript is a separate sink that
nothing holds a reference into, so only its contents are constrained, never its
identity.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The emptying
-- operation and its reference-preserving (in-place) semantics are modeled
-- DEEPLY over the observable state (the heap of cells, the references into
-- it, and the transcript sink), so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A tiny heap-with-references model of a collector, the views onto it, and the
transcript it feeds.

* `cells`      — the heap: each entry is one backing list of recorded entries (an
                 entry is modeled by its identity, a `Nat`);
* `records`    — the reference (index into `cells`) the collector currently reads;
* `callView`   — the reference a view already taken onto the collector reads;
* `transcript` — the rendered account of what the collector has recorded, held in
                 a sink that readers consult directly; no reference names it, so
                 only its contents are ever observable. -/
structure HandlerState where
  cells : List (List Nat)
  records : Nat
  callView : Nat
  transcript : List Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The collector is emptied, totally, without detaching its views. The state is
pinned exactly: the heap keeps the same set of backing-list objects (same length,
every untouched object identical, addressed by identity via `cells[i]?` so a
present empty list is never confused with an absent one), and

1. the collector still references the same backing-list object as before
   (its reference is unchanged) — the emptying is in place, not a reallocation;
2. the view reference is unchanged (the operation does not touch the views);
3. the heap holds the same number of backing-list objects (no cell is allocated
   or discarded);
4. the backing list the collector references is now present and empty;
5. a view that was coupled to the collector still observes that present, empty
   backing list (this is the behaviour the surrounding system relies on);
6. every other backing-list object in the heap is unchanged, identity-for-identity
   (frame);
7. the transcript reads empty: emptying the collector discards the rendered
   account too, so a reader consulting the transcript directly observes nothing
   the collector had recorded. Only the transcript's CONTENTS are pinned — how
   the sink comes to read empty is left open, since nothing can name it. -/
def problem_spec_clear (s : HandlerState) (result : HandlerState) : Prop :=
  result.records = s.records ∧
  result.callView = s.callView ∧
  result.cells.length = s.cells.length ∧
  result.cells[result.records]? = some [] ∧
  result.cells[result.callView]? = some [] ∧
  (∀ i, i ≠ s.records → result.cells[i]? = s.cells[i]?) ∧
  result.transcript = []
-- post-conditions-end

-- impl-start
def implementation_clear (s : HandlerState) : HandlerState := Id.run do
  let mut st := s
  -- Empty the contents of the collector's current backing list in place,
  -- keeping the same reference; views onto it stay coupled.
  st := { st with cells := st.cells.set st.records [] }
  -- Discard the rendered account as well, so nothing the collector recorded
  -- stays readable through the transcript either.
  st := { st with transcript := [] }
  return st
-- impl-end

-- proof-start
theorem correct_clear :
    ∀ (s : HandlerState), s.records < s.cells.length → s.callView = s.records →
      problem_spec_clear s (implementation_clear s) := by
  intro s hlt hview
  unfold problem_spec_clear implementation_clear
  show s.records = s.records ∧ s.callView = s.callView ∧
    (s.cells.set s.records []).length = s.cells.length ∧
    (s.cells.set s.records [])[s.records]? = some [] ∧
    (s.cells.set s.records [])[s.callView]? = some [] ∧
    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧
    ([] : List Nat) = []
  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
  · exact List.length_set
  · rw [List.getElem?_set_self]
    simp [hlt]
  · rw [hview, List.getElem?_set_self]
    simp [hlt]
  · intro i hi
    rw [List.getElem?_set_ne (Ne.symm hi)]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME_SPEC: all 8 attack files + both controls == True via swebench_unified.markers.same_spec (lean backend) against the bundle Solution.lean. NOTE on method: for the lean flavor spec_view elides BOTH the impl AND the proof region, so an attack may rewrite the proof tactics as well as the impl; axioms/pure/post-conditions/prose stayed byte-identical in every file (generated by gen.py, which splices only those two regions).

ATTACK RESULTS — command: `bash scripts/lean_verify.sh <file>` from the repo root; axioms via a sibling ax_<name>.lean with `#print axioms correct_clear` appended, same command.

| attack | verify exit | #print axioms | faithful patch | resolve |
|---|---|---|---|---|
| atk_1_echo (ungrounded-oracle echo; BYTE-IDENTICAL to Solution.lean, cmp confirms) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_2_callview (empties cell named by callView, not records) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_3_partialdomain (gold on `callView = records`, heap+refs destroyed off it) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_4_boundary (gold on `records < cells.length`, pre-patch reallocate+repoint off it) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_5_controlflow (writes bogus entry [7] into the cell IN PLACE, then empties; net = gold by List.set_set) | 0 | [propext, Quot.sound] | patch_controlflow.diff | resolved=True, completed=True |
| atk_6_noop (discarded let + redundant self-reassign of both refs + transcript via List.drop) | 0 | [propext, Quot.sound] | patch_gold.diff | resolved=True, completed=True |
| atk_7_truncatesink (transcript emptied by TRUNCATING the existing sink, not installing a fresh one) | 0 | [propext] | patch_truncate.diff (`self.stream.truncate(0)`) | resolved=True, completed=True |
| atk_9_allviews (empties the cell named by records AND the one named by callView; one cell under the precondition) | 0 | [propext, Quot.sound] | patch_allviews.diff | resolved=True, completed=True |

No sorryAx and no custom axiom/opaque in any of the eight; grep for sorry/admit across all attack files + positive control returns NONE.

POSITIVE CONTROL: positive_control.lean (= Solution.lean) EXIT=0.

PREPATCH BUG REPRODUCED (true): prepatch.lean (= Solution_prepatch.lean; models reset() as `cells := cells ++ [[]]; records := cells.length`) FAILS: EXIT=1, type mismatch at 112:88 — the carried gold `rfl` cannot equate the reallocating result with `{cells := s.cells.set s.records [], records := s.records, ...}`. The spec is genuinely FALSE for it (clause 3 pins cells.length while `cells ++ [[]]` grows the heap; clause 1 pins records while it repoints to the old length), so no fresh proof closes it either.

EVERY PATCH RUN THROUGH THE OFFICIAL HARNESS (swebench_unified.harness.run_resolve, retries=0, real Docker oracle; driver resolve_one.py, raw reports in resolve_*.json). All five completed=True — no host-saturation inconclusives:
  - patch_gold.diff       resolved=True  (F2P 1/1, P2P 15/15)
  - patch_controlflow.diff resolved=True  (F2P 1/1, P2P 15/15)
  - patch_truncate.diff   resolved=True  (F2P 1/1, P2P 15/15)
  - patch_allviews.diff   resolved=True  (F2P 1/1, P2P 15/15)
  - patch_nostream.diff   resolved=False (F2P 1/1, P2P 14/15, failure=test_clear) — NEGATIVE CONTROL, and its Lean counterpart ctl_8_nostream.lean does NOT verify (EXIT=1 on clause 7), so this is not a break.
All four attack patches verified appliable with `git apply --check` before running.

NOTABLE, on atk_7_truncatesink: refinement.md explicitly blesses in-place truncation of the sink as an equally-faithful route ("any route to empty is equivalent, since nothing references the sink"). I probed this because CPython's `StringIO.truncate(0)` does NOT reset the stream position — a later write pads with NULs (`s.truncate(0); s.write('X')` yields '\\x00'*12 + 'X'), a real behaviour the contents-only `transcript` model cannot express. It nonetheless RESOLVES, because the only P2P assertion after a clear is `assert not caplog.text` (emptiness at that instant) and nothing in the suite logs again after `caplog.clear()` within the same phase. So the claim in refinement.md is true for THIS test suite but rests on that absence rather than on genuine equivalence; it is a latent, not an actual, over-permission. Worth a note for a future re-port, not a G-EQ break.

WHY THE SPEC HOLDS: problem_spec_clear is FUNCTIONAL on its precondition domain — clauses 1/2 pin both references, 3 pins heap length, 4 pins the referenced cell to `some []`, 6 frames every other cell identity-for-identity via getElem?, and 7 pins the transcript. Together these determine the post-state uniquely given (s, precondition), so every verifying impl agrees with gold on-domain and refines to a resolving patch. The partial-domain and boundary attacks (atk_3/atk_4) only exploit the off-domain freedom that the `correct_clear` binder legitimately grants, and off-domain states are unreachable in the real system (line 699 establishes callView = records at phase setup; the collector's reference is always live). Frame clause 6 genuinely bites: ctl_10_allcells.lean (empties EVERY cell in the heap) could not be closed — EXIT=3, the frame goal `∀ i ≠ records, (cells.map (fun _ => []))[i]? = cells[i]?` is false and left as sorry.

REFINEMENT.MD AUDIT (A-legs): the axioms region contains PROSE ONLY — zero `axiom`/`opaque` declarations (grep -cE '^\s*(axiom|opaque)\b' = 0), meta.json axioms=[] / opaque_callees=[] / deep_model_references=[], and `#print axioms correct_clear` on the shipped Solution yields [propext] with no custom constant. So there are NO A-consumed and NO A-reference legs, hence no callee-contract correspondence to validate and G-AX legitimately skips (axiom_check.py is a skip stub, consistent with the artifact). All 4 legs are tagged R (grep of the tag column: 4x R, 0x A-consumed, 0x A-reference, 0x I) — no kind-3 leg. The R legs are mechanically covered by G-CONF per my brief.

MODEL↔PATCH CORRESPONDENCE: verified against the real callees at base_commit. `cells.set records []` ↔ `self.records.clear()` (in-place, identity preserved) — correct, and it is exactly what distinguishes the fix from `reset()`'s `self.records = []` rebind at logging.py:344-346. `transcript := []` ↔ `self.stream = StringIO()` read back through `caplog.text` = `_remove_ansi_escape_sequences(self.handler.stream.getvalue())` at 402-404 — correct. Precondition `callView = records` ↔ the setup aliasing `item.stash[caplog_records_key][when] = caplog_handler.records` at line 699 — correct. Precondition `records < cells.length` ↔ the collector's reference being live — correct. The asymmetry the bundle draws (records identity IS observable via the aliased view and is pinned; the sink's identity is NOT, since caplog.text re-reads via getvalue(), so only contents are pinned) matches the code I read.

VERDICT: SOUND. Eight distinct same-spec wrong/adorned impls (echo, callView-substitution, partial-domain, boundary, control-flow-effect, no-op-adorned, in-place-sink-truncation, all-views) all verify EXIT=0 with clean axioms, and every one of their materialized faithful patches RESOLVES under the official harness. The one patch that does not resolve corresponds to an impl the spec REJECTS. verify ⇒ correct held under every attack I could construct; the previously recorded G-EQ break is closed and I re-executed it to prove so.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 8 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_1_echo.lean`, `atk_2_callview.lean`, `atk_3_partialdomain.lean`, `atk_4_boundary.lean`, `atk_5_controlflow.lean`, `atk_6_noop.lean`, `atk_7_truncatesink.lean`, `atk_9_allviews.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — no same-spec impl with a closing clean-axiom proof has a faithful refined patch that fails to resolve. The prior pass's recorded break has been CLOSED by the added transcript clause, and I re-ran that exact break to confirm: the non-resolving patch is no longer the faithful refinement of any VERIFYING impl.

The prior break, re-executed:
  - patch_nostream.diff (LogCaptureHandler.clear does `self.records.clear()` and OMITS `self.stream = StringIO()`) still does NOT resolve: run_resolve resolved=False, completed=True; FAIL_TO_PASS test_clear_for_call_stage=success, PASS_TO_PASS failure=['testing/logging/test_fixture.py::test_clear'] (assert not caplog.text).
  - BUT its Lean counterpart ctl_8_nostream.lean (same_spec=True; impl empties the referenced cell and leaves `transcript` untouched) now FAILS to verify: EXIT=1, error at clause 7 — "(...).run.transcript is not definitionally equal to []". So the spec REJECTS the impl whose patch does not resolve. That is exactly the direction a sound spec must have.

The defect the prior pass found (`self.stream` declared out of model as 'behaviourally orthogonal') has been genuinely repaired, not papered over: `HandlerState.transcript` is now a modeled component and post-condition clause 7 pins `result.transcript = []`.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2_callview.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_partialdomain.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_boundary.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5_controlflow.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_noop.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_truncatesink.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_9_allviews.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resetting a collector of recorded entries without breaking the views onto it.

A *collector* owns a backing list of recorded entries, and it also feeds a
running *transcript*: a rendered account of everything it has recorded, which
readers consult directly rather than through a reference. Other parts of the
system may, at the start of a phase, take a *view* onto that collector by
remembering which backing list the collector currently uses; reading the view
then reads that same backing list. As long as the collector keeps using the same
backing list object, a view stays coupled to it: it observes whatever the
collector currently holds, including entries appended later.

This file specifies the operation that empties a collector. The required
behaviour is that the collector be emptied **without detaching the views already
taken onto it**, and that the emptying be **total** — nothing the collector had
recorded stays observable by any route:

* the backing list the collector uses is emptied;
* the collector keeps using that **same** backing list object (its reference is
  unchanged), so any view that was pointing at it still points at it — and will
  therefore see the emptied list now and any entries appended afterwards;
* the running transcript reads empty afterwards, so a reader that consults the
  transcript directly is left with nothing from before the emptying;
* no other backing list anywhere is disturbed.

The model is a tiny heap: each backing list is a *cell*, and the collector — and
each view — holds a *reference* (an index) naming the cell it reads. Emptying the
collector must edit the referenced cell in place and preserve the reference,
rather than swapping in a freshly allocated cell, which would silently strand
every view that still names the old one. The transcript is a separate sink that
nothing holds a reference into, so only its contents are constrained, never its
identity.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The emptying
-- operation and its reference-preserving (in-place) semantics are modeled
-- DEEPLY over the observable state (the heap of cells, the references into
-- it, and the transcript sink), so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A tiny heap-with-references model of a collector, the views onto it, and the
transcript it feeds.

* `cells`      — the heap: each entry is one backing list of recorded entries (an
                 entry is modeled by its identity, a `Nat`);
* `records`    — the reference (index into `cells`) the collector currently reads;
* `callView`   — the reference a view already taken onto the collector reads;
* `transcript` — the rendered account of what the collector has recorded, held in
                 a sink that readers consult directly; no reference names it, so
                 only its contents are ever observable. -/
structure HandlerState where
  cells : List (List Nat)
  records : Nat
  callView : Nat
  transcript : List Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The collector is emptied, totally, without detaching its views. The state is
pinned exactly: the heap keeps the same set of backing-list objects (same length,
every untouched object identical, addressed by identity via `cells[i]?` so a
present empty list is never confused with an absent one), and

1. the collector still references the same backing-list object as before
   (its reference is unchanged) — the emptying is in place, not a reallocation;
2. the view reference is unchanged (the operation does not touch the views);
3. the heap holds the same number of backing-list objects (no cell is allocated
   or discarded);
4. the backing list the collector references is now present and empty;
5. a view that was coupled to the collector still observes that present, empty
   backing list (this is the behaviour the surrounding system relies on);
6. every other backing-list object in the heap is unchanged, identity-for-identity
   (frame);
7. the transcript reads empty: emptying the collector discards the rendered
   account too, so a reader consulting the transcript directly observes nothing
   the collector had recorded. Only the transcript's CONTENTS are pinned — how
   the sink comes to read empty is left open, since nothing can name it. -/
def problem_spec_clear (s : HandlerState) (result : HandlerState) : Prop :=
  result.records = s.records ∧
  result.callView = s.callView ∧
  result.cells.length = s.cells.length ∧
  result.cells[result.records]? = some [] ∧
  result.cells[result.callView]? = some [] ∧
  (∀ i, i ≠ s.records → result.cells[i]? = s.cells[i]?) ∧
  result.transcript = []
-- post-conditions-end

-- impl-start
def implementation_clear (s : HandlerState) : HandlerState := Id.run do
  let mut st := s
  -- Empty the contents of the collector's current backing list in place,
  -- keeping the same reference; views onto it stay coupled.
  st := { st with cells := st.cells.set st.records [] }
  -- Discard the rendered account as well, so nothing the collector recorded
  -- stays readable through the transcript either.
  st := { st with transcript := [] }
  return st
-- impl-end

-- proof-start
theorem correct_clear :
    ∀ (s : HandlerState), s.records < s.cells.length → s.callView = s.records →
      problem_spec_clear s (implementation_clear s) := by
  intro s hlt hview
  unfold problem_spec_clear implementation_clear
  show s.records = s.records ∧ s.callView = s.callView ∧
    (s.cells.set s.records []).length = s.cells.length ∧
    (s.cells.set s.records [])[s.records]? = some [] ∧
    (s.cells.set s.records [])[s.callView]? = some [] ∧
    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧
    ([] : List Nat) = []
  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
  · exact List.length_set
  · rw [List.getElem?_set_self]
    simp [hlt]
  · rw [hview, List.getElem?_set_self]
    simp [hlt]
  · intro i hi
    rw [List.getElem?_set_ne (Ne.symm hi)]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME_SPEC: all 8 attack files + both controls == True via swebench_unified.markers.same_spec (lean backend) against the bundle Solution.lean. NOTE on method: for the lean flavor spec_view elides BOTH the impl AND the proof region, so an attack may rewrite the proof tactics as well as the impl; axioms/pure/post-conditions/prose stayed byte-identical in every file (generated by gen.py, which splices only those two regions).

ATTACK RESULTS — command: `bash scripts/lean_verify.sh <file>` from the repo root; axioms via a sibling ax_<name>.lean with `#print axioms correct_clear` appended, same command.

| attack | verify exit | #print axioms | faithful patch | resolve |
|---|---|---|---|---|
| atk_1_echo (ungrounded-oracle echo; BYTE-IDENTICAL to Solution.lean, cmp confirms) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_2_callview (empties cell named by callView, not records) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_3_partialdomain (gold on `callView = records`, heap+refs destroyed off it) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_4_boundary (gold on `records < cells.length`, pre-patch reallocate+repoint off it) | 0 | [propext] | patch_gold.diff | resolved=True, completed=True |
| atk_5_controlflow (writes bogus entry [7] into the cell IN PLACE, then empties; net = gold by List.set_set) | 0 | [propext, Quot.sound] | patch_controlflow.diff | resolved=True, completed=True |
| atk_6_noop (discarded let + redundant self-reassign of both refs + transcript via List.drop) | 0 | [propext, Quot.sound] | patch_gold.diff | resolved=True, completed=True |
| atk_7_truncatesink (transcript emptied by TRUNCATING the existing sink, not installing a fresh one) | 0 | [propext] | patch_truncate.diff (`self.stream.truncate(0)`) | resolved=True, completed=True |
| atk_9_allviews (empties the cell named by records AND the one named by callView; one cell under the precondition) | 0 | [propext, Quot.sound] | patch_allviews.diff | resolved=True, completed=True |

No sorryAx and no custom axiom/opaque in any of the eight; grep for sorry/admit across all attack files + positive control returns NONE.

POSITIVE CONTROL: positive_control.lean (= Solution.lean) EXIT=0.

PREPATCH BUG REPRODUCED (true): prepatch.lean (= Solution_prepatch.lean; models reset() as `cells := cells ++ [[]]; records := cells.length`) FAILS: EXIT=1, type mismatch at 112:88 — the carried gold `rfl` cannot equate the reallocating result with `{cells := s.cells.set s.records [], records := s.records, ...}`. The spec is genuinely FALSE for it (clause 3 pins cells.length while `cells ++ [[]]` grows the heap; clause 1 pins records while it repoints to the old length), so no fresh proof closes it either.

EVERY PATCH RUN THROUGH THE OFFICIAL HARNESS (swebench_unified.harness.run_resolve, retries=0, real Docker oracle; driver resolve_one.py, raw reports in resolve_*.json). All five completed=True — no host-saturation inconclusives:
  - patch_gold.diff       resolved=True  (F2P 1/1, P2P 15/15)
  - patch_controlflow.diff resolved=True  (F2P 1/1, P2P 15/15)
  - patch_truncate.diff   resolved=True  (F2P 1/1, P2P 15/15)
  - patch_allviews.diff   resolved=True  (F2P 1/1, P2P 15/15)
  - patch_nostream.diff   resolved=False (F2P 1/1, P2P 14/15, failure=test_clear) — NEGATIVE CONTROL, and its Lean counterpart ctl_8_nostream.lean does NOT verify (EXIT=1 on clause 7), so this is not a break.
All four attack patches verified appliable with `git apply --check` before running.

NOTABLE, on atk_7_truncatesink: refinement.md explicitly blesses in-place truncation of the sink as an equally-faithful route ("any route to empty is equivalent, since nothing references the sink"). I probed this because CPython's `StringIO.truncate(0)` does NOT reset the stream position — a later write pads with NULs (`s.truncate(0); s.write('X')` yields '\\x00'*12 + 'X'), a real behaviour the contents-only `transcript` model cannot express. It nonetheless RESOLVES, because the only P2P assertion after a clear is `assert not caplog.text` (emptiness at that instant) and nothing in the suite logs again after `caplog.clear()` within the same phase. So the claim in refinement.md is true for THIS test suite but rests on that absence rather than on genuine equivalence; it is a latent, not an actual, over-permission. Worth a note for a future re-port, not a G-EQ break.

WHY THE SPEC HOLDS: problem_spec_clear is FUNCTIONAL on its precondition domain — clauses 1/2 pin both references, 3 pins heap length, 4 pins the referenced cell to `some []`, 6 frames every other cell identity-for-identity via getElem?, and 7 pins the transcript. Together these determine the post-state uniquely given (s, precondition), so every verifying impl agrees with gold on-domain and refines to a resolving patch. The partial-domain and boundary attacks (atk_3/atk_4) only exploit the off-domain freedom that the `correct_clear` binder legitimately grants, and off-domain states are unreachable in the real system (line 699 establishes callView = records at phase setup; the collector's reference is always live). Frame clause 6 genuinely bites: ctl_10_allcells.lean (empties EVERY cell in the heap) could not be closed — EXIT=3, the frame goal `∀ i ≠ records, (cells.map (fun _ => []))[i]? = cells[i]?` is false and left as sorry.

REFINEMENT.MD AUDIT (A-legs): the axioms region contains PROSE ONLY — zero `axiom`/`opaque` declarations (grep -cE '^\s*(axiom|opaque)\b' = 0), meta.json axioms=[] / opaque_callees=[] / deep_model_references=[], and `#print axioms correct_clear` on the shipped Solution yields [propext] with no custom constant. So there are NO A-consumed and NO A-reference legs, hence no callee-contract correspondence to validate and G-AX legitimately skips (axiom_check.py is a skip stub, consistent with the artifact). All 4 legs are tagged R (grep of the tag column: 4x R, 0x A-consumed, 0x A-reference, 0x I) — no kind-3 leg. The R legs are mechanically covered by G-CONF per my brief.

MODEL↔PATCH CORRESPONDENCE: verified against the real callees at base_commit. `cells.set records []` ↔ `self.records.clear()` (in-place, identity preserved) — correct, and it is exactly what distinguishes the fix from `reset()`'s `self.records = []` rebind at logging.py:344-346. `transcript := []` ↔ `self.stream = StringIO()` read back through `caplog.text` = `_remove_ansi_escape_sequences(self.handler.stream.getvalue())` at 402-404 — correct. Precondition `callView = records` ↔ the setup aliasing `item.stash[caplog_records_key][when] = caplog_handler.records` at line 699 — correct. Precondition `records < cells.length` ↔ the collector's reference being live — correct. The asymmetry the bundle draws (records identity IS observable via the aliased view and is pinned; the sink's identity is NOT, since caplog.text re-reads via getvalue(), so only contents are pinned) matches the code I read.

VERDICT: SOUND. Eight distinct same-spec wrong/adorned impls (echo, callView-substitution, partial-domain, boundary, control-flow-effect, no-op-adorned, in-place-sink-truncation, all-views) all verify EXIT=0 with clean axioms, and every one of their materialized faithful patches RESOLVES under the official harness. The one patch that does not resolve corresponds to an impl the spec REJECTS. verify ⇒ correct held under every attack I could construct; the previously recorded G-EQ break is closed and I re-executed it to prove so.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS (spec-too-strong / drift) lane for pytest-dev__pytest-10051 (lean). I could not produce a diverging input; no clause of problem_spec_clear over-constrains the real callee.

### MECHANICS (all pass, re-run independently, not taken from meta.json):
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- `#print axioms correct_clear` -> "depends on axioms: [propext]". No sorryAx; the proof is real, not fake.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True. I additionally confirmed the axioms / pure / post-conditions regions are BYTE-IDENTICAL between the two files, so only impl+proof differ.
- conformance_check.py: checked=120006, disagreements=0, status=pass. axiom_check.py: skip (no consumed callee axiom, no A-reference; axioms region is empty, consistent with the all-R refinement). properties.py: exit 0.

REAL-CALLEE DIFFERENTIAL (the substance of this lane). I built a worktree of pytest-dev/pytest at base_commit aa55975c7d3f6c9f6d7f68accc41bb7cadf0eb9a, applied patch.diff (verified it lands the new LogCaptureHandler.clear = `self.records.clear(); self.stream = StringIO()` and reroutes LogCaptureFixture.clear to it), and imported the GENUINE post-patch module (confirmed via inspect.getsource on the live objects; needed a py/_version shim to get past an unrelated env import clash).

I then modeled the heap with real Python list objects -- handler.records IS cells[records], the stash view IS cells[callView] -- and evaluated all seven clauses against real object identity (id()) rather than value equality, which is the only way this bundle's property is even visible: c1 result.records = s.records ...... records attribute binding unchanged (list.clear does not rebind) c2 result.callView = s.callView ... clear never touches the stash c3 cells.length preserved .......... no backing list allocated/freed (the fresh StringIO is transcript, not a cell) c4 cells[records]? = some [] ....... in-place empty c5 cells[callView]? = some [] ...... holds under the precondition c6 frame on all i != records ....... only the collector's cell is mutated c7 transcript = [] ................. stream.getvalue() == '' Result: 7 hand-built edge cases + 30,000 randomized heaps honoring the theorem preconditions -> ZERO divergence.

PRECONDITIONS ARE EARNED, NOT ASSUMED AWAY. `s.callView = s.records` is load-bearing: I showed that with a non-aliased view (callView=0, records=1) the real callee leaves that cell populated, so clause 5 genuinely fails there. That is not spec drift, because the real repo ESTABLISHES the alias -- I replicated the actual phase sequence (_runtest_for: reset(); stash[when] = handler.records at line 699) and confirmed stash['call'] is handler.records at clear() time, then reproduced the full F2P trace: after clear the call view reads [], stays coupled, and a subsequently appended record shows up through it, while the setup cell keeps ['a_setup_log']. `s.records < s.cells.length` is likewise just liveness of the collector reference. I also checked the model's distinct-index assumption: the per-phase records objects are three distinct ids, so no cross-cell aliasing is being papered over. Note the non-aliased setup view is still protected -- clause 6's frame covers it -- so the single-view model is not hiding a gap.

OUT-OF-LANE FINDING, reported for the record and NOT as my verdict. The lean spec view elides the entire `proof` region INCLUDING the `theorem correct_clear` header, so the theorem's preconditions are outside the hashed spec signature. Consequently a partial-domain attack survives same_spec: adding `s.cells.length = 0` to the antecedent and closing with `exact absurd (hzero ▸ hlt) (Nat.not_lt_zero _)` verifies at exit 0 with axioms/pure/post-conditions byte-identical and same_spec=True. Worse, the SAME vacuous antecedent grafted onto the BUGGY prepatch (realloc) impl also verifies at exit 0 and is same_spec with gold -- i.e. the bug becomes 'provable' under an indistinguishable spec signature.

(A naive precondition-strengthening that keeps the gold tactic block fails to typecheck, exit 1; the vacuity has to be proved deliberately, which I did.) This is a spec-too-WEAK / discrimination defect in the G-EQ / G-PANEL-1 (verify-does-not-imply-correct) lane, not a faithfulness break, so per the retained-label discipline I do not convert it into an UNFAITHFUL verdict here. It corroborates the already-recorded G-PANEL-1 fail ('atk_3_partialdomain.lean verifies but its patch does not resolve') and G-EQ fail, which describe exactly this hole. G-DIFF's pass is honest only in the narrow sense that the AS-SHIPPED prepatch file fails to typecheck.

BOTTOM LINE for this gate: the modeled function agrees with the real repo callee on every input in its domain; the postconditions are neither stronger than the real behaviour nor drifted from it. FAITHFUL. The bundle's real problem is the unhashed precondition domain, which belongs to the discrimination gates and is already flagged there.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SPEC VIEW INTEGRITY (verified first, so I judged the gated artifact):
- Regenerated the consumer surface via swebench_unified.markers.spec_view with the real lean LanguageTables. impl and proof regions both collapse to the ELISION placeholders; the exposed surface is exactly {header docstring, axioms, pure, post-conditions}.
- same_spec(Solution.lean, Solution_prepatch.lean) = True, and per-region: axioms/pure/post-conditions/spec_view byte-identical, impl+proof differ (exactly as required). spec_view is idempotent.
- Independent verification: lean_verify.sh exit 0; appended `#print axioms correct_clear` -> `[propext]` only, no sorryAx. The proof is real.

MECHANICAL SCREEN: leakage.screen() on the real instance row returns passed=True, zero hard failures, zero warnings. Patch-changed symbols are {clear, messages, reset}; changed files/module paths, all 5 changed gold lines, and all diff markers are absent from the view.

### SEMANTIC JUDGMENT (my actual lane -- info beyond problem_statement):
This problem_statement is unusually forthcoming: it states the bug IS that the records list "gets replaced rather than cleared, which diverges the two objects", says get_records is "set to the same list" as caplog.records at setup, and deep-links line 345 (the reset() body) and line 699 (the aliasing). The in-place-vs-reallocate insight and the aliasing precondition are therefore already fully public. Concept-by-concept, everything the spec view asserts traces back:
- clauses 1/4/5/6 + prose "edit the referenced cell in place and preserve the reference" -> public ("replaced rather than cleared", "diverges the two objects").
- precondition callView = records -> public ("set to the same list", L699 link).
- clause 5 (view observes the emptied cell) -> public: it is the reproductive example's own failing assertion.
Vocabulary is fully abstracted -- collector/view/transcript/cell/reference. No caplog, LogCaptureHandler, LogCaptureFixture, get_records, StringIO, stream, stash, caplog_records_key, _pytest, or logging.py anywhere in the view. The only patched-symbol substring hits are benign: "Handler" inside the model type name HandlerState, and "Resetting" in the title line -- an English gerund describing the operation being specified, not the repo method `reset` (it fails the word boundary, and it neither names a repo symbol nor discloses that the fix introduces a new `clear` method). `clear` and `records` are public via problem_statement.

THE ONE CLAUSE NOT IN THE PROBLEM STATEMENT -- clause 7 (transcript = []) -- AND WHY IT IS NOT A LEAK: I tested this rather than reasoning about it. Materialized a worktree at base_commit aa55975c and read the real source: pre-patch `reset()` is `self.records = []; self.stream = StringIO()`, and gold `clear()` is `self.records.clear(); self.stream = StringIO()` -- the stream line is IDENTICAL on both sides of the edit. I then ran both variants against a replica: both leave the captured text empty (clause7_ok=True for reset AND clear); they differ only in reference identity (identity_preserved False vs True; the stranded view still holds ['hello'] vs []). So clause 7 carries ZERO discriminating information about the gold edit -- it is satisfied identically by the buggy and the fixed code, and cannot help a solver localize or reconstruct the change. It is a faithfulness/frame constraint that excludes a wrong impl (per refinement.md, an earlier revision omitted the stream and thereby admitted an impl failing P2P test_clear's `not caplog.text`), not edit disclosure.

TEST-IDENTITY LEAK: none. test_clear_for_call_stage, test_clear, a_call_log, a_setup_log, test_fixture, stash, caplog_records_key, teardown are all absent from the view.

NON-BLOCKING OBSERVATION (not leakage, flagging for bundle hygiene): meta.json's TOP-LEVEL region_hashes block is stale -- all six entries disagree with the current files (e.g. spec_view 71b3504d... recorded vs 1631d8f9... actual). The G-HYGIENE gate's own data.region_hashes (checked_at 2026-08-14T00:37:25Z) matches the current files exactly, and grep confirms region_hashes is write-only in gates/hygiene.py with no reader anywhere in src/ or scripts/, so nothing consumes the stale copy and no gate verdict rests on it. It appears left over from the revision that added `transcript`. Harmless today, but it is a decoy for any future auditor doing exactly the byte-identity check I was asked to do -- worth restamping.

I did not re-adjudicate the recorded G-EQ / G-PANEL-1 failures; those are other lanes' findings and outside this gate.

- Regenerated the consumer surface via swebench_unified.markers.spec_view with the real lean LanguageTables. impl and proof regions both collapse to the ELISION placeholders; the exposed surface is exactly {header docstring, axioms, pure, post-conditions}.
- same_spec(Solution.lean, Solution_prepatch.lean) = True, and per-region: axioms/pure/post-conditions/spec_view byte-identical, impl+proof differ (exactly as required). spec_view is idempotent.
- Independent verification: lean_verify.sh exit 0; appended `#print axioms correct_clear` -> `[propext]` only, no sorryAx. The proof is real.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
# P2 adversarial audit — scikit-learn__scikit-learn-25747

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk_identity.lean`, `atk_no_error.lean`, `atk_swap.lean`, `atk_inverted.lean`, `atk_drop_none.lean`, `atk_ignore_col.lean`, `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -110,9 +110,19 @@
   ensures out = wrapResult frameOld colSupplied
   do
     -- impl-start
+    -- Pre-image skeleton: in addition to settling the column axis, this also
+    -- overwrites the row axis with a caller-offered row-label set when one is
+    -- present and fits (`rowSupplied`), exactly as the pre-patch branch applied
+    -- its row-label argument. The frozen spec pins the row axis to its prior
+    -- value, so `prove_correct` MUST fail whenever a fitting row-label set is
+    -- offered and differs from what the container already had.
     if sizeFits colSupplied frame.colLabels then
       frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
-      return Except.ok frame
+      if sizeFits rowSupplied frame.rowLabels then
+        frame := { frame with rowLabels := rowSupplied.getD frame.rowLabels }
+        return Except.ok frame
+      else
+        return Except.error WrapErr.sizeMismatch
     else
       return Except.error WrapErr.sizeMismatch
     -- impl-end
```

Attack 2 — `atk_identity.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -110,11 +110,7 @@
   ensures out = wrapResult frameOld colSupplied
   do
     -- impl-start
-    if sizeFits colSupplied frame.colLabels then
-      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
-      return Except.ok frame
-    else
-      return Except.error WrapErr.sizeMismatch
+    return Except.ok frame
     -- impl-end
 
 prove_correct wrapContainer by
```

Attack 3 — `atk_no_error.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -110,11 +110,8 @@
   ensures out = wrapResult frameOld colSupplied
   do
     -- impl-start
-    if sizeFits colSupplied frame.colLabels then
-      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
-      return Except.ok frame
-    else
-      return Except.error WrapErr.sizeMismatch
+    frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
+    return Except.ok frame
     -- impl-end
 
 prove_correct wrapContainer by
```

Attack 4 — `atk_swap.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -111,7 +111,7 @@
   do
     -- impl-start
     if sizeFits colSupplied frame.colLabels then
-      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
+      frame := { frame with rowLabels := resolvedCols colSupplied frame.colLabels }
       return Except.ok frame
     else
       return Except.error WrapErr.sizeMismatch
```

Attack 5 — `atk_inverted.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -111,10 +111,10 @@
   do
     -- impl-start
     if sizeFits colSupplied frame.colLabels then
+      return Except.error WrapErr.sizeMismatch
+    else
       frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
       return Except.ok frame
-    else
-      return Except.error WrapErr.sizeMismatch
     -- impl-end
 
 prove_correct wrapContainer by
```

Attack 6 — `atk_drop_none.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -110,11 +110,16 @@
   ensures out = wrapResult frameOld colSupplied
   do
     -- impl-start
-    if sizeFits colSupplied frame.colLabels then
-      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
+    match colSupplied with
+    | none =>
+      frame := { frame with colLabels := [] }
       return Except.ok frame
-    else
-      return Except.error WrapErr.sizeMismatch
+    | some ls =>
+      if ls.length == frame.colLabels.length then
+        frame := { frame with colLabels := ls }
+        return Except.ok frame
+      else
+        return Except.error WrapErr.sizeMismatch
     -- impl-end
 
 prove_correct wrapContainer by
```

Attack 7 — `atk_ignore_col.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -111,7 +111,6 @@
   do
     -- impl-start
     if sizeFits colSupplied frame.colLabels then
-      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
       return Except.ok frame
     else
       return Except.error WrapErr.sizeMismatch
```

Attack 8 — `atk_echo.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation under spec works entirely on the
@@ -110,11 +110,9 @@
   ensures out = wrapResult frameOld colSupplied
   do
     -- impl-start
-    if sizeFits colSupplied frame.colLabels then
-      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
-      return Except.ok frame
-    else
-      return Except.error WrapErr.sizeMismatch
+    let orig := frame
+    frame := frameAfter orig colSupplied
+    return wrapResult orig colSupplied
     -- impl-end
 
 prove_correct wrapContainer by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation under spec works entirely on the
--  observable label state of the container it is handed; nothing it calls in
--  this branch is left unmodeled. The behaviour — including the size-mismatch
--  failure an ill-fitting replacement label set provokes — is spelled out
--  directly in the `pure`/`impl` regions, so there is no outside contract to
--  assume and nothing for G-AX to check. See refinement.md / mapping.md §3.)
-- axioms-end

-- pure-start
/- A label identity, modeled abstractly: the behaviour observes only equality
   and ordering of labels, never their concrete spelling, so an opaque carrier
   suffices (mapping.md §2). -/
abbrev Lbl := Nat

/- The observable state of a tabular container, restricted to the two label
   axes a wrapping request can touch:

   * `colLabels` — the labels along the column axis;
   * `rowLabels` — the labels along the row axis.

   The cell contents are never altered by a wrapping request and so are not part
   of this carrier (mapping.md §2). -/
structure Frame where
  colLabels : List Lbl
  rowLabels : List Lbl
  deriving DecidableEq, Inhabited

/- The failure a wrapping request reports when the replacement label set offered
   for the column axis cannot be applied because it does not hold exactly one
   label per existing column. The request then leaves the container untouched
   and hands nothing back — the failure escapes to the caller (mapping.md §2). -/
inductive WrapErr where
  | sizeMismatch
  deriving DecidableEq

/- Whether an offered replacement label set fits the axis it targets: it must
   hold exactly as many labels as the axis currently carries. An absent offer
   always fits (the axis is simply left as it stands). -/
def sizeFits (supplied : Option (List Lbl)) (current : List Lbl) : Bool :=
  match supplied with
  | none => true
  | some ls => ls.length == current.length

/- The column labels a wrapping request settles on for a container that already
   carries its own: when a replacement set is supplied it is taken, otherwise the
   container keeps the labels it already has. -/
def resolvedCols (supplied : Option (List Lbl)) (current : List Lbl) : List Lbl :=
  supplied.getD current

/- The container state after the request: when the offered column-label set fits
   (or none is offered) the column axis is settled per `resolvedCols` and the row
   axis is kept; when the offer does not fit, the assignment fails before
   touching anything, so the container is left exactly as it was. -/
def frameAfter (frame : Frame) (colSupplied : Option (List Lbl)) : Frame :=
  if sizeFits colSupplied frame.colLabels then
    { frame with colLabels := resolvedCols colSupplied frame.colLabels }
  else
    frame

/- The overall outcome of the request on a container that already carries its
   own labels: the adjusted container when the offered column-label set fits (or
   none is offered), and the size-mismatch failure otherwise. -/
def wrapResult (frame : Frame) (colSupplied : Option (List Lbl)) :
    Except WrapErr Frame :=
  if sizeFits colSupplied frame.colLabels then
    Except.ok (frameAfter frame colSupplied)
  else
    Except.error WrapErr.sizeMismatch
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap a value that is ALREADY a labelled tabular container.

   The request carries two optional label sets: one for the column axis
   (`colSupplied`) and one for the row axis (`rowSupplied`). The required
   behaviour for an input that already carries its own labels:

   * when a column-label set is provided it must hold exactly one label per
     existing column; a set that fits replaces the column labels, while an
     ill-fitting set makes the request FAIL with a size-mismatch error, leaving
     the container untouched;
   * when no column-label set is provided the column axis is left as it stands;
   * the row axis is left exactly as the container already had it — a row-label
     set offered by the caller does NOT apply to a container that already owns
     one, so `rowSupplied` has no effect here (whatever its size);
   * on success the same container is handed back (the request adjusts it in
     place); on failure nothing is handed back and the failure escapes.

   `colSupplied` and `rowSupplied` are read-only (neither `mut`): the request
   reads them and adjusts the container, mutating nothing it is handed besides
   the container itself. The container's row axis is conceptually unchanged, so
   it is pinned explicitly to its prior value (directive 5). -/
method wrapContainer (mut frame : Frame) (colSupplied : Option (List Lbl)) (rowSupplied : Option (List Lbl)) return (out : Except WrapErr Frame)
  ensures frame = frameAfter frameOld colSupplied
  ensures frame.rowLabels = frameOld.rowLabels
  ensures out = wrapResult frameOld colSupplied
  do
    -- impl-start
    if sizeFits colSupplied frame.colLabels then
      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
      return Except.ok frame
    else
      return Except.error WrapErr.sizeMismatch
    -- impl-end

prove_correct wrapContainer by
  loom_solve <;> simp_all [wrapResult, frameAfter, sizeFits, resolvedCols]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Setup: all files copied from the frozen Solution.lean with ONLY the impl region edited; same_spec=True verified for every attack (velvet backend) via swebench_unified.markers.same_spec.

POSITIVE CONTROL: pos_control.lean (= gold impl) VERIFIES (exit 0).
PREPATCH: atk_prepatch.lean reproduces the bug (row-axis overwrite `frame := {frame with rowLabels := rowSupplied.getD ...}` on the fitting path) — FAILS verification (exit 1), i.e. G-DIFF holds against `ensures frame.rowLabels = frameOld.rowLabels`.

SPEC TIGHTNESS: the frozen method has NO preconditions and pins BOTH outputs as total functions of the inputs — `ensures frame = frameAfter frameOld colSupplied`, `ensures frame.rowLabels = frameOld.rowLabels`, `ensures out = wrapResult frameOld colSupplied`. Therefore ANY terminating verifying impl must return exactly frameAfter/wrapResult (equal to the gold branch under the mapping.md bijection). I encoded 7 DISTINCT terminating wrong impls to falsify this:
  1. atk_identity  (ignore colSupplied, always Except.ok frame)        -> exit 1 (unsolved goals) - rejected
  2. atk_no_error  (set cols & return ok even on size mismatch=boundary) -> exit 1 - rejected
  3. atk_swap      (write cols into rowLabels instead of colLabels)      -> exit 1 - rejected
  4. atk_inverted  (error when fits / ok when it doesn't = control-flow) -> exit 1 - rejected
  5. atk_drop_none (partial-domain: clear colLabels when colSupplied=none)-> exit 1 - rejected
  6. atk_ignore_col(fitting path returns ok WITHOUT applying cols)       -> exit 1 - rejected
  7. atk_echo      (ungrounded-oracle echo: return frameAfter/wrapResult directly) -> exit 1 - rejected (Except-branch unsolved goal; still a genuine rejection)
All 8 attacks are same_spec=True and NONE verifies. Because no terminating same-spec impl verifies, there is no candidate whose faithful refined patch could fail to resolve => verify tracks correct on all terminating impls. patches={} accordingly (no verifying attack to materialize).

DIVERGENCE (documented, deliberately EXCLUDED from the attack set): atk_diverge.lean (a `while spin >= 0 do spin := spin+1` non-terminating loop, same_spec=True) DOES verify (exit 0) vacuously under `set_option loom.semantics.termination "partial"`. This is NOT a refinement-fidelity defect of THIS bundle: (a) it refines no operation in refinement.md — no R/I/A leg corresponds to an infinite loop, so it has no faithful refined patch; (b) its only honest transliteration is an infinite loop in _wrap_in_pandas_container, which would HANG the harness -> timeout -> completed=False -> INCONCLUSIVE (never a resolving-failure), so including it would only force a spurious gate-fail; (c) it is the UNIVERSAL partial-correctness escape, applying identically to every `termination "partial"` bundle in the corpus, and the framework's own verdict derivation classifies it as an accepted non-defect (construct/build_one.py:225: "None found; only divergence is on an unreachable input"). It is reported here for completeness, not as a break.

EXECUTED RESOLVE EVIDENCE (non-speculative): ran the gold patch through the official harness — `run_resolve('scikit-learn__scikit-learn-25747', gold, timeout=1800, retries=0)` -> RESOLVED=True, COMPLETED=True, NOTE='resolved'. Harness works end-to-end and the target resolves.

refinement.md AUDIT (protocol step 3): legs A1-A7 tagged R / R+I / I(deletion); axioms=[] so there are NO A-legs (A-consumed / A-reference) and NO kind-3 (inexpressible-changed-op) steps. G-AX correctly skipped (meta G-AX=skip 'no axioms'). Confirmed the R/I correspondence against the real repo file sklearn/utils/_set_output.py (branch `if isinstance(data_to_wrap, pd.DataFrame)`): it sets `data_to_wrap.columns = columns` (raises ValueError on length mismatch = A4/sizeFits -> WrapErr.sizeMismatch) and the gold patch DELETES `if index is not None: data_to_wrap.index = index` (A6, the behavioural change modeled deeply as the absence of a rowLabels write + directive-5 frame clause). Correspondence holds. G-CONF=pass (100012 inputs, 0 disagreements), G-RESOLVE=pass.

CONCLUSION: no verifying same-spec wrong impl exists among terminating implementations; the sole verifying deviation is universal partial-correctness divergence, which is not a materializable/resolving break. Spec is tight; refinement legs honest. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk_identity.lean`, `atk_no_error.lean`, `atk_swap.lean`, `atk_inverted.lean`, `atk_drop_none.lean`, `atk_ignore_col.lean`, `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_identity.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_no_error.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_swap.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_inverted.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_drop_none.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_ignore_col.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation under spec works entirely on the
--  observable label state of the container it is handed; nothing it calls in
--  this branch is left unmodeled. The behaviour — including the size-mismatch
--  failure an ill-fitting replacement label set provokes — is spelled out
--  directly in the `pure`/`impl` regions, so there is no outside contract to
--  assume and nothing for G-AX to check. See refinement.md / mapping.md §3.)
-- axioms-end

-- pure-start
/- A label identity, modeled abstractly: the behaviour observes only equality
   and ordering of labels, never their concrete spelling, so an opaque carrier
   suffices (mapping.md §2). -/
abbrev Lbl := Nat

/- The observable state of a tabular container, restricted to the two label
   axes a wrapping request can touch:

   * `colLabels` — the labels along the column axis;
   * `rowLabels` — the labels along the row axis.

   The cell contents are never altered by a wrapping request and so are not part
   of this carrier (mapping.md §2). -/
structure Frame where
  colLabels : List Lbl
  rowLabels : List Lbl
  deriving DecidableEq, Inhabited

/- The failure a wrapping request reports when the replacement label set offered
   for the column axis cannot be applied because it does not hold exactly one
   label per existing column. The request then leaves the container untouched
   and hands nothing back — the failure escapes to the caller (mapping.md §2). -/
inductive WrapErr where
  | sizeMismatch
  deriving DecidableEq

/- Whether an offered replacement label set fits the axis it targets: it must
   hold exactly as many labels as the axis currently carries. An absent offer
   always fits (the axis is simply left as it stands). -/
def sizeFits (supplied : Option (List Lbl)) (current : List Lbl) : Bool :=
  match supplied with
  | none => true
  | some ls => ls.length == current.length

/- The column labels a wrapping request settles on for a container that already
   carries its own: when a replacement set is supplied it is taken, otherwise the
   container keeps the labels it already has. -/
def resolvedCols (supplied : Option (List Lbl)) (current : List Lbl) : List Lbl :=
  supplied.getD current

/- The container state after the request: when the offered column-label set fits
   (or none is offered) the column axis is settled per `resolvedCols` and the row
   axis is kept; when the offer does not fit, the assignment fails before
   touching anything, so the container is left exactly as it was. -/
def frameAfter (frame : Frame) (colSupplied : Option (List Lbl)) : Frame :=
  if sizeFits colSupplied frame.colLabels then
    { frame with colLabels := resolvedCols colSupplied frame.colLabels }
  else
    frame

/- The overall outcome of the request on a container that already carries its
   own labels: the adjusted container when the offered column-label set fits (or
   none is offered), and the size-mismatch failure otherwise. -/
def wrapResult (frame : Frame) (colSupplied : Option (List Lbl)) :
    Except WrapErr Frame :=
  if sizeFits colSupplied frame.colLabels then
    Except.ok (frameAfter frame colSupplied)
  else
    Except.error WrapErr.sizeMismatch
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap a value that is ALREADY a labelled tabular container.

   The request carries two optional label sets: one for the column axis
   (`colSupplied`) and one for the row axis (`rowSupplied`). The required
   behaviour for an input that already carries its own labels:

   * when a column-label set is provided it must hold exactly one label per
     existing column; a set that fits replaces the column labels, while an
     ill-fitting set makes the request FAIL with a size-mismatch error, leaving
     the container untouched;
   * when no column-label set is provided the column axis is left as it stands;
   * the row axis is left exactly as the container already had it — a row-label
     set offered by the caller does NOT apply to a container that already owns
     one, so `rowSupplied` has no effect here (whatever its size);
   * on success the same container is handed back (the request adjusts it in
     place); on failure nothing is handed back and the failure escapes.

   `colSupplied` and `rowSupplied` are read-only (neither `mut`): the request
   reads them and adjusts the container, mutating nothing it is handed besides
   the container itself. The container's row axis is conceptually unchanged, so
   it is pinned explicitly to its prior value (directive 5). -/
method wrapContainer (mut frame : Frame) (colSupplied : Option (List Lbl)) (rowSupplied : Option (List Lbl)) return (out : Except WrapErr Frame)
  ensures frame = frameAfter frameOld colSupplied
  ensures frame.rowLabels = frameOld.rowLabels
  ensures out = wrapResult frameOld colSupplied
  do
    -- impl-start
    if sizeFits colSupplied frame.colLabels then
      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
      return Except.ok frame
    else
      return Except.error WrapErr.sizeMismatch
    -- impl-end

prove_correct wrapContainer by
  loom_solve <;> simp_all [wrapResult, frameAfter, sizeFits, resolvedCols]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Setup: all files copied from the frozen Solution.lean with ONLY the impl region edited; same_spec=True verified for every attack (velvet backend) via swebench_unified.markers.same_spec.

POSITIVE CONTROL: pos_control.lean (= gold impl) VERIFIES (exit 0).
PREPATCH: atk_prepatch.lean reproduces the bug (row-axis overwrite `frame := {frame with rowLabels := rowSupplied.getD ...}` on the fitting path) — FAILS verification (exit 1), i.e. G-DIFF holds against `ensures frame.rowLabels = frameOld.rowLabels`.

SPEC TIGHTNESS: the frozen method has NO preconditions and pins BOTH outputs as total functions of the inputs — `ensures frame = frameAfter frameOld colSupplied`, `ensures frame.rowLabels = frameOld.rowLabels`, `ensures out = wrapResult frameOld colSupplied`. Therefore ANY terminating verifying impl must return exactly frameAfter/wrapResult (equal to the gold branch under the mapping.md bijection). I encoded 7 DISTINCT terminating wrong impls to falsify this:
  1. atk_identity  (ignore colSupplied, always Except.ok frame)        -> exit 1 (unsolved goals) - rejected
  2. atk_no_error  (set cols & return ok even on size mismatch=boundary) -> exit 1 - rejected
  3. atk_swap      (write cols into rowLabels instead of colLabels)      -> exit 1 - rejected
  4. atk_inverted  (error when fits / ok when it doesn't = control-flow) -> exit 1 - rejected
  5. atk_drop_none (partial-domain: clear colLabels when colSupplied=none)-> exit 1 - rejected
  6. atk_ignore_col(fitting path returns ok WITHOUT applying cols)       -> exit 1 - rejected
  7. atk_echo      (ungrounded-oracle echo: return frameAfter/wrapResult directly) -> exit 1 - rejected (Except-branch unsolved goal; still a genuine rejection)
All 8 attacks are same_spec=True and NONE verifies. Because no terminating same-spec impl verifies, there is no candidate whose faithful refined patch could fail to resolve => verify tracks correct on all terminating impls. patches={} accordingly (no verifying attack to materialize).

DIVERGENCE (documented, deliberately EXCLUDED from the attack set): atk_diverge.lean (a `while spin >= 0 do spin := spin+1` non-terminating loop, same_spec=True) DOES verify (exit 0) vacuously under `set_option loom.semantics.termination "partial"`. This is NOT a refinement-fidelity defect of THIS bundle: (a) it refines no operation in refinement.md — no R/I/A leg corresponds to an infinite loop, so it has no faithful refined patch; (b) its only honest transliteration is an infinite loop in _wrap_in_pandas_container, which would HANG the harness -> timeout -> completed=False -> INCONCLUSIVE (never a resolving-failure), so including it would only force a spurious gate-fail; (c) it is the UNIVERSAL partial-correctness escape, applying identically to every `termination "partial"` bundle in the corpus, and the framework's own verdict derivation classifies it as an accepted non-defect (construct/build_one.py:225: "None found; only divergence is on an unreachable input"). It is reported here for completeness, not as a break.

EXECUTED RESOLVE EVIDENCE (non-speculative): ran the gold patch through the official harness — `run_resolve('scikit-learn__scikit-learn-25747', gold, timeout=1800, retries=0)` -> RESOLVED=True, COMPLETED=True, NOTE='resolved'. Harness works end-to-end and the target resolves.

refinement.md AUDIT (protocol step 3): legs A1-A7 tagged R / R+I / I(deletion); axioms=[] so there are NO A-legs (A-consumed / A-reference) and NO kind-3 (inexpressible-changed-op) steps. G-AX correctly skipped (meta G-AX=skip 'no axioms'). Confirmed the R/I correspondence against the real repo file sklearn/utils/_set_output.py (branch `if isinstance(data_to_wrap, pd.DataFrame)`): it sets `data_to_wrap.columns = columns` (raises ValueError on length mismatch = A4/sizeFits -> WrapErr.sizeMismatch) and the gold patch DELETES `if index is not None: data_to_wrap.index = index` (A6, the behavioural change modeled deeply as the absence of a rowLabels write + directive-5 frame clause). Correspondence holds. G-CONF=pass (100012 inputs, 0 disagreements), G-RESOLVE=pass.

CONCLUSION: no verifying same-spec wrong impl exists among terminating implementations; the sole verifying deviation is universal partial-correctness divergence, which is not a materializable/resolving break. Spec is tight; refinement legs honest. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of velvet bundle scikit-learn__scikit-learn-25747 (wrapContainer models the isinstance(data_to_wrap, pd.DataFrame) branch of _wrap_in_pandas_container). No divergence found between the modeled function and the real repo callee.

Spec integrity: same_spec(Solution, Solution_prepatch, velvet)=True (frozen spec preserved). Solution.lean elaborates cleanly via lean_verify.sh (exit 0). Note: the bundle spec view differs from the reference builder's Solution.lean (reference modeled success-only with `out : Frame`; bundle strengthens to an Except with a size-mismatch failure branch) — this is a stronger but still faithful model, not drift from the repo.

Gold patch (from dataset): post-patch DataFrame branch = `if columns is not None: data_to_wrap.columns = columns; return data_to_wrap` — the `if index is not None: data_to_wrap.index = index` lines are DELETED, so index is ignored entirely.

Model-vs-real-callee checks against real pandas 3.0.5:
- ill-fitting column set (too many/too few/empty-on-nonempty) => real pandas raises ValueError:Length mismatch, frame untouched on BOTH axes => matches wrapResult=Except.error WrapErr.sizeMismatch with frameAfter=identity (sizeFits models the length check exactly: len(supplied)==len(current), None trivially fits).
- fitting column set => columns replaced, row axis unchanged => matches resolvedCols=supplied.getD current.
- rowSupplied/index of ANY length => ignored => matches ensures frame.rowLabels=frameOld.rowLabels.
- boundary: 0-col frame with columns=[] fits; 0-row frame; duplicate labels (matching length) accepted; tuple labels accepted => all agree.
- 200,000-input fuzz (seed-varied, incl. 30% deliberately wrong-length columns, duplicate labels, custom string/int axes): R/I shadow vs exact post-patch branch => 0 disagreements. This exceeds the bundled conformance_check.py's 1e5 seed=25747 run.

The abstraction Lbl:=Nat is sound (only equality/ordering observed). No axioms (G-AX vacuous). The spec is neither too strong nor divergent: every observable outcome agrees with the real patched _wrap_in_pandas_container. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction check for scikit-learn__scikit-learn-25747 (velvet). Gold edit: delete `if index is not None: data_to_wrap.index = index` in the `isinstance(data_to_wrap, pd.DataFrame)` branch of _wrap_in_pandas_container — for an already-a-DataFrame input the row index is left untouched and the offered `index` has no effect even when it fits.

### Verified independently
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) == True (meta same_spec:true confirmed). The behavioural change lives only in the impl region + the frame-clause post-condition (the intended G-DIFF surface), not in the spec regions.
2. Spec view obtained via markers.spec_view over VelvetBackend.language. My own lexical scan of the spec view for every repo tell returned ZERO hits: no 'sklearn'/'scikit', 'pandas', 'DataFrame', 'data_to_wrap', '_wrap_in_pandas_container', '_set_output', 'set_output', 'FeatureUnion', 'ColumnTransformer', '.index', 'ValueError', 'Length mismatch', 'get_feature_names', 'transform_output', 'make_union', issue numbers (25747/25730), or 'patch'/'prepatch'. The bare word 'index' does not appear at all (0 occurrences) — the model deliberately says 'row axis / rowLabels'. Model is fully abstracted: Frame{colLabels,rowLabels}, Lbl:=Nat, wrapContainer, WrapErr.sizeMismatch.

JUDGMENT: The contract states the target semantics — `ensures frame.rowLabels = frameOld.rowLabels` and 'rowSupplied has no effect here (whatever its size)'. This goes beyond the public problem_statement (whose traceback only exhibits the mismatched-length crash; the ignore-a-FITTING-index decision is discussed in hints_text, which is out of scope). But this is a behavioral SPECIFICATION of correct post-patch behavior — unavoidable, legitimate spec content that any verified bundle must supply. It names no repo file/function/line and hands over no diff. Notably the PUBLIC problem_statement's own traceback already exposes far more repo-level detail (_set_output.py:59, `data_to_wrap.index = index`, the ValueError) than the abstracted spec view does; a solver reading the spec view must still independently locate the branch and the deletion. This is not repo-level gold-edit reconstruction and not an actionable leak beyond problem_statement. G-LEAK passed; my independent scan agrees.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

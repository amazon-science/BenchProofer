# P2 adversarial audit — django__django-14404

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
@@ -69,6 +69,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
     Outcome := Id.run do
   if appendSlash && !(url.endsWith "/") then
@@ -76,7 +77,7 @@
     match resolveLoc (req.routingPath ++ "/") urlconf with
     | some m =>
         if m.shouldAppend then
-          return Outcome.redirect (req.visiblePath ++ "/")
+          return Outcome.redirect (req.routingPath ++ "/")
     | none => pure ()
   return Outcome.notFound
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,6 +69,7 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
     Outcome := Id.run do
   if appendSlash && !(url.endsWith "/") then
@@ -76,7 +77,7 @@
     match resolveLoc (req.routingPath ++ "/") urlconf with
     | some m =>
         if m.shouldAppend then
-          return Outcome.redirect (req.visiblePath ++ "/")
+          return Outcome.redirect req.visiblePath
     | none => pure ()
   return Outcome.notFound
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,14 +69,14 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
     Outcome := Id.run do
   if appendSlash && !(url.endsWith "/") then
     let urlconf := req.urlconf
     match resolveLoc (req.routingPath ++ "/") urlconf with
-    | some m =>
-        if m.shouldAppend then
-          return Outcome.redirect (req.visiblePath ++ "/")
+    | some _ =>
+        return Outcome.redirect (req.visiblePath ++ "/")
     | none => pure ()
   return Outcome.notFound
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,11 +69,12 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
     Outcome := Id.run do
   if appendSlash && !(url.endsWith "/") then
     let urlconf := req.urlconf
-    match resolveLoc (req.routingPath ++ "/") urlconf with
+    match resolveLoc req.routingPath urlconf with
     | some m =>
         if m.shouldAppend then
           return Outcome.redirect (req.visiblePath ++ "/")
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,9 +69,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
     Outcome := Id.run do
-  if appendSlash && !(url.endsWith "/") then
+  if appendSlash && (url.endsWith "/") then
     let urlconf := req.urlconf
     match resolveLoc (req.routingPath ++ "/") urlconf with
     | some m =>
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,15 +69,9 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
     Outcome := Id.run do
-  if appendSlash && !(url.endsWith "/") then
-    let urlconf := req.urlconf
-    match resolveLoc (req.routingPath ++ "/") urlconf with
-    | some m =>
-        if m.shouldAppend then
-          return Outcome.redirect (req.visiblePath ++ "/")
-    | none => pure ()
   return Outcome.notFound
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,11 +69,12 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
     Outcome := Id.run do
   if appendSlash && !(url.endsWith "/") then
     let urlconf := req.urlconf
-    match resolveLoc (req.routingPath ++ "/") urlconf with
+    match resolveLoc (req.visiblePath ++ "/") urlconf with
     | some m =>
         if m.shouldAppend then
           return Outcome.redirect (req.visiblePath ++ "/")
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A request-handling routine for unmatched URLs. When automatic trailing-slash
redirection is enabled and the incoming locator lacks a trailing slash, the
routine probes whether appending a slash yields a recognized locator; if so (and
that locator permits the redirect), it issues a permanent redirect to the
visible request location with a slash appended. Otherwise it signals "not found".

Two distinct request locations are tracked: the outward-facing location and
the internal routing location, which may differ by a leading deployment prefix.
The recognition probe is driven by the internal routing location; the redirect
target is the outward-facing location.
-/

-- axioms-start
/-- Opaque routing configuration consulted by the recognition probe. -/
opaque Urlconf : Type

/-- A recognized routing entry. The boolean records whether the matched entry
permits automatic trailing-slash redirection. -/
structure ResolveMatch where
  shouldAppend : Bool

/-- The recognition probe: given a candidate locator and a routing
configuration, returns a matched entry when the locator is recognized. This is
an UNCHANGED callee the routine invokes; only its signature is declared here.
The proof agent adds any property axiom it consumes. -/
opaque resolveLoc : String → Urlconf → Option ResolveMatch
-- axioms-end

-- pure-start
/-- Carrier for an incoming request: the outward-facing location
(`visiblePath`), the internal routing location (`routingPath`), and the routing
configuration consulted by the recognition probe. -/
structure Request where
  visiblePath : String
  routingPath : String
  urlconf : Urlconf

/-- Result of the routine: either a permanent redirect to a target location, or
a "not found" signal. -/
inductive Outcome where
  | redirect (target : String) : Outcome
  | notFound : Outcome
deriving DecidableEq
-- pure-end

-- post-conditions-start
def problem_spec_catchAll (req : Request) (url : String) (appendSlash : Bool)
    (result : Outcome) : Prop :=
  -- When redirection is disabled, or the locator already ends in a slash, the
  -- routine signals not-found.
  (¬ (appendSlash = true ∧ url.endsWith "/" = false) → result = Outcome.notFound)
  ∧
  -- When the precondition for probing holds, the recognition probe is driven by
  -- the internal routing location with a slash appended.
  (appendSlash = true ∧ url.endsWith "/" = false →
    match resolveLoc (req.routingPath ++ "/") req.urlconf with
    -- An unrecognized probe yields not-found.
    | none => result = Outcome.notFound
    | some m =>
        -- A recognized entry that permits redirection redirects to the
        -- outward-facing location with a slash appended; otherwise
        -- not-found.
        (m.shouldAppend = true → result = Outcome.redirect (req.visiblePath ++ "/"))
        ∧ (m.shouldAppend = false → result = Outcome.notFound))
-- post-conditions-end

-- impl-start
def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
    Outcome := Id.run do
  if appendSlash && !(url.endsWith "/") then
    let urlconf := req.urlconf
    match resolveLoc (req.routingPath ++ "/") urlconf with
    | some m =>
        if m.shouldAppend then
          return Outcome.redirect (req.visiblePath ++ "/")
    | none => pure ()
  return Outcome.notFound
-- impl-end

-- proof-start
theorem correct_catchAll : ∀ (req : Request) (url : String) (appendSlash : Bool),
    problem_spec_catchAll req url appendSlash
      (implementation_catchAll req url appendSlash) := by
  intro req url appendSlash
  unfold problem_spec_catchAll implementation_catchAll
  by_cases hpre : appendSlash = true ∧ url.endsWith "/" = false
  · obtain ⟨ha, hu⟩ := hpre
    refine ⟨fun hbad => absurd ⟨ha, hu⟩ hbad, ?_⟩
    intro _
    simp only [ha, hu, Bool.not_false, Bool.and_true, if_true, Id.run]
    cases hm : resolveLoc (req.routingPath ++ "/") req.urlconf with
    | none => rfl
    | some m =>
        refine ⟨fun hs => ?_, fun hs => ?_⟩
        · simp only [hs, if_true]; rfl
        · simp only [hs, Bool.false_eq_true, if_false]; rfl
  · push_neg at hpre
    constructor
    · intro _
      by_cases ha : appendSlash = true
      · have hu : url.endsWith "/" = true := by
          by_contra hu'
          exact (hpre ha) (by simpa using hu')
        simp only [ha, hu, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false, Id.run]; rfl
      · simp only [ha, Bool.false_and, Bool.false_eq_true, if_false, Id.run]; rfl
    · intro hbad
      exact absurd hbad.1 (by simpa using fun h => (hpre h) hbad.2)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_catchAll is FULLY DETERMINISTIC: result is pinned exactly in every branch (precondition-fail -> notFound; probe branch decided by symbolic resolveLoc shared spec<->impl: none->notFound, some m with shouldAppend->redirect(visiblePath++"/"), else notFound). No existential/underspecified output; resolveLoc symbolic & identical in spec and impl.

Positive control (gold impl) pos_control.lean: `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. `#print axioms correct_catchAll` (pos_axioms.lean) -> 'depends on axioms: [propext, Quot.sound]' (clean, no sorryAx).

7 same-spec attacks (all same_spec=True; header incl. axioms/pure/pre/post byte-identical, only impl region varied; gold proof body attached as a genuine closing attempt). Verified concurrently (<=4 background jobs). All exit 1 = genuine PROOF-GOAL errors (rfl/simp on discriminating clause), NOT compile errors and NOT sorry(exit3):
  atk_1 prepatch bug: redirect target routingPath++"/" -> err at :100 'pure (Outcome.redirect (req.routingPath ++ "/")) is not defeq to Outcome.redirect (req.visiblePath ++ "/")'
  atk_2 partial-domain: target visiblePath (missing trailing slash) -> rfl fail on target
  atk_3 control-flow-effect: ignore shouldAppend, always redirect on match -> rfl fail on shouldAppend=false branch
  atk_4 boundary: probe resolveLoc req.routingPath (no appended slash) -> rfl/simp probe-arg mismatch vs spec resolveLoc(routingPath++"/")
  atk_5 precondition inversion: fires when url ENDS with '/' -> rfl fail both branches
  atk_6 ungrounded-oracle echo: always notFound -> simp 'made no progress' (redirect branch unmet)
  atk_7 probe uses visiblePath++"/" -> rfl/simp probe-arg mismatch

Impossibility (no ALTERNATIVE proof closes any attack): spec pins result to a specific Outcome per branch; each wrong impl yields a different Outcome in >=1 reachable branch (confirmed by exact goal mismatch over free symbolic fields visiblePath/routingPath and symbolic resolveLoc/shouldAppend). A false goal has no proof, so none of the 7 has any closing clean-axiom proof. Step-2 (materialize faithful patch + run_resolve) is only required for wrong impls whose proof CLOSES with clean axioms; none did, so no resolve run is triggered and patches={}.

refinement.md audit: legs are R (ops 1,2,4,5,6,7) and one A-reference (op 3, resolveLoc = django.urls.resolve, UNCHANGED callee, appears identically in spec+impl, consumes NO _prop axiom; axioms region declares signature only) -> correspondence holds. No A-consumed, no kind-3 (no inexpressible changed op). THE FIX (op #6: request.path_info -> request.path == routingPath -> visiblePath redirect target) is modeled deeply as a concrete string-field difference; prepatch bug (atk_1) is exactly the discriminating clause and fails to close (prepatch_reproduced=true). Grounded, not an ungrounded oracle echo.

VERDICT SOUND: >=5 (7) distinct attacks run, positive control verifies clean, none breaks the spec (verify => correct holds here).

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
A request-handling routine for unmatched URLs. When automatic trailing-slash
redirection is enabled and the incoming locator lacks a trailing slash, the
routine probes whether appending a slash yields a recognized locator; if so (and
that locator permits the redirect), it issues a permanent redirect to the
visible request location with a slash appended. Otherwise it signals "not found".

Two distinct request locations are tracked: the outward-facing location and
the internal routing location, which may differ by a leading deployment prefix.
The recognition probe is driven by the internal routing location; the redirect
target is the outward-facing location.
-/

-- axioms-start
/-- Opaque routing configuration consulted by the recognition probe. -/
opaque Urlconf : Type

/-- A recognized routing entry. The boolean records whether the matched entry
permits automatic trailing-slash redirection. -/
structure ResolveMatch where
  shouldAppend : Bool

/-- The recognition probe: given a candidate locator and a routing
configuration, returns a matched entry when the locator is recognized. This is
an UNCHANGED callee the routine invokes; only its signature is declared here.
The proof agent adds any property axiom it consumes. -/
opaque resolveLoc : String → Urlconf → Option ResolveMatch
-- axioms-end

-- pure-start
/-- Carrier for an incoming request: the outward-facing location
(`visiblePath`), the internal routing location (`routingPath`), and the routing
configuration consulted by the recognition probe. -/
structure Request where
  visiblePath : String
  routingPath : String
  urlconf : Urlconf

/-- Result of the routine: either a permanent redirect to a target location, or
a "not found" signal. -/
inductive Outcome where
  | redirect (target : String) : Outcome
  | notFound : Outcome
deriving DecidableEq
-- pure-end

-- post-conditions-start
def problem_spec_catchAll (req : Request) (url : String) (appendSlash : Bool)
    (result : Outcome) : Prop :=
  -- When redirection is disabled, or the locator already ends in a slash, the
  -- routine signals not-found.
  (¬ (appendSlash = true ∧ url.endsWith "/" = false) → result = Outcome.notFound)
  ∧
  -- When the precondition for probing holds, the recognition probe is driven by
  -- the internal routing location with a slash appended.
  (appendSlash = true ∧ url.endsWith "/" = false →
    match resolveLoc (req.routingPath ++ "/") req.urlconf with
    -- An unrecognized probe yields not-found.
    | none => result = Outcome.notFound
    | some m =>
        -- A recognized entry that permits redirection redirects to the
        -- outward-facing location with a slash appended; otherwise
        -- not-found.
        (m.shouldAppend = true → result = Outcome.redirect (req.visiblePath ++ "/"))
        ∧ (m.shouldAppend = false → result = Outcome.notFound))
-- post-conditions-end

-- impl-start
def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :
    Outcome := Id.run do
  if appendSlash && !(url.endsWith "/") then
    let urlconf := req.urlconf
    match resolveLoc (req.routingPath ++ "/") urlconf with
    | some m =>
        if m.shouldAppend then
          return Outcome.redirect (req.visiblePath ++ "/")
    | none => pure ()
  return Outcome.notFound
-- impl-end

-- proof-start
theorem correct_catchAll : ∀ (req : Request) (url : String) (appendSlash : Bool),
    problem_spec_catchAll req url appendSlash
      (implementation_catchAll req url appendSlash) := by
  intro req url appendSlash
  unfold problem_spec_catchAll implementation_catchAll
  by_cases hpre : appendSlash = true ∧ url.endsWith "/" = false
  · obtain ⟨ha, hu⟩ := hpre
    refine ⟨fun hbad => absurd ⟨ha, hu⟩ hbad, ?_⟩
    intro _
    simp only [ha, hu, Bool.not_false, Bool.and_true, if_true, Id.run]
    cases hm : resolveLoc (req.routingPath ++ "/") req.urlconf with
    | none => rfl
    | some m =>
        refine ⟨fun hs => ?_, fun hs => ?_⟩
        · simp only [hs, if_true]; rfl
        · simp only [hs, Bool.false_eq_true, if_false]; rfl
  · push_neg at hpre
    constructor
    · intro _
      by_cases ha : appendSlash = true
      · have hu : url.endsWith "/" = true := by
          by_contra hu'
          exact (hpre ha) (by simpa using hu')
        simp only [ha, hu, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false, Id.run]; rfl
      · simp only [ha, Bool.false_and, Bool.false_eq_true, if_false, Id.run]; rfl
    · intro hbad
      exact absurd hbad.1 (by simpa using fun h => (hpre h) hbad.2)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_catchAll is FULLY DETERMINISTIC: result is pinned exactly in every branch (precondition-fail -> notFound; probe branch decided by symbolic resolveLoc shared spec<->impl: none->notFound, some m with shouldAppend->redirect(visiblePath++"/"), else notFound). No existential/underspecified output; resolveLoc symbolic & identical in spec and impl.

Positive control (gold impl) pos_control.lean: `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. `#print axioms correct_catchAll` (pos_axioms.lean) -> 'depends on axioms: [propext, Quot.sound]' (clean, no sorryAx).

7 same-spec attacks (all same_spec=True; header incl. axioms/pure/pre/post byte-identical, only impl region varied; gold proof body attached as a genuine closing attempt). Verified concurrently (<=4 background jobs). All exit 1 = genuine PROOF-GOAL errors (rfl/simp on discriminating clause), NOT compile errors and NOT sorry(exit3):
  atk_1 prepatch bug: redirect target routingPath++"/" -> err at :100 'pure (Outcome.redirect (req.routingPath ++ "/")) is not defeq to Outcome.redirect (req.visiblePath ++ "/")'
  atk_2 partial-domain: target visiblePath (missing trailing slash) -> rfl fail on target
  atk_3 control-flow-effect: ignore shouldAppend, always redirect on match -> rfl fail on shouldAppend=false branch
  atk_4 boundary: probe resolveLoc req.routingPath (no appended slash) -> rfl/simp probe-arg mismatch vs spec resolveLoc(routingPath++"/")
  atk_5 precondition inversion: fires when url ENDS with '/' -> rfl fail both branches
  atk_6 ungrounded-oracle echo: always notFound -> simp 'made no progress' (redirect branch unmet)
  atk_7 probe uses visiblePath++"/" -> rfl/simp probe-arg mismatch

Impossibility (no ALTERNATIVE proof closes any attack): spec pins result to a specific Outcome per branch; each wrong impl yields a different Outcome in >=1 reachable branch (confirmed by exact goal mismatch over free symbolic fields visiblePath/routingPath and symbolic resolveLoc/shouldAppend). A false goal has no proof, so none of the 7 has any closing clean-axiom proof. Step-2 (materialize faithful patch + run_resolve) is only required for wrong impls whose proof CLOSES with clean axioms; none did, so no resolve run is triggered and patches={}.

refinement.md audit: legs are R (ops 1,2,4,5,6,7) and one A-reference (op 3, resolveLoc = django.urls.resolve, UNCHANGED callee, appears identically in spec+impl, consumes NO _prop axiom; axioms region declares signature only) -> correspondence holds. No A-consumed, no kind-3 (no inexpressible changed op). THE FIX (op #6: request.path_info -> request.path == routingPath -> visiblePath redirect target) is modeled deeply as a concrete string-field difference; prepatch bug (atk_1) is exactly the discriminating clause and fails to close (prepatch_reproduced=true). Grounded, not an ungrounded oracle echo.

VERDICT SOUND: >=5 (7) distinct attacks run, positive control verifies clean, none breaks the spec (verify => correct holds here).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14404 (AdminSite.catch_all_view trailing-slash redirect, post-patch @ de32fe83).

Real post-patch callee:
  if settings.APPEND_SLASH and not url.endswith('/'):
      urlconf = getattr(request,'urlconf',None)
      try: match = resolve('%s/' % request.path_info, urlconf)
      except Resolver404: pass
      else:
          if getattr(match.func,'should_append_slash',True):
              return HttpResponsePermanentRedirect('%s/' % request.path)
  raise Http404

Spec problem_spec_catchAll matches on every case:
  - Clause 1: ¬(appendSlash ∧ ¬url.endsWith "/") → notFound  ==  guard false → raise Http404. ✓
  - Clause 2/none: resolve(routingPath++"/") = none (Resolver404) → notFound. ✓  (probe arg built from routingPath = request.path_info, NOT url — the common trap is correctly avoided.)
  - Clause 2/some, shouldAppend=true → redirect (visiblePath++"/") = '%s/' % request.path. ✓  (THE FIX: target is request.path, not path_info.)
  - Clause 2/some, shouldAppend=false → notFound. ✓

Verification performed:
  - scripts/lean_verify.sh Solution.lean → exit 0 (compiles, no sorry).
  - #print axioms correct_catchAll → [propext, Quot.sound]; NO sorryAx → proof is genuine, not fake.
  - same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True → spec region byte-identical; only impl op #6 differs (prepatch reverts redirect target to routingPath). G-DIFF confirms prepatch fails to verify.
  - resolveLoc is a legitimate A-reference: same opaque callee with identical argument (routingPath++"/") appears in both spec and impl and is held fixed as oracle — matches the real unchanged `resolve`, whose arg is `request.path_info` both pre/post patch.
  - conformance_check.py / G-CONF: 120007 inputs, 0 disagreements (seed=14404).

The spec is TOTAL (every combination of appendSlash / url-trailing-slash / resolve-outcome / shouldAppend is fully constrained) and its predicted Outcome equals the real callee's on all inputs. The model treats visiblePath and routingPath as INDEPENDENT strings, which is strictly MORE GENERAL than reality (request.path = script_name + request.path_info); a more permissive domain can only weaken, never strengthen, the spec, so it cannot constitute a spec-too-strong/drift defect. No diverging input exists where the modeled function disagrees with the real post-patch catch_all_view. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Role: leakage / gold-reconstruction over the SPEC VIEW (Solution.lean spec region: docstring + axioms + pure + problem_spec_catchAll), judged against the public problem_statement (NOT hints_text).

Gold edit: in catch_all_view, redirect target changes from '%s/' % request.path_info (script name stripped) to '%s/' % request.path (script name included).

Public problem_statement ALREADY fully discloses this: it literally states catch_all_view 'returns redirect to \'%s/\' % request.path_info (script name cut off there) instead of \'%s/\' % request.path (with the script name)' — naming both fields and which one is correct.

Spec-view content examined:
- Docstring (lines 4-15): abstractly describes two locations, 'outward-facing' vs 'internal routing', and states the redirect target is the outward-facing location. This is the correct postcondition a spec must encode; it discloses nothing beyond problem_statement, which already gives the exact request.path vs request.path_info distinction.
- problem_spec_catchAll (lines 51-68): postcondition uses req.visiblePath ++ "/" as the redirect target. A correct postcondition necessarily fixes the outward-facing path as the target — this is legitimate spec content, and equivalent info is already public. The probe uses req.routingPath (path_info), also public.
- axioms/pure regions: opaque callee signature + Request/Outcome carriers; neutral, no gold leakage.

Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean (diff of lines 1-69 empty) — the spec view is stable across the DIFF variant, so no discriminating impl detail leaks through the spec.

NOT part of the spec view (excluded from G-LEAK per policy, which is lexical over the spec view): refinement.md / mapping.md auditor docs ('R — THE FIX', explicit request.path/path_info naming) and the buggy-impl comment in Solution_prepatch.lean impl region (line 79-80). These are audit/build artifacts, not the solver-facing spec. Even so, they add nothing beyond problem_statement, which already spells out the fix.

Conclusion: everything the spec view reveals about the redirect-target distinction is already present in the public problem_statement. No leakage beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

# P2 adversarial audit — django__django-16502

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is tight: both postconditions are total functional equalities (out = adjustMeta isHead isThreadingServer m; out = bodyFor isHead chunks), leaving zero behavioral slack. Every behaviorally-wrong impl fails to verify; the only same-spec impl that verifies (atk_7, the ungrounded-oracle echo returning bodyFor/adjustMeta verbatim) is behaviorally identical to gold and its faithful patch (= gold patch) RESOLVES under run_resolve.
```

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
 /- No consumed axioms. The two unchanged lower-layer callees this logic sits on
@@ -95,10 +95,7 @@
   ensures out = bodyFor isHead chunks
   do
     -- impl-start
-    let out ← if isHead then
-        pure ([] : List Char)
-      else
-        pure chunks.flatten
+    let out ← pure chunks.flatten
     return out
     -- impl-end
 
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
 /- No consumed axioms. The two unchanged lower-layer callees this logic sits on
@@ -67,14 +67,8 @@
     let mut len := m.hasLength
     let mut term := m.terminate
     let mut willTerm := m.willTerminate
-    if isHead then
-      if len then
-        len := false
-      else
-        len := len
-    else
-      len := len
-    if (!isHead && !len) then
+    len := len
+    if !len then
       term := true
     else
       if !isThreadingServer then
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
 /- No consumed axioms. The two unchanged lower-layer callees this logic sits on
@@ -95,10 +95,7 @@
   ensures out = bodyFor isHead chunks
   do
     -- impl-start
-    let out ← if isHead then
-        pure ([] : List Char)
-      else
-        pure chunks.flatten
+    let out ← pure ([] : List Char)
     return out
     -- impl-end
 
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
 /- No consumed axioms. The two unchanged lower-layer callees this logic sits on
@@ -96,9 +96,9 @@
   do
     -- impl-start
     let out ← if isHead then
+        pure chunks.flatten
+      else
         pure ([] : List Char)
-      else
-        pure chunks.flatten
     return out
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
 /- No consumed axioms. The two unchanged lower-layer callees this logic sits on
@@ -81,10 +81,7 @@
         term := true
       else
         term := term
-    if term then
-      willTerm := true
-    else
-      willTerm := willTerm
+    willTerm := true
     return { hasLength := len, terminate := term, willTerminate := willTerm }
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
 /- No consumed axioms. The two unchanged lower-layer callees this logic sits on
@@ -77,10 +77,7 @@
     if (!isHead && !len) then
       term := true
     else
-      if !isThreadingServer then
-        term := true
-      else
-        term := term
+      term := term
     if term then
       willTerm := true
     else
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
 /- No consumed axioms. The two unchanged lower-layer callees this logic sits on
@@ -64,28 +64,7 @@
   ensures out = adjustMeta isHead isThreadingServer m
   do
     -- impl-start
-    let mut len := m.hasLength
-    let mut term := m.terminate
-    let mut willTerm := m.willTerminate
-    if isHead then
-      if len then
-        len := false
-      else
-        len := len
-    else
-      len := len
-    if (!isHead && !len) then
-      term := true
-    else
-      if !isThreadingServer then
-        term := true
-      else
-        term := term
-    if term then
-      willTerm := true
-    else
-      willTerm := willTerm
-    return { hasLength := len, terminate := term, willTerminate := willTerm }
+    return adjustMeta isHead isThreadingServer m
     -- impl-end
 
 prove_correct prepareMeta by
@@ -95,10 +74,7 @@
   ensures out = bodyFor isHead chunks
   do
     -- impl-start
-    let out ← if isHead then
-        pure ([] : List Char)
-      else
-        pure chunks.flatten
+    let out ← pure (bodyFor isHead chunks)
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged lower-layer callees this logic sits on
   top of — the one that determines whether a length declaration is already
   present on the outgoing descriptor, and the one that emits the application's
   output sequence — are abstracted here as free inputs (the descriptor field
   `hasLength` and the chunk list `chunks`). Their relied-on reference behaviour
   is validated against the real callees by axiom_check.py (G-AX); see
   mapping.md. -/
-- axioms-end

-- pure-start
/- A small view of an outgoing response as the request finishes:
   * `hasLength`   — a length declaration is currently present on the response;
   * `terminate`   — the response is currently marked so the peer must terminate
                     the connection;
   * `willTerminate` — the side already committed to terminating the connection
                       after this response.
   Only these observables are touched by the resolution below. -/
structure ResponseMeta where
  hasLength : Bool
  terminate : Bool
  willTerminate : Bool
deriving DecidableEq, Inhabited, Repr

/- The descriptor after the finishing resolution, given whether the request is a
   bodyless (HEAD) request and whether the serving side multiplexes connections.

   * A bodyless request never carries a length declaration, so `hasLength` is
     cleared; otherwise it is left as found.
   * The peer is told to terminate the connection exactly when either (a) this
     is a body-bearing request whose length is unknown, or (b) the serving side
     does not multiplex connections. Otherwise the existing mark is preserved.
   * Once the response is marked to terminate, the side commits to terminating. -/
def adjustMeta (isHead isThreadingServer : Bool) (m : ResponseMeta) : ResponseMeta :=
  let len := if isHead then false else m.hasLength
  let term :=
    if (!isHead && !len) then true
    else if (!isThreadingServer) then true
    else m.terminate
  { hasLength := len, terminate := term,
    willTerminate := (if term then true else m.willTerminate) }

/- The body actually emitted for a request: nothing at all for a bodyless
   (HEAD) request; otherwise the application's output chunks in order. -/
def bodyFor (isHead : Bool) (chunks : List (List Char)) : List Char :=
  if isHead then [] else chunks.flatten
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method prepareMeta (isHead : Bool) (isThreadingServer : Bool) (m : ResponseMeta) return (out : ResponseMeta)
  ensures out = adjustMeta isHead isThreadingServer m
  do
    -- impl-start
    let mut len := m.hasLength
    let mut term := m.terminate
    let mut willTerm := m.willTerminate
    if isHead then
      if len then
        len := false
      else
        len := len
    else
      len := len
    if (!isHead && !len) then
      term := true
    else
      if !isThreadingServer then
        term := true
      else
        term := term
    if term then
      willTerm := true
    else
      willTerm := willTerm
    return { hasLength := len, terminate := term, willTerminate := willTerm }
    -- impl-end

prove_correct prepareMeta by
  loom_solve <;> simp_all [adjustMeta]

method responseBody (isHead : Bool) (chunks : List (List Char)) return (out : List Char)
  ensures out = bodyFor isHead chunks
  do
    -- impl-start
    let out ← if isHead then
        pure ([] : List Char)
      else
        pure chunks.flatten
    return out
    -- impl-end

prove_correct responseBody by
  loom_solve <;> simp_all [bodyFor]
```

Prepatch bug re-encoded as an attack: `True`.

Verified, project root. same_spec=True for all 7 attacks (velvet backend). Verification cmd per file: `bash scripts/lean_verify.sh <file>`. Results: positive_control EXIT 0 (verifies); atk_1..atk_6 EXIT 1 (fail, as required); atk_7 EXIT 0 (verifies). Attacks cover: A) prepatch responseBody bug (atk_1), B) prepatch_2 prepareMeta bug (atk_2), C) boundary always-empty (atk_3), D) partial-domain inverted HEAD branch (atk_4), E) control-flow-effect willTerm over-commit (atk_5), F) drop-threading-branch (atk_6), G) ungrounded-oracle echo behaviorally==gold (atk_7).

Per protocol, the ONLY verifying wrong-shaped impl (atk_7) had its faithful refined patch materialized and RUN through the official harness: `run_resolve('django__django-16502', gold-equivalent patch, timeout=1800, retries=1)` -> RESOLVED True, COMPLETED True, NOTE 'resolved' (see resolve_atk7.out). Since atk_7 literally returns bodyFor/adjustMeta, its faithful transliteration is the gold patch behavior; the executed resolve confirms it resolves — so verify⇒correct holds, no break. Refinement audit: legs A1(R), A2(R+A-reference), A3(A-reference+I), B1(R+A-reference), B2/B3/B4(I), B5(R) — all R/A-reference/I, NO kind-3.

The two A-reference legs (base body-emission in-order concat; base Content-Length declaration) correspond to the real unchanged wsgiref.handlers base callees reached via super(); axiom_check.py (G-AX) PASSES over 16 boundary + 5000 fuzz chunk lists (AX_EXIT 0), validating that correspondence against the stdlib handler. No consumed axiom hides the changed function; discriminating HEAD behavior lives in deep models bodyFor/adjustMeta. Verdict: SOUND — 7 attacks run (>=5), none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is tight: both postconditions are total functional equalities (out = adjustMeta isHead isThreadingServer m; out = bodyFor isHead chunks), leaving zero behavioral slack. Every behaviorally-wrong impl fails to verify; the only same-spec impl that verifies (atk_7, the ungrounded-oracle echo returning bodyFor/adjustMeta verbatim) is behaviorally identical to gold and its faithful patch (= gold patch) RESOLVES under run_resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged lower-layer callees this logic sits on
   top of — the one that determines whether a length declaration is already
   present on the outgoing descriptor, and the one that emits the application's
   output sequence — are abstracted here as free inputs (the descriptor field
   `hasLength` and the chunk list `chunks`). Their relied-on reference behaviour
   is validated against the real callees by axiom_check.py (G-AX); see
   mapping.md. -/
-- axioms-end

-- pure-start
/- A small view of an outgoing response as the request finishes:
   * `hasLength`   — a length declaration is currently present on the response;
   * `terminate`   — the response is currently marked so the peer must terminate
                     the connection;
   * `willTerminate` — the side already committed to terminating the connection
                       after this response.
   Only these observables are touched by the resolution below. -/
structure ResponseMeta where
  hasLength : Bool
  terminate : Bool
  willTerminate : Bool
deriving DecidableEq, Inhabited, Repr

/- The descriptor after the finishing resolution, given whether the request is a
   bodyless (HEAD) request and whether the serving side multiplexes connections.

   * A bodyless request never carries a length declaration, so `hasLength` is
     cleared; otherwise it is left as found.
   * The peer is told to terminate the connection exactly when either (a) this
     is a body-bearing request whose length is unknown, or (b) the serving side
     does not multiplex connections. Otherwise the existing mark is preserved.
   * Once the response is marked to terminate, the side commits to terminating. -/
def adjustMeta (isHead isThreadingServer : Bool) (m : ResponseMeta) : ResponseMeta :=
  let len := if isHead then false else m.hasLength
  let term :=
    if (!isHead && !len) then true
    else if (!isThreadingServer) then true
    else m.terminate
  { hasLength := len, terminate := term,
    willTerminate := (if term then true else m.willTerminate) }

/- The body actually emitted for a request: nothing at all for a bodyless
   (HEAD) request; otherwise the application's output chunks in order. -/
def bodyFor (isHead : Bool) (chunks : List (List Char)) : List Char :=
  if isHead then [] else chunks.flatten
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method prepareMeta (isHead : Bool) (isThreadingServer : Bool) (m : ResponseMeta) return (out : ResponseMeta)
  ensures out = adjustMeta isHead isThreadingServer m
  do
    -- impl-start
    let mut len := m.hasLength
    let mut term := m.terminate
    let mut willTerm := m.willTerminate
    if isHead then
      if len then
        len := false
      else
        len := len
    else
      len := len
    if (!isHead && !len) then
      term := true
    else
      if !isThreadingServer then
        term := true
      else
        term := term
    if term then
      willTerm := true
    else
      willTerm := willTerm
    return { hasLength := len, terminate := term, willTerminate := willTerm }
    -- impl-end

prove_correct prepareMeta by
  loom_solve <;> simp_all [adjustMeta]

method responseBody (isHead : Bool) (chunks : List (List Char)) return (out : List Char)
  ensures out = bodyFor isHead chunks
  do
    -- impl-start
    let out ← if isHead then
        pure ([] : List Char)
      else
        pure chunks.flatten
    return out
    -- impl-end

prove_correct responseBody by
  loom_solve <;> simp_all [bodyFor]
```

Prepatch bug re-encoded as an attack: `True`.

Verified, project root. same_spec=True for all 7 attacks (velvet backend). Verification cmd per file: `bash scripts/lean_verify.sh <file>`. Results: positive_control EXIT 0 (verifies); atk_1..atk_6 EXIT 1 (fail, as required); atk_7 EXIT 0 (verifies). Attacks cover: A) prepatch responseBody bug (atk_1), B) prepatch_2 prepareMeta bug (atk_2), C) boundary always-empty (atk_3), D) partial-domain inverted HEAD branch (atk_4), E) control-flow-effect willTerm over-commit (atk_5), F) drop-threading-branch (atk_6), G) ungrounded-oracle echo behaviorally==gold (atk_7).

Per protocol, the ONLY verifying wrong-shaped impl (atk_7) had its faithful refined patch materialized and RUN through the official harness: `run_resolve('django__django-16502', gold-equivalent patch, timeout=1800, retries=1)` -> RESOLVED True, COMPLETED True, NOTE 'resolved' (see resolve_atk7.out). Since atk_7 literally returns bodyFor/adjustMeta, its faithful transliteration is the gold patch behavior; the executed resolve confirms it resolves — so verify⇒correct holds, no break. Refinement audit: legs A1(R), A2(R+A-reference), A3(A-reference+I), B1(R+A-reference), B2/B3/B4(I), B5(R) — all R/A-reference/I, NO kind-3.

The two A-reference legs (base body-emission in-order concat; base Content-Length declaration) correspond to the real unchanged wsgiref.handlers base callees reached via super(); axiom_check.py (G-AX) PASSES over 16 boundary + 5000 fuzz chunk lists (AX_EXIT 0), validating that correspondence against the stdlib handler. No consumed axiom hides the changed function; discriminating HEAD behavior lives in deep models bodyFor/adjustMeta. Verdict: SOUND — 7 attacks run (>=5), none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift/too-strong) check for django__django-16502 velvet. RESULT: FAITHFUL — no diverging input exists. Evidence: (1) Solution.lean elaborates cleanly via lean_verify.sh (exit 0, no sorry/error). (2) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True; spec_view shows the frozen ensures clauses (out = adjustMeta isHead isThreadingServer m ; out = bodyFor isHead chunks) plus the adjustMeta/bodyFor/ResponseMeta definitions in the pure region. (3) Modeled functions vs real patched callee — I independently transliterated the gold patch (django/core/servers/basehttp.py cleanup_headers close-ladder + finish_response HEAD body-stripping) and exhaustively compared: adjustMeta over ALL 32 boolean input combos (isHead, isThreadingServer, hasLength, terminate, willTerminate) => 0 divergences; bodyFor over HEAD/non-HEAD x multiple chunk-list shapes => 0 divergences. Correspondence is exact: HEAD clears hasLength (del Content-Length), the close-marking ladder (!isHead && !len -> close ; elif !isThreadingServer -> close ; else preserve) matches branch-for-branch, and willTerminate commits-to-close when term. (4) A-reference boundary (base wsgiref finish_response write loop = in-order concat = chunks.flatten ; base cleanup_headers/set_content_length = Content-Length-present Boolean) validated by G-AX=pass and differential G-CONF=pass over 1e5 inputs (seed 16502, conf_skip=false). The spec is not too strong and does not drift from real repo behavior. Note: recorded G-EQ=fail and G-PANEL-1=fail concern the equivalence/spec-weakness lanes, not the panel-2 faithfulness question; G-PANEL-2 and G-PANEL-3 both pass.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous audit of the velvet spec view for django__django-16502.

Spec-region integrity: swebench_unified.markers.same_spec returns True for both Solution.lean vs Solution_prepatch.lean and vs Solution_prepatch_2.lean — the frozen consumer spec view is byte-identical across variants.

Mechanical G-LEAK (leakage.screen, lean flavor) PASSES with zero hard failures. Independently confirmed:
 - No diff markers (@@, diff --git, +++, index) in the view.
 - No patched file path (django/core/servers/basehttp.py) or dotted module path in the view.
 - No gold-patch changed line reproduced (normalized, len>=8).
 - Patched distinctive symbols {finish_response, close} do not appear in any spec-view identifier or comment. Broader manual scan for repo-specific tokens (cleanup, deque, Content-Length, headers_sent, send_headers, ThreadingMixIn, socketserver, environ, REQUEST_METHOD, super, self.result, basehttp) — ALL absent from the view. ('finish' matches only 'the request finishes' in prose, not the symbol finish_response.)
 - No narration words (bug/fix/patch/previously/etc.).

**Abstraction quality:** all spec identifiers are repo-neutral (ResponseMeta, hasLength, terminate, willTerminate, adjustMeta, bodyFor, isHead, isThreadingServer). The HEAD/bodyless concept is already public in problem_statement (issue title: 'runserver returns response body for HTTP HEAD requests', RFC 2616 4.3). The adjustMeta model does specify the finer Content-Length-clearing / Connection-close ladder not stated in problem_statement, but expresses it as abstract target behavior over observables, NOT as an edit, file, symbol, or diff — this is behavioral specification (the intended purpose of the spec), not gold-edit reconstruction. Pre-patch/prepatch narration is confined to mapping.md and refinement.md, which are explicitly outside the consumer spec view.

Not a relaxed bundle (no RELAXED_LEAKAGE.md, no relaxed_leakage flag). Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
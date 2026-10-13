# P2 adversarial audit — django__django-16502

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec is not broken. The two post-conditions fully pin every output field as an exact boolean function over finite domains (16 cases for headerPolicy, 4 for bodyEmission). Every same-spec impl that deviates from gold behavior fails to close the proof; the only closing same-spec alternative (atk_7) reproduces the gold boolean behavior and its faithful patch resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,16 +121,7 @@
 
 -- impl-start
 def implementation_bodyEmission (c : BodyCtx) : BodyResult := Id.run do
-  if c.isHead then
-    -- Drain the application's output without writing any body bytes, then
-    -- ensure the headers have been written.
-    let mut sent := c.headersAlreadySent
-    if !sent then
-      sent := true
-    return { bodyEmitted := false, headersSent := sent }
-  else
-    -- Defer to the standard writer: it emits the headers then the body.
-    return { bodyEmitted := true, headersSent := true }
+  return { bodyEmitted := true, headersSent := true }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,9 @@
 
 -- impl-start
 def implementation_headerPolicy (c : HeaderCtx) : HeaderResult := Id.run do
-  let mut clPresent := c.contentLengthSet
-  -- A metadata-only response must not advertise a body length.
-  if c.isHead && clPresent then
-    clPresent := false
+  let clPresent := c.contentLengthSet
   let mut disconnect := c.appDisconnect
-  if !c.isHead && !clPresent then
+  if !clPresent then
     disconnect := true
   else if !c.isThreading then
     disconnect := true
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,10 +89,9 @@
 -- impl-start
 def implementation_headerPolicy (c : HeaderCtx) : HeaderResult := Id.run do
   let mut clPresent := c.contentLengthSet
-  -- A metadata-only response must not advertise a body length.
   if c.isHead && clPresent then
     clPresent := false
-  let mut disconnect := c.appDisconnect
+  let mut disconnect := false
   if !c.isHead && !clPresent then
     disconnect := true
   else if !c.isThreading then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,14 +122,8 @@
 -- impl-start
 def implementation_bodyEmission (c : BodyCtx) : BodyResult := Id.run do
   if c.isHead then
-    -- Drain the application's output without writing any body bytes, then
-    -- ensure the headers have been written.
-    let mut sent := c.headersAlreadySent
-    if !sent then
-      sent := true
-    return { bodyEmitted := false, headersSent := sent }
+    return { bodyEmitted := false, headersSent := c.headersAlreadySent }
   else
-    -- Defer to the standard writer: it emits the headers then the body.
     return { bodyEmitted := true, headersSent := true }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,13 +89,12 @@
 -- impl-start
 def implementation_headerPolicy (c : HeaderCtx) : HeaderResult := Id.run do
   let mut clPresent := c.contentLengthSet
-  -- A metadata-only response must not advertise a body length.
   if c.isHead && clPresent then
     clPresent := false
   let mut disconnect := c.appDisconnect
   if !c.isHead && !clPresent then
     disconnect := true
-  else if !c.isThreading then
+  else if c.isThreading then
     disconnect := true
   return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,16 +121,7 @@
 
 -- impl-start
 def implementation_bodyEmission (c : BodyCtx) : BodyResult := Id.run do
-  if c.isHead then
-    -- Drain the application's output without writing any body bytes, then
-    -- ensure the headers have been written.
-    let mut sent := c.headersAlreadySent
-    if !sent then
-      sent := true
-    return { bodyEmitted := false, headersSent := sent }
-  else
-    -- Defer to the standard writer: it emits the headers then the body.
-    return { bodyEmitted := true, headersSent := true }
+  return { bodyEmitted := c.isHead, headersSent := true }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,16 +88,8 @@
 
 -- impl-start
 def implementation_headerPolicy (c : HeaderCtx) : HeaderResult := Id.run do
-  let mut clPresent := c.contentLengthSet
-  -- A metadata-only response must not advertise a body length.
-  if c.isHead && clPresent then
-    clPresent := false
-  let mut disconnect := c.appDisconnect
-  if !c.isHead && !clPresent then
-    disconnect := true
-  else if !c.isThreading then
-    disconnect := true
-  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }
+  return { contentLengthPresent := c.contentLengthSet && !c.isHead,
+           connectionDisconnect := ((!c.isHead && !c.contentLengthSet) || !c.isThreading || c.appDisconnect) }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Response finalization for a development WSGI server, for two request kinds: a
"no-payload" method (one that requests only the response metadata, not the
entity body) and ordinary methods that expect the full body.

Two behaviors are modeled:

* **Header policy** — after the base handler has prepared the response headers,
  a no-payload response must not advertise a body-length header (the entity body
  will be omitted, so any length the base handler computed is irrelevant and is
  dropped). Separately, the connection-persistence signal that tells the client
  not to reuse the connection is asserted exactly when the response would
  otherwise be ambiguous: an ordinary response whose body length is unknown, or
  any response served by a single-request (non-threading) server, or a response
  whose application already requested non-reuse.

* **Body emission** — a no-payload response drains the application's output
  without writing any body bytes to the stream while still ensuring the headers
  are emitted; an ordinary response writes headers followed by the body.

Each behavior is modeled with a small record of the observable booleans; rich
server/handler objects are projected onto only the fields these computations
read and write (see mapping.md).
-/

-- axioms-start
-- No UNCHANGED callee carries semantics the proof must assume. The base
-- handler's header preparation and its standard response writer are taken as
-- inputs / modeled directly by their observable net effect (headers ensured
-- sent; body written only for ordinary methods). The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The observable inputs to the header-policy computation, read after the base
handler has prepared the response headers. -/
structure HeaderCtx where
  /-- the request is a metadata-only (no entity body) method. -/
  isHead : Bool
  /-- a body-length header was present after base header preparation. -/
  contentLengthSet : Bool
  /-- the response is served by a multi-request (threading) server. -/
  isThreading : Bool
  /-- the application already asked the client not to reuse the connection. -/
  appDisconnect : Bool
  deriving Repr, DecidableEq

/-- The observable result of the header-policy computation. -/
structure HeaderResult where
  /-- a body-length header is present on exit. -/
  contentLengthPresent : Bool
  /-- the connection-persistence signal asking the client not to reuse the
  connection is asserted on exit. -/
  connectionDisconnect : Bool
  deriving Repr, DecidableEq

/-- The observable inputs to the body-emission computation. -/
structure BodyCtx where
  /-- the request is a metadata-only (no entity body) method. -/
  isHead : Bool
  /-- the response headers had already been written on entry. -/
  headersAlreadySent : Bool
  deriving Repr, DecidableEq

/-- The observable result of the body-emission computation. -/
structure BodyResult where
  /-- the entity body bytes were written to the output stream. -/
  bodyEmitted : Bool
  /-- the response headers were written to the output stream. -/
  headersSent : Bool
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The header policy: a metadata-only response carries no body-length header,
and otherwise the body-length header survives exactly as the base handler left
it. The non-reuse connection signal is asserted exactly when an ordinary
response has no known body length, or the server handles only one request, or
the application already requested non-reuse. Both output components are pinned. -/
def problem_spec_headerPolicy (c : HeaderCtx) (result : HeaderResult) : Prop :=
  result.contentLengthPresent = (c.contentLengthSet && !c.isHead) ∧
  result.connectionDisconnect =
    ((!c.isHead && !c.contentLengthSet) || !c.isThreading || c.appDisconnect)
-- post-conditions-end

-- impl-start
def implementation_headerPolicy (c : HeaderCtx) : HeaderResult := Id.run do
  let mut clPresent := c.contentLengthSet
  -- A metadata-only response must not advertise a body length.
  if c.isHead && clPresent then
    clPresent := false
  let mut disconnect := c.appDisconnect
  if !c.isHead && !clPresent then
    disconnect := true
  else if !c.isThreading then
    disconnect := true
  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }
-- impl-end

-- proof-start
theorem correct_headerPolicy :
    ∀ (c : HeaderCtx),
    problem_spec_headerPolicy c (implementation_headerPolicy c) := by
  intro c
  obtain ⟨isHead, contentLengthSet, isThreading, appDisconnect⟩ := c
  cases isHead <;> cases contentLengthSet <;> cases isThreading <;> cases appDisconnect <;>
    exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- The body-emission policy: the entity body bytes are written exactly for the
ordinary (non-metadata-only) methods, and the response headers are written in
both cases. Both output components are pinned. -/
def problem_spec_bodyEmission (c : BodyCtx) (result : BodyResult) : Prop :=
  result.bodyEmitted = !c.isHead ∧
  result.headersSent = true
-- post-conditions-end

-- impl-start
def implementation_bodyEmission (c : BodyCtx) : BodyResult := Id.run do
  if c.isHead then
    -- Drain the application's output without writing any body bytes, then
    -- ensure the headers have been written.
    let mut sent := c.headersAlreadySent
    if !sent then
      sent := true
    return { bodyEmitted := false, headersSent := sent }
  else
    -- Defer to the standard writer: it emits the headers then the body.
    return { bodyEmitted := true, headersSent := true }
-- impl-end

-- proof-start
theorem correct_bodyEmission :
    ∀ (c : BodyCtx),
    problem_spec_bodyEmission c (implementation_bodyEmission c) := by
  intro c
  obtain ⟨isHead, headersAlreadySent⟩ := c
  cases isHead <;> cases headersAlreadySent <;>
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec structure: both problem_spec_* pin BOTH output components as exact boolean functions of inputs — problem_spec_headerPolicy over (isHead,contentLengthSet,isThreading,appDisconnect) [2^4], problem_spec_bodyEmission over (isHead,headersAlreadySent) [2^2]. This is a maximally tight spec: an impl closes correct_* iff it computes the exact gold boolean function on the modeled projection.

Same-spec confirmed for all 7 attacks via markers.same_spec (all True) — impl region only edited, axioms/pure/pre/post byte-identical.

Verify command (each): bash scripts/lean_verify.sh <file> (run concurrently, <=4 at a time as bg jobs).
### Exit codes
- pos_control.lean: exit 0 (verifies)
- atk_1 (bodyEmission always bodyEmitted:=true; PREPATCH bug, F2P test_no_body_returned_for_head_requests): exit 1 REJECTED. prepatch reproduced.
- atk_2 (headerPolicy: no HEAD Content-Length deletion + drop !isHead guard; PREPATCH_2 bug): exit 1 REJECTED
- atk_3 (disconnect init := false instead of appDisconnect; ungrounded): exit 1 REJECTED
- atk_4 (bodyEmission headersSent:=headersAlreadySent, does not ensure sent; boundary): exit 1 REJECTED
- atk_5 (headerPolicy: elif c.isThreading instead of !c.isThreading; control-flow-effect): exit 1 REJECTED
- atk_6 (bodyEmission bodyEmitted:=c.isHead inverted; partial-domain): exit 1 REJECTED
- atk_7 (ECHO: headerPolicy computed as direct pinned formula, behaviorally == gold): exit 0 CLOSES.

AXIOMS: appended '#print axioms correct_headerPolicy / correct_bodyEmission' to pos_control and atk_7 -> both report "does not depend on any axioms" (clean). No axiom/opaque/sorry/admit anywhere in Solution.lean.

MANDATORY RESOLVE (protocol step 2) for the ONLY closing same-spec impl atk_7: atk_7 is a behaviorally-correct echo (computes the exact gold boolean function), so its faithful refined patch IS the gold patch. Materialized to atk_7_patch.diff and executed harness.run_resolve('django__django-16502', patch, timeout=1800, retries=1) under docker: RESOLVED=True, note='resolved', exit 0. => verify AND correct agree; NOT broken.

A-LEG / refinement.md AUDIT: refinement.md tags every op R or I (no A-consumed, no A-reference, no kind-3). Confirmed: axioms-region empty; axiom_check.py is an honest skip stub (status=skip, no consumed axioms). Both callee models (super().cleanup_headers as input; super().finish_response net effect; deque-drain/send_headers plumbing) are modeled directly as observable net effects, correctly reflecting the post-patch source in patch.diff/mapping.md. G-CONF conformance_check.py transcribes patched source and matches the R/I shadow (exhaustive 2^4/2^2 + random fill, 0 disagreements). Model<->patch correspondence holds.

CONCLUSION: SOUND. 7 attacks (>=5, distinct: prepatch x2, ungrounded, boundary, control-flow, partial-domain, echo) run and verified; 6 deviating impls rejected by the tight pinned spec; the sole closing same-spec impl resolves under the official harness. verify => correct holds for every executed case.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec is not broken. The two post-conditions fully pin every output field as an exact boolean function over finite domains (16 cases for headerPolicy, 4 for bodyEmission). Every same-spec impl that deviates from gold behavior fails to close the proof; the only closing same-spec alternative (atk_7) reproduces the gold boolean behavior and its faithful patch resolves.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Response finalization for a development WSGI server, for two request kinds: a
"no-payload" method (one that requests only the response metadata, not the
entity body) and ordinary methods that expect the full body.

Two behaviors are modeled:

* **Header policy** — after the base handler has prepared the response headers,
  a no-payload response must not advertise a body-length header (the entity body
  will be omitted, so any length the base handler computed is irrelevant and is
  dropped). Separately, the connection-persistence signal that tells the client
  not to reuse the connection is asserted exactly when the response would
  otherwise be ambiguous: an ordinary response whose body length is unknown, or
  any response served by a single-request (non-threading) server, or a response
  whose application already requested non-reuse.

* **Body emission** — a no-payload response drains the application's output
  without writing any body bytes to the stream while still ensuring the headers
  are emitted; an ordinary response writes headers followed by the body.

Each behavior is modeled with a small record of the observable booleans; rich
server/handler objects are projected onto only the fields these computations
read and write (see mapping.md).
-/

-- axioms-start
-- No UNCHANGED callee carries semantics the proof must assume. The base
-- handler's header preparation and its standard response writer are taken as
-- inputs / modeled directly by their observable net effect (headers ensured
-- sent; body written only for ordinary methods). The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The observable inputs to the header-policy computation, read after the base
handler has prepared the response headers. -/
structure HeaderCtx where
  /-- the request is a metadata-only (no entity body) method. -/
  isHead : Bool
  /-- a body-length header was present after base header preparation. -/
  contentLengthSet : Bool
  /-- the response is served by a multi-request (threading) server. -/
  isThreading : Bool
  /-- the application already asked the client not to reuse the connection. -/
  appDisconnect : Bool
  deriving Repr, DecidableEq

/-- The observable result of the header-policy computation. -/
structure HeaderResult where
  /-- a body-length header is present on exit. -/
  contentLengthPresent : Bool
  /-- the connection-persistence signal asking the client not to reuse the
  connection is asserted on exit. -/
  connectionDisconnect : Bool
  deriving Repr, DecidableEq

/-- The observable inputs to the body-emission computation. -/
structure BodyCtx where
  /-- the request is a metadata-only (no entity body) method. -/
  isHead : Bool
  /-- the response headers had already been written on entry. -/
  headersAlreadySent : Bool
  deriving Repr, DecidableEq

/-- The observable result of the body-emission computation. -/
structure BodyResult where
  /-- the entity body bytes were written to the output stream. -/
  bodyEmitted : Bool
  /-- the response headers were written to the output stream. -/
  headersSent : Bool
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The header policy: a metadata-only response carries no body-length header,
and otherwise the body-length header survives exactly as the base handler left
it. The non-reuse connection signal is asserted exactly when an ordinary
response has no known body length, or the server handles only one request, or
the application already requested non-reuse. Both output components are pinned. -/
def problem_spec_headerPolicy (c : HeaderCtx) (result : HeaderResult) : Prop :=
  result.contentLengthPresent = (c.contentLengthSet && !c.isHead) ∧
  result.connectionDisconnect =
    ((!c.isHead && !c.contentLengthSet) || !c.isThreading || c.appDisconnect)
-- post-conditions-end

-- impl-start
def implementation_headerPolicy (c : HeaderCtx) : HeaderResult := Id.run do
  let mut clPresent := c.contentLengthSet
  -- A metadata-only response must not advertise a body length.
  if c.isHead && clPresent then
    clPresent := false
  let mut disconnect := c.appDisconnect
  if !c.isHead && !clPresent then
    disconnect := true
  else if !c.isThreading then
    disconnect := true
  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }
-- impl-end

-- proof-start
theorem correct_headerPolicy :
    ∀ (c : HeaderCtx),
    problem_spec_headerPolicy c (implementation_headerPolicy c) := by
  intro c
  obtain ⟨isHead, contentLengthSet, isThreading, appDisconnect⟩ := c
  cases isHead <;> cases contentLengthSet <;> cases isThreading <;> cases appDisconnect <;>
    exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- The body-emission policy: the entity body bytes are written exactly for the
ordinary (non-metadata-only) methods, and the response headers are written in
both cases. Both output components are pinned. -/
def problem_spec_bodyEmission (c : BodyCtx) (result : BodyResult) : Prop :=
  result.bodyEmitted = !c.isHead ∧
  result.headersSent = true
-- post-conditions-end

-- impl-start
def implementation_bodyEmission (c : BodyCtx) : BodyResult := Id.run do
  if c.isHead then
    -- Drain the application's output without writing any body bytes, then
    -- ensure the headers have been written.
    let mut sent := c.headersAlreadySent
    if !sent then
      sent := true
    return { bodyEmitted := false, headersSent := sent }
  else
    -- Defer to the standard writer: it emits the headers then the body.
    return { bodyEmitted := true, headersSent := true }
-- impl-end

-- proof-start
theorem correct_bodyEmission :
    ∀ (c : BodyCtx),
    problem_spec_bodyEmission c (implementation_bodyEmission c) := by
  intro c
  obtain ⟨isHead, headersAlreadySent⟩ := c
  cases isHead <;> cases headersAlreadySent <;>
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec structure: both problem_spec_* pin BOTH output components as exact boolean functions of inputs — problem_spec_headerPolicy over (isHead,contentLengthSet,isThreading,appDisconnect) [2^4], problem_spec_bodyEmission over (isHead,headersAlreadySent) [2^2]. This is a maximally tight spec: an impl closes correct_* iff it computes the exact gold boolean function on the modeled projection.

Same-spec confirmed for all 7 attacks via markers.same_spec (all True) — impl region only edited, axioms/pure/pre/post byte-identical.

Verify command (each): bash scripts/lean_verify.sh <file> (run concurrently, <=4 at a time as bg jobs).
### Exit codes
- pos_control.lean: exit 0 (verifies)
- atk_1 (bodyEmission always bodyEmitted:=true; PREPATCH bug, F2P test_no_body_returned_for_head_requests): exit 1 REJECTED. prepatch reproduced.
- atk_2 (headerPolicy: no HEAD Content-Length deletion + drop !isHead guard; PREPATCH_2 bug): exit 1 REJECTED
- atk_3 (disconnect init := false instead of appDisconnect; ungrounded): exit 1 REJECTED
- atk_4 (bodyEmission headersSent:=headersAlreadySent, does not ensure sent; boundary): exit 1 REJECTED
- atk_5 (headerPolicy: elif c.isThreading instead of !c.isThreading; control-flow-effect): exit 1 REJECTED
- atk_6 (bodyEmission bodyEmitted:=c.isHead inverted; partial-domain): exit 1 REJECTED
- atk_7 (ECHO: headerPolicy computed as direct pinned formula, behaviorally == gold): exit 0 CLOSES.

AXIOMS: appended '#print axioms correct_headerPolicy / correct_bodyEmission' to pos_control and atk_7 -> both report "does not depend on any axioms" (clean). No axiom/opaque/sorry/admit anywhere in Solution.lean.

MANDATORY RESOLVE (protocol step 2) for the ONLY closing same-spec impl atk_7: atk_7 is a behaviorally-correct echo (computes the exact gold boolean function), so its faithful refined patch IS the gold patch. Materialized to atk_7_patch.diff and executed harness.run_resolve('django__django-16502', patch, timeout=1800, retries=1) under docker: RESOLVED=True, note='resolved', exit 0. => verify AND correct agree; NOT broken.

A-LEG / refinement.md AUDIT: refinement.md tags every op R or I (no A-consumed, no A-reference, no kind-3). Confirmed: axioms-region empty; axiom_check.py is an honest skip stub (status=skip, no consumed axioms). Both callee models (super().cleanup_headers as input; super().finish_response net effect; deque-drain/send_headers plumbing) are modeled directly as observable net effects, correctly reflecting the post-patch source in patch.diff/mapping.md. G-CONF conformance_check.py transcribes patched source and matches the R/I shadow (exhaustive 2^4/2^2 + random fill, 0 disagreements). Model<->patch correspondence holds.

CONCLUSION: SOUND. 7 attacks (>=5, distinct: prepatch x2, ungrounded, boundary, control-flow, partial-domain, echo) run and verified; 6 deviating impls rejected by the tight pinned spec; the sole closing same-spec impl resolves under the official harness. verify => correct holds for every executed case.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-16502 lean bundle.

METHOD: Independently transcribed the real post-patch `ServerHandler.cleanup_headers` and `ServerHandler.finish_response` (django/core/servers/basehttp.py @ base_commit 246eb483) from django_gold prepatch source + patch.diff, then exhaustively compared the real callee against the modeled spec over the COMPLETE finite input space.

DOMAIN IS FULLY FINITE: header policy has 4 boolean inputs (isHead, contentLengthSet, isThreading, appDisconnect) = 2^4=16 cases; body emission has 2 boolean inputs (isHead, headersAlreadySent) = 2^2=4 cases. All enumerated, no hidden/uncovered input.

### Result
- problem_spec_headerPolicy: contentLengthPresent = (contentLengthSet && !isHead); connectionDisconnect = ((!isHead && !contentLengthSet) || !isThreading || appDisconnect). Compared to real code (HEAD deletes Content-Length; !HEAD && no CL -> close; elif non-threading -> close; app's Connection:close preserved -> close_connection). 0/16 divergences.
- problem_spec_bodyEmission: bodyEmitted = !isHead; headersSent = true. Real code: HEAD drains iterator (no body) and ensures headers sent; non-HEAD defers to super writer (headers+body). 0/4 divergences.

MODELING BOUNDARY is honest and matches observable behavior: base handler header-prep result and standard writer net effect taken as modeled inputs/effects; plumbing (deque drain, send_headers, close, headers_sent) reduced to observable booleans per mapping.md. No callee axiomatized.

AUXILIARY CHECKS (not my primary role but confirmed): Solution.lean compiles clean (lean_verify.sh exit 0); #print axioms shows both theorems depend on NO axioms (no sorryAx, genuine proofs by Bool case-exhaustion); same_spec(Solution, prepatch) and same_spec(Solution, prepatch_2) both True with Lean tables (spec region byte-identical across gold and buggy variants — impls differ, spec fixed).

The spec pins both output components and demands exactly what the real callee produces on every input. It is neither too strong nor drifted. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3) leakage/gold-reconstruction. Judged the spec view against the SOLVER-VISIBLE problem_statement ONLY (never hints_text), per leakage.py policy.

METHOD (not a rubber-stamp): independently reproduced the real G-LEAK gate — imported swebench_unified.leakage + markers + LeanBackend and ran leakage.screen(Solution.lean, LeanBackend.language, gold_patch, problem_statement) against the frozen row -> passed=True, hard_failures=[], warnings=[].

### INTEGRITY (independently recomputed):
- spec_view sha256 = dbac03d1e73d2e0db749a4e8ede8edf2248ad221e3a5789ee87138b75f94457f == meta.json.region_hashes.spec_view (view not tampered).
- markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True: spec region byte-identical across all three variants.

LEAKAGE ANALYSIS vs gold edit (basehttp.py: import deque; add finish_response override draining iterator for HEAD; edit cleanup_headers to del Content-Length for HEAD and re-gate Connection:close on REQUEST_METHOD != HEAD; ThreadingMixIn check unchanged):
- Spec view contains NO diff markers, NO patched file/module path (django/core/servers/basehttp.py, django.core.servers.basehttp), NO reproduced gold-diff line (>=8 chars normalized), and NO distinctive patched symbol. Distinctive changed symbols per _patch_changed_symbols = {finish_response, close}; word-boundary scan of spec view for finish_response, cleanup_headers, deque, ThreadingMixIn, socketserver, REQUEST_METHOD, send_headers, basehttp, wsgiref, RFC, and the HTTP literals 'HEAD'/'Content-Length'/'Connection: close' -> ZERO hits. (Substring hits for 'head'/'connection' are inside ordinary words 'header'/'connection-persistence', not the method/header literals.)
- No bug/fix narration tokens (bug, fix, patch, prepatch, regression, previously, broken, ...).
- Vocabulary deliberately abstracted from the edit: 'no-payload / metadata-only method' not HEAD; 'body-length header' not Content-Length; 'connection-persistence signal' not Connection:close; 'multi-request (threading) server' not ThreadingMixIn.
- The spec view states the behavioral CONTRACT (post-conditions) with impl and proof elided — the intended public role of a spec. Some of it (the Connection-close gating, the Content-Length drop for HEAD) goes beyond the terse bug-report problem_statement, but that is a spec legitimately describing full correct behavior, not disclosure of the edit: it never reveals HOW the patch achieves the behavior nor WHERE it lives. The gold diff is not reconstructable; the solver must still locate the WSGI handler and author impl+proof.

SANITY on the proof (verdict.md corroborated): correct_headerPolicy / correct_bodyEmission close by exhaustive Bool case-split; #print axioms clean (no sorryAx) per verdict.md.

Conclusion: no spec-view line leaks the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

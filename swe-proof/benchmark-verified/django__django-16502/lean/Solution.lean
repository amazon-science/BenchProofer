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

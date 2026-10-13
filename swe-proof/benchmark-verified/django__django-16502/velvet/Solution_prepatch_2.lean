import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

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
    -- Pre-image skeleton: the finishing resolution does not special-case a
    -- bodyless request. The length declaration is left as found (never cleared
    -- for HEAD), and the close mark is driven purely by whether a length is
    -- declared, without the bodyless guard. The frozen spec clears the length
    -- declaration for a bodyless request, so prove_correct MUST fail.
    let mut len := m.hasLength
    let mut term := m.terminate
    let mut willTerm := m.willTerminate
    len := len
    if !len then
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

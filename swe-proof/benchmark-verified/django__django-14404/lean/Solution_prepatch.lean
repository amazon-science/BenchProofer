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
          -- Pre-patch (buggy): the redirect target is the INTERNAL routing
          -- location, dropping any leading deployment prefix.
          return Outcome.redirect (req.routingPath ++ "/")
    | none => pure ()
  return Outcome.notFound
-- impl-end

-- proof-start
theorem correct_catchAll : ∀ (req : Request) (url : String) (appendSlash : Bool),
    problem_spec_catchAll req url appendSlash
      (implementation_catchAll req url appendSlash) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end

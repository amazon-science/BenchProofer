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

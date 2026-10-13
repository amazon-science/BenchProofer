import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An axis limit ENDPOINT, as the limit machinery handles one. It is an opaque
   type carrying nothing but a linear order.

   That is deliberate, and it is the whole modelling decision: the behaviour
   under specification is ORDER-ONLY. Both operations below decide ONE
   comparison between two endpoints, hand endpoints to a callee, and report two
   of the endpoints they were given, possibly exchanged. Neither ever computes a
   NEW endpoint from old ones. Giving the carrier a field's arithmetic would
   therefore hand an implementation operations the real code does not perform,
   and any of them that happened to be the identity on the carrier while
   perturbing a real endpoint would be invisible here yet observable in the
   committed pair, which downstream callers compare exactly. An endpoint is
   consequently something that can only be COMPARED and MOVED, never combined:
   the pair an operation reports must be assembled from the endpoints it
   received, because there is no way to manufacture any other one. (mapping.md
   §2; the executable soundness checks G-AX / G-CONF run the real float code on
   both sides, where the order relation is exactly `<` on a finite float.) -/
axiom Endpoint : Type

/- Endpoints are totally ordered, and that order is the ONLY structure they
   carry. It is what both operations branch on and what the orientation clauses
   speak about; it corresponds to `<` / `>` on the finite floats the real code
   compares, which is decidable and total on them. -/
axiom instEndpointLinearOrder : LinearOrder Endpoint
attribute [instance] instEndpointLinearOrder

/- A distinguished endpoint: the origin of the axis coordinate, the value a real
   endpoint is compared against when code wants to know its SIGN. It carries no
   arithmetic either — it is simply one more endpoint that can be compared with
   the others.

   It is here because the operations below really are entitled to branch on a
   comparison against it, and a carrier that could not express such a branch
   would leave the clauses looking stronger than they are: it would make a
   partial restore, applied on only part of the requested domain, UNSAYABLE
   rather than FALSE. The clauses below are total over the carrier precisely so
   that such a partial restore is refuted where it differs, and that refutation
   is only meaningful if the partial domain can be named. -/
axiom originEndpoint : Endpoint


/- The domain-adjustment core of the shared range widener, applied to an
   ALREADY-ASCENDING pair: it hands back an interval a locator may safely use —
   the pair unchanged when the interval is wide enough to be resolvable, and a
   widened interval when it is degenerate or too tiny. Its two arguments always
   arrive in ascending order, because the member that applies it sorts them
   first.

   NOTHING about the values it returns is assumed. In particular this axiom is
   NOT the operation `defaultMemberAdjust` below is specified against: that
   operation's content is entirely about WHICH ARGUMENTS the core is applied to
   and WHICH ORDER its answer is reported in, both of which are pinned by the
   clauses, not assumed here. (Provenance + executable soundness check:
   mapping.md / axiom_check.py, G-AX. Reached imperatively through the `:|` stub
   method `expandRange` below, sound by construction.) -/
axiom expandAscending : Endpoint → Endpoint → Endpoint × Endpoint
-- axioms-end

-- pure-start

/- The pair the DEFAULT normalizer member reports for a requested pair
   `(e0, e1)`: sort the two arguments, adjust the resulting ascending interval,
   and report THAT. The order the two arguments arrived in is deliberately NOT
   reinstated — this member holds no orientation authority, so a caller that
   wants the requested orientation back has to reinstate it itself (which is
   exactly what `commitLimits` does). That division of labour is OBSERVABLE, not
   a convention: were this member to reinstate the received order as well, the
   caller's reinstatement would be a SECOND exchange of the same two endpoints
   and the committed interval would come out reversed. So the two operations are
   specified together, each pinned on its own. -/
noncomputable def defaultMemberPair (e0 e1 : Endpoint) : Endpoint × Endpoint :=
  if e1 < e0 then expandAscending e1 e0 else expandAscending e0 e1

@[grind] lemma defaultMemberPair_ordered (e0 e1 : Endpoint) (h : ¬ e1 < e0) :
    defaultMemberPair e0 e1 = expandAscending e0 e1 := by
  simp [defaultMemberPair, h]

@[grind] lemma defaultMemberPair_reversed (e0 e1 : Endpoint) (h : e1 < e0) :
    defaultMemberPair e0 e1 = expandAscending e1 e0 := by
  simp [defaultMemberPair, h]

/- The non-deterministic choice of the normalizer's result is well-posed: for any
   target value `v`, the set of values equal to `v` is non-empty (`v` itself).
   This supplies the constructive existence witness so the `:|` choice elaborates.
   It does NOT weaken verification: under demonic choice the postcondition must
   still hold for every value the predicate allows, here exactly `normalize a b`. -/
noncomputable instance findableEqPair (v : Endpoint × Endpoint) (n : Lean.Name) :
    Findable (fun e : Endpoint × Endpoint => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section

/- LAYERING — part of the specification, not of its presentation.

   The two operations specified here sit at two different levels of ONE real
   call graph. The normalizer a limit setter consults is a FAMILY of
   interchangeable members, and the member specified below is one of them, so
   the setter's level is built ON TOP of the member's level.

   The declaration order records that, and it is load-bearing. An operation can
   only name what is declared ABOVE it, so the whole VOCABULARY of the
   normalizer chain — the pure `normalize` its answer is read through, the
   `committedLimits` written in terms of that, and the imperative stub
   `normalizeRange` it is reached by — is introduced BELOW the member
   operation, at the level entitled to it. The member's level therefore has no
   name for the chain in any form, pure or imperative; the range widener is the
   only callee it can reach.

   That completeness is the whole of the argument, and a partial fence would be
   worth nothing. A member that obtained the chain's answer would be consulting
   the very family it belongs to — on the default path the member the chain
   dispatches to IS this member — so obtaining that answer re-enters the
   operation being defined and never returns. Which NAME it is obtained by
   makes no difference: the axiom and the stub denote the same callee, and in
   the code under specification there is no way to learn what that callee
   reports without running it. A model that let this level name the chain at
   all would therefore be admitting an implementation that cannot run.

   The order below is deliberate and normative: range widener stub, member
   operation, chain vocabulary, chain stub, setter operation. -/

/- The imperative range widener, reached as a callee by the default normalizer
   member. Its result is the pure `expandAscending` of its arguments; nothing
   about that value is assumed. Sound by construction (`:|`). -/
method expandRange (a : Endpoint) (b : Endpoint) return (r : Endpoint × Endpoint)
  ensures r = expandAscending a b
  do
    -- impl-start
    let r :| r = expandAscending a b
    return r
    -- impl-end

/- The DEFAULT normalizer member: turn a requested pair `(e0, e1)` into a
   well-formed interval by sorting it and adjusting the ascending pair. It must
   report the ADJUSTED ASCENDING pair, NOT the pair reordered back the way its
   arguments arrived: this member is not the holder of orientation authority, and
   a caller that reinstates the requested orientation (`commitLimits`) would
   otherwise exchange the endpoints a second time and commit a reversed interval.

   TOTAL over the carrier: every pair is in-domain, either sign, either order,
   degenerate (`e0 = e1`) included. `e0` and `e1` are read-only. -/
method defaultMemberAdjust (e0 : Endpoint) (e1 : Endpoint) return (out : Endpoint × Endpoint)
  -- P1 — the exact reported pair, over the WHOLE carrier.
  ensures out = defaultMemberPair e0 e1
  -- P2 — the load-bearing half: given a REVERSED pair, the member sorts it and
  -- reports the adjusted ascending pair. It does NOT restore the order it
  -- received, so the caller's reinstatement is the only exchange that happens.
  ensures e1 < e0 → out = expandAscending e1 e0
  -- P3 — an already-ordered (or degenerate) pair is adjusted in place.
  ensures ¬ (e1 < e0) → out = expandAscending e0 e1
  -- P4 — the same content as an ORDER fact rather than an identity, conditioned
  -- on the observable this member is not entitled to assume (whether the
  -- adjusted interval is itself ordered): whenever it is, what this member
  -- reports is ordered too, WHICHEVER way round its arguments arrived. This is
  -- the property a caller-side orientation authority relies on, and it is the
  -- one a member that reinstated the received order would violate on a
  -- reversed pair.
  ensures (defaultMemberPair e0 e1).1 ≤ (defaultMemberPair e0 e1).2 →
    out.1 ≤ out.2
  do
    -- impl-start
    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the
    -- order the arguments arrived in is not reinstated here.
    let reversed := e1 < e0
    let a := if reversed then e1 else e0
    let b := if reversed then e0 else e1
    let e ← expandRange a b
    return e
    -- impl-end

/- The normalizer chain's VOCABULARY, introduced HERE — at the level of
   the operation that is entitled to consult it, and below the member
   operation, which is not. See the LAYERING block above: the pure axiom
   and the imperative stub name the SAME callee, so a level that must not
   reach it must not be able to name it either way. -/

/- The axis normalizer the limit setter consults before committing a requested
   endpoint pair. Given a requested low/high pair it returns a "well-formed"
   interval after applying whatever domain adjustment the axis's scale asks for
   (clamping to a permitted domain, widening a degenerate interval, …).

   NOTHING about the ORDER of its two results is assumed. Which order it reports
   them in depends on the scale and on which normalizer object the axis carries:
   members of that family differ — some hand back the two values in the order
   they received them, some canonicalize the pair — and the setter is not
   entitled to either behaviour. The pair's own ordering is therefore treated as
   an OBSERVABLE: the orientation clauses of `commitLimits` below take it as a
   HYPOTHESIS about the value returned on this call, never as a promise about the
   callee. (Provenance + executable soundness check: mapping.md /
   axiom_check.py, G-AX. This models a callee, not the operation under spec; the
   callee is imperative, so it is reached through the `:|` stub method
   `normalizeRange` below, sound by construction, while the bare `axiom` gives
   the pure view the spec is stated against.) -/
axiom normalize : Endpoint → Endpoint → Endpoint × Endpoint

/- The intended committed endpoints for a requested pair `(lo, hi)`: take the
   normalizer's well-formed interval, and — if the request was descending
   (`lo > hi`) — commit its two endpoints exchanged, so the committed interval
   carries the requested orientation. When the request was not descending the
   normalizer's interval is committed exactly as reported. This is the
   per-request expansion the operation must realise. -/
noncomputable def committedLimits (lo hi : Endpoint) : Endpoint × Endpoint :=
  let n := normalize lo hi
  if lo > hi then (n.2, n.1) else (n.1, n.2)

@[grind] lemma committedLimits_ascending (lo hi : Endpoint) (h : ¬ lo > hi) :
    committedLimits lo hi = normalize lo hi := by
  simp [committedLimits, h]

@[grind] lemma committedLimits_descending (lo hi : Endpoint) (h : lo > hi) :
    committedLimits lo hi = ((normalize lo hi).2, (normalize lo hi).1) := by
  simp [committedLimits, h]

/- The imperative axis normalizer, reached as a callee. It returns a well-formed
   interval whose value is the pure `normalize` of its arguments; the ORDER of
   that pair's two components is left entirely open. Sound by construction
   (`:|`). -/
method normalizeRange (a : Endpoint) (b : Endpoint) return (r : Endpoint × Endpoint)
  ensures r = normalize a b
  do
    -- impl-start
    let r :| r = normalize a b
    return r
    -- impl-end

/- Commit a requested axis limit pair `(lo, hi)` to the view, going through the
   axis normalizer that turns it into a well-formed interval. The requested
   ORIENTATION must survive that round trip: the committed pair is the
   normalizer's pair with its two endpoints exchanged exactly when the request
   was descending (`lo > hi`), and as the normalizer reported them otherwise.
   Preserving the orientation is therefore this operation's responsibility, and
   it must read the orientation off the REQUESTED endpoints — once the normalizer
   has answered, its pair no longer records which way round the request was.

   The operation is TOTAL over the carrier: every requested pair is in-domain,
   of either sign and in either order, degenerate (`lo = hi`) included. There is
   no precondition. The same commit block is reached whatever scale the axis
   carries, and on a scale whose permitted domain is the whole line a requested
   endpoint may legitimately be zero or negative; a precondition confining the
   request to positive endpoints would leave the operation unconstrained on
   requests it really receives.

   `lo` and `hi` are read-only requested values (not `mut`); the operation
   derives the committed pair and the inputs are unchanged. -/
method commitLimits (lo : Endpoint) (hi : Endpoint) return (out : Endpoint × Endpoint)
  -- Q1 — the exact committed pair, over the WHOLE carrier. `committedLimits`
  -- only re-arranges the normalizer's own two components, so this pins the
  -- operation's behaviour without pinning any concrete endpoint value.
  ensures out = committedLimits lo hi
  -- Q2 / Q3 — the same content branch by branch, spelled against the
  -- normalizer's result directly: a descending request commits that pair
  -- exchanged, every other request commits it as reported.
  ensures (lo > hi) → out = ((normalize lo hi).2, (normalize lo hi).1)
  ensures (lo ≤ hi) → out = normalize lo hi
  -- Q4 / Q5 — orientation preservation, conditioned on the normalizer's OWN
  -- output order, the observable this operation is not entitled to assume:
  -- WHENEVER the normalizer reported its pair ascending, a descending request
  -- commits a (weakly) descending interval and a strictly ascending request
  -- commits a (weakly) ascending one.
  ensures (normalize lo hi).1 ≤ (normalize lo hi).2 → (lo > hi) → out.2 ≤ out.1
  ensures (normalize lo hi).1 ≤ (normalize lo hi).2 → (lo < hi) → out.1 ≤ out.2
  -- Q6 — and the correspondence runs both ways, not just one: when the
  -- normalizer's reported interval is non-degenerate, the committed interval is
  -- descending IF AND ONLY IF the request was.
  ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
  do
    -- impl-start
    -- Read the requested orientation BEFORE consulting the normalizer: its
    -- answer no longer records which way round the request was.
    let swapped := lo > hi
    let n ← normalizeRange lo hi
    -- Commit the normalizer's endpoints in the requested orientation.
    let out := if swapped then (n.2, n.1) else (n.1, n.2)
    return out
    -- impl-end

end

prove_correct expandRange by
  loom_solve

prove_correct defaultMemberAdjust by
  loom_solve

prove_correct normalizeRange by
  loom_solve

prove_correct commitLimits by
  loom_solve <;>
    intros <;>
    split <;>
    simp_all [asymm, not_lt] <;>
    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)

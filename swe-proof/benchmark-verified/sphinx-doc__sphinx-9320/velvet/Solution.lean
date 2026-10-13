import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The unchanged path primitives the strict path-name validator is built from,
   the one boundary fact each of them has, and the one fact about WHERE the
   expansion answers at all.

   `expansionAnswers` says whether ASKING for the home-directory expansion of THIS
   entry hands an answer back at all; `rawExpansion` is that expansion, which can
   only be read where it answers; `pathIsDir` models the directory test applied to
   an expanded entry.

   WHICH OF THESE IS TOTAL — AND WHY THAT IS IN THE TERMS RATHER THAN IN THIS
   COMMENT. `pathIsDir` and `expansionAnswers` are TOTAL: each answers for every
   input, reading one answers nothing else, and neither can take control away from
   whoever reads it (mapping.md §1 binds them to a directory test that reports
   `false` rather than taking control away, and to asking whether the expansion
   answered). THE EXPANSION ITSELF IS NOT TOTAL. Where `expansionAnswers` does not
   hold, control leaves whoever asked for the expansion and does not come back:
   there is no expansion for anyone to read, test or discard. That is why
   `rawExpansion` takes a PROOF that the entry is one the expansion answers for —
   reading the expansion is an act that has to be EARNED, at whatever entry it is
   read — and why the freely readable form below, `pathExpanded`, carries that
   guard in the term itself instead of a promise in a comment. A program may read
   `pathExpanded` at any entry it likes, including one it derives from its own
   input; what it reads there is the GUARDED expansion, so a refinement of that
   read carries the guard too (mapping.md §1.1).

   Beyond its boundary fact no primitive carries any contract — nothing is assumed
   about which entries expand to what, which expansions name a directory, or which
   entries the expansion answers for beyond the empty one.

   `expansionAnswers_empty`: expanding an empty entry answers.
   `pathIsDir_empty`: the empty entry names no directory.
   `rawExpansion_empty`: expanding an empty entry yields the empty entry. -/
opaque pathIsDir : List Char → Bool
opaque expansionAnswers : List Char → Bool

axiom pathIsDir_empty : pathIsDir [] = false
axiom expansionAnswers_empty : expansionAnswers [] = true

opaque rawExpansion : (entry : List Char) → expansionAnswers entry = true → List Char

axiom rawExpansion_empty (answered : expansionAnswers [] = true) :
  rawExpansion [] answered = []

/- The expansion as any program may READ it: the GUARDED expansion. Reading this
   is free and total — at an entry the expansion answers for it IS the expansion,
   and at any other entry it is the empty entry, which is a value and not an
   answer. Two things follow, and the whole refinement of a read turns on them.
   First, the guard is part of this definition, so refining a read of it refines
   the guard as well (mapping.md §1.1): there is no reading of it anywhere, at any
   entry, that can take control away. Second, `expansionAnswers` is opaque and
   only ever known at the empty entry, so no program can show any particular entry
   to be outside the guard, and nothing can be concluded from the `[]` in the
   second branch. -/
def pathExpanded (entry : List Char) : List Char :=
  if answered : expansionAnswers entry = true then rawExpansion entry answered else []

/- Expanding an empty entry yields the empty entry: the empty entry is one the
   expansion answers for (`expansionAnswers_empty`) and its expansion is itself
   (`rawExpansion_empty`). A THEOREM, not a further assumption. -/
theorem pathExpanded_empty : pathExpanded [] = [] := by
  simp [pathExpanded, expansionAnswers_empty, rawExpansion_empty]

/- The strict validator's ACCEPTANCE DECISION as a pure predicate: it accepts an
   entry exactly when the guarded expansion of that entry names an existing
   directory. Deciding is free and TOTAL — it reads the two total primitives above
   through the guarded expansion and returns a `Bool`, so it can be decided
   anywhere, for any entry, in any order, and a decision taken at an entry the
   expansion does not answer for reads the guarded value rather than taking control
   away from the decider. On the obligation's domain this `Bool` IS the strict
   validator's decision; off that domain it is not, and nothing below reads it as
   one. Deciding acceptance is therefore a different operation from SUBMITTING an
   entry to the strict validator, which is declared below and which does not answer
   at all for an entry it does not accept. -/
def strictAccepts (entry : List Char) : Bool := pathIsDir (pathExpanded entry)

/- An empty entry is never accepted by the strict validator: the two boundary
   facts together say the expansion of an empty entry names no directory. This is
   why an empty entry needs a lenient layer at all — the strict validator on its
   own can never let one through. The empty entry is in the obligation's domain
   (`expansionAnswers_empty`), so this is a statement about a governed entry. -/
theorem strictAccepts_empty : strictAccepts [] = false := by
  simp [strictAccepts, pathExpanded_empty, pathIsDir_empty]

/- ACCEPTANCE IMPLIES DOMAIN MEMBERSHIP. If the guarded expansion of an entry
   names a directory then that entry is one the expansion answers for: off the
   domain the guarded expansion is the empty entry (that is what `pathExpanded`
   is) and the empty entry names no directory (`pathIsDir_empty`), so no entry
   outside the domain is ever accepted. A THEOREM, derived from the guard and one
   boundary fact — nothing further is assumed.

   This is what makes the guard honest in both directions, and it is why a program
   may ACT on an acceptance it decided at an entry the `require` says nothing
   about: whatever entry it derived, showing that entry accepted also shows it is
   in the domain, so the submission it earns is one the real callee answers.
   The real code satisfies the same implication for the same reason —
   `os.path.isdir` of the guarded expansion can only be true where the expansion
   answered — and axiom_check.py measures exactly that at every accepted read,
   at the entry and at a derived one (mapping.md §1.1).

   Note the direction. Being in the domain does NOT imply being accepted, so this
   gives away no part of the accept/turn-away decision; it only says the two
   guards on a submission are not independent. -/
theorem accepted_in_domain (entry : List Char) :
    strictAccepts entry = true → expansionAnswers entry = true := by
  intro accepted
  by_cases answered : expansionAnswers entry = true
  · exact answered
  · simp [strictAccepts, pathExpanded, answered, pathIsDir_empty] at accepted

/- SUBMITTING an entry to the strict path-name validator. The strict validator is
   an UNCHANGED helper — invoked here, never redefined — and it is NOT a function
   from entries to outcomes. For an entry it accepts it hands back the expanded
   entry. For an entry it does not accept it hands back nothing at all: control
   leaves whoever submitted the entry and does not return to it, so there is no
   outcome for that submitter to read, test or discard.

   It is therefore declared as an opaque PROGRAM rather than as a value, and what
   is assumed about it is exactly the two halves of that description:

     `strictPathValidator_accepted`  — on an entry the expansion answers for and
       the validator accepts, a submission is just the expanded entry, handed
       straight back;
     `strictPathValidator_turns_away` — on an entry it does not accept, there is
       no guarantee that a submission finishes at all, which is the modeled form
       of control never coming back. This one is unguarded on purpose: an entry
       the expansion does not answer for takes control away from the submitter
       inside the validator, so a submission carries no guarantee of coming back
       there either.

   Two consequences worth stating, because the whole obligation below turns on
   them. First, submitting is OBSERVABLE — an act a program has to EARN. There is
   no total function underneath and no body to unfold, so a submission can appear
   in a program that verifies only where that entry is shown to be ACCEPTED at the
   point it is handed over — which by `accepted_in_domain` also shows it is one the
   expansion answers for, so the two halves of `strictPathValidator_accepted` are
   earned together; a program that hands over an entry it cannot show accepted has
   no guarantee to offer there, whatever value it would have gone on to compute.
   That is true of an entry it derived from its own input as much as of the input
   itself: a derived submission is earnable exactly when the derived entry is shown
   accepted, and never otherwise. Second, deciding
   acceptance is NOT submitting: `strictAccepts` above is free and answers
   everywhere — at every entry, including derived ones, because the expansion it
   reads is the guarded one — so a program may consult it as often as it likes, at
   whatever entry it likes, and in any order. Consulting the decision is free;
   acting on an entry the decision has not accepted is not.

   The facts are jointly satisfiable — a submission that answers with the expanded
   entry on exactly the accepted entries the expansion answers for, and never
   comes back otherwise, meets both — so nothing below is established from an
   impossible assumption. A concrete Lean-checked model of all five assumed facts
   is recorded in refinement.md §D.

   `strictPathValidator_hands_back` is the contract the obligation below is
   discharged against. It is a THEOREM, derived from the two facts, not a further
   assumption.

   Provenance of every assumed fact, and the executable soundness check of each
   against the real unchanged callee (an empty entry's expansion answers and is
   not accepted; an accepted entry comes back as its expansion, verbatim; an entry
   that is not accepted does not come back; neither does one whose expansion does
   not answer): mapping.md §3 / axiom_check.py (G-AX). -/
opaque strictPathValidator : List Char → VelvetM (List Char)

axiom strictPathValidator_accepted (entry : List Char) :
  expansionAnswers entry = true →
  strictAccepts entry = true →
  strictPathValidator entry = pure (pathExpanded entry)

axiom strictPathValidator_turns_away (entry : List Char) :
  strictAccepts entry = false →
  ¬ triple (l := Prop) True (strictPathValidator entry) (fun _ => True)

@[loomSpec]
theorem strictPathValidator_hands_back (entry : List Char) :
  triple (with_name_prefix `submission_earned
      (expansionAnswers entry = true ∧ strictAccepts entry = true))
    (strictPathValidator entry)
    (fun out => with_name_prefix `hands_back_expanded (out = pathExpanded entry)) := by
  unfold triple
  intro earned
  rw [strictPathValidator_accepted entry earned.1 earned.2, wp_pure]
-- axioms-end

-- pure-start
-- pure-end

-- pre-conditions-start
/- The one domain restriction: the entry must be one the expansion answers for
   (`expansionAnswers entry = true`). Inside that domain every entry has a pinned
   outcome — the empty entry is accepted as the empty value and every other entry
   gets the strict validator's own verdict — and none is left to an
   implementation's discretion, including every entry the strict validator turns
   away. Outside it there is no outcome to pin: asking for the expansion takes
   control away from whoever asked, so the entry has no accepted value and no
   turn-away either, and neither this obligation nor any other of this shape (an
   outcome for every entry) could be faithful there. The restriction is therefore
   the boundary of what is specifiable rather than a convenience, and it is a
   restriction on the ENTRY alone: it says nothing about which entries the
   validator accepts, so the whole accept/turn-away decision stays inside the
   obligation. The empty entry — the entry the change is about — is in the domain
   by `expansionAnswers_empty`, not by assumption. -/
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Validate an optional path entry.

   Desired behavior, for an entry the expansion answers for: an empty entry is an
   ACCEPTED sentinel — it is returned verbatim (here, accepted as the empty value)
   and it is never submitted to the strict validator, so that an empty entry can
   serve as a deliberate "no path / leave" signal rather than being turned away.
   Any non-empty entry is governed by the strict validator: it is accepted,
   carrying the expanded entry, exactly where the strict validator accepts it, and
   turned away everywhere else.

   This is the missing behavior the public problem statement reports: when the
   strict validator alone governs the entry, an empty entry is turned away and
   the prompt can never be satisfied by leaving it empty; routing the empty entry
   around the strict validator lets it be accepted and acted upon. Routing AROUND
   is a statement about which submissions happen and not only about which value
   comes out, and that is why the strict validator is modeled as a submission
   with a precondition rather than as a value to read: an empty entry has to be
   accepted here without the strict validator being handed anything at all, and
   no program that hands it an entry it cannot show is accepted can verify.

   `entry` is the read-only input (not `mut`): the validator computes an outcome
   and mutates no input (directive 5). It is modeled as a `List Char` (a string
   is a sequence of code points; an empty string is the empty list); the outcome
   is `Except Unit (List Char)` — `error` = the entry is turned away, `ok v` = the
   entry `v` is accepted (mapping.md §2). The `require` is the domain of the whole
   obligation and is discussed in the pre-conditions region above: an outcome is
   claimed for exactly the entries the expansion answers for. -/
method optionalPathValidator (entry : List Char)
    return (out : Except Unit (List Char))
  require expansionAnswers entry = true
  ensures entry = [] → out = Except.ok []
  ensures entry ≠ [] →
    out = (if strictAccepts entry then Except.ok (pathExpanded entry)
           else Except.error ())
  do
    -- impl-start
    -- An empty entry is accepted verbatim and is never handed to the strict
    -- validator. A non-empty entry the strict validator accepts is submitted to
    -- it and comes back as the accepted value; one it does not accept is turned
    -- away.
    if entry = [] then
      return Except.ok []
    else
      if strictAccepts entry then
        let accepted ← strictPathValidator entry
        return Except.ok accepted
      else
        return Except.error ()
    -- impl-end

prove_correct optionalPathValidator by
  loom_solve

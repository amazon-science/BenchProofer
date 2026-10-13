import Velvet.Std
-- imports-end

-- Total-correctness semantics: the modeled display computation is a straight-line
-- ladder that always terminates and produces the banner text, so an
-- implementation that diverges (e.g. loops forever instead of producing the
-- expanded address) must NOT verify. Partial correctness would vacuously admit
-- such non-terminating implementations.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no deep-model references. The operation is a
--  pure, total computation over a flag and a character sequence — square-bracket
--  wrapping, a single literal-equality test, and string literals — every step of
--  which is directly expressible. There is no unchanged callee whose behaviour
--  the proof must assume, so the `axioms` region is intentionally empty.)
-- axioms-end

-- pure-start
/- The display form of a network host shown in a server's startup banner.

   Three cases, decided in order:
     * a host flagged as already being in delimited (bracketed) literal form is
       wrapped in a pair of square brackets, so it reads back as a single host
       token in a URL;
     * otherwise, the unspecified-host shorthand "0" is expanded to its
       canonical dotted-quad form "0.0.0.0", so the printed address is one a
       browser can actually follow;
     * any other host is shown exactly as given.

   The middle case is the behaviour of interest: the bare "0" shorthand must be
   normalised to "0.0.0.0" for display, while every other (non-bracketed) host
   is passed through unchanged. -/
def displayAddress (bracketed : Bool) (host : List Char) : List Char :=
  if bracketed then ['['] ++ host ++ [']']
  else if host = "0".toList then "0.0.0.0".toList
  else host
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Format a host for display in a startup banner. The two inputs are read-only:
   neither the bracket flag nor the host sequence is mutated (none is `mut`;
   directive 5). The result is pinned exactly to `displayAddress`, so no
   implementation that disagrees on any (flag, host) pair can verify.

   Alongside the exact-equality postcondition, the three observable branches are
   each pinned to a witnessed input combination: a bracketed host is wrapped; a
   non-bracketed host equal to the "0" shorthand becomes "0.0.0.0"; any other
   non-bracketed host is returned verbatim. -/
method formatHost (bracketed : Bool) (host : List Char) return (out : List Char)
  ensures out = displayAddress bracketed host
  ensures bracketed = true → out = ['['] ++ host ++ [']']
  ensures (bracketed = false ∧ host = "0".toList) → out = "0.0.0.0".toList
  ensures (bracketed = false ∧ host ≠ "0".toList) → out = host
  do
    -- impl-start
    -- Pre-image skeleton: the display form is only the bracket-wrapping branch;
    -- a non-bracketed host (including the bare "0" shorthand) is shown verbatim,
    -- with no expansion of "0" to "0.0.0.0". The frozen spec requires that
    -- expansion, so prove_correct MUST fail on the "0" clause.
    if bracketed then
      return ['['] ++ host ++ [']']
    else
      return host
    -- impl-end

prove_correct formatHost by
  loom_solve <;> simp_all [displayAddress]

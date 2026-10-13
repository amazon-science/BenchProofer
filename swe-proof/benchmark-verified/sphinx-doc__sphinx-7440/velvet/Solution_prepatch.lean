import Velvet.Std
-- imports-end

/- Total correctness: the real registration-key computation always terminates
   (it is a straight-line pass of the term's text to the registry), so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The cross-reference key under which a glossary term is recorded in the
   project-wide object registry, and under which that registry later reports it.
   It is the term's own text, taken exactly as written — character-for-character,
   with case preserved. Modeled as the identity on the term text: registering a
   term named `t` records it under `t` and reports it back as `t`.

   The registry itself (record-a-name / enumerate-recorded-names) is an unchanged
   community component; that it stores and yields a name verbatim — case included
   — is its identity-on-name contract, validated against the real component by
   axiom_check.py (G-AX). See mapping.md §3. -/
@[grind] def registeredKey (termText : List Char) : List Char := termText
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method registerGlossaryName (termText : List Char) return (out : List Char)
  ensures out = registeredKey termText
  do
    -- impl-start
    -- Pre-image skeleton: the key handed to the registry is case-folded to
    -- lower case before recording, so a term written `TERM2` is recorded (and
    -- reported) under `term2`. The frozen spec requires the verbatim key
    -- (registeredKey = the term text as written), so prove_correct MUST fail.
    return termText.map Char.toLower
    -- impl-end

prove_correct registerGlossaryName by
  loom_solve

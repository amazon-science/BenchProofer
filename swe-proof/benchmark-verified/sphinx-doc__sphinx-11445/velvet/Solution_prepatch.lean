import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Whether a single text line is recognised by the strict line-classifier this
   module relies on (a standard reStructuredText line-classification grammar).

   A line is classified when it begins with ':' immediately followed by a
   character that is neither ':' nor a space, and then — scanning forward over
   the remaining characters — a ':' is reached that is *terminated* (it is the
   last character, or the next character is a space) while the character just
   before that closing ':' is not a space. A ':' that is immediately followed by
   a backtick does NOT terminate the marker (so an inline cross-reference such
   as `:role:` followed by a backtick is rejected). A backslash escapes the
   following character (the escaped character cannot act as a closing ':' or
   terminator). Provenance + executable soundness check: mapping.md /
   axiom_check.py (G-AX validates this model against the real classifier). -/
def metaScan : List Char → Char → Bool
  | [], _ => false
  | c :: cs, prev =>
    if c = ':' then
      match cs with
      | [] => decide (prev ≠ ' ')
      | d :: _ =>
        if d = ' ' then decide (prev ≠ ' ')
        else if d = '`' then false
        else metaScan cs c
    else if c = '\\' then
      match cs with
      | [] => false
      | _ :: ds => metaScan ds (cs.headD ' ')
    else
      metaScan cs c

/- A line is a metadata line when it starts with ':' followed by a non-space,
   non-colon character, and the forward scan from that point finds a terminating
   ':'. The leading ':' serves as the scan's initial predecessor character. -/
def isMetadataLine : List Char → Bool
  | [] => false
  | [_] => false
  | a :: b :: rest =>
    if a = ':' && b ≠ ':' && b ≠ ' ' then metaScan (b :: rest) ':' else false

/- The number of leading lines (a prefix run) that are metadata lines: count
   from the front, stopping at the first line that is not a metadata line.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def leadingMetadata : List (List Char) → Nat
  | []          => 0
  | line :: rest => if isMetadataLine line then 1 + leadingMetadata rest else 0

@[grind] lemma leadingMetadata_nil : leadingMetadata [] = 0 := rfl
@[grind] lemma leadingMetadata_cons (line : List Char) (rest : List (List Char)) :
    leadingMetadata (line :: rest)
      = (if isMetadataLine line then 1 + leadingMetadata rest else 0) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The drop-step: dropping `i` instead of `i+1` exposes the line at index `i`
   on the front. The single goal `loom_solve` leaves for the loop body. -/
lemma drop_step (content : List (List Char)) (i : Nat) (hlt : i < content.length) :
    content.drop i = content[i]! :: content.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  rw [h]

/- One forward step: when the line at `i` is a metadata line, `leadingMetadata`
   of the suffix peels one off. -/
lemma leadingMetadata_step (content : List (List Char)) (i : Nat)
    (h : i < content.length) (hp : isMetadataLine content[i]!) :
    leadingMetadata (content.drop i) = 1 + leadingMetadata (content.drop (i + 1)) := by
  rw [drop_step content i h, leadingMetadata_cons, if_pos hp]

/- Termination: when the loop stops (suffix exhausted, or the current line is
   not a metadata line), the remaining prefix run is empty. -/
lemma leadingMetadata_stop (content : List (List Char)) (i : Nat)
    (h : i ≤ content.length)
    (hd : i = content.length ∨ ¬ isMetadataLine content[i]!) :
    leadingMetadata (content.drop i) = 0 := by
  by_cases hi : i = content.length
  · subst hi; rw [List.drop_length, leadingMetadata_nil]
  · have hlt : i < content.length := lt_of_le_of_ne h hi
    rw [drop_step content i hlt, leadingMetadata_cons, if_neg]
    rcases hd with h1 | h2
    · exact absurd h1 hi
    · simpa using h2

method countLeadingMetadataLines (content : List (List Char)) return (pos : Nat)
  ensures pos = leadingMetadata content
  do
    -- impl-start
    -- PRE-PATCH (buggy) skeleton: the loop advances over every line accepted by
    -- the LOOSE classifier — a line that starts with ':' then a run of word
    -- characters then ':' — instead of the strict classifier `isMetadataLine`
    -- the frozen spec counts via `leadingMetadata`. The loose test wrongly
    -- accepts a leading cross-reference role marker (':role:`…`'), so on such a
    -- document `pos` over-counts and `pos = leadingMetadata content` fails:
    -- `prove_correct` MUST NOT close (G-DIFF).
    let looseMetadataLine : List Char → Bool := fun line =>
      match line with
      | ':' :: rest =>
          let word := rest.takeWhile (fun c => c.isAlpha || c.isDigit || c = '_')
          !word.isEmpty && ((rest.drop word.length).headD ' ' == ':')
      | _ => false
    let mut i := 0
    while i < content.length ∧ looseMetadataLine content[i]!
      invariant i ≤ content.length
      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
      decreasing content.length - i
    do
      i := i + 1
    return i
    -- impl-end

prove_correct countLeadingMetadataLines by
  loom_solve
  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
      at invariant_2
    omega
  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
    omega

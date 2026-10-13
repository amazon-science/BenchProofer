import Mathlib
-- imports-end

/-!
Encoding a message into Morse code.

A message is a sequence of characters. It is read as a series of WORDS separated
by word breaks (the space and the other ASCII blank characters). Each character
that the standard alphabet supports contributes its Morse code word — a short
sequence of dot/dash symbols, written here with `'.'` and `'-'`. A character the
alphabet does NOT support contributes nothing at all: it is passed over, and the
characters around it stay in the same word.

The authoritative code-word table is the standard International Morse alphabet:
the 26 Latin letters, the ten decimal digits, and a handful of punctuation
marks. For the decimal digits the standard code words are

  `0 = -----`, `1 = .----`, `2 = ..---`, `3 = ...--`, `4 = ....-`,
  `5 = .....`, `6 = -....`, `7 = --...`, `8 = ---..`, `9 = ----.`

Anything outside that table — a `'#'`, a `'%'`, a `'^'`, a `'&'` — has no code
word and so is simply absent from the output.

The encoded message is assembled at two levels. Within a word, the code words of
the supported characters appear in the order they occur, joined by ONE copy of
the separator. Between words, the encoded words are joined by TWO copies of it. A
word contributing no code word at all — one written entirely in unsupported
characters — is not represented in the output and produces no word break of its
own. Finally, if the message ends in a word break, the output ends in one more
doubled separator.

The separator is a character SEQUENCE chosen by the caller, of any length: the
empty sequence, a single character, or several. Only one family is excluded — a
separator consisting of exactly one character that the alphabet already has a
code word for, or that is the space marking a word break, since then a reader
could not tell a separator from the signal it delimits. The same code-word table
is used regardless of a character's position.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The authoritative
-- per-character code-word table is modeled DEEPLY as the concrete function
-- `charMorse` (in the `pure` region) — it is the standard data the modeled
-- behavior is specified against, not a callee to axiomatize. The word split,
-- the pass-over of unsupported characters and the separator-joined assembly are
-- expressed directly over the input sequence, so the spec needs no
-- `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The authoritative International Morse code-word table: each supported
character is mapped to its standard dot/dash code word (as a `List Char`);
unsupported characters map to `none`. This is the SPECIFICATION of the
encoding (the standard alphabet), independent of any particular program. -/
def charMorse : Char → Option (List Char)
  | 'A' => some ".-".toList
  | 'B' => some "-...".toList
  | 'C' => some "-.-.".toList
  | 'D' => some "-..".toList
  | 'E' => some ".".toList
  | 'F' => some "..-.".toList
  | 'G' => some "--.".toList
  | 'H' => some "....".toList
  | 'I' => some "..".toList
  | 'J' => some ".---".toList
  | 'K' => some "-.-".toList
  | 'L' => some ".-..".toList
  | 'M' => some "--".toList
  | 'N' => some "-.".toList
  | 'O' => some "---".toList
  | 'P' => some ".--.".toList
  | 'Q' => some "--.-".toList
  | 'R' => some ".-.".toList
  | 'S' => some "...".toList
  | 'T' => some "-".toList
  | 'U' => some "..-".toList
  | 'V' => some "...-".toList
  | 'W' => some ".--".toList
  | 'X' => some "-..-".toList
  | 'Y' => some "-.--".toList
  | 'Z' => some "--..".toList
  | '0' => some "-----".toList
  | '1' => some ".----".toList
  | '2' => some "..---".toList
  | '3' => some "...--".toList
  | '4' => some "....-".toList
  | '5' => some ".....".toList
  | '6' => some "-....".toList
  | '7' => some "--...".toList
  | '8' => some "---..".toList
  | '9' => some "----.".toList
  | '.' => some ".-.-.-".toList
  | ',' => some "--..--".toList
  | ':' => some "---...".toList
  | ';' => some "-.-.-.".toList
  | '?' => some "..--..".toList
  | '-' => some "-....-".toList
  | '_' => some "..--.-".toList
  | '(' => some "-.--.".toList
  | ')' => some "-.--.-".toList
  | '\'' => some ".----.".toList
  | '=' => some "-...-".toList
  | '+' => some ".-.-.".toList
  | '/' => some "-..-.".toList
  | '@' => some ".--.-.".toList
  | '$' => some "...-..-".toList
  | '!' => some "-.-.--".toList
  | _   => none

/-- Total standard code-word lookup: the standard code word of a supported
character, or the empty sequence for an unsupported one. -/
def morseOf (c : Char) : List Char := (charMorse c).getD []

/-- A word break: the space, and the other ASCII blank characters (tab, line
feed, carriage return, vertical tab, form feed). These separate the message
into words; they are never part of a word. -/
def isWordBreak (c : Char) : Bool :=
  c.toNat = 32 || (9 ≤ c.toNat && c.toNat ≤ 13)

/-- The characters the encoding is specified over: the printable ASCII range
together with the ASCII blanks. Outside it, whether a character counts as a word
break is not settled by this alphabet, so the message is left unconstrained
there. -/
def isModeledChar (c : Char) : Bool :=
  (32 ≤ c.toNat && c.toNat ≤ 126) || (9 ≤ c.toNat && c.toNat ≤ 13)

/-- Which separators the encoding is specified for. Any sequence will do — empty,
one character, or several — EXCEPT a sequence of exactly one character that the
alphabet already gives a code word to, or that is the space marking a word break:
such a separator could not be told apart from the signal it delimits, and the
encoding is not defined for it. -/
def isUsableSep (sep : List Char) : Bool :=
  match sep with
  | [c] => (charMorse c).isNone && c != ' '
  | _   => true

/-- The message split into words at every word break. Word breaks are consumed;
a run of them yields the empty words between them, and a message that begins or
ends in a break yields an empty word at that end. -/
def wordRuns : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
      if isWordBreak c then [] :: wordRuns cs
      else match wordRuns cs with
           | []      => [[c]]
           | w :: ws => (c :: w) :: ws

/-- Whether the message's last character is a word break (false for the empty
message). -/
def endsInWordBreak (msg : List Char) : Bool :=
  match msg.getLast? with
  | some c => isWordBreak c
  | none   => false

/-- The words that are actually represented in the output: each word of the
message with its unsupported characters passed over, keeping the supported ones
in order, and then those words that retain at least one supported character. A
word whose characters are all unsupported contributes nothing. -/
def supportedWords (msg : List Char) : List (List Char) :=
  ((wordRuns msg).map (fun w => w.filter (fun c => (charMorse c).isSome))).filter
    (fun w => w ≠ [])
-- pure-end

-- post-conditions-start
/-- The encoded message is fully pinned to the input. Each represented word is
its supported characters' standard code words `morseOf c`, in order, joined by
ONE copy of `sep`; those encoded words are joined by TWO copies of `sep`; and a
message ending in a word break contributes one further doubled `sep`. Every
character with no standard code word is absent from the result and contributes no
separator, and a word with no supported character at all is absent together with
its word break. The separator enters the result only through those joins, whatever
its length. No output component is left free — the whole result is determined by
the message and the separator. -/
def problem_spec_encodeMorse
    (sep : List Char) (msg : List Char) (result : List Char) : Prop :=
  result =
    List.intercalate (sep ++ sep)
        ((supportedWords msg).map (fun w => List.intercalate sep (w.map morseOf)))
      ++ (if endsInWordBreak msg then sep ++ sep else [])
-- post-conditions-end

-- impl-start
/-- The decoding table the program stores: for each code word it holds, the
character that code word stands for. This is the program's own data; the
per-character table the encoder consults is derived from it by inversion. -/
def morseTable : List (List Char × Char) :=
  [
   (".-".toList, 'A'), ("-...".toList, 'B'), ("-.-.".toList, 'C'),
   ("-..".toList, 'D'), (".".toList, 'E'), ("..-.".toList, 'F'),
   ("--.".toList, 'G'), ("....".toList, 'H'), ("..".toList, 'I'),
   (".---".toList, 'J'), ("-.-".toList, 'K'), (".-..".toList, 'L'),
   ("--".toList, 'M'), ("-.".toList, 'N'), ("---".toList, 'O'),
   (".--.".toList, 'P'), ("--.-".toList, 'Q'), (".-.".toList, 'R'),
   ("...".toList, 'S'), ("-".toList, 'T'), ("..-".toList, 'U'),
   ("...-".toList, 'V'), (".--".toList, 'W'), ("-..-".toList, 'X'),
   ("-.--".toList, 'Y'), ("--..".toList, 'Z'), ("-----".toList, '0'),
   (".----".toList, '1'), ("..---".toList, '2'), ("...--".toList, '3'),
   ("....-".toList, '4'), (".....".toList, '5'), ("-....".toList, '6'),
   ("--...".toList, '7'), ("---..".toList, '8'), ("----.".toList, '9'),
   (".-.-.-".toList, '.'), ("--..--".toList, ','), ("---...".toList, ':'),
   ("-.-.-.".toList, ';'), ("..--..".toList, '?'), ("-....-".toList, '-'),
   ("..--.-".toList, '_'), ("-.--.".toList, '('), ("-.--.-".toList, ')'),
   (".----.".toList, '\''), ("-...-".toList, '='), (".-.-.".toList, '+'),
   ("-..-.".toList, '/'), (".--.-.".toList, '@'), ("...-..-".toList, '$'),
   ("-.-.--".toList, '!')]

/-- The program's own code-word table (the lookup the encoder actually uses). -/
def codeMorse : Char → Option (List Char)
  | 'A' => some ".-".toList
  | 'B' => some "-...".toList
  | 'C' => some "-.-.".toList
  | 'D' => some "-..".toList
  | 'E' => some ".".toList
  | 'F' => some "..-.".toList
  | 'G' => some "--.".toList
  | 'H' => some "....".toList
  | 'I' => some "..".toList
  | 'J' => some ".---".toList
  | 'K' => some "-.-".toList
  | 'L' => some ".-..".toList
  | 'M' => some "--".toList
  | 'N' => some "-.".toList
  | 'O' => some "---".toList
  | 'P' => some ".--.".toList
  | 'Q' => some "--.-".toList
  | 'R' => some ".-.".toList
  | 'S' => some "...".toList
  | 'T' => some "-".toList
  | 'U' => some "..-".toList
  | 'V' => some "...-".toList
  | 'W' => some ".--".toList
  | 'X' => some "-..-".toList
  | 'Y' => some "-.--".toList
  | 'Z' => some "--..".toList
  | '0' => some "-----".toList
  | '1' => some ".----".toList
  | '2' => some "..---".toList
  | '3' => some "...--".toList
  | '4' => some "....-".toList
  | '5' => some ".....".toList
  | '6' => some "-....".toList
  | '7' => some "--...".toList
  | '8' => some "---..".toList
  | '9' => some "----.".toList
  | '.' => some ".-.-.-".toList
  | ',' => some "--..--".toList
  | ':' => some "---...".toList
  | ';' => some "-.-.-.".toList
  | '?' => some "..--..".toList
  | '-' => some "-....-".toList
  | '_' => some "..--.-".toList
  | '(' => some "-.--.".toList
  | ')' => some "-.--.-".toList
  | '\'' => some ".----.".toList
  | '=' => some "-...-".toList
  | '+' => some ".-.-.".toList
  | '/' => some "-..-.".toList
  | '@' => some ".--.-.".toList
  | '$' => some "...-..-".toList
  | '!' => some "-.-.--".toList
  | _   => none

/-- The encoder's total per-character lookup. -/
def codeOf (c : Char) : List Char := (codeMorse c).getD []

def implementation_encodeMorse
    (sep : List Char) (msg : List Char) : List Char := Id.run do
  -- Within each word keep only the characters the table has an entry for, and
  -- drop a word that retains nothing.
  let mut kept : List (List Char) := []
  for w in wordRuns msg do
    let supported := w.filter (fun c => (codeMorse c).isSome)
    kept := kept ++ (if supported ≠ [] then [supported] else [])
  -- Render each surviving word as its code words joined by one copy of the
  -- separator.
  let mut encoded : List (List Char) := []
  for w in kept do
    encoded := encoded ++ [List.intercalate sep (w.map codeOf)]
  -- Join the words by a doubled separator, and add one if the message ended in
  -- a word break.
  return List.intercalate (sep ++ sep) encoded
           ++ (if endsInWordBreak msg then sep ++ sep else [])
-- impl-end

-- proof-start
/-- The obligation has five clauses.

(1) The encoding itself: on a message drawn from the alphabet the encoding is
specified over, and a usable separator, the result is the value
`problem_spec_encodeMorse` pins.

(2) The encoder observed on EVERY character of the whole `Char` type, through the
single-character messages — the only messages on which the modeled word split and
the real one are guaranteed to agree, because a lone character is either a word
break (the split yields no word, and the trailing-break suffix supplies
`sep ++ sep`) or a non-break character (the program emits its code word, and
drops it when it has none).

(3) and (4) The stored table holds EXACTLY the standard alphabet's code words and
no others: every code word it stores stands for the character the standard
alphabet gives that code word (3), and every standard code word is stored for its
own character (4). These are obligations in their own right, because an encoding
is not the whole of what this table determines. The same stored data also settles
which code words have a meaning AT ALL, and it must give a meaning to precisely
the standard ones — a stored code word outside the standard alphabet would
acquire a reading it must not have. Clauses (1) and (2) cannot see that: a code
word can be stored for a character that no encoding ever emits — a word break,
say, which the split consumes before any lookup — so no message reveals it.

(5) The encoder's per-character table is drawn from that same stored data:
whenever it gives a character a code word, the stored table records that code word
for that character. This is what ties (3) and (4) to the encoder — the two are one
body of data, not two independent tables. It is stated away from the space, whose
entry the encoder takes from the separator rather than from the stored alphabet. -/
theorem correct_encodeMorse :
    (∀ (sep : List Char) (msg : List Char),
        (∀ c ∈ msg, isModeledChar c) → isUsableSep sep = true →
        problem_spec_encodeMorse sep msg (implementation_encodeMorse sep msg))
    ∧ (∀ (sep : List Char) (c : Char),
        isUsableSep sep = true →
        problem_spec_encodeMorse sep [c] (implementation_encodeMorse sep [c]))
    ∧ (∀ p ∈ morseTable, charMorse p.2 = some p.1)
    ∧ (∀ (c : Char) (w : List Char), charMorse c = some w → (w, c) ∈ morseTable)
    ∧ (∀ (c : Char) (w : List Char),
        c ≠ ' ' → codeMorse c = some w → (w, c) ∈ morseTable) := by
  have codeOf_eq : codeOf = morseOf := by
    funext c
    unfold codeOf morseOf
    cases c using Char.rec with
    | _ => rfl
  have tblf : (fun c => (codeMorse c).isSome) = (fun c => (charMorse c).isSome) := by
    funext c
    cases c using Char.rec with
    | _ => rfl
  have keepLoop : ∀ (ws acc : List (List Char)),
      (forIn ws acc (fun w r => (pure (ForInStep.yield
          (r ++ (if w.filter (fun c => (codeMorse c).isSome) ≠ [] then
                   [w.filter (fun c => (codeMorse c).isSome)] else []))) : Id _)))
        = acc ++ ((ws.map (fun w => w.filter (fun c => (codeMorse c).isSome))).filter
                    (fun w => w ≠ [])) := by
    intro ws
    induction ws with
    | nil => intro acc; simp; rfl
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn as (acc ++ (if a.filter (fun c => (codeMorse c).isSome) ≠ [] then
              [a.filter (fun c => (codeMorse c).isSome)] else []))
              (fun w r => (pure (ForInStep.yield
                (r ++ (if w.filter (fun c => (codeMorse c).isSome) ≠ [] then
                         [w.filter (fun c => (codeMorse c).isSome)] else []))) : Id _))) = _
      rw [ih]
      simp only [List.map_cons, List.filter_cons]
      -- branch on whether this word retains a supported character, with the
      -- filtered word abstracted so the branch is a plain list case split
      generalize hgen : a.filter (fun c => (codeMorse c).isSome) = fa
      cases fa with
      | nil => simp
      | cons x xs => simp [List.append_assoc]
  have renderLoop : ∀ (sep : List Char) (ws acc : List (List Char)),
      (forIn ws acc (fun w r => (pure (ForInStep.yield
          (r ++ [List.intercalate sep (w.map codeOf)])) : Id _)))
        = acc ++ ws.map (fun w => List.intercalate sep (w.map codeOf)) := by
    intro sep ws
    induction ws with
    | nil => intro acc; simp; rfl
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn as (acc ++ [List.intercalate sep (a.map codeOf)])
              (fun w r => (pure (ForInStep.yield
                (r ++ [List.intercalate sep (w.map codeOf)])) : Id _))) = _
      rw [ih]
      simp [List.append_assoc]
  -- the modeled behaviour holds for EVERY message and separator; the two
  -- clauses are the two instances of it the obligation states
  have main : ∀ (sep : List Char) (msg : List Char),
      problem_spec_encodeMorse sep msg (implementation_encodeMorse sep msg) := by
    intro sep msg
    unfold problem_spec_encodeMorse implementation_encodeMorse supportedWords
    simp only [Id.run, bind]
    rw [keepLoop]
    simp only [List.nil_append]
    rw [renderLoop]
    simp only [List.nil_append, codeOf_eq]
    rw [tblf]
    rfl
  refine ⟨fun sep msg _ _ => main sep msg, fun sep c _ => main sep [c], ?_, ?_, ?_⟩
  -- (3) every stored code word stands for the character the standard alphabet
  -- gives it
  · intro p hp
    fin_cases hp <;> rfl
  -- (4) every standard code word is stored for its own character
  · intro c w h
    unfold charMorse at h
    split at h <;> first | (injection h with h; subst h; decide) | simp at h
  -- (5) the encoder's table is drawn from the stored data
  · intro c w _ h
    unfold codeMorse at h
    split at h <;> first | (injection h with h; subst h; decide) | simp at h
-- proof-end

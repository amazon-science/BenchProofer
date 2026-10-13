import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no consumed axioms. The operation under spec —
--  recovering the literal text carried by ONE column-width record of a value
--  written across several such records — is modeled DEEPLY below as concrete
--  code over `List Char`. The upstream machinery that breaks a value into
--  records and the downstream whole-value decode are unchanged and out of
--  scope; bridged in mapping.md and exercised by conformance_check.py
--  (G-CONF). No contract is assumed.)
-- axioms-end

-- pure-start
/- A record's alphabet: the delimiter that bookends the record's content and
   that may also stand, doubled, inside it; the character the record is padded
   out to its column width with; the character that introduces the optional
   annotation a record may carry after its content; and the line break a record
   may be terminated by. -/
def quoteCh : Char := '\''
def spaceCh : Char := ' '
def annotCh : Char := '/'
def breakCh : Char := '\n'

/- The characters a record's content is drawn from: the printable range of the
   record character set, `' '` through `'~'`. A record's content holds nothing
   outside that range, so text carrying such a character is not the content of a
   record. -/
def isContentChar (c : Char) : Bool := spaceCh ≤ c && c ≤ '~'

/- Remove the right padding: drop every trailing pad character. Expressed via
   `reverse` so the "from the end" direction is explicit. -/
def rstripSpaces (s : List Char) : List Char :=
  (s.reverse.dropWhile (· = spaceCh)).reverse

/- A record that is not the final one of a run carries a single trailing
   continuation marker `&`; recovering the literal text drops exactly that one
   marker when present. -/
def dropTrailingAmp (s : List Char) : List Char :=
  if s.getLast? = some '&' then s.dropLast else s

/- Everything a record may still hold once its content is over: padding, and
   then at most an annotation — which, once introduced, runs to the end of the
   record — or else the single line break a record may be terminated by. -/
def onlyPaddingThenAnnotation (rest : List Char) : Bool :=
  match rest.dropWhile (· = spaceCh) with
  | [] => true
  | c :: more => c == annotCh || (c == breakCh && more.isEmpty)

/- `rest` opens with the delimiter that CLOSES the content of a record: a
   delimiter past which the record holds nothing but padding and at most an
   annotation. -/
def closesContent (rest : List Char) : Bool :=
  match rest with
  | c :: more => c == quoteCh && onlyPaddingThenAnnotation more
  | [] => false

/- Generic scan over a record's content characters: the shortest NON-EMPTY
   prefix of `l` that is made of content characters ONLY and whose remainder
   satisfies `p`, if `l` has one. The caller supplies what it is scanning for;
   the scan stops dead at the first character a record's content cannot hold. -/
def firstPrefix (p : List Char → Bool) : List Char → Option (List Char)
  | [] => none
  | c :: rest =>
      if !isContentChar c then none
      else if p rest then some [c]
      else
        match firstPrefix p rest with
        | some pre => some (c :: pre)
        | none => none

/- The content of one record, read off the record's own grammar: the content is
   bookended by delimiters, is drawn from the record character set, and the
   delimiter that closes it is one past which the record holds only padding and
   at most an annotation. `none` when the text is not a record at all — no
   delimiter in it closes a content. -/
def recordContent : List Char → Option (List Char)
  | [] => some []
  | c :: rest =>
      if c == quoteCh then
        match firstPrefix closesContent rest with
        | some content => some content
        | none => if closesContent rest then some [] else none
      else if onlyPaddingThenAnnotation (c :: rest) then some [] else none

/- Left-to-right, non-overlapping rewrite of each doubled delimiter (`''`) to a
   single one. This collapse belongs to the WHOLE-VALUE decode performed once,
   downstream, after every record's text has been concatenated; it is defined
   here only so the per-record recovery can state, by its ABSENCE, that it does
   NOT perform this rewrite on a single record. -/
def collapseDoubledQuotes : List Char → List Char
  | c₁ :: c₂ :: rest =>
      if c₁ = quoteCh ∧ c₂ = quoteCh then quoteCh :: collapseDoubledQuotes rest
      else c₁ :: collapseDoubledQuotes (c₂ :: rest)
  | rest => rest

/- The literal text carried by ONE record of a value written across several
   records: take the record's content, then remove the right padding and a
   single trailing continuation marker when present. Text that is not a record
   at all yields no literal text (`none`) — it is handled elsewhere, unchanged.

   The content is otherwise taken VERBATIM — every character of it, a doubled
   delimiter (`''`) included, is preserved exactly as it stands. Collapsing a
   doubled delimiter to a single one is the business of the single whole-value
   decode performed downstream, once, after all record texts are concatenated,
   NOT of this per-record step. -/
def recovered (field : List Char) : Option (List Char) :=
  (recordContent field).map (fun content => dropTrailingAmp (rstripSpaces content))

@[grind] lemma recovered_def (field : List Char) :
    recovered field
      = (recordContent field).map (fun content =>
          dropTrailingAmp (rstripSpaces content)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Recover the literal text carried by one record of a value written across
   several column-width records.

   A record holds its content bookended by delimiters, is right-padded out to a
   column width, and may carry an annotation past the delimiter that closes its
   content; a non-final record's content additionally ends in a single
   continuation marker. Recovering the literal text reads the record's content
   off that grammar, removes the padding and the continuation marker — and
   otherwise preserves the content EXACTLY, so that the per-record results can
   be concatenated and decoded once as a whole. In particular the recovery must
   not rewrite any character of the content: a doubled delimiter (`''`) inside
   the content stays a doubled delimiter here. Text that is not a record at all
   yields no literal text.

   `field` is the record. It is consulted but not `mut`; a fresh value is
   produced and the input is not mutated (directive 5). -/
method recoverSegmentText (field : List Char) return (out : Option (List Char))
  ensures out = recovered field
  do
    -- impl-start
    -- The record's content read with a WEAKER close test: a delimiter counts as
    -- closing the content as soon as the very next character is padding or the
    -- annotation introducer, instead of requiring that only padding and at most
    -- an annotation follow it; and any text is then taken to be a record.
    let closesEarly : List Char → Bool := fun rest =>
      match rest with
      | c :: more =>
          c == quoteCh &&
            (match more with
             | [] => true
             | d :: _ => d == spaceCh || d == annotCh)
      | [] => false
    let contentEarly : List Char → List Char := fun f =>
      match f with
      | [] => []
      | c :: rest =>
          if c == quoteCh then
            match firstPrefix closesEarly rest with
            | some content => content
            | none => []
          else []
    let out : Option (List Char) :=
      some (
        let content : List Char := contentEarly field
        let trimmed : List Char := (content.reverse.dropWhile (· = spaceCh)).reverse
        if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed)
    return out
    -- impl-end

prove_correct recoverSegmentText by
  loom_solve
  simp only [recovered, dropTrailingAmp, rstripSpaces]

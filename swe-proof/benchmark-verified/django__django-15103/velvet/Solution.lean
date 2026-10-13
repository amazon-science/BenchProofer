import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The JSON-encoding of the payload and the escaping of
--  the identifier are unchanged operations, taken as plain inputs: `content` is
--  the already-encoded, already-safe payload text and `identifier` is the
--  already-escaped identifier text. The operation under specification only
--  decides the surrounding markup, so neither input is produced here.)
-- axioms-end

-- pure-start
/- The constant markup fragments of the wrapper. The payload is placed inside a
   `<script type="application/json"> … </script>` element. An identifier, when
   present, is carried by an extra `id="…"` attribute. -/
def scriptClose : List Char := "</script>".toList

/- The opening tag WITHOUT an identifier attribute. -/
def openPlain : List Char := "<script type=\"application/json\">".toList

/- The opening tag WITH the identifier attribute carrying `identifier`. -/
def openWithId (identifier : List Char) : List Char :=
  "<script id=\"".toList ++ identifier ++ "\" type=\"application/json\">".toList

/- The element produced when no identifier is supplied: the payload wrapped in a
   bare script element, with no `id` attribute at all. -/
def wrapNoId (content : List Char) : List Char :=
  openPlain ++ content ++ scriptClose

/- The element produced when an identifier is supplied: the payload wrapped in a
   script element carrying that identifier in an `id` attribute. -/
def wrapWithId (identifier content : List Char) : List Char :=
  openWithId identifier ++ content ++ scriptClose
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap an encoded payload in a `<script type="application/json">` element.

   The element may optionally carry an identifier. The identifier is optional:
   supplying an empty identifier means "no identifier", in which case the result
   is the bare element with NO `id` attribute. When a non-empty identifier is
   supplied, the result additionally carries that identifier in an `id`
   attribute.

   `identifier` and `content` are read-only inputs (neither is `mut`): the
   routine derives the markup and alters nothing (directive 5). Both the
   identifier and the encoded payload are modeled as per-code-point strings
   (`List Char`); the empty identifier `[]` is the "no identifier" case
   (mapping.md §2). -/
method jsonScriptTag (identifier : List Char) (content : List Char) return (out : List Char)
  ensures identifier = []  → out = wrapNoId content
  ensures identifier ≠ []  → out = wrapWithId identifier content
  do
    -- impl-start
    if identifier = [] then
      return wrapNoId content
    else
      return wrapWithId identifier content
    -- impl-end

prove_correct jsonScriptTag by
  loom_solve

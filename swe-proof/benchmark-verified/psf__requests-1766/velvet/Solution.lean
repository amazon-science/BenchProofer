import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none — the protection-directive segment is assembled deeply from the
--  caller-supplied count/client-nonce sequences and constant character
--  literals; no opaque library callee is invoked on this path, so there is
--  nothing to axiomatize or G-AX-check.)
-- axioms-end

-- pure-start
/- The quality-of-protection value emitted as a QUOTED string: an opening
   double quote, the four characters of the token `auth`, and a closing double
   quote. This is the value form RFC 2617 mandates for the qop-options
   directive (a quoted string of tokens) rather than a bare token. -/
def quotedValueToken : List Char := ['"', 'a', 'u', 't', 'h', '"']

/- The literal head of the directive segment up to the count value:
   `, qop=` then the QUOTED value token then `, nc=`. -/
def directiveHead : List Char :=
  [',', ' ', 'q', 'o', 'p', '='] ++ quotedValueToken ++ [',', ' ', 'n', 'c', '=']

/- The literal between the count value and the client-nonce value:
   `, cnonce="` (the client-nonce being a quoted string as well). -/
def directiveMid : List Char := [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']

/- The literal closing the client-nonce value: a single double quote. -/
def directiveTail : List Char := ['"']

/- The whole directive segment appended when a quality-of-protection token is
   present: the literal head (carrying the QUOTED value token `"auth"`), the
   count value emitted bare, the literal mid, the client-nonce value, and the
   closing quote. -/
def qopSegment (ncvalue cnonce : List Char) : List Char :=
  directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail

@[grind] lemma directiveHead_def :
    directiveHead =
      [',', ' ', 'q', 'o', 'p', '='] ++ quotedValueToken ++ [',', ' ', 'n', 'c', '='] := rfl

@[grind] lemma qopSegment_def (ncvalue cnonce : List Char) :
    qopSegment ncvalue cnonce =
      directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method appendQopDirective (base : List Char) (ncvalue : List Char) (cnonce : List Char) return (out : List Char)
  ensures out = base ++ qopSegment ncvalue cnonce
  ensures (out.drop base.length).take directiveHead.length = directiveHead
  ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
  do
    -- impl-start
    let mut result : List Char := base
    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
    result := result ++ [',', ' ', 'n', 'c', '=']
    -- the count value, bare (no surrounding quotes)
    result := result ++ ncvalue
    -- ', cnonce="'
    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
    -- the client-nonce value
    result := result ++ cnonce
    -- closing double quote
    result := result ++ ['"']
    return result
    -- impl-end

prove_correct appendQopDirective by
  loom_solve <;> simp_all [qopSegment, directiveHead, directiveMid, directiveTail, quotedValueToken]
